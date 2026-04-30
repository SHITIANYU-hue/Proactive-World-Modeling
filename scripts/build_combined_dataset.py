"""Build one PIWM dataset from multiple generated archive roots."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from piwm_data import rules
from piwm_data.archive_loader import sample_frames
from piwm_data.build_dataset import (
    ContinuationNotPassedError,
    QAGateNotPassedError,
    _count_sessions,
    _has_action_contrast,
    _session_qa_pass,
    _world_model_stats,
    _write_main_schema,
)
from piwm_data.exporters import (
    build_policy_preference_row,
    export_policy_preference,
    export_state_inference,
    export_state_inference_with_cue,
    export_transition_modeling,
    export_world_model_continuation,
)
from piwm_data.validate import validate_image_paths, validate_main_schema


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build combined PIWM JSONL data from multiple archives.")
    parser.add_argument("--archive-root", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frame-sample", type=int, default=3)
    parser.add_argument("--limit-per-root", type=int, default=None)
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--allow-unreviewed", action="store_true")
    parser.add_argument("--require-continuation", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    records, source_rows, stats = build_combined_dataset(
        args.archive_root,
        args.output_dir,
        frame_sample=args.frame_sample,
        limit_per_root=args.limit_per_root,
        no_validate=args.no_validate,
        require_qa_pass=not args.allow_unreviewed,
        require_continuation=args.require_continuation,
        strict=args.strict,
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0 if records or source_rows else 1


def build_combined_dataset(
    archive_roots: list[Path],
    output_dir: Path,
    *,
    frame_sample: int = 3,
    limit_per_root: int | None = None,
    no_validate: bool = False,
    require_qa_pass: bool = True,
    require_continuation: bool = False,
    strict: bool = False,
) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any]]:
    from piwm_data.archive_loader import load_session

    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    source_rows: list[dict[str, Any]] = []
    seen_state_ids: dict[str, str] = {}
    skipped_reasons: Counter[str] = Counter()
    per_source: dict[str, Counter[str]] = defaultdict(Counter)
    total_sessions = 0

    for archive_root in archive_roots:
        source_name = archive_root.as_posix()
        if not archive_root.exists():
            skipped_reasons["ArchiveRootMissing"] += 1
            per_source[source_name]["missing_root"] += 1
            continue
        session_dirs = [
            path
            for path in sorted(archive_root.iterdir())
            if path.is_dir() and not path.name.startswith("_")
        ]
        if limit_per_root is not None:
            session_dirs = session_dirs[:limit_per_root]
        total_sessions += len(session_dirs)
        per_source[source_name]["total"] += len(session_dirs)

        for session_dir in session_dirs:
            try:
                if require_qa_pass:
                    qa_ok, qa_reason = _session_qa_pass(session_dir)
                    if not qa_ok:
                        raise QAGateNotPassedError(qa_reason)
                record = load_session(session_dir)
                if record.state_id in seen_state_ids:
                    raise DuplicateStateIDError(f"{record.state_id} already loaded from {seen_state_ids[record.state_id]}")
                if require_continuation and not any(c.qa_overall_pass for c in record.continuations.values()):
                    raise ContinuationNotPassedError("no qa-passed continuation found")
                sampled = record.model_copy(update={"images": sample_frames(record.images, frame_sample)})
                if not no_validate:
                    errors = validate_main_schema(sampled) + validate_image_paths(sampled, Path.cwd())
                    if errors:
                        raise ValueError("; ".join(errors))
                records.append(sampled)
                seen_state_ids[record.state_id] = source_name
                per_source[source_name]["loaded"] += 1
                source_rows.append(
                    {
                        "state_id": record.state_id,
                        "source_archive": source_name,
                        "session_dir": session_dir.as_posix(),
                        "viewpoint": record.viewpoint,
                        "product_category": record.product_category,
                        "split": record.split,
                        "target_cues": record.observable_cues,
                        "has_qa_passed_continuation": any(c.qa_overall_pass for c in record.continuations.values()),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - combined stats must preserve skip classes.
                if strict:
                    raise
                name = type(exc).__name__
                skipped_reasons[name] += 1
                per_source[source_name][f"skipped:{name}"] += 1

    _write_outputs(records, source_rows, output_dir)
    stats = _stats(records, source_rows, archive_roots, total_sessions, skipped_reasons, per_source, frame_sample, require_qa_pass, require_continuation)
    (output_dir / "_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records, source_rows, stats


class DuplicateStateIDError(ValueError):
    pass


def _write_outputs(records: list[Any], source_rows: list[dict[str, Any]], output_dir: Path) -> None:
    _write_main_schema(records, output_dir / "main_schema.jsonl")
    export_state_inference(records, output_dir / "state_inference.jsonl")
    export_state_inference_with_cue(records, output_dir / "state_inference_with_cue.jsonl")
    export_transition_modeling(records, output_dir / "transition_modeling.jsonl")
    export_policy_preference(records, output_dir / "policy_preference.jsonl")
    export_world_model_continuation(records, output_dir / "world_model_continuation.jsonl")
    with (output_dir / "source_archive_index.jsonl").open("w", encoding="utf-8") as handle:
        for row in source_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _stats(
    records: list[Any],
    source_rows: list[dict[str, Any]],
    archive_roots: list[Path],
    total_sessions: int,
    skipped_reasons: Counter[str],
    per_source: dict[str, Counter[str]],
    frame_sample: int,
    require_qa_pass: bool,
    require_continuation: bool,
) -> dict[str, Any]:
    source_loaded = Counter(row["source_archive"] for row in source_rows)
    stats: dict[str, Any] = {
        "artifact": "combined_piwm_dataset",
        "archive_roots": [root.as_posix() for root in archive_roots],
        "n_archive_roots": len(archive_roots),
        "n_sessions_total": total_sessions,
        "n_sessions_loaded": len(records),
        "n_sessions_skipped": sum(skipped_reasons.values()),
        "n_sessions_by_source_archive": dict(sorted(source_loaded.items())),
        "per_source": {source: dict(counter) for source, counter in sorted(per_source.items())},
        "skipped_reasons": dict(sorted(skipped_reasons.items())),
        "require_qa_pass": require_qa_pass,
        "require_continuation": require_continuation,
        "rule_version": rules.RULE_VERSION,
        "frame_sample": frame_sample,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_policy_preference_skipped_no_pair": sum(1 for record in records if build_policy_preference_row(record) is None),
        "n_state_inference_rows": len(records),
        "n_state_inference_with_cue_rows": len(records),
        "n_transition_modeling_rows": sum(len(record.candidate_actions) for record in records),
        "n_policy_preference_rows": sum(1 for record in records if build_policy_preference_row(record) is not None),
        "n_world_model_continuation_rows": sum(
            1
            for record in records
            for continuation in record.continuations.values()
            if continuation.qa_overall_pass
        ),
        "n_states_with_strict_action_contrast": sum(1 for record in records if _has_action_contrast(record)),
    }
    stats.update(_world_model_stats(records))
    return stats


if __name__ == "__main__":
    raise SystemExit(main())
