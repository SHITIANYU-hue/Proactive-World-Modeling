"""Run PIWM pilot zero-shot/baseline artifact generation.

The local ``rule_oracle`` row is deterministic and metadata-assisted. External
VLM rows are availability records only unless their adapters are implemented.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from piwm_infer.baselines import (
    API_BASELINES,
    LOCAL_BASELINES,
    api_status,
    compute_metrics,
    is_local_baseline,
    predict_rule_oracle,
    prediction_to_record,
)


DEFAULT_DATA_DIR = Path("data/official/piwm_world_model_v1")
DEFAULT_OUT = Path("data/piwm_results/pilot24_zero_shot_baselines.json")
DEFAULT_MODELS = ["rule_oracle", "gpt4v", "gemini", "claude", "qwen_vl"]


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if limit == 0:
        return []

    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def run_baselines(data_dir: Path, models: list[str], limit: int | None = None) -> dict[str, Any]:
    state_path = data_dir / "state_inference.jsonl"
    policy_path = data_dir / "policy_preference.jsonl"
    main_schema_path = data_dir / "main_schema.jsonl"

    state_rows = read_jsonl(state_path, limit)
    policy_rows = read_jsonl(policy_path, limit)
    main_schema_rows = read_jsonl(main_schema_path, limit)
    policy_by_id = {
        row.get("state_id"): row
        for row in policy_rows
        if isinstance(row.get("state_id"), str)
    }

    model_results = []
    for model in models:
        if is_local_baseline(model):
            model_results.append(_run_local_model(model, state_rows, policy_by_id))
        else:
            model_results.append(api_status(model))

    return {
        "artifact": "pilot24_zero_shot_baselines",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "is_training_result": False,
        "training_result": False,
        "data_dir": str(data_dir),
        "input_files": {
            "state_inference": str(state_path),
            "policy_preference": str(policy_path),
            "main_schema": str(main_schema_path),
        },
        "n_state_inference_rows": len(state_rows),
        "n_policy_preference_rows": len(policy_rows),
        "n_main_schema_rows": len(main_schema_rows),
        "notes": [
            "Local deterministic baselines are smoke/evaluation plumbing numbers, not trained PIWM results.",
            "External VLM baselines do not run network calls in this offline-safe runner; missing keys become api_unavailable rows.",
        ],
        "models": model_results,
    }


def _run_local_model(
    model: str,
    state_rows: list[dict[str, Any]],
    policy_by_id: dict[Any, dict[str, Any]],
) -> dict[str, Any]:
    if model != "rule_oracle":
        raise ValueError(f"Unsupported local baseline: {model}")

    outputs = []
    for row in state_rows:
        state_id = row.get("state_id", "unknown")
        policy_row = policy_by_id.get(state_id)
        prediction = predict_rule_oracle(row, policy_row)
        outputs.append(
            prediction_to_record(
                state_id=str(state_id),
                prediction=prediction,
                gold=_gold_from_state_row(row),
                policy_gold=_gold_from_policy_row(policy_row),
            )
        )

    return {
        "model": model,
        "status": "ok",
        "is_training_result": False,
        "baseline_type": "deterministic_metadata_assisted",
        "not_real_model_result": True,
        "metrics": compute_metrics(outputs),
        "outputs": outputs,
    }


def _gold_from_state_row(row: dict[str, Any]) -> dict[str, Any]:
    output = row.get("output")
    if not isinstance(output, dict):
        output = {}
    return {
        "aida_stage": output.get("aida_stage"),
        "state_subtype": output.get("state_subtype") or output.get("current_state"),
        "intent": output.get("intent"),
        "best_action": output.get("best_action"),
    }


def _gold_from_policy_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "chosen": row.get("chosen"),
        "rejected": row.get("rejected"),
        "reward_gap": row.get("reward_gap"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help=f"Models to include. Local: {sorted(LOCAL_BASELINES)}; API placeholders: {sorted(API_BASELINES)}",
    )
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit is not None and args.limit < 0:
        raise SystemExit("--limit must be non-negative")

    payload = run_baselines(args.data_dir, args.models, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
