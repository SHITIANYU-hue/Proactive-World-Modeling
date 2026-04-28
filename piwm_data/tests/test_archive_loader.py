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
    assert record.latent_state == "high_hesitation"
    assert record.intent == "compare_value_for_money"
    assert record.proactive_score == 4
    assert record.candidate_actions == [
        "A1_silent_observe",
        "A2_offer_value_comparison",
        "A4_open_with_question",
    ]
    assert record.best_action == "A2_offer_value_comparison"
    assert len(record.images) == 3
    assert record.images[0].relative_path == "tiny_session/session_test_001/frames/000.jpg"


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


def test_annotation_override_intent_updates_provenance(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path, monkeypatch)
    annotation = {"intent": "seek_reassurance"}
    (session_dir / "piwm_annotation.json").write_text(
        json.dumps(annotation, ensure_ascii=False),
        encoding="utf-8",
    )
    record = load_session(session_dir)
    assert record.intent == "seek_reassurance"
    assert any(
        item.field_name == "intent" and item.source == "annotation_override"
        for item in record.provenance
    )

