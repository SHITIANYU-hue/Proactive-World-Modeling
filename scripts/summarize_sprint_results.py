"""Build a sprint result snapshot from PIWM dataset and evaluation artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DATASET_STATS = Path("data/piwm_dataset_pilot30_with_continuations/_stats.json")
DEFAULT_MOCK_EVAL = Path("data/piwm_results/pilot24_mock_pipeline_eval.json")
DEFAULT_SFT_SUMMARY = Path("data/piwm_results/sft_train_summary.json")
DEFAULT_ZERO_SHOT = Path("data/piwm_results/pilot24_zero_shot_baselines.json")
DEFAULT_SUMMARY_OUT = Path("data/piwm_results/sprint_summary.json")
DEFAULT_MARKDOWN_OUT = Path("docs/92_neurips_sprint_result_snapshot.md")

UNKNOWN = "unknown"
MISSING = "missing"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> tuple[str, Any | None, str | None]:
    if not path.exists():
        return MISSING, None, None
    try:
        return "present", json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return "invalid", None, f"JSONDecodeError: {exc}"


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _metric(payload: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = payload.get(name)
        if value is not None:
            return value
    return UNKNOWN


def _fmt(value: Any) -> str:
    if value is None:
        return UNKNOWN
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _source_record(path: Path, root: Path, status: str, error: str | None, nature: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": _rel(path, root),
        "status": status,
        "nature": nature,
    }
    if error:
        record["error"] = error
    return record


def _dataset_section(path: Path, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    status, payload, error = _read_json(path)
    source = _source_record(path, root, status, error, "synthetic/rule-derived dataset statistics")
    rel_path = _rel(path, root)
    is_unreviewed_priority = "priority" in rel_path and "unreviewed" in rel_path
    label = (
        "Priority high-throughput synthetic train split"
        if is_unreviewed_priority
        else "Pilot30 QA-reviewed continuation dataset"
    )
    notes = (
        "Generated synthetic train split with file-level QA; visual/manual QA is pending, so do not report as QA-pass data."
        if is_unreviewed_priority
        else "Counts describe QA-reviewed synthetic pilot data; they are not model performance."
    )
    if not isinstance(payload, dict):
        return source, {
            "label": label,
            "status": status,
            "result_nature": "synthetic/rule-derived",
            "n_sessions_loaded": UNKNOWN,
            "n_state_inference_rows": UNKNOWN,
            "n_transition_modeling_rows": UNKNOWN,
            "n_world_model_continuation_rows": UNKNOWN,
            "n_states_with_action_contrast": UNKNOWN,
            "split_counts": UNKNOWN,
            "viewpoint_counts": UNKNOWN,
            "notes": "dataset stats unavailable",
        }

    return source, {
        "label": label,
        "status": status,
        "result_nature": (
            "high-throughput synthetic train split, pending visual QA"
            if is_unreviewed_priority
            else "QA-reviewed synthetic pilot"
        ),
        "n_sessions_loaded": _metric(payload, "n_sessions_loaded"),
        "n_sessions_skipped": _metric(payload, "n_sessions_skipped"),
        "n_state_inference_rows": _metric(payload, "n_state_inference_rows"),
        "n_transition_modeling_rows": _metric(payload, "n_transition_modeling_rows"),
        "n_policy_preference_rows": _metric(payload, "n_policy_preference_rows"),
        "n_world_model_continuation_rows": _metric(payload, "n_world_model_continuation_rows"),
        "n_states_with_action_contrast": _metric(payload, "n_states_with_action_contrast"),
        "split_counts": _metric(payload, "n_sessions_by_split"),
        "viewpoint_counts": _metric(payload, "n_sessions_by_viewpoint"),
        "product_counts": _metric(payload, "n_sessions_by_product_category"),
        "timestamp_utc": _metric(payload, "timestamp_utc"),
        "notes": notes,
    }


def _mock_eval_section(path: Path, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    status, payload, error = _read_json(path)
    source = _source_record(path, root, status, error, "mock pipeline evaluation")
    if not isinstance(payload, dict):
        return source, {
            "label": "MockVLM pipeline eval",
            "status": status,
            "result_nature": "mock",
            "model": UNKNOWN,
            "n_records": UNKNOWN,
            "strategy_accuracy_vs_label": UNKNOWN,
            "parse_failure_count": UNKNOWN,
            "fallback_count": UNKNOWN,
            "is_training_result": False,
            "notes": "mock evaluation artifact unavailable",
        }

    is_training_result = bool(payload.get("is_training_result", False))
    mode = str(payload.get("mode", UNKNOWN))
    model = str(payload.get("model", UNKNOWN))
    return source, {
        "label": "MockVLM pipeline eval",
        "status": status,
        "result_nature": "mock",
        "model": model,
        "mode": mode,
        "n_records": _metric(payload, "n_records"),
        "n_success": _metric(payload, "n_success"),
        "strategy_accuracy_vs_label": _metric(payload, "strategy_accuracy_vs_label"),
        "parse_failure_count": _metric(payload, "parse_failure_count"),
        "fallback_count": _metric(payload, "fallback_count"),
        "is_training_result": is_training_result,
        "notes": (
            "MockVLM checks inference plumbing only; do not cite as a trained model result."
            if not is_training_result
            else "Artifact marks itself as a training result; verify provenance before paper use."
        ),
    }


def _sft_section(path: Path, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    status, payload, error = _read_json(path)
    source = _source_record(path, root, status, error, "SFT training summary")
    if not isinstance(payload, dict):
        return source, {
            "label": "SFT model",
            "status": status,
            "result_nature": "training",
            "model": UNKNOWN,
            "train_loss": UNKNOWN,
            "eval_loss": UNKNOWN,
            "strategy_accuracy_vs_label": UNKNOWN,
            "is_training_result": UNKNOWN,
            "notes": "no SFT training summary found; leave paper metrics unknown",
        }

    return source, {
        "label": str(payload.get("model", "SFT model")),
        "status": status,
        "result_nature": "training",
        "model": _metric(payload, "model", "base_model"),
        "train_loss": _metric(payload, "train_loss", "final_train_loss"),
        "last_step_loss": _metric(payload, "last_step_loss"),
        "token_acc": _metric(payload, "token_acc"),
        "global_step": _metric(payload, "global_step"),
        "epoch": _metric(payload, "epoch"),
        "last_checkpoint": _metric(payload, "last_checkpoint"),
        "eval_loss": _metric(payload, "eval_loss", "validation_loss", "final_eval_loss"),
        "strategy_accuracy_vs_label": _metric(
            payload,
            "strategy_accuracy_vs_label",
            "strategy_accuracy",
            "action_accuracy",
        ),
        "is_training_result": bool(payload.get("is_training_result", True)),
        "contains_unreviewed_synthetic": bool(payload.get("contains_unreviewed_synthetic", False)),
        "notes": (
            "SFT metrics are read only from the supplied summary artifact; this is a training run, not an evaluated model result."
        ),
    }


def _zero_shot_section(path: Path, root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    status, payload, error = _read_json(path)
    source = _source_record(path, root, status, error, "zero-shot baseline evaluation")
    if not isinstance(payload, dict):
        return source, [
            {
                "label": "Zero-shot baselines",
                "status": status,
                "result_nature": "baseline",
                "model": UNKNOWN,
                "n_records": UNKNOWN,
                "strategy_accuracy_vs_label": UNKNOWN,
                "parse_failure_count": UNKNOWN,
                "notes": "no zero-shot baseline summary found; leave paper metrics unknown",
            }
        ]

    rows: list[dict[str, Any]] = []
    candidates = payload.get("models") or payload.get("results") or payload.get("baselines")
    if isinstance(candidates, dict):
        iterable = [
            {"model": model_name, **metrics} if isinstance(metrics, dict) else {"model": model_name}
            for model_name, metrics in candidates.items()
        ]
    elif isinstance(candidates, list):
        iterable = [item for item in candidates if isinstance(item, dict)]
    else:
        iterable = [payload]

    for item in iterable:
        metrics = item.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {}
        metric_source = {**item, **metrics}
        has_metrics = bool(metrics) or any(
            key in item
            for key in [
                "strategy_accuracy_vs_label",
                "strategy_accuracy_vs_best_action",
                "strategy_accuracy",
                "action_accuracy",
            ]
        )
        not_real_model_result = bool(item.get("not_real_model_result"))
        baseline_type = str(item.get("baseline_type", "zero-shot"))
        result_nature = (
            "synthetic/rule-derived baseline"
            if not_real_model_result or "rule" in baseline_type
            else "zero-shot baseline"
        )
        notes = (
            "rule-derived baseline only; not a real VLM/API model result"
            if result_nature == "synthetic/rule-derived baseline"
            else "zero-shot baseline metrics are read only from the supplied artifact"
        )
        if not has_metrics:
            notes = "baseline artifact entry exists, but metrics are missing; leave paper metrics unknown"
        rows.append(
            {
                "label": f"Zero-shot {item.get('model', UNKNOWN)}",
                "status": status if has_metrics else MISSING,
                "result_nature": result_nature,
                "baseline_type": baseline_type,
                "model": _metric(metric_source, "model", "name"),
                "n_records": _metric(metric_source, "n_records", "num_records"),
                "strategy_accuracy_vs_label": _metric(
                    metric_source,
                    "strategy_accuracy_vs_label",
                    "strategy_accuracy_vs_best_action",
                    "strategy_accuracy",
                    "action_accuracy",
                ),
                "intent_accuracy": _metric(metric_source, "intent_accuracy"),
                "state_subtype_accuracy": _metric(metric_source, "state_subtype_accuracy"),
                "policy_pair_accuracy": _metric(metric_source, "policy_pair_accuracy"),
                "parse_failure_count": _metric(metric_source, "parse_failure_count"),
                "not_real_model_result": not_real_model_result,
                "notes": notes,
            }
        )
    return source, rows


def build_summary(
    *,
    root: Path,
    dataset_stats: Path,
    mock_eval: Path,
    sft_summary: Path,
    zero_shot: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or _utc_now()
    inputs: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    inputs["dataset_stats"], dataset_row = _dataset_section(root / dataset_stats, root)
    rows.append(dataset_row)

    inputs["mock_pipeline_eval"], mock_row = _mock_eval_section(root / mock_eval, root)
    rows.append(mock_row)

    inputs["sft_train_summary"], sft_row = _sft_section(root / sft_summary, root)
    rows.append(sft_row)

    inputs["zero_shot_baselines"], zero_rows = _zero_shot_section(root / zero_shot, root)
    rows.extend(zero_rows)

    return {
        "artifact": "piwm_sprint_summary",
        "generated_at_utc": generated_at_utc,
        "inputs": inputs,
        "result_rows": rows,
        "paper_table": {
            "columns": [
                "label",
                "status",
                "result_nature",
                "model",
                "n_records",
                "strategy_accuracy_vs_label",
                "train_loss",
                "eval_loss",
                "notes",
            ],
            "rows": rows,
        },
        "use_policy": [
            "Missing artifacts are reported as missing/unknown and must not be filled by assumption.",
            "High-throughput synthetic training rows are not QA-pass data unless manual visual QA is explicitly present.",
            "Synthetic/rule-derived rows describe data generation coverage, not model performance.",
            "Mock rows validate pipeline mechanics only and must not be cited as trained model results.",
            "OOM checkpoint evaluation is an inference-resource failure, not a model accuracy number.",
        ],
    }


def build_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# NeurIPS Sprint Result Snapshot",
        "",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        "- Scope: dataset coverage, training summaries, mock pipeline checks, and baseline artifacts.",
        "- Guardrail: high-throughput synthetic data must not be reported as QA-pass unless manual visual QA is present.",
        "- Guardrail: mock, rule-oracle, and OOM eval artifacts must not be reported as trained-model performance.",
        "",
        "## Input Artifacts",
        "",
        "| Artifact | Path | Status | Nature |",
        "| --- | --- | --- | --- |",
    ]
    for name, record in summary["inputs"].items():
        lines.append(
            f"| `{name}` | `{record['path']}` | `{record['status']}` | {record['nature']} |"
        )

    lines.extend(
        [
            "",
            "## Paper Table Draft",
            "",
            "| Row | Status | Nature | Model | N | Strategy Acc. | Train Loss | Eval Loss | Notes |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in summary["paper_table"]["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _fmt(row.get("label", UNKNOWN)),
                    _fmt(row.get("status", UNKNOWN)),
                    _fmt(row.get("result_nature", UNKNOWN)),
                    _fmt(row.get("model", UNKNOWN)),
                    _fmt(row.get("n_records", row.get("n_state_inference_rows", UNKNOWN))),
                    _fmt(row.get("strategy_accuracy_vs_label", UNKNOWN)),
                    _fmt(row.get("train_loss", UNKNOWN)),
                    _fmt(row.get("eval_loss", UNKNOWN)),
                    _fmt(row.get("notes", "")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Dataset Coverage",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    dataset_row = summary["result_rows"][0]
    for key in [
        "n_sessions_loaded",
        "n_sessions_skipped",
        "n_state_inference_rows",
        "n_transition_modeling_rows",
        "n_policy_preference_rows",
        "n_world_model_continuation_rows",
        "n_states_with_action_contrast",
        "split_counts",
        "viewpoint_counts",
        "product_counts",
    ]:
        lines.append(f"| `{key}` | {_fmt(dataset_row.get(key, UNKNOWN))} |")

    lines.extend(
        [
            "",
            "## Use Policy",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["use_policy"])
    lines.append("")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dataset-stats", type=Path, default=DEFAULT_DATASET_STATS)
    parser.add_argument("--mock-eval", type=Path, default=DEFAULT_MOCK_EVAL)
    parser.add_argument("--sft-summary", type=Path, default=DEFAULT_SFT_SUMMARY)
    parser.add_argument("--zero-shot", type=Path, default=DEFAULT_ZERO_SHOT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--generated-at-utc", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = args.root.resolve()
    summary = build_summary(
        root=root,
        dataset_stats=args.dataset_stats,
        mock_eval=args.mock_eval,
        sft_summary=args.sft_summary,
        zero_shot=args.zero_shot,
        generated_at_utc=args.generated_at_utc,
    )

    summary_out = root / args.summary_out
    markdown_out = root / args.markdown_out
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
