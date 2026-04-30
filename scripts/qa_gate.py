"""First-pass QA gate for generated PIWM video sessions.

The gate is intentionally conservative. File and prompt-leak checks are fully
automatic; visual cue visibility and physical consistency require a manual
review JSON until a VLM-based reviewer is added.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from piwm_data import rules
from scripts.prompt_builder import forbidden_label_hits

QA_VERSION = "phase4_viewpoint_v1"
CONTINUATION_QA_VERSION = "phase7_continuation_v1"
DEFAULT_MANUAL_REVIEW = "qa_manual_review.json"

VIEWPOINT_REQUIRED_VISIBILITY = {
    "salesperson_observable": ["face_visible", "gaze_visible", "hands_visible", "product_visible", "price_area_visible"],
    "surveillance_oblique": ["body_trajectory_visible", "dwell_visible", "hands_or_arm_movement_visible", "product_area_visible"],
    "third_party_side": ["profile_visible", "head_direction_visible", "hands_visible", "product_visible"],
    "first_person_pov": ["customer_face_or_gaze_visible", "interaction_distance_visible", "product_partial_visible"],
}

CONTINUATION_REQUIRED_VISIBILITY = {
    "salesperson_observable": [
        "reaction_visible",
        "body_language_change_visible",
        "pre_action_continuity_pass",
        "no_scene_change",
        "no_new_subjects",
    ],
    "surveillance_oblique": [
        "body_trajectory_change_visible",
        "pre_action_continuity_pass",
        "no_scene_change",
    ],
    "third_party_side": [
        "reaction_visible",
        "head_direction_change_visible",
        "pre_action_continuity_pass",
        "no_scene_change",
    ],
    "first_person_pov": [
        "reaction_visible",
        "interaction_distance_visible",
        "pre_action_continuity_pass",
        "no_scene_change",
    ],
}

CONTINUATION_REACTION_CHECKLIST = {
    "engaged_dialogue": ["body_opens_up", "eye_contact_or_head_turn_to_salesperson", "stays_or_moves_in"],
    "defensive_withdrawal": ["step_back_or_body_turn_away", "gaze_break", "hands_retract_from_product"],
    "continued_hesitation": ["no_clear_engagement", "no_clear_withdrawal", "stays_in_position"],
    "disengaged": ["walks_away_or_turns_to_leave", "no_further_product_interaction"],
    "active_evaluation": ["continues_product_examining", "hands_stay_on_or_near_product", "no_body_reorientation"],
    "high_hesitation": ["checks_price_or_product_again", "closed_or_cautious_posture", "stays_undecided"],
    "ready_to_decide": ["orients_to_service_area", "stays_near_product", "prepares_to_ask_or_decide"],
    "early_browsing": ["light_browsing_continues", "minimal_product_contact", "noncommittal_movement"],
    "post_decision_reassurance": ["selected_product_remains_focus", "seeks_confirmation", "no_withdrawal"],
}


def run_qa_for_session(session_dir: Path, overwrite: bool = True) -> dict[str, Any]:
    prompt_path = session_dir / "prompt.json"
    video_path = session_dir / "video.mp4"
    manifest_path = session_dir / "frame_manifest.json"
    manual_review_path = session_dir / DEFAULT_MANUAL_REVIEW

    prompt = _read_json(prompt_path) if prompt_path.exists() else {}
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    manual_review = _read_json(manual_review_path) if manual_review_path.exists() else {}
    viewpoint = prompt.get("viewpoint") or manifest.get("viewpoint") or rules.DEFAULT_VIEWPOINT
    if viewpoint not in rules.VIEWPOINTS:
        viewpoint = rules.DEFAULT_VIEWPOINT

    frame_entries = manifest.get("sampled_frames", [])
    frame_paths = [session_dir / entry.get("path", "") for entry in frame_entries]
    prompt_text = prompt.get("kling_prompt", "") or prompt.get("behavior_description", "")
    leakage_hits = forbidden_label_hits(prompt_text) if prompt_text else []

    file_checks = {
        "prompt_json_exists": prompt_path.exists(),
        "video_exists": video_path.exists(),
        "frame_manifest_exists": manifest_path.exists(),
        "sampled_frame_count": len(frame_entries),
        "sampled_frames_exist": bool(frame_entries) and all(path.exists() for path in frame_paths),
    }

    review_fields = {
        "cue_visible_in_video": manual_review.get("cue_visible_in_video"),
        "cue_visible_in_sampled_frames": manual_review.get("cue_visible_in_sampled_frames"),
        "physical_consistency_pass": manual_review.get("physical_consistency_pass"),
        "extra_subjects": manual_review.get("extra_subjects"),
        "reviewer_notes": manual_review.get("reviewer_notes"),
    }
    required_visibility = _required_visibility(viewpoint, manual_review.get("required_visibility", {}))
    viewpoint_pass = manual_review.get("viewpoint_pass")
    if viewpoint_pass is None and required_visibility:
        if all(value is not None for value in required_visibility.values()):
            viewpoint_pass = all(value is True for value in required_visibility.values())
    prompt_physical_pass = _prompt_physical_consistency(prompt)
    physical_consistency_pass = review_fields["physical_consistency_pass"]
    if physical_consistency_pass is None:
        physical_consistency_pass = prompt_physical_pass
    else:
        physical_consistency_pass = bool(physical_consistency_pass) and prompt_physical_pass

    file_checks_pass = (
        file_checks["prompt_json_exists"]
        and file_checks["video_exists"]
        and file_checks["frame_manifest_exists"]
        and file_checks["sampled_frame_count"] >= 3
        and file_checks["sampled_frames_exist"]
    )
    label_leakage = bool(leakage_hits)
    cue_visible_in_video = review_fields["cue_visible_in_video"]
    cue_visible_in_sampled_frames = review_fields["cue_visible_in_sampled_frames"]
    extra_subjects = review_fields["extra_subjects"]

    manual_review_required = any(
        value is None
        for value in (
            review_fields["cue_visible_in_video"],
            review_fields["cue_visible_in_sampled_frames"],
            review_fields["physical_consistency_pass"],
            review_fields["extra_subjects"],
            viewpoint_pass,
        )
    )

    video_level_pass = (
        file_checks_pass
        and not label_leakage
        and physical_consistency_pass is True
        and cue_visible_in_video is True
        and extra_subjects is False
        and viewpoint_pass is True
    )
    sampled_frames_pass = (
        file_checks_pass
        and cue_visible_in_sampled_frames is True
    )
    overall_pass = video_level_pass and sampled_frames_pass

    report = {
        "qa_version": QA_VERSION,
        "session_id": prompt.get("session_id", session_dir.name),
        "viewpoint": viewpoint,
        "target_cue": prompt.get("target_cue"),
        "training_input_mode": prompt.get("training_input_mode"),
        "file_checks_pass": file_checks_pass,
        "video_level_pass": video_level_pass,
        "sampled_frames_pass": sampled_frames_pass,
        "overall_pass": overall_pass,
        "cue_visible_in_video": cue_visible_in_video,
        "cue_visible_in_sampled_frames": cue_visible_in_sampled_frames,
        "physical_consistency_pass": physical_consistency_pass,
        "prompt_physical_consistency_pass": prompt_physical_pass,
        "viewpoint_pass": viewpoint_pass,
        "required_visibility": required_visibility,
        "label_leakage": label_leakage,
        "label_leakage_hits": leakage_hits,
        "extra_subjects": extra_subjects,
        "manual_review_required": manual_review_required,
        "rejection_reason": None if overall_pass else _rejection_reason(
            file_checks_pass=file_checks_pass,
            label_leakage=label_leakage,
            physical_consistency_pass=physical_consistency_pass,
            viewpoint_pass=viewpoint_pass,
            cue_visible_in_video=cue_visible_in_video,
            cue_visible_in_sampled_frames=cue_visible_in_sampled_frames,
            extra_subjects=extra_subjects,
            manual_review_required=manual_review_required,
        ),
        "checks": {
            "files": file_checks,
            "manual_review_path": manual_review_path.as_posix() if manual_review_path.exists() else None,
            "frame_manifest": manifest_path.as_posix() if manifest_path.exists() else None,
            "video": video_path.as_posix() if video_path.exists() else None,
        },
        "reviewer_notes": review_fields["reviewer_notes"],
    }
    if overwrite:
        (session_dir / "qa_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def run_qa_for_archive(archive_root: Path, overwrite: bool = True) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for session_dir in _session_dirs(archive_root):
        reports.append(run_qa_for_session(session_dir, overwrite=overwrite))
    return reports


def run_qa_for_continuation(continuation_dir: Path, overwrite: bool = True) -> dict[str, Any]:
    prompt_path = continuation_dir / "continuation_prompt.json"
    video_path = continuation_dir / "video.mp4"
    manifest_path = continuation_dir / "frame_manifest.json"
    manual_review_path = continuation_dir / DEFAULT_MANUAL_REVIEW

    prompt = _read_json(prompt_path) if prompt_path.exists() else {}
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    manual_review = _read_json(manual_review_path) if manual_review_path.exists() else {}
    viewpoint = prompt.get("continuation_viewpoint") or manifest.get("viewpoint") or rules.DEFAULT_VIEWPOINT
    if viewpoint not in rules.VIEWPOINTS:
        viewpoint = rules.DEFAULT_VIEWPOINT

    frame_entries = manifest.get("sampled_frames", [])
    frame_paths = [continuation_dir / entry.get("path", "") for entry in frame_entries]
    prompt_text = prompt.get("kling_prompt", "")
    leakage_hits = forbidden_label_hits(prompt_text) if prompt_text else []
    expected_next_state = prompt.get("expected_next_state")

    file_checks = {
        "continuation_prompt_exists": prompt_path.exists(),
        "video_exists": video_path.exists(),
        "frame_manifest_exists": manifest_path.exists(),
        "sampled_frame_count": len(frame_entries),
        "sampled_frames_exist": bool(frame_entries) and all(path.exists() for path in frame_paths),
    }
    file_checks_pass = (
        file_checks["continuation_prompt_exists"]
        and file_checks["video_exists"]
        and file_checks["frame_manifest_exists"]
        and file_checks["sampled_frame_count"] >= 2
        and file_checks["sampled_frames_exist"]
    )
    required_visibility = _continuation_required_visibility(viewpoint, manual_review.get("required_visibility", {}))
    reaction_checklist = _reaction_checklist(expected_next_state, manual_review.get("reaction_checklist", {}))
    reaction_visible = manual_review.get("reaction_visible")
    reaction_matches_expected_state = manual_review.get("reaction_matches_expected_state")
    pre_action_continuity_pass = manual_review.get("pre_action_continuity_pass")
    no_scene_change = manual_review.get("no_scene_change")
    no_new_subjects = manual_review.get("no_new_subjects")
    viewpoint_pass = manual_review.get("viewpoint_pass")
    if viewpoint_pass is None and required_visibility:
        if all(value is not None for value in required_visibility.values()):
            viewpoint_pass = all(value is True for value in required_visibility.values())
    manual_review_required = any(
        value is None
        for value in (
            reaction_visible,
            reaction_matches_expected_state,
            pre_action_continuity_pass,
            no_scene_change,
            no_new_subjects,
            viewpoint_pass,
        )
    )
    label_leakage = bool(leakage_hits)
    overall_pass = (
        file_checks_pass
        and not label_leakage
        and reaction_visible is True
        and reaction_matches_expected_state is True
        and pre_action_continuity_pass is True
        and no_scene_change is True
        and no_new_subjects is True
        and viewpoint_pass is True
    )
    report = {
        "qa_version": CONTINUATION_QA_VERSION,
        "continuation_id": prompt.get("continuation_id", continuation_dir.name),
        "parent_state_id": prompt.get("parent_state_id"),
        "candidate_action": prompt.get("candidate_action"),
        "continuation_role": prompt.get("continuation_role"),
        "expected_next_state": expected_next_state,
        "viewpoint": viewpoint,
        "file_checks_pass": file_checks_pass,
        "overall_pass": overall_pass,
        "reaction_visible": reaction_visible,
        "reaction_matches_expected_state": reaction_matches_expected_state,
        "pre_action_continuity_pass": pre_action_continuity_pass,
        "no_scene_change": no_scene_change,
        "no_new_subjects": no_new_subjects,
        "viewpoint_pass": viewpoint_pass,
        "required_visibility": required_visibility,
        "reaction_checklist": reaction_checklist,
        "label_leakage": label_leakage,
        "label_leakage_hits": leakage_hits,
        "manual_review_required": manual_review_required,
        "rejection_reason": None if overall_pass else _continuation_rejection_reason(
            file_checks_pass=file_checks_pass,
            label_leakage=label_leakage,
            reaction_visible=reaction_visible,
            reaction_matches_expected_state=reaction_matches_expected_state,
            pre_action_continuity_pass=pre_action_continuity_pass,
            no_scene_change=no_scene_change,
            no_new_subjects=no_new_subjects,
            viewpoint_pass=viewpoint_pass,
            manual_review_required=manual_review_required,
        ),
        "checks": {
            "files": file_checks,
            "manual_review_path": manual_review_path.as_posix() if manual_review_path.exists() else None,
            "frame_manifest": manifest_path.as_posix() if manifest_path.exists() else None,
            "video": video_path.as_posix() if video_path.exists() else None,
        },
        "reviewer_notes": manual_review.get("reviewer_notes"),
    }
    if overwrite:
        (continuation_dir / "qa_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run first-pass PIWM QA gate.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--session-dir", type=Path)
    group.add_argument("--archive-root", type=Path)
    parser.add_argument("--index-out", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    if args.session_dir:
        reports = [run_qa_for_session(args.session_dir, overwrite=not args.no_write)]
    else:
        reports = run_qa_for_archive(args.archive_root, overwrite=not args.no_write)

    if args.index_out:
        _write_jsonl(reports, args.index_out)

    summary = {
        "n_sessions": len(reports),
        "n_overall_pass": sum(1 for report in reports if report["overall_pass"]),
        "n_manual_review_required": sum(1 for report in reports if report["manual_review_required"]),
        "n_viewpoint_fail": sum(1 for report in reports if report["viewpoint_pass"] is not True),
        "n_label_leakage": sum(1 for report in reports if report["label_leakage"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _prompt_physical_consistency(prompt: dict[str, Any]) -> bool:
    cue = prompt.get("target_cue")
    scene = json.dumps(prompt.get("kling_prompt_sections", {}).get("scene", ""), ensure_ascii=False)
    prompt_text = prompt.get("kling_prompt", "")
    text = f"{scene}\n{prompt_text}".lower()
    if cue in {"repeated_product_handling", "trying_on_or_testing"}:
        return ("open presentation tray" in text or "accessible demo" in text) and "inside any glass case" not in text
    return True


def _required_visibility(viewpoint: str, manual_visibility: Any) -> dict[str, bool | None]:
    manual_visibility = manual_visibility if isinstance(manual_visibility, dict) else {}
    return {
        field: manual_visibility.get(field)
        for field in VIEWPOINT_REQUIRED_VISIBILITY[viewpoint]
    }


def _continuation_required_visibility(viewpoint: str, manual_visibility: Any) -> dict[str, bool | None]:
    manual_visibility = manual_visibility if isinstance(manual_visibility, dict) else {}
    return {
        field: manual_visibility.get(field)
        for field in CONTINUATION_REQUIRED_VISIBILITY[viewpoint]
    }


def _reaction_checklist(expected_next_state: str | None, manual_checklist: Any) -> dict[str, bool | None]:
    manual_checklist = manual_checklist if isinstance(manual_checklist, dict) else {}
    fields = CONTINUATION_REACTION_CHECKLIST.get(str(expected_next_state), [])
    return {field: manual_checklist.get(field) for field in fields}


def _rejection_reason(
    *,
    file_checks_pass: bool,
    label_leakage: bool,
    physical_consistency_pass: bool | None,
    viewpoint_pass: bool | None,
    cue_visible_in_video: bool | None,
    cue_visible_in_sampled_frames: bool | None,
    extra_subjects: bool | None,
    manual_review_required: bool,
) -> str:
    reasons: list[str] = []
    if not file_checks_pass:
        reasons.append("required files or sampled frames missing")
    if label_leakage:
        reasons.append("prompt contains internal labels")
    if physical_consistency_pass is not True:
        reasons.append("physical consistency not confirmed")
    if viewpoint_pass is not True:
        reasons.append("viewpoint visibility not confirmed")
    if cue_visible_in_video is not True:
        reasons.append("target cue visibility in video not confirmed")
    if cue_visible_in_sampled_frames is not True:
        reasons.append("target cue visibility in sampled frames not confirmed")
    if extra_subjects is not False:
        reasons.append("extra subjects not ruled out")
    if manual_review_required:
        reasons.append("manual review incomplete")
    return "; ".join(reasons)


def _continuation_rejection_reason(
    *,
    file_checks_pass: bool,
    label_leakage: bool,
    reaction_visible: bool | None,
    reaction_matches_expected_state: bool | None,
    pre_action_continuity_pass: bool | None,
    no_scene_change: bool | None,
    no_new_subjects: bool | None,
    viewpoint_pass: bool | None,
    manual_review_required: bool,
) -> str:
    reasons: list[str] = []
    if not file_checks_pass:
        reasons.append("required continuation files or sampled frames missing")
    if label_leakage:
        reasons.append("continuation prompt contains internal labels")
    if reaction_visible is not True:
        reasons.append("reaction visibility not confirmed")
    if reaction_matches_expected_state is not True:
        reasons.append("reaction does not match expected next state")
    if pre_action_continuity_pass is not True:
        reasons.append("pre-action continuity not confirmed")
    if no_scene_change is not True:
        reasons.append("scene continuity not confirmed")
    if no_new_subjects is not True:
        reasons.append("new subjects not ruled out")
    if viewpoint_pass is not True:
        reasons.append("continuation viewpoint visibility not confirmed")
    if manual_review_required:
        reasons.append("manual review incomplete")
    return "; ".join(reasons)


def _session_dirs(archive_root: Path) -> list[Path]:
    if not archive_root.exists():
        return []
    return [
        path
        for path in sorted(archive_root.iterdir())
        if path.is_dir() and not path.name.startswith("_")
    ]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count


if __name__ == "__main__":
    raise SystemExit(main())
