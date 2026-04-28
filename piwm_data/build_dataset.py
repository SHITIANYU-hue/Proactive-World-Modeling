"""CLI entry point for building PIWM data artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import rules
from .archive_loader import iter_archive, sample_frames
from .exporters import (
    build_policy_preference_row,
    export_policy_preference,
    export_state_inference,
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
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    archive_root = args.archive_root
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    total_sessions = _count_sessions(archive_root, args.limit)
    records: list[MainSchemaRecord] = []
    skipped_reasons: Counter[str] = Counter()

    try:
        iterator = iter_archive(archive_root, limit=args.limit)
        for record in iterator:
            try:
                sampled = record.model_copy(update={"images": sample_frames(record.images, args.frame_sample)})
                if not args.no_validate:
                    errors = validate_main_schema(sampled) + validate_image_paths(sampled, Path.cwd())
                    if errors:
                        raise ValueError("; ".join(errors))
                records.append(sampled)
            except Exception as exc:  # noqa: BLE001 - CLI records exception classes in stats.
                if args.strict:
                    raise
                skipped_reasons[type(exc).__name__] += 1
    except Exception as exc:  # iter_archive can raise while loading the next session.
        if args.strict:
            raise
        # Fall back to per-session loading so one bad directory does not stop all later sessions.
        records, skipped_reasons = _load_sessions_lenient(
            archive_root,
            limit=args.limit,
            frame_sample=args.frame_sample,
            no_validate=args.no_validate,
        )

    _write_main_schema(records, output_dir / "main_schema.jsonl")
    n_state = export_state_inference(records, output_dir / "state_inference.jsonl")
    n_transition = export_transition_modeling(records, output_dir / "transition_modeling.jsonl")
    n_preference = export_policy_preference(records, output_dir / "policy_preference.jsonl")
    n_preference_skipped = sum(1 for record in records if build_policy_preference_row(record) is None)

    stats = {
        "n_sessions_total": total_sessions,
        "n_sessions_loaded": len(records),
        "n_sessions_skipped": sum(skipped_reasons.values()),
        "n_sessions_anchor": sum(1 for record in records if record.is_anchor),
        "n_state_inference_rows": n_state,
        "n_transition_modeling_rows": n_transition,
        "n_policy_preference_rows": n_preference,
        "n_policy_preference_skipped_no_pair": n_preference_skipped,
        "skipped_reasons": dict(skipped_reasons),
        "rule_version": rules.RULE_VERSION,
        "frame_sample": args.frame_sample,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
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
            record = load_session(session_dir)
            sampled = record.model_copy(update={"images": sample_frames(record.images, frame_sample)})
            if not no_validate:
                errors = validate_main_schema(sampled) + validate_image_paths(sampled, Path.cwd())
                if errors:
                    raise ValueError("; ".join(errors))
            records.append(sampled)
        except Exception as exc:  # noqa: BLE001 - stats require exception class.
            skipped_reasons[type(exc).__name__] += 1
    return records, skipped_reasons


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


if __name__ == "__main__":
    raise SystemExit(main())

