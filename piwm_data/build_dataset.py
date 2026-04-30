"""CLI entry point for building PIWM data artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import rules
from .archive_loader import sample_frames
from .exporters import (
    build_policy_preference_row,
    export_policy_preference,
    export_state_inference,
    export_state_inference_with_cue,
    export_transition_modeling,
)
from .schemas import MainSchemaRecord
from .validate import validate_image_paths, validate_main_schema


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PIWM JSONL training data.")
    parser.add_argument("--archive-root", type=Path, default=Path("Archive"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/piwm_dataset"))
    parser.add_argument("--frame-sample", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-unreviewed", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    archive_root = args.archive_root
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    total_sessions = _count_sessions(archive_root, args.limit)
    records: list[MainSchemaRecord] = []
    skipped_reasons: Counter[str] = Counter()

    records, skipped_reasons = _load_sessions_lenient(
        archive_root,
        limit=args.limit,
        frame_sample=args.frame_sample,
        no_validate=args.no_validate,
        require_qa_pass=not args.allow_unreviewed,
        strict=args.strict,
    )

    _write_main_schema(records, output_dir / "main_schema.jsonl")
    n_state = export_state_inference(records, output_dir / "state_inference.jsonl")
    n_state_with_cue = export_state_inference_with_cue(records, output_dir / "state_inference_with_cue.jsonl")
    n_transition = export_transition_modeling(records, output_dir / "transition_modeling.jsonl")
    n_preference = export_policy_preference(records, output_dir / "policy_preference.jsonl")
    n_preference_skipped = sum(1 for record in records if build_policy_preference_row(record) is None)

    stats = {
        "n_sessions_total": total_sessions,
        "n_sessions_loaded": len(records),
        "n_sessions_skipped": sum(skipped_reasons.values()),
        "n_sessions_anchor": sum(1 for record in records if record.is_anchor),
        "n_state_inference_rows": n_state,
        "n_state_inference_with_cue_rows": n_state_with_cue,
        "n_transition_modeling_rows": n_transition,
        "n_policy_preference_rows": n_preference,
        "n_policy_preference_skipped_no_pair": n_preference_skipped,
        "skipped_reasons": dict(skipped_reasons),
        "require_qa_pass": not args.allow_unreviewed,
        "rule_version": rules.RULE_VERSION,
        "frame_sample": args.frame_sample,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    stats.update(_world_model_stats(records))
    (output_dir / "_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def _load_sessions_lenient(
    archive_root: Path,
    limit: int | None,
    frame_sample: int,
    no_validate: bool,
    require_qa_pass: bool,
    strict: bool = False,
) -> tuple[list[MainSchemaRecord], Counter[str]]:
    from .archive_loader import load_session

    records: list[MainSchemaRecord] = []
    skipped_reasons: Counter[str] = Counter()
    session_dirs = [
        path
        for path in sorted(archive_root.iterdir())
        if path.is_dir() and not path.name.startswith("_")
    ]
    if limit is not None:
        session_dirs = session_dirs[:limit]
    for session_dir in session_dirs:
        try:
            if require_qa_pass:
                qa_ok, qa_reason = _session_qa_pass(session_dir)
                if not qa_ok:
                    raise QAGateNotPassedError(qa_reason)
            record = load_session(session_dir)
            sampled = record.model_copy(update={"images": sample_frames(record.images, frame_sample)})
            if not no_validate:
                errors = validate_main_schema(sampled) + validate_image_paths(sampled, Path.cwd())
                if errors:
                    raise ValueError("; ".join(errors))
            records.append(sampled)
        except Exception as exc:  # noqa: BLE001 - stats require exception class.
            if strict:
                raise
            skipped_reasons[type(exc).__name__] += 1
    return records, skipped_reasons


class QAGateNotPassedError(ValueError):
    pass


def _session_qa_pass(session_dir: Path) -> tuple[bool, str]:
    qa_path = session_dir / "qa_report.json"
    if not qa_path.exists():
        return False, "missing qa_report.json"
    try:
        report = json.loads(qa_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"invalid qa_report.json: {exc}"
    if report.get("overall_pass") is not True:
        return False, str(report.get("rejection_reason") or "overall_pass is not true")
    return True, "qa pass"


def _count_sessions(archive_root: Path, limit: int | None) -> int:
    if not archive_root.exists():
        return 0
    count = sum(1 for path in archive_root.iterdir() if path.is_dir() and not path.name.startswith("_"))
    return min(count, limit) if limit is not None else count


def _write_main_schema(records: list[MainSchemaRecord], out: Path) -> int:
    with out.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
    return len(records)


def _world_model_stats(records: list[MainSchemaRecord]) -> dict[str, int | float | dict[str, int]]:
    action_counts = [len(record.candidate_actions) for record in records]
    n_with_contrast = sum(1 for record in records if _has_action_contrast(record))
    viewpoint_counts: dict[str, int] = {}
    contrast_by_viewpoint: dict[str, int] = {}
    product_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    for record in records:
        viewpoint = record.viewpoint
        viewpoint_counts[viewpoint] = viewpoint_counts.get(viewpoint, 0) + 1
        product_counts[record.product_category] = product_counts.get(record.product_category, 0) + 1
        if record.split is not None:
            split_counts[record.split] = split_counts.get(record.split, 0) + 1
        if _has_action_contrast(record):
            contrast_by_viewpoint[viewpoint] = contrast_by_viewpoint.get(viewpoint, 0) + 1
    return {
        "n_transition_parent_states": len(records),
        "avg_actions_per_state": sum(action_counts) / len(action_counts) if action_counts else 0.0,
        "n_states_with_action_contrast": n_with_contrast,
        "n_states_without_action_contrast": len(records) - n_with_contrast,
        "n_sessions_by_viewpoint": dict(sorted(viewpoint_counts.items())),
        "n_sessions_by_product_category": dict(sorted(product_counts.items())),
        "n_sessions_by_split": dict(sorted(split_counts.items())),
        "n_states_with_action_contrast_by_viewpoint": dict(sorted(contrast_by_viewpoint.items())),
    }


def _has_action_contrast(record: MainSchemaRecord) -> bool:
    signatures = {
        (
            record.next_state_by_action[action].next_state,
            record.next_state_by_action[action].next_aida_stage,
            record.next_state_by_action[action].reward,
            record.next_state_by_action[action].risk,
            record.next_state_by_action[action].benefit,
        )
        for action in record.candidate_actions
    }
    return len(signatures) > 1


if __name__ == "__main__":
    raise SystemExit(main())
