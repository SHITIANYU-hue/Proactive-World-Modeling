import json
import shutil
from pathlib import Path

from piwm_data import reaction_templates, rules
from piwm_data.archive_loader import load_session
from scripts.continuation_prompt_builder import build_best_worst_prompts, build_continuation_prompt
from scripts.prompt_builder import forbidden_label_hits
from scripts.qa_gate import run_qa_for_continuation


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_session"


def copy_fixture(tmp_path, monkeypatch):
    archive_root = tmp_path / "tiny_session"
    shutil.copytree(FIXTURE_ROOT, archive_root)
    monkeypatch.chdir(tmp_path)
    return archive_root / "session_test_001"


def test_reaction_template_registry_covers_all_latent_states():
    assert set(reaction_templates.NEXT_STATE_TO_TEMPLATE) == set(rules.LATENT_STATES)


def test_action_visible_behavior_does_not_use_action_enum_labels():
    for action, text in rules.ACTION_VISIBLE_BEHAVIOR.items():
        assert action not in text
        assert forbidden_label_hits(text) == []


def test_continuation_prompt_has_no_forbidden_label_hits(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    record = load_session(session_dir)
    prompt = build_continuation_prompt(record, "A3_strong_recommend", continuation_role="worst")
    assert prompt["expected_next_state"] == "defensive_withdrawal"
    assert prompt["forbidden_label_hits"] == []
    assert forbidden_label_hits(prompt["kling_prompt"]) == []


def test_build_best_worst_prompts_selects_reward_extremes(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    record = load_session(session_dir)
    prompts = build_best_worst_prompts(record)
    assert [prompt["continuation_role"] for prompt in prompts] == ["best", "worst"]
    assert prompts[0]["candidate_action"] == record.best_action
    assert prompts[1]["expected_reward"] < prompts[0]["expected_reward"]


def test_run_qa_for_continuation_passes_with_manual_review(tmp_path):
    cdir = tmp_path / "cont"
    (cdir / "frames").mkdir(parents=True)
    for name in ("000.jpg", "001.jpg"):
        (cdir / "frames" / name).write_bytes(b"fake")
    (cdir / "video.mp4").write_bytes(b"fake")
    (cdir / "continuation_prompt.json").write_text(
        json.dumps(
            {
                "continuation_id": "session_test_001#worst_A3_strong_recommend",
                "parent_state_id": "session_test_001",
                "candidate_action": "A3_strong_recommend",
                "continuation_role": "worst",
                "continuation_viewpoint": "salesperson_observable",
                "expected_next_state": "defensive_withdrawal",
                "kling_prompt": "A customer steps back, looks away, and retracts hands after a firm visible recommendation.",
            }
        ),
        encoding="utf-8",
    )
    (cdir / "frame_manifest.json").write_text(
        json.dumps(
            {
                "sampled_frames": [
                    {"path": "frames/000.jpg", "timestamp_sec": 1.0, "role": "reaction_onset"},
                    {"path": "frames/001.jpg", "timestamp_sec": 3.0, "role": "reaction_peak"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (cdir / "qa_manual_review.json").write_text(
        json.dumps(
            {
                "reaction_visible": True,
                "reaction_matches_expected_state": True,
                "pre_action_continuity_pass": True,
                "no_scene_change": True,
                "no_new_subjects": True,
                "viewpoint_pass": True,
                "required_visibility": {
                    "reaction_visible": True,
                    "body_language_change_visible": True,
                    "pre_action_continuity_pass": True,
                    "no_scene_change": True,
                    "no_new_subjects": True,
                },
                "reaction_checklist": {
                    "step_back_or_body_turn_away": True,
                    "gaze_break": True,
                    "hands_retract_from_product": True,
                },
            }
        ),
        encoding="utf-8",
    )
    report = run_qa_for_continuation(cdir)
    assert report["overall_pass"] is True
    assert report["reaction_matches_expected_state"] is True
    assert (cdir / "qa_report.json").exists()


def test_archive_loader_loads_qa_passed_continuation(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    record = load_session(session_dir)
    prompt = build_continuation_prompt(record, "A2_offer_value_comparison", continuation_role="best")
    cdir = session_dir / "continuations" / "best_A2_offer_value_comparison"
    (cdir / "frames").mkdir(parents=True)
    for name in ("000.jpg", "001.jpg"):
        (cdir / "frames" / name).write_bytes(b"fake")
    (cdir / "video.mp4").write_bytes(b"fake")
    (cdir / "continuation_prompt.json").write_text(json.dumps(prompt), encoding="utf-8")
    (cdir / "frame_manifest.json").write_text(
        json.dumps(
            {
                "sampled_frames": [
                    {"path": "frames/000.jpg", "timestamp_sec": 1.0, "role": "reaction_onset"},
                    {"path": "frames/001.jpg", "timestamp_sec": 3.0, "role": "reaction_peak"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (cdir / "qa_report.json").write_text(
        json.dumps(
            {
                "overall_pass": True,
                "reaction_visible": True,
                "reaction_matches_expected_state": True,
                "pre_action_continuity_pass": True,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_session(session_dir)
    assert "A2_offer_value_comparison" in loaded.continuations
    assert loaded.continuations["A2_offer_value_comparison"].qa_overall_pass is True
