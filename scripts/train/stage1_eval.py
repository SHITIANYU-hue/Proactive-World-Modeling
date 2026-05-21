"""Run or summarize Stage-1 validation metrics for PIWM.

The current Stage-1 schema exposes an explicit `intent_label`, so task B can
be scored as accuracy. If a future schema removes `intent_label`, define a
new discrete intention label table before using task B as a gating metric.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"
DEFAULT_USER_VAL = Path("data/official/ms_swift/piwm_train_stage1_user_intent_val_v1.jsonl")
DEFAULT_NEXT_VAL = Path("data/official/ms_swift/piwm_train_stage1_next_state_prediction_val_v1.jsonl")
DEFAULT_RAW_DIR = Path("data/piwm_results/stage1_qwen25vl_7b_v1/raw_eval")
DEFAULT_OUT_JSON = Path("data/piwm_results/stage1_qwen25vl_7b_v1/stage1_val_metrics.json")
DEFAULT_OUT_MD = Path("data/piwm_results/stage1_qwen25vl_7b_v1/stage1_val_metrics.md")
STAGE1_PASS_THRESHOLD = 0.6


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    user_result = args.user_eval_result or args.raw_dir / "stage1_user_intent_val_raw.json"
    next_result = args.next_eval_result or args.raw_dir / "stage1_next_state_prediction_val_raw.json"

    commands = _eval_commands(args, user_result=user_result, next_result=next_result)
    if args.dry_run:
        print("Stage-1 eval dry-run commands:")
        for command in commands:
            print(" ".join(_quote(part) for part in command))
        return 0

    if args.user_eval_result is None or args.next_eval_result is None:
        if args.checkpoint is None:
            raise SystemExit("--checkpoint is required unless --user-eval-result and --next-eval-result are provided")
        if not args.checkpoint.exists():
            raise SystemExit(f"checkpoint path does not exist: {args.checkpoint}")
        args.raw_dir.mkdir(parents=True, exist_ok=True)
        for command in commands:
            subprocess.run(command, check=True)

    metrics = summarize_stage1_eval(
        user_result=user_result,
        next_result=next_result,
        out_json=args.out_json,
        out_md=args.out_md,
        model=args.model,
        checkpoint=args.checkpoint,
        user_val=args.user_val,
        next_val=args.next_val,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


def _eval_commands(args: argparse.Namespace, *, user_result: Path, next_result: Path) -> list[list[str]]:
    checkpoint = str(args.checkpoint or "CHECKPOINT_PATH")
    common = [
        sys.executable,
        "-m",
        "scripts.eval_ms_swift_checkpoint",
        "--model",
        args.model,
        "--checkpoint",
        checkpoint,
        "--image-limit",
        str(args.image_limit),
        "--max-new-tokens",
        str(args.max_new_tokens),
        "--torch-dtype",
        args.torch_dtype,
        "--device-map",
        args.device_map,
    ]
    return [
        common
        + [
            "--eval-label",
            "stage1_user_intent_val",
            "--input-jsonl",
            args.user_val.as_posix(),
            "--out",
            user_result.as_posix(),
        ],
        common
        + [
            "--eval-label",
            "stage1_next_state_prediction_val",
            "--input-jsonl",
            args.next_val.as_posix(),
            "--out",
            next_result.as_posix(),
        ],
    ]


def summarize_stage1_eval(
    *,
    user_result: Path,
    next_result: Path,
    out_json: Path,
    out_md: Path,
    model: str,
    checkpoint: Path | None,
    user_val: Path,
    next_val: Path,
) -> dict[str, Any]:
    user = _read_json(user_result)
    next_state = _read_json(next_result)
    user_metrics = user.get("metrics", {})
    next_metrics = next_state.get("metrics", {})

    task_a_macro_f1 = user_metrics.get("stage_macro_f1")
    task_a_accuracy = user_metrics.get("stage_accuracy")
    task_b_accuracy = user_metrics.get("intent_accuracy")
    task_b_macro_f1 = user_metrics.get("intent_macro_f1")
    task_b_core_macro_f1 = user_metrics.get("intent_core_5class_macro_f1")
    task_b_core_accuracy = user_metrics.get("intent_core_5class_accuracy")
    task_b_core_n = user_metrics.get("intent_core_5class_n")
    task_c_accuracy = next_metrics.get("next_stage_accuracy")
    task_c_macro_f1 = next_metrics.get("next_stage_macro_f1")
    can_enter_stage2 = _passes(task_a_macro_f1) and _passes(task_c_macro_f1)

    metrics = {
        "artifact": "piwm_stage1_val_metrics",
        "is_training_result": True,
        "model": model,
        "checkpoint": checkpoint.as_posix() if checkpoint else None,
        "user_intent_val_jsonl": user_val.as_posix(),
        "next_state_prediction_val_jsonl": next_val.as_posix(),
        "user_intent_eval_result": user_result.as_posix(),
        "next_state_eval_result": next_result.as_posix(),
        "task_a_aida_stage_macro_f1": task_a_macro_f1,
        "task_a_aida_stage_accuracy": task_a_accuracy,
        "task_b_intention_accuracy": task_b_accuracy,
        "task_b_intention_full_7class_macro_f1": task_b_macro_f1,
        "task_b_intention_core_5class_macro_f1": task_b_core_macro_f1,
        "task_b_intention_core_5class_accuracy": task_b_core_accuracy,
        "task_b_intention_core_5class_n": task_b_core_n,
        "task_b_low_confidence_intents": _low_confidence_intent_metrics(user_metrics),
        "task_c_next_stage_accuracy": task_c_accuracy,
        "task_c_next_stage_macro_f1": task_c_macro_f1,
        "stage1_completion_threshold": {
            "task_a_aida_stage_macro_f1_gt": STAGE1_PASS_THRESHOLD,
            "task_c_next_stage_macro_f1_gt": STAGE1_PASS_THRESHOLD,
            "task_b_intention_core_5class_macro_f1": "reported as the A3+ primary intent metric; no hard threshold yet",
            "task_b_low_confidence_intents": "reported separately as visually unidentifiable labels",
        },
        "can_enter_stage2_by_current_rule": can_enter_stage2,
        "task_counts": {
            "user_intent": user.get("task_counts", {}),
            "next_state_prediction": next_state.get("task_counts", {}),
        },
        "parse_rates": {
            "user_intent": user.get("parse_rate"),
            "next_state_prediction": next_state.get("parse_rate"),
        },
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(_markdown(metrics), encoding="utf-8")
    return metrics


def _passes(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > STAGE1_PASS_THRESHOLD


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _low_confidence_intent_metrics(user_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    labels = str(user_metrics.get("intent_low_confidence_labels") or "").split(",")
    out = []
    for label in [item for item in labels if item]:
        prefix = f"intent_low_confidence_{label}"
        out.append(
            {
                "intent_label": label,
                "sample_count": user_metrics.get(f"{prefix}_sample_count"),
                "pred_count": user_metrics.get(f"{prefix}_pred_count"),
                "f1": user_metrics.get(f"{prefix}_f1"),
                "note": user_metrics.get(f"{prefix}_note", "visually unidentifiable"),
            }
        )
    return out


def _markdown(metrics: dict[str, Any]) -> str:
    status = "PASS" if metrics["can_enter_stage2_by_current_rule"] else "NOT READY"
    low_conf_rows = [
        "| intent_label | sample_count | pred_count | F1 | note |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics["task_b_low_confidence_intents"]:
        low_conf_rows.append(
            "| `{intent_label}` | {sample_count} | {pred_count} | {f1} | {note} |".format(
                intent_label=item["intent_label"],
                sample_count=_fmt(item.get("sample_count")),
                pred_count=_fmt(item.get("pred_count")),
                f1=_fmt(item.get("f1")),
                note=item.get("note", ""),
            )
        )
    return "\n".join(
        [
            "# PIWM Stage-1 Validation Metrics",
            "",
            f"- model: `{metrics['model']}`",
            f"- checkpoint: `{metrics['checkpoint'] or '-'}`",
            f"- user_intent_val: `{metrics['user_intent_val_jsonl']}`",
            f"- next_state_prediction_val: `{metrics['next_state_prediction_val_jsonl']}`",
            f"- status_by_current_rule: `{status}`",
            f"- task A AIDA macro F1: `{_fmt(metrics['task_a_aida_stage_macro_f1'])}`",
            f"- task A AIDA accuracy: `{_fmt(metrics['task_a_aida_stage_accuracy'])}`",
            f"- task B intention primary A3+ core 5-class macro F1: `{_fmt(metrics['task_b_intention_core_5class_macro_f1'])}`",
            f"- task B intention core 5-class accuracy: `{_fmt(metrics['task_b_intention_core_5class_accuracy'])}`",
            f"- task B intention full 7-class macro F1: `{_fmt(metrics['task_b_intention_full_7class_macro_f1'])}`",
            f"- task B intention full 7-class accuracy: `{_fmt(metrics['task_b_intention_accuracy'])}`",
            f"- task C next-stage accuracy: `{_fmt(metrics['task_c_next_stage_accuracy'])}`",
            f"- task C next-stage macro F1: `{_fmt(metrics['task_c_next_stage_macro_f1'])}`",
            "",
            "## A3+ Intent Metrics",
            "",
            "- Primary intent metric: core 5-class macro F1, excluding `seek_reassurance` and `negotiate_price` because they are visually underdetermined in the current visual-only Stage-1 contract.",
            "- Secondary intent metrics: full 7-class macro F1 plus per-label statistics for the two low-confidence labels.",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| core 5-class N | {_fmt(metrics['task_b_intention_core_5class_n'])} |",
            f"| core 5-class macro F1 | {_fmt(metrics['task_b_intention_core_5class_macro_f1'])} |",
            f"| core 5-class accuracy | {_fmt(metrics['task_b_intention_core_5class_accuracy'])} |",
            f"| full 7-class macro F1 | {_fmt(metrics['task_b_intention_full_7class_macro_f1'])} |",
            f"| full 7-class accuracy | {_fmt(metrics['task_b_intention_accuracy'])} |",
            "",
            "### Low-Confidence Intent Labels",
            "",
            *low_conf_rows,
            "",
            "## Threshold Comparison",
            "",
            "| Task | Metric | Threshold | Current | Pass |",
            "|---|---|---:|---:|---|",
            _threshold_row("AIDA stage", "macro F1", metrics["task_a_aida_stage_macro_f1"]),
            _threshold_row("next-stage", "macro F1", metrics["task_c_next_stage_macro_f1"]),
            "| intention | A3+ core 5-class macro F1 | pending | "
            f"{_fmt(metrics['task_b_intention_core_5class_macro_f1'])} | reported only |",
            "",
            "Task B now reports the A3+ primary core 5-class macro F1 and preserves full 7-class metrics as secondary analysis; it does not yet gate Stage-2.",
            "",
        ]
    )


def _threshold_row(task: str, metric: str, value: Any) -> str:
    passed = _passes(value)
    return f"| {task} | {metric} | > {STAGE1_PASS_THRESHOLD:.1f} | {_fmt(value)} | {'yes' if passed else 'no'} |"


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if value is None:
        return "-"
    return str(value)


def _quote(value: str) -> str:
    if not value or any(ch.isspace() for ch in value):
        return repr(value)
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=None, help="Stage-1 LoRA checkpoint path.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--user-val", type=Path, default=DEFAULT_USER_VAL)
    parser.add_argument("--next-val", type=Path, default=DEFAULT_NEXT_VAL)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--user-eval-result", type=Path, default=None)
    parser.add_argument("--next-eval-result", type=Path, default=None)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--image-limit", type=int, default=3)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--torch-dtype", choices=["bfloat16", "float16"], default="bfloat16")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--dry-run", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
