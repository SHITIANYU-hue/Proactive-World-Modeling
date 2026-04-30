import json
import shutil
from pathlib import Path

import pytest

from piwm_data.archive_loader import (
    InvalidEnumValueError,
    MissingRequiredFieldError,
    load_session,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_session"


def copy_fixture(tmp_path, monkeypatch):
    archive_root = tmp_path / "tiny_session"
    shutil.copytree(FIXTURE_ROOT, archive_root)
    monkeypatch.chdir(tmp_path)
    return archive_root / "session_test_001"


def read_prompt(session_dir):
    return json.loads((session_dir / "prompt.json").read_text(encoding="utf-8"))


def write_prompt(session_dir, data):
    (session_dir / "prompt.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_load_tiny_session_fills_rule_fields(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    record = load_session(session_dir)
    assert record.state_id == "session_test_001"
    assert record.product_category == "luxury_watch"
    assert record.split is None
    assert record.latent_state == "high_hesitation"
    assert record.viewpoint == "salesperson_observable"
    assert record.intent == "compare_value_for_money"
    assert record.bdi.belief
    assert "long_dwell_with_price_check" not in record.bdi.belief
    assert record.bdi.desire
    assert record.bdi.intention
    assert record.proactive_score == 4
    assert record.candidate_actions == [
        "A1_silent_observe",
        "A2_offer_value_comparison",
        "A4_open_with_question",
        "A3_strong_recommend",
    ]
    assert record.best_action == "A2_offer_value_comparison"
    assert record.next_state_by_action["A2_offer_value_comparison"].next_bdi.intention
    assert record.next_state_by_action["A2_offer_value_comparison"].next_aida_stage == "desire"
    assert (
        record.next_state_by_action["A2_offer_value_comparison"].reward_components.final_reward
        == record.reward_by_action["A2_offer_value_comparison"]
    )
    assert len(record.images) == 3
    assert record.images[0].relative_path == "tiny_session/session_test_001/frames/000.jpg"


def test_invalid_split_raises_invalid_enum(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    prompt = read_prompt(session_dir)
    prompt["split"] = "not_a_split"
    write_prompt(session_dir, prompt)
    with pytest.raises(InvalidEnumValueError):
        load_session(session_dir)


def test_missing_required_prompt_field_raises(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    prompt = read_prompt(session_dir)
    prompt.pop("target_cue")
    write_prompt(session_dir, prompt)
    with pytest.raises(MissingRequiredFieldError):
        load_session(session_dir)


def test_invalid_cue_raises_invalid_enum(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    prompt = read_prompt(session_dir)
    prompt["target_cue"] = "not_a_cue"
    write_prompt(session_dir, prompt)
    with pytest.raises(InvalidEnumValueError):
        load_session(session_dir)


def test_invalid_viewpoint_raises_invalid_enum(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    prompt = read_prompt(session_dir)
    prompt["viewpoint"] = "not_a_viewpoint"
    write_prompt(session_dir, prompt)
    with pytest.raises(InvalidEnumValueError):
        load_session(session_dir)


def test_annotation_override_intent_updates_provenance(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    annotation = {"intent": "seek_reassurance"}
    (session_dir / "piwm_annotation.json").write_text(
        json.dumps(annotation, ensure_ascii=False),
        encoding="utf-8",
    )
    record = load_session(session_dir)
    assert record.intent == "seek_reassurance"
    assert record.bdi.intention == "look for reassurance or clarification"
    assert any(
        item.field_name == "intent" and item.source == "annotation_override"
        for item in record.provenance
    )
