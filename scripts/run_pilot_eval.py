"""Run a minimal pilot evaluation artifact for the PIWM inference pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from piwm_infer.decision_loop import PIWMDecisionLoop
from piwm_infer.tests.fixtures.mock_vlm import MockVLM


def _read_jsonl(path: Path, limit: int | None) -> list[dict[str, Any]]:
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


def _safe_gold_action(row: dict[str, Any]) -> str | None:
    output = row.get("output")
    if not isinstance(output, dict):
        return None
    action = output.get("best_action")
    return action if isinstance(action, str) else None


def run_mock_eval(data_dir: Path, limit: int | None) -> dict[str, Any]:
    data_path = data_dir / "state_inference.jsonl"
    rows = _read_jsonl(data_path, limit)
    loop = PIWMDecisionLoop(MockVLM())

    outputs: list[dict[str, Any]] = []
    n_success = 0
    n_correct = 0
    parse_failure_count = 0
    fallback_count = 0

    for row in rows:
        state_id = row.get("state_id", "unknown")
        gold_action = _safe_gold_action(row)
        predicted_action: str | None = None
        used_fallback = False
        errors: list[str] = []

        try:
            decision = loop.decide(row)
            n_success += 1
            predicted_action = decision.chosen_action
            used_fallback = decision.used_fallback
            errors = list(decision.errors)
        except Exception as exc:  # noqa: BLE001 - artifact should record per-row pipeline failures.
            errors = [f"{type(exc).__name__}: {exc}"]

        if errors:
            parse_failure_count += 1
        if used_fallback:
            fallback_count += 1
        if gold_action is not None and predicted_action == gold_action:
            n_correct += 1

        outputs.append(
            {
                "state_id": state_id,
                "gold_action": gold_action,
                "predicted_action": predicted_action,
                "used_fallback": used_fallback,
                "errors": errors,
            }
        )

    n_records = len(rows)
    accuracy = (n_correct / n_records) if n_records else None
    return {
        "artifact": "pilot_eval",
        "mode": "mock",
        "model": "MockVLM",
        "is_training_result": False,
        "data_file": str(data_path),
        "n_records": n_records,
        "n_success": n_success,
        "parse_failure_count": parse_failure_count,
        "fallback_count": fallback_count,
        "strategy_accuracy_vs_label": accuracy,
        "outputs": outputs,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=["mock"], default="mock")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.limit is not None and args.limit < 0:
        raise SystemExit("--limit must be non-negative")

    result = run_mock_eval(args.data_dir, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
