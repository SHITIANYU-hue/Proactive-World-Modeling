"""Dependency-free DPO data adapter for PIWM action preference rows."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .prompts import build_action_prompt
from .targets import build_action_target


DEFAULT_INPUT = Path("data/official/piwm_world_model_v1/policy_preference.jsonl")
DEFAULT_OUTPUT_DIR = Path("data/piwm_results/dpo_adapter_smoke")
DEFAULT_OUTPUT_JSONL = DEFAULT_OUTPUT_DIR / "dpo_train_smoke.jsonl"
DEFAULT_SUMMARY_JSON = DEFAULT_OUTPUT_DIR / "summary.json"


@dataclass(frozen=True)
class MalformedRecord:
    line_number: int
    state_id: str | None
    reason: str


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_preference_record(record: dict[str, Any]) -> list[str]:
    """Return validation errors for one policy-preference row."""
    errors: list[str] = []
    reward_gap = record.get("reward_gap")
    if not isinstance(reward_gap, (int, float)):
        errors.append("reward_gap_missing_or_non_numeric")
    elif reward_gap <= 0:
        errors.append("reward_gap_must_be_positive")

    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not _non_empty_text(chosen):
        errors.append("chosen_empty")
    if not _non_empty_text(rejected):
        errors.append("rejected_empty")
    if _non_empty_text(chosen) and _non_empty_text(rejected) and chosen == rejected:
        errors.append("chosen_equals_rejected")

    for side in ("chosen", "rejected"):
        block = record.get(f"{side}_json")
        if not isinstance(block, dict):
            errors.append(f"{side}_json_missing")
            continue
        if not _non_empty_text(block.get("action")):
            errors.append(f"{side}_json_action_empty")
        if not _non_empty_text(block.get("rationale")):
            errors.append(f"{side}_json_rationale_empty")

    meta = record.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta_missing")
    else:
        frames = meta.get("frames")
        if frames is not None and not isinstance(frames, list):
            errors.append("meta_frames_not_list")
        if "state_summary" not in meta:
            errors.append("meta_state_summary_missing")
        if "candidate_block" not in meta:
            errors.append("meta_candidate_block_missing")

    return errors


def preference_to_dpo_pair(record: dict[str, Any]) -> dict[str, Any]:
    """Convert one validated policy-preference row to a DPO training pair."""
    meta = record["meta"]
    return {
        "prompt": build_action_prompt(record),
        "chosen": build_action_target(record, "chosen"),
        "rejected": build_action_target(record, "rejected"),
        "images": list(meta.get("frames", [])),
        "meta": {
            "state_id": record.get("state_id"),
            "source_prompt": record.get("prompt"),
            "chosen_action": record.get("chosen"),
            "rejected_action": record.get("rejected"),
            "reward_gap": float(record["reward_gap"]),
            "split": meta.get("split"),
            "product_category": meta.get("product_category"),
            "viewpoint": meta.get("viewpoint"),
            "rule_version": meta.get("rule_version"),
            "is_training_result": False,
        },
        "is_training_result": False,
    }


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any] | None, str | None]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_number, None, f"json_decode_error:{exc.msg}"
                continue
            if not isinstance(parsed, dict):
                yield line_number, None, "row_not_object"
                continue
            yield line_number, parsed, None


def build_dpo_dataset(input_path: Path, output_jsonl: Path, summary_json: Path) -> dict[str, Any]:
    """Convert a policy-preference JSONL file and write smoke artifacts."""
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    written = 0
    malformed: list[MalformedRecord] = []

    with output_jsonl.open("w", encoding="utf-8") as out:
        for line_number, record, parse_error in iter_jsonl(input_path):
            total += 1
            if parse_error is not None or record is None:
                malformed.append(MalformedRecord(line_number, None, parse_error or "unknown_parse_error"))
                continue

            errors = validate_preference_record(record)
            if errors:
                state_id = record.get("state_id") if isinstance(record.get("state_id"), str) else None
                malformed.append(MalformedRecord(line_number, state_id, ",".join(errors)))
                continue

            pair = preference_to_dpo_pair(record)
            out.write(json.dumps(pair, ensure_ascii=False) + "\n")
            written += 1

    summary = {
        "is_training_result": False,
        "input_path": str(input_path),
        "output_jsonl": str(output_jsonl),
        "total_records": total,
        "written_pairs": written,
        "malformed_count": len(malformed),
        "malformed_records": [
            {
                "line_number": item.line_number,
                "state_id": item.state_id,
                "reason": item.reason,
            }
            for item in malformed
        ],
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_dpo_dataset(args.input, args.output_jsonl, args.summary_json)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
