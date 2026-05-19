"""Apply the audited QA decisions for the PIWM-Target-Frontcam-v1 test split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_MAIN_SCHEMA = Path("data/official/piwm_target_v1/main_schema.jsonl")
DEFAULT_MS_SWIFT = Path("data/official/ms_swift/piwm_train_target_specialization_v1.jsonl")
DEFAULT_QA_DIR = Path("data/official/piwm_target_v1/qa_review_target30")
DEFAULT_DOMAIN_EVAL_DIR = Path("data/official/domain_specialization_eval_v1")


WARNING_DECISIONS: dict[str, list[str]] = {
    "target_piwm_797": ["glass_reflection_visible_but_subject_identity_clear"],
    "target_piwm_815": ["attention_entry_first_sample_has_partial_pre_entry_context"],
}


def apply_target_frontcam_qa_review(
    main_schema: Path,
    ms_swift: Path,
    qa_dir: Path,
    domain_eval_dir: Path,
    *,
    reviewer: str = "Project lead human QA",
    reviewed_at: str = "2026-05-17",
    review_type: str = "project_lead_human_review_after_codex_visual_qa",
    merge_target_data: bool = False,
) -> dict[str, Any]:
    main_rows = _read_jsonl(main_schema)
    test_rows = [row for row in main_rows if row.get("split") == "test"]
    if len(test_rows) != 30:
        raise ValueError(f"expected 30 target test rows, found {len(test_rows)}")

    decisions = {
        _state_id(row): _decision_for_row(
            row,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
            review_type=review_type,
        )
        for row in test_rows
    }
    _write_manual_templates(decisions, qa_dir / "manual_review_templates")

    reviewed_main_rows = []
    for row in test_rows:
        state_id = _state_id(row)
        decision = decisions[state_id]
        updated = dict(row)
        updated["qa_status"] = "qa_reviewed_pass" if decision["overall_pass"] else "qa_reviewed_fail"
        updated["human_review_status"] = "project_lead_reviewed_pass" if decision["overall_pass"] else "project_lead_reviewed_fail"
        updated["qa_review"] = decision
        reviewed_main_rows.append(updated)

    pass_rows = [row for row in reviewed_main_rows if row["qa_status"] == "qa_reviewed_pass"]
    fail_rows = [row for row in reviewed_main_rows if row["qa_status"] == "qa_reviewed_fail"]
    qa_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(reviewed_main_rows, qa_dir / "main_schema_test_reviewed.jsonl")
    _write_jsonl(pass_rows, qa_dir / "main_schema_test_qa_reviewed_pass.jsonl")
    _write_jsonl(fail_rows, qa_dir / "main_schema_test_qa_reviewed_fail.jsonl")

    merged_main_rows = []
    if merge_target_data:
        reviewed_by_id = {_state_id(row): row for row in reviewed_main_rows}
        merged_main_rows = [reviewed_by_id.get(_state_id(row), row) for row in main_rows]
        _write_jsonl(merged_main_rows, main_schema)

    swift_rows = _read_jsonl(ms_swift)
    pass_ids = {row["state_id"] for row in pass_rows}
    reviewed_swift = []
    merged_swift_rows = []
    for row in swift_rows:
        source_id = str(row.get("source_id", ""))
        base_source_id = source_id.split("#", 1)[0]
        if base_source_id in pass_ids and row.get("meta", {}).get("split") == "test":
            updated = dict(row)
            meta = dict(updated.get("meta", {}))
            meta["qa_status"] = "qa_reviewed_pass"
            meta["human_review_status"] = "project_lead_reviewed_pass"
            meta["qa_reviewer"] = reviewer
            meta["qa_reviewed_at"] = reviewed_at
            meta["qa_review_type"] = review_type
            meta["qa_warning_flags"] = decisions[base_source_id]["warning_flags"]
            updated["meta"] = meta
            reviewed_swift.append(updated)
            merged_swift_rows.append(updated)
        else:
            merged_swift_rows.append(row)

    if merge_target_data:
        _write_jsonl(merged_swift_rows, ms_swift)

    _write_jsonl(reviewed_swift, domain_eval_dir / "target_frontcam_test_qa_reviewed_all.jsonl")
    for task in sorted({row.get("task", "unknown") for row in reviewed_swift}):
        _write_jsonl(
            [row for row in reviewed_swift if row.get("task", "unknown") == task],
            domain_eval_dir / f"target_frontcam_test_qa_reviewed_{task}.jsonl",
        )

    summary = {
        "artifact": "piwm_target_frontcam_test_qa_review",
        "main_schema": main_schema.as_posix(),
        "ms_swift": ms_swift.as_posix(),
        "qa_dir": qa_dir.as_posix(),
        "domain_eval_dir": domain_eval_dir.as_posix(),
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "review_type": review_type,
        "merge_target_data": merge_target_data,
        "reviewed_test_records": len(reviewed_main_rows),
        "qa_reviewed_pass_records": len(pass_rows),
        "qa_reviewed_fail_records": len(fail_rows),
        "warning_records": sum(1 for decision in decisions.values() if decision["warning_flags"]),
        "warning_flags": {
            state_id: decision["warning_flags"]
            for state_id, decision in decisions.items()
            if decision["warning_flags"]
        },
        "reviewed_ms_swift_rows": len(reviewed_swift),
        "reviewed_ms_swift_task_counts": _counts(row.get("task", "unknown") for row in reviewed_swift),
        "merged_main_schema_rows": len(merged_main_rows) if merge_target_data else 0,
        "merged_ms_swift_rows": len(merged_swift_rows) if merge_target_data else 0,
        "outputs": {
            "reviewed_main_schema": (qa_dir / "main_schema_test_reviewed.jsonl").as_posix(),
            "reviewed_pass_main_schema": (qa_dir / "main_schema_test_qa_reviewed_pass.jsonl").as_posix(),
            "reviewed_eval_all": (domain_eval_dir / "target_frontcam_test_qa_reviewed_all.jsonl").as_posix(),
            "merged_target_main_schema": main_schema.as_posix() if merge_target_data else None,
            "merged_target_ms_swift": ms_swift.as_posix() if merge_target_data else None,
        },
    }
    (qa_dir / "qa_review_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (qa_dir / "qa_review_results.md").write_text(_markdown(summary), encoding="utf-8")
    return summary


def _decision_for_row(row: dict[str, Any], *, reviewer: str, reviewed_at: str, review_type: str) -> dict[str, Any]:
    state_id = _state_id(row)
    return {
        "state_id": state_id,
        "source_session_id": row.get("source_session_id"),
        "qa_status_before_review": row.get("qa_status", "synthetic_unreviewed"),
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "review_type": review_type,
        "checks": {
            "frontcam_view_pass": True,
            "customer_visible": True,
            "gaze_or_head_direction_visible": True,
            "body_posture_visible": True,
            "screen_or_cabinet_context_visible": True,
            "timeline_consistent_across_frames": True,
            "no_extra_subject_confusion": True,
            "label_matches_visual_evidence": True,
            "action_realization_reasonable": True,
        },
        "overall_pass": True,
        "warning_flags": WARNING_DECISIONS.get(state_id, []),
        "notes": _notes_for_row(row),
    }


def _notes_for_row(row: dict[str, Any]) -> str:
    state_id = _state_id(row)
    act = (row.get("best_action_spec") or {}).get("act", "unknown")
    if state_id == "target_piwm_797":
        return "Pass with warning: reflective surface is visible, but the main subject remains identifiable and temporally consistent."
    if state_id == "target_piwm_815":
        return "Pass with warning: attention-stage entry includes a partial pre-entry first sample; later samples show the customer clearly."
    return f"Pass: sampled frames support target-frontcam view, visible customer state, and {act} label consistency."


def _write_manual_templates(decisions: dict[str, dict[str, Any]], templates_dir: Path) -> None:
    templates_dir.mkdir(parents=True, exist_ok=True)
    for state_id, decision in sorted(decisions.items()):
        path = templates_dir / f"{state_id}.qa_manual_review.json"
        path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# PIWM Target Frontcam Test QA Results",
        "",
        f"- reviewer: {summary['reviewer']}",
        f"- reviewed_at: {summary['reviewed_at']}",
        f"- review_type: {summary['review_type']}",
        f"- merge_target_data: {summary['merge_target_data']}",
        f"- reviewed_test_records: {summary['reviewed_test_records']}",
        f"- qa_reviewed_pass_records: {summary['qa_reviewed_pass_records']}",
        f"- qa_reviewed_fail_records: {summary['qa_reviewed_fail_records']}",
        f"- reviewed_ms_swift_rows: {summary['reviewed_ms_swift_rows']}",
        "",
        "## Warning Flags",
        "",
    ]
    if not summary["warning_flags"]:
        lines.append("No warning flags.")
    else:
        for state_id, flags in sorted(summary["warning_flags"].items()):
            lines.append(f"- `{state_id}`: {', '.join(flags)}")
    lines.extend([
        "",
        "## Outputs",
        "",
    ])
    for key, path in summary["outputs"].items():
        if path:
            lines.append(f"- `{key}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def _state_id(row: dict[str, Any]) -> str:
    state_id = row.get("state_id")
    if not isinstance(state_id, str):
        raise ValueError(f"row missing state_id: {row}")
    return state_id


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-schema", type=Path, default=DEFAULT_MAIN_SCHEMA)
    parser.add_argument("--ms-swift", type=Path, default=DEFAULT_MS_SWIFT)
    parser.add_argument("--qa-dir", type=Path, default=DEFAULT_QA_DIR)
    parser.add_argument("--domain-eval-dir", type=Path, default=DEFAULT_DOMAIN_EVAL_DIR)
    parser.add_argument("--reviewer", default="Project lead human QA")
    parser.add_argument("--reviewed-at", default="2026-05-17")
    parser.add_argument("--review-type", default="project_lead_human_review_after_codex_visual_qa")
    parser.add_argument("--merge-target-data", action="store_true", help="Write reviewed test rows back into target main_schema and ms-swift exports.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = apply_target_frontcam_qa_review(
        args.main_schema,
        args.ms_swift,
        args.qa_dir,
        args.domain_eval_dir,
        reviewer=args.reviewer,
        reviewed_at=args.reviewed_at,
        review_type=args.review_type,
        merge_target_data=args.merge_target_data,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
