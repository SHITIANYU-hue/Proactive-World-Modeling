"""Build mixed general+target ms-swift data for PIWM domain-specialization experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_GENERAL = Path("data/official/ms_swift/piwm_train_synth_v2.jsonl")
DEFAULT_TARGET = Path("data/official/ms_swift/piwm_train_target_specialization_v1.jsonl")
DEFAULT_OUTPUT = Path("data/official/ms_swift/piwm_train_general_plus_target_v1.jsonl")


def build_domain_specialization_dataset(
    general_jsonl: Path,
    target_jsonl: Path,
    output_jsonl: Path,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    task_counts: dict[str, dict[str, int]] = {"general": {}, "target": {}}

    for role, path in [("general", general_jsonl), ("target", target_jsonl)]:
        for row in _read_jsonl(path):
            row.setdefault("meta", {})
            row["meta"]["corpus_role"] = role
            row["meta"]["domain_specialization_stage"] = "stage1_general" if role == "general" else "stage2_target"
            rows.append(row)
            counts[role] = counts.get(role, 0) + 1
            task = row.get("task", "unknown")
            task_counts[role][task] = task_counts[role].get(task, 0) + 1

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")

    summary = {
        "artifact": "piwm_general_plus_target_ms_swift",
        "is_training_result": False,
        "general_jsonl": general_jsonl.as_posix(),
        "target_jsonl": target_jsonl.as_posix(),
        "output_jsonl": output_jsonl.as_posix(),
        "n_examples": len(rows),
        "corpus_role_counts": counts,
        "task_counts": task_counts,
        "training_usage": {
            "stage1_general": general_jsonl.as_posix(),
            "stage2_target": target_jsonl.as_posix(),
            "mixed_view_joint_sft": output_jsonl.as_posix(),
        },
        "qa_warning": "target rows are synthetic_unreviewed until manual target QA is complete",
    }
    output_jsonl.with_name(f"{output_jsonl.stem}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--general-jsonl", type=Path, default=DEFAULT_GENERAL)
    parser.add_argument("--target-jsonl", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_domain_specialization_dataset(args.general_jsonl, args.target_jsonl, args.output_jsonl)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
