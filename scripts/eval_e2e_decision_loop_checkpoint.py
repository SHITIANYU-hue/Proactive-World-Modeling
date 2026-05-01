"""Run an end-to-end PIWM decision-loop evaluation with a Qwen-VL checkpoint.

Unlike ``eval_ms_swift_checkpoint.py``, this script does not score isolated
training rows with gold intermediate state. It starts from state-inference rows
that contain only visual frames/history, asks the model to infer perception,
then feeds the model's own structured perception into deliberation/action
selection. This matches the deployed guide loop more closely:

    frames -> perception -> per-action transition -> action choice
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from piwm_data import rules
from piwm_infer import config as infer_config
from piwm_infer.parsers import (
    MalformedOutputError,
    parse_action_output,
    parse_deliberation_output,
    parse_perception_output,
)
from piwm_train import config as train_config
from piwm_train.prompts import (
    PIWM_SYSTEM_PROMPT,
    build_action_prompt,
    build_deliberation_prompt,
    build_perception_prompt,
)


def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def _resolve_images(paths: list[str], root: Path, image_limit: int | None) -> list[str]:
    if image_limit is not None:
        paths = paths[:image_limit]
    resolved = []
    for path in paths:
        image_path = Path(path)
        if not image_path.is_absolute():
            image_path = root / image_path
        if not image_path.exists():
            raise FileNotFoundError(f"image not found: {image_path}")
        resolved.append(image_path.resolve().as_posix())
    return resolved


def _messages(prompt: str, images: list[str], max_pixels: int | None) -> list[dict[str, Any]]:
    text = (
        prompt
        .replace("<image>", "")
        .replace(train_config.IMAGE_PLACEHOLDER, "")
        .strip()
    )
    content: list[dict[str, Any]] = []
    for image in images:
        item: dict[str, Any] = {"type": "image", "image": image}
        if max_pixels is not None:
            item["max_pixels"] = max_pixels
        content.append(item)
    content.append({"type": "text", "text": text})
    return [
        {"role": "system", "content": PIWM_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def _generate(model, processor, prompt: str, images: list[str], args: argparse.Namespace, max_new_tokens: int) -> str:
    messages = _messages(prompt, images, args.max_pixels)
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)
    with torch.inference_mode():
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    prompt_len = inputs["input_ids"].shape[-1]
    generated_ids = generated_ids[:, prompt_len:]
    return processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def _primary_structured_block(raw: str) -> str:
    return raw.split("\n[recap]", 1)[0].strip()


def _predicted_state_summary(row: dict[str, Any], perception: dict[str, Any]) -> dict[str, Any]:
    persona_summary = row.get("input", {}).get("persona_summary", "unknown")
    persona_type = persona_summary.split(":", 1)[0] if isinstance(persona_summary, str) else "unknown"
    return {
        "aida_stage": perception["aida_stage"],
        "state_subtype": "predicted_by_perception",
        "state": "predicted_by_perception",
        "intent": perception["bdi"]["intention"],
        "bdi": perception["bdi"],
        "proactive_score": perception["proactive_score"],
        "persona_type": persona_type,
        "observable_cues": [],
    }


def _deliberation_row(row: dict[str, Any], perception: dict[str, Any], action: str) -> dict[str, Any]:
    return {
        "input": {
            "frames": row["input"].get("frames", []),
            "current_state_summary": _predicted_state_summary(row, perception),
            "candidate_action": action,
        }
    }


def _action_row(row: dict[str, Any], perception: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "meta": {
            "frames": row["input"].get("frames", []),
            "state_summary": _predicted_state_summary(row, perception),
            "candidate_block": candidates,
        }
    }


def _gold(row: dict[str, Any]) -> dict[str, Any]:
    output = row.get("output", {})
    return {
        "aida_stage": output.get("aida_stage"),
        "proactive_score": output.get("proactive_score"),
        "candidate_actions": output.get("candidate_actions", []),
        "best_action": output.get("best_action"),
    }


def _safe_action_fallback(candidates: list[str]) -> str:
    if infer_config.FALLBACK_ACTION_ON_PARSE_ERROR in candidates:
        return infer_config.FALLBACK_ACTION_ON_PARSE_ERROR
    return candidates[0] if candidates else infer_config.FALLBACK_ACTION_ON_PARSE_ERROR


def _highest_reward_action(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    return min(rows, key=lambda row: (-float(row["reward"]), rules.ACTIONS.index(row["action"])))["action"]


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    rows = _read_jsonl(args.state_jsonl, args.limit)
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=True)
    base = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16 if args.torch_dtype == "bfloat16" else torch.float16,
        device_map=args.device_map,
        trust_remote_code=True,
    )
    if args.checkpoint is not None:
        model = PeftModel.from_pretrained(base, args.checkpoint)
        checkpoint = str(args.checkpoint)
        label = args.eval_label or "piwm_sft_e2e"
    else:
        model = base
        checkpoint = None
        label = args.eval_label or "base_e2e"
    model.eval()

    outputs: list[dict[str, Any]] = []
    totals = {
        "perception_parse_ok": 0,
        "action_parse_ok": 0,
        "fallback": 0,
        "strategy_correct": 0,
        "stage_correct": 0,
        "score_correct": 0,
        "candidates_exact": 0,
        "chosen_in_gold_candidates": 0,
    }
    n_delib_attempted = 0
    n_delib_parsed = 0

    start_time = time.time()
    partial_path = args.out.with_suffix(args.out.suffix + ".partial")

    for index, row in enumerate(rows, start=1):
        state_id = row.get("state_id", "unknown")
        gold = _gold(row)
        images = _resolve_images(row["input"].get("frames", []), root, args.image_limit)
        record: dict[str, Any] = {
            "state_id": state_id,
            "gold": gold,
            "images": images,
            "perception_raw": None,
            "perception": None,
            "candidate_predictions": [],
            "action_raw": None,
            "chosen_action": None,
            "used_fallback": False,
            "errors": [],
        }

        try:
            perception_raw = _generate(
                model,
                processor,
                build_perception_prompt(row),
                images,
                args,
                args.max_new_tokens_perception,
            )
            record["perception_raw"] = perception_raw
            perception = parse_perception_output(_primary_structured_block(perception_raw))
            record["perception"] = perception
            totals["perception_parse_ok"] += 1
            totals["stage_correct"] += int(perception["aida_stage"] == gold["aida_stage"])
            totals["score_correct"] += int(perception["proactive_score"] == gold["proactive_score"])
            totals["candidates_exact"] += int(perception["candidate_actions"] == gold["candidate_actions"])
        except (MalformedOutputError, RuntimeError, ValueError, FileNotFoundError) as exc:
            record["errors"].append(f"perception:{type(exc).__name__}: {exc}")
            record["chosen_action"] = infer_config.FALLBACK_ACTION_ON_PARSE_ERROR
            record["used_fallback"] = True
            totals["fallback"] += 1
            outputs.append(record)
            _maybe_log_progress(index, len(rows), totals, n_delib_attempted, n_delib_parsed, start_time, args)
            _maybe_write_partial(partial_path, index, len(rows), label, checkpoint, outputs, totals, n_delib_attempted, n_delib_parsed, args)
            continue

        predicted_candidates = list(perception["candidate_actions"])
        if perception["proactive_score"] <= args.silence_threshold:
            chosen = _safe_action_fallback(predicted_candidates)
            record["chosen_action"] = chosen
            record["used_fallback"] = True
            totals["fallback"] += 1
            totals["chosen_in_gold_candidates"] += int(chosen in set(gold["candidate_actions"]))
            totals["strategy_correct"] += int(chosen == gold["best_action"])
            outputs.append(record)
            _maybe_log_progress(index, len(rows), totals, n_delib_attempted, n_delib_parsed, start_time, args)
            _maybe_write_partial(partial_path, index, len(rows), label, checkpoint, outputs, totals, n_delib_attempted, n_delib_parsed, args)
            continue

        candidate_rows: list[dict[str, Any]] = []
        for action in predicted_candidates[: args.max_actions]:
            n_delib_attempted += 1
            try:
                delib_raw = _generate(
                    model,
                    processor,
                    build_deliberation_prompt(_deliberation_row(row, perception, action)),
                    images,
                    args,
                    args.max_new_tokens_deliberation,
                )
                delib = parse_deliberation_output(_primary_structured_block(delib_raw))
                n_delib_parsed += 1
                candidate_rows.append(
                    {
                        "action": action,
                        "next_aida_stage": delib["next_aida_stage"],
                        "risk": delib["risk"],
                        "benefit": delib["benefit"],
                        "reward": delib["reward"],
                        "raw": delib_raw,
                    }
                )
            except (MalformedOutputError, RuntimeError, ValueError) as exc:
                record["errors"].append(f"deliberation:{action}:{type(exc).__name__}: {exc}")
            finally:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        record["candidate_predictions"] = candidate_rows
        if not candidate_rows:
            chosen = _safe_action_fallback(predicted_candidates)
            record["chosen_action"] = chosen
            record["used_fallback"] = True
            totals["fallback"] += 1
            totals["chosen_in_gold_candidates"] += int(chosen in set(gold["candidate_actions"]))
            totals["strategy_correct"] += int(chosen == gold["best_action"])
            outputs.append(record)
            _maybe_log_progress(index, len(rows), totals, n_delib_attempted, n_delib_parsed, start_time, args)
            _maybe_write_partial(partial_path, index, len(rows), label, checkpoint, outputs, totals, n_delib_attempted, n_delib_parsed, args)
            continue

        try:
            action_raw = _generate(
                model,
                processor,
                build_action_prompt(_action_row(row, perception, candidate_rows)),
                images,
                args,
                args.max_new_tokens_action,
            )
            record["action_raw"] = action_raw
            parsed_action = parse_action_output(
                _primary_structured_block(action_raw),
                valid_actions={candidate["action"] for candidate in candidate_rows},
            )
            chosen = parsed_action["chosen"]
            totals["action_parse_ok"] += 1
        except (MalformedOutputError, RuntimeError, ValueError) as exc:
            record["errors"].append(f"action:{type(exc).__name__}: {exc}")
            chosen = _highest_reward_action(candidate_rows) or _safe_action_fallback(predicted_candidates)
            record["used_fallback"] = True
            totals["fallback"] += 1

        record["chosen_action"] = chosen
        totals["chosen_in_gold_candidates"] += int(chosen in set(gold["candidate_actions"]))
        totals["strategy_correct"] += int(chosen == gold["best_action"])
        outputs.append(record)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        _maybe_log_progress(index, len(rows), totals, n_delib_attempted, n_delib_parsed, start_time, args)
        _maybe_write_partial(partial_path, index, len(rows), label, checkpoint, outputs, totals, n_delib_attempted, n_delib_parsed, args)

    n = len(rows)
    result = {
        "artifact": "e2e_decision_loop_checkpoint_eval",
        "is_training_result": True,
        "eval_label": label,
        "model": str(args.model),
        "checkpoint": checkpoint,
        "state_jsonl": str(args.state_jsonl),
        "eval_args": {
            "limit": args.limit,
            "image_limit": args.image_limit,
            "max_pixels": args.max_pixels,
            "max_actions": args.max_actions,
            "silence_threshold": args.silence_threshold,
            "torch_dtype": args.torch_dtype,
            "device_map": args.device_map,
        },
        "n_records": n,
        "n_deliberation_attempted": n_delib_attempted,
        "n_deliberation_parsed": n_delib_parsed,
        "metrics": {
            "perception_parse_rate": totals["perception_parse_ok"] / n if n else None,
            "action_parse_rate": totals["action_parse_ok"] / n if n else None,
            "fallback_rate": totals["fallback"] / n if n else None,
            "stage_accuracy": totals["stage_correct"] / n if n else None,
            "score_accuracy": totals["score_correct"] / n if n else None,
            "candidate_exact": totals["candidates_exact"] / n if n else None,
            "chosen_in_gold_candidates_rate": totals["chosen_in_gold_candidates"] / n if n else None,
            "strategy_accuracy_vs_best_action": totals["strategy_correct"] / n if n else None,
            "deliberation_parse_rate": n_delib_parsed / n_delib_attempted if n_delib_attempted else None,
        },
        "outputs": outputs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _maybe_log_progress(
    index: int,
    total: int,
    totals: dict[str, int],
    n_delib_attempted: int,
    n_delib_parsed: int,
    start_time: float,
    args: argparse.Namespace,
) -> None:
    if not args.progress_every or (index != 1 and index % args.progress_every != 0 and index != total):
        return
    print(
        json.dumps(
            {
                "event": "e2e_eval_progress",
                "index": index,
                "total": total,
                "perception_parse_ok": totals["perception_parse_ok"],
                "action_parse_ok": totals["action_parse_ok"],
                "deliberation_parsed": n_delib_parsed,
                "deliberation_attempted": n_delib_attempted,
                "elapsed_sec": round(time.time() - start_time, 1),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def _maybe_write_partial(
    partial_path: Path,
    index: int,
    total: int,
    label: str,
    checkpoint: str | None,
    outputs: list[dict[str, Any]],
    totals: dict[str, int],
    n_delib_attempted: int,
    n_delib_parsed: int,
    args: argparse.Namespace,
) -> None:
    if not args.partial_out_every or (index % args.partial_out_every != 0 and index != total):
        return
    partial = {
        "artifact": "e2e_decision_loop_checkpoint_eval_partial",
        "eval_label": label,
        "checkpoint": checkpoint,
        "processed": index,
        "total": total,
        "totals": totals,
        "n_deliberation_attempted": n_delib_attempted,
        "n_deliberation_parsed": n_delib_parsed,
        "outputs": outputs,
    }
    partial_path.write_text(json.dumps(partial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--eval-label", default=None)
    parser.add_argument("--state-jsonl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--image-limit", type=int, default=3)
    parser.add_argument("--max-pixels", type=int, default=200704)
    parser.add_argument("--max-actions", type=int, default=4)
    parser.add_argument("--silence-threshold", type=int, default=1)
    parser.add_argument("--max-new-tokens-perception", type=int, default=128)
    parser.add_argument("--max-new-tokens-deliberation", type=int, default=128)
    parser.add_argument("--max-new-tokens-action", type=int, default=128)
    parser.add_argument("--torch-dtype", choices=["bfloat16", "float16"], default="float16")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--progress-every", type=int, default=5)
    parser.add_argument("--partial-out-every", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    result = evaluate(parse_args())
    print(json.dumps({k: v for k, v in result.items() if k != "outputs"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
