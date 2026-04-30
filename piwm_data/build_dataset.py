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
    export_world_model_continuation,
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
    parser.add_argument("--require-continuation", action="store_true")
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
        require_continuation=args.require_continuation,
        strict=args.strict,
    )

    _write_main_schema(records, output_dir / "main_schema.jsonl")
    n_state = export_state_inference(records, output_dir / "state_inference.jsonl")
    n_state_with_cue = export_state_inference_with_cue(records, output_dir / "state_inference_with_cue.jsonl")
    n_transition = export_transition_modeling(records, output_dir / "transition_modeling.jsonl")
    n_preference = export_policy_preference(records, output_dir / "policy_preference.jsonl")
    n_world_model_continuation = export_world_model_continuation(records, output_dir / "world_model_continuation.jsonl")
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
        "n_world_model_continuation_rows": n_world_model_continuation,
        "skipped_reasons": dict(skipped_reasons),
        "require_qa_pass": not args.allow_unreviewed,
        "require_continuation": args.require_continuation,
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
    require_continuation: bool,
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
            if require_continuation and not any(c.qa_overall_pass for c in record.continuations.values()):
                raise ContinuationNotPassedError("no qa-passed continuation found")
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


class ContinuationNotPassedError(ValueError):
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
    continuation_role_counts: dict[str, int] = {}
    negative_reward_continuations = 0
    qa_pass_continuations = 0
    reward_gaps: list[float] = []
    for record in records:
        viewpoint = record.viewpoint
        viewpoint_counts[viewpoint] = viewpoint_counts.get(viewpoint, 0) + 1
        product_counts[record.product_category] = product_counts.get(record.product_category, 0) + 1
        if record.split is not None:
            split_counts[record.split] = split_counts.get(record.split, 0) + 1
        if _has_action_contrast(record):
            contrast_by_viewpoint[viewpoint] = contrast_by_viewpoint.get(viewpoint, 0) + 1
        passed_continuations = [continuation for continuation in record.continuations.values() if continuation.qa_overall_pass]
        for continuation in passed_continuations:
            role = continuation.continuation_role.value
            continuation_role_counts[role] = continuation_role_counts.get(role, 0) + 1
            qa_pass_continuations += 1
            if continuation.expected_reward < 0:
                negative_reward_continuations += 1
        if len(passed_continuations) >= 2:
            rewards = [continuation.expected_reward for continuation in passed_continuations]
            reward_gaps.append(max(rewards) - min(rewards))
    return {
        "n_transition_parent_states": len(records),
        "avg_actions_per_state": sum(action_counts) / len(action_counts) if action_counts else 0.0,
        "n_states_with_action_contrast": n_with_contrast,
        "n_states_without_action_contrast": len(records) - n_with_contrast,
        "n_sessions_by_viewpoint": dict(sorted(viewpoint_counts.items())),
        "n_sessions_by_product_category": dict(sorted(product_counts.items())),
        "n_sessions_by_split": dict(sorted(split_counts.items())),
        "n_states_with_action_contrast_by_viewpoint": dict(sorted(contrast_by_viewpoint.items())),
        "n_continuations_with_visual_qa_pass": qa_pass_continuations,
        "n_continuations_by_role": dict(sorted(continuation_role_counts.items())),
        "n_negative_reward_continuations": negative_reward_continuations,
        "best_worst_reward_gap_distribution": _reward_gap_distribution(reward_gaps),
    }


def _reward_gap_distribution(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "max": 0.0}
    values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2:
        median = values[mid]
    else:
        median = (values[mid - 1] + values[mid]) / 2
    return {"min": values[0], "median": median, "max": values[-1]}


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
