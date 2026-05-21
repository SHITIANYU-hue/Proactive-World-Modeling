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

from piwm_train.a3plus_metrics import intent_a3plus_metrics
from piwm_infer.parsers import (
    MalformedOutputError,
    parse_action_output,
    parse_continuation_caption_output,
    parse_deliberation_output,
    parse_future_verification_output,
    parse_perception_output,
    parse_user_intent_output,
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
    if task == "user_intent":
        return parse_user_intent_output
    if task == "perception":
        return parse_perception_output
    if task in {"deliberation", "next_state_prediction"}:
        return parse_deliberation_output
    if task == "continuation_caption":
        return parse_continuation_caption_output
    if task == "future_verification":
        return parse_future_verification_output
    if task in {"action_selection", "action_selection_5act"}:
        return (lambda raw: parse_action_output(raw, five_act_only=True)) if task == "action_selection_5act" else parse_action_output
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
    if task == "user_intent":
        return {
            "stage_exact": parsed.get("aida_stage") == gold.get("aida_stage"),
            "intent_exact": parsed.get("intent_label") == gold.get("intent_label"),
        }
    if task == "perception":
        return {
            "stage_exact": parsed.get("aida_stage") == gold.get("aida_stage"),
            "score_exact": parsed.get("proactive_score") == gold.get("proactive_score"),
            "candidates_exact": parsed.get("candidate_actions") == gold.get("candidate_actions"),
        }
    if task in {"deliberation", "next_state_prediction"}:
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
            "engagement_pattern_change_exact": parsed_reaction.get("engagement_pattern_change")
            == gold_reaction.get("engagement_pattern_change"),
            "gaze_and_attention_change_exact": parsed_reaction.get("gaze_and_attention_change")
            == gold_reaction.get("gaze_and_attention_change"),
            "body_and_hands_change_exact": parsed_reaction.get("body_and_hands_change")
            == gold_reaction.get("body_and_hands_change"),
        }
    if task in {"action_selection", "action_selection_5act"}:
        return {"chosen_exact": parsed.get("chosen") == gold.get("chosen")}
    return {}


def _classification_items(parsed: dict[str, Any], gold: dict[str, Any], row: dict[str, Any], task: str) -> dict[str, tuple[str | None, str | None]]:
    if task == "user_intent":
        return {
            "stage": (parsed.get("aida_stage"), gold.get("aida_stage")),
            "intent": (parsed.get("intent_label"), gold.get("intent_label")),
        }
    if task in {"deliberation", "next_state_prediction"}:
        return {"next_stage": (parsed.get("next_aida_stage"), gold.get("next_aida_stage"))}
    if task in {"action_selection", "action_selection_5act"}:
        pred = parsed.get("chosen")
        target = gold.get("chosen")
        mapping = row.get("meta", {}).get("candidate_action_acts", {})
        return {
            "action": (_action_to_act(pred, mapping), _action_to_act(target, mapping)),
            "go_no_go": (_go_no_go(_action_to_act(pred, mapping)), _go_no_go(_action_to_act(target, mapping))),
        }
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
            for name, (pred_label, gold_label) in _classification_items(parsed, gold, row, task).items():
                if pred_label is not None and gold_label is not None:
                    _add_classification_item(metric_totals, metric_denoms, name, pred_label, gold_label)
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
        if not key.startswith("__labels__")
    }
    metrics.update(_macro_metrics(metric_totals, metric_denoms))
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


def _action_to_act(action: str | None, mapping: dict[str, str]) -> str | None:
    if action is None:
        return None
    if action in mapping:
        return mapping[action]
    if "_" in action:
        prefix = action.split("_", 1)[0]
        if prefix in {"Elicit", "Inform", "Recommend", "Reassure", "Hold", "Greet"}:
            return prefix
    return action


def _go_no_go(act: str | None) -> str | None:
    if act is None:
        return None
    return "no_go" if act == "Hold" else "go"


def _add_classification_item(
    metric_totals: dict[str, int],
    metric_denoms: dict[str, int],
    name: str,
    pred_label: str,
    gold_label: str,
) -> None:
    labels_key = f"__labels__{name}"
    encoded = f"{pred_label}\t{gold_label}"
    metric_totals[labels_key + "\t" + encoded] = metric_totals.get(labels_key + "\t" + encoded, 0) + 1
    metric_denoms[labels_key] = metric_denoms.get(labels_key, 0) + 1


def _macro_metrics(metric_totals: dict[str, int], metric_denoms: dict[str, int]) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {}
    names = [key.removeprefix("__labels__") for key in metric_denoms if key.startswith("__labels__")]
    for name in sorted(names):
        pairs: list[tuple[str, str]] = []
        prefix = f"__labels__{name}\t"
        for key, count in metric_totals.items():
            if not key.startswith(prefix):
                continue
            pred, gold = key[len(prefix):].split("\t", 1)
            pairs.extend([(pred, gold)] * count)
        metrics[f"{name}_accuracy"] = _accuracy(pairs)
        metrics[f"{name}_macro_f1"] = _macro_f1(pairs)
        if name == "intent":
            metrics.update(intent_a3plus_metrics(pairs))
        if name == "go_no_go":
            metrics["go_precision"] = _precision(pairs, positive="go")
            metrics["go_recall"] = _recall(pairs, positive="go")
            metrics["no_go_precision"] = _precision(pairs, positive="no_go")
            metrics["no_go_recall"] = _recall(pairs, positive="no_go")
    return metrics


def _accuracy(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    return sum(int(pred == gold) for pred, gold in pairs) / len(pairs)


def _macro_f1(pairs: list[tuple[str, str]]) -> float | None:
    labels = sorted({label for pair in pairs for label in pair})
    if not labels:
        return None
    f1s = []
    for label in labels:
        tp = sum(1 for pred, gold in pairs if pred == label and gold == label)
        fp = sum(1 for pred, gold in pairs if pred == label and gold != label)
        fn = sum(1 for pred, gold in pairs if pred != label and gold == label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append((2 * precision * recall / (precision + recall)) if precision + recall else 0.0)
    return sum(f1s) / len(f1s)


def _precision(pairs: list[tuple[str, str]], *, positive: str) -> float | None:
    predicted = sum(1 for pred, _ in pairs if pred == positive)
    if predicted == 0:
        return None
    return sum(1 for pred, gold in pairs if pred == positive and gold == positive) / predicted


def _recall(pairs: list[tuple[str, str]], *, positive: str) -> float | None:
    gold_count = sum(1 for _, gold in pairs if gold == positive)
    if gold_count == 0:
        return None
    return sum(1 for pred, gold in pairs if pred == positive and gold == positive) / gold_count


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
