"""Evaluate a Qwen-VL base model or LoRA checkpoint on PIWM ms-swift JSONL rows.

This is a sprint-oriented smoke evaluator: it measures whether the trained
checkpoint can emit the required PIWM structured tags on held-out examples. It
does not replace the full decision-loop evaluation.
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

from piwm_infer.parsers import (
    MalformedOutputError,
    parse_action_output,
    parse_continuation_caption_output,
    parse_deliberation_output,
    parse_future_verification_output,
    parse_perception_output,
)


def _read_rows(path: Path, limit: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def _task_parser(task: str):
    if task == "perception":
        return parse_perception_output
    if task == "deliberation":
        return parse_deliberation_output
    if task == "continuation_caption":
        return parse_continuation_caption_output
    if task == "future_verification":
        return parse_future_verification_output
    if task == "action_selection":
        return parse_action_output
    raise ValueError(f"unsupported task: {task}")


def _primary_structured_block(raw: str) -> str:
    """Drop auxiliary recap tags that are useful for SFT but not parser scoring."""
    return raw.split("\n[recap]", 1)[0].strip()


def _normalize_messages(row: dict[str, Any], *, image_limit: int | None = None, max_pixels: int | None = None) -> list[dict[str, Any]]:
    messages = row["messages"]
    system = messages[0]
    user = messages[1]
    text = str(user["content"]).replace("<image>", "").strip()
    content: list[dict[str, str]] = []
    images = row.get("images", [])
    if image_limit is not None:
        images = images[:image_limit]
    for image in images:
        item: dict[str, Any] = {"type": "image", "image": image}
        if max_pixels is not None:
            item["max_pixels"] = max_pixels
        content.append(item)
    content.append({"type": "text", "text": text})
    return [{"role": "system", "content": system["content"]}, {"role": "user", "content": content}]


def _generate_one(model, processor, row: dict[str, Any], args: argparse.Namespace) -> str:
    messages = _normalize_messages(row, image_limit=args.image_limit, max_pixels=args.max_pixels)
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
        generated_ids = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
    prompt_len = inputs["input_ids"].shape[-1]
    generated_ids = generated_ids[:, prompt_len:]
    return processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def _score(parsed: dict[str, Any], gold: dict[str, Any], task: str) -> dict[str, bool]:
    if task == "perception":
        return {
            "stage_exact": parsed.get("aida_stage") == gold.get("aida_stage"),
            "score_exact": parsed.get("proactive_score") == gold.get("proactive_score"),
            "candidates_exact": parsed.get("candidate_actions") == gold.get("candidate_actions"),
        }
    if task == "deliberation":
        return {
            "next_stage_exact": parsed.get("next_aida_stage") == gold.get("next_aida_stage"),
            "risk_exact": parsed.get("risk") == gold.get("risk"),
            "benefit_exact": parsed.get("benefit") == gold.get("benefit"),
            "reward_exact": parsed.get("reward") == gold.get("reward"),
        }
    if task == "continuation_caption":
        return {"caption_exact": parsed.get("reaction_caption") == gold.get("reaction_caption")}
    if task == "future_verification":
        parsed_reaction = parsed.get("visible_reaction", {})
        gold_reaction = gold.get("visible_reaction", {})
        return {
            "match_exact": parsed.get("match") == gold.get("match"),
            "expected_state_exact": parsed.get("expected_next_state") == gold.get("expected_next_state"),
            "body_change_exact": parsed_reaction.get("body_change") == gold_reaction.get("body_change"),
            "gaze_change_exact": parsed_reaction.get("gaze_change") == gold_reaction.get("gaze_change"),
            "hand_change_exact": parsed_reaction.get("hand_change") == gold_reaction.get("hand_change"),
            "movement_change_exact": parsed_reaction.get("movement_change") == gold_reaction.get("movement_change"),
        }
    if task == "action_selection":
        return {"chosen_exact": parsed.get("chosen") == gold.get("chosen")}
    return {}


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    rows = _read_rows(args.input_jsonl, args.limit)
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
        eval_label = args.eval_label or "lora_checkpoint"
    else:
        model = base
        checkpoint = None
        eval_label = args.eval_label or "base_model"
    model.eval()

    outputs: list[dict[str, Any]] = []
    task_counts: dict[str, int] = {}
    parse_success = 0
    metric_totals: dict[str, int] = {}
    metric_denoms: dict[str, int] = {}

    start_time = time.time()
    partial_path = args.out.with_suffix(args.out.suffix + ".partial")

    for index, row in enumerate(rows, start=1):
        task = row.get("task", "unknown")
        task_counts[task] = task_counts.get(task, 0) + 1
        parser = _task_parser(task)
        gold_raw = _primary_structured_block(row["messages"][2]["content"])
        gold = parser(gold_raw)
        record: dict[str, Any] = {
            "source_id": row.get("source_id"),
            "task": task,
            "target": gold_raw,
        }
        try:
            pred_raw = _generate_one(model, processor, row, args)
            record["prediction"] = pred_raw
            parsed = parser(_primary_structured_block(pred_raw))
            parse_success += 1
            scores = _score(parsed, gold, task)
            for key, ok in scores.items():
                metric_denoms[key] = metric_denoms.get(key, 0) + 1
                metric_totals[key] = metric_totals.get(key, 0) + int(ok)
            record.update({"prediction": pred_raw, "parsed": parsed, "parse_ok": True, "scores": scores})
        except (MalformedOutputError, RuntimeError, ValueError) as exc:
            record.update({"prediction": record.get("prediction"), "parse_ok": False, "error": f"{type(exc).__name__}: {exc}"})
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        outputs.append(record)

        if args.progress_every and (index == 1 or index % args.progress_every == 0 or index == len(rows)):
            elapsed = time.time() - start_time
            print(
                json.dumps(
                    {
                        "event": "eval_progress",
                        "index": index,
                        "total": len(rows),
                        "task": task,
                        "parse_success": parse_success,
                        "elapsed_sec": round(elapsed, 1),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

        if args.partial_out_every and (index % args.partial_out_every == 0 or index == len(rows)):
            partial = {
                "artifact": "ms_swift_checkpoint_eval_partial",
                "eval_label": eval_label,
                "checkpoint": checkpoint,
                "input_jsonl": str(args.input_jsonl),
                "processed": index,
                "total": len(rows),
                "parse_success": parse_success,
                "outputs": outputs,
            }
            partial_path.write_text(json.dumps(partial, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    metrics = {
        key: (metric_totals.get(key, 0) / denom if denom else None)
        for key, denom in sorted(metric_denoms.items())
    }
    result = {
        "artifact": "ms_swift_checkpoint_eval",
        "is_training_result": True,
        "eval_label": eval_label,
        "model": str(args.model),
        "checkpoint": checkpoint,
        "input_jsonl": str(args.input_jsonl),
        "eval_args": {
            "limit": args.limit,
            "max_new_tokens": args.max_new_tokens,
            "image_limit": args.image_limit,
            "max_pixels": args.max_pixels,
            "torch_dtype": args.torch_dtype,
            "device_map": args.device_map,
        },
        "n_records": len(rows),
        "task_counts": task_counts,
        "parse_success": parse_success,
        "parse_rate": parse_success / len(rows) if rows else None,
        "metrics": metrics,
        "outputs": outputs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--eval-label", default=None)
    parser.add_argument("--input-jsonl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--image-limit", type=int, default=None)
    parser.add_argument("--max-pixels", type=int, default=None)
    parser.add_argument("--torch-dtype", choices=["bfloat16", "float16"], default="bfloat16")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--partial-out-every", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    result = evaluate(parse_args())
    print(json.dumps({k: v for k, v in result.items() if k != "outputs"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
