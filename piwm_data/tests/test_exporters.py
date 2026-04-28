import json
from pathlib import Path

from piwm_data import rules
from piwm_data.exporters import (
    build_policy_preference_row,
    export_policy_preference,
    export_state_inference,
    export_transition_modeling,
)
from piwm_data.schemas import ActionOutcome, FrameRef, MainSchemaRecord, Persona, Provenance


def make_record(**overrides):
    data = {
        "state_id": "session_test_001",
        "images": [FrameRef(index=0, relative_path="Archive/session_test_001/frames/000.jpg")],
        "observable_cues": ["long_dwell_with_price_check"],
        "persona": Persona(type="price_sensitive_cautious", description="测试用 persona"),
        "aida_stage": "interest",
        "latent_state": "high_hesitation",
        "intent": "compare_value_for_money",
        "proactive_score": 4,
        "candidate_actions": [
            "A1_silent_observe",
            "A2_offer_value_comparison",
            "A4_open_with_question",
        ],
        "best_action": "A2_offer_value_comparison",
        "next_state_by_action": {
            "A1_silent_observe": ActionOutcome(
                next_state="continued_hesitation",
                reward=0.3,
                risk="low",
                benefit="medium",
                rationale="silent rationale",
            ),
            "A2_offer_value_comparison": ActionOutcome(
                next_state="engaged_dialogue",
                reward=0.8,
                risk="low",
                benefit="high",
                rationale="best rationale",
            ),
            "A4_open_with_question": ActionOutcome(
                next_state="engaged_dialogue",
                reward=0.6,
                risk="low",
                benefit="high",
                rationale="question rationale",
            ),
        },
        "reward_by_action": {
            "A1_silent_observe": 0.3,
            "A2_offer_value_comparison": 0.8,
            "A4_open_with_question": 0.6,
        },
        "rationale": None,
        "provenance": [Provenance(field_name="latent_state", source="rule_derived", rule_version=rules.RULE_VERSION)],
        "is_anchor": False,
    }
    data.update(overrides)
    return MainSchemaRecord(**data)


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_state_inference_exports_one_row(tmp_path):
    out = tmp_path / "state_inference.jsonl"
    count = export_state_inference([make_record()], out)
    rows = read_jsonl(out)
    assert count == 1
    assert len(rows) == 1
    assert rows[0]["output"]["current_state"] == "high_hesitation"
    assert rows[0]["input"]["history_summary"] is None


def test_transition_modeling_exports_one_row_per_candidate(tmp_path):
    record = make_record()
    out = tmp_path / "transition_modeling.jsonl"
    count = export_transition_modeling([record], out)
    rows = read_jsonl(out)
    assert count == len(record.candidate_actions)
    assert rows[0]["state_id"].startswith("session_test_001#")
    assert "worth_doing" in rows[0]["output"]


def test_policy_preference_candidate_count_one_exports_zero_rows(tmp_path):
    record = make_record()
    only_action = "A1_silent_observe"
    bad_record = MainSchemaRecord.model_construct(
        **{
            **record.model_dump(),
            "candidate_actions": [only_action],
            "best_action": only_action,
            "next_state_by_action": {only_action: record.next_state_by_action[only_action]},
            "reward_by_action": {only_action: record.reward_by_action[only_action]},
        }
    )
    out = tmp_path / "policy_preference.jsonl"
    count = export_policy_preference([bad_record], out)
    assert count == 0
    assert out.read_text(encoding="utf-8") == ""


def test_policy_preference_all_rewards_equal_exports_zero_rows(tmp_path):
    record = make_record(
        reward_by_action={
            "A1_silent_observe": 0.5,
            "A2_offer_value_comparison": 0.5,
            "A4_open_with_question": 0.5,
        },
        next_state_by_action={
            "A1_silent_observe": ActionOutcome(next_state="continued_hesitation", reward=0.5, risk="low", benefit="medium"),
            "A2_offer_value_comparison": ActionOutcome(next_state="engaged_dialogue", reward=0.5, risk="low", benefit="high"),
            "A4_open_with_question": ActionOutcome(next_state="engaged_dialogue", reward=0.5, risk="low", benefit="high"),
        },
    )
    out = tmp_path / "policy_preference.jsonl"
    count = export_policy_preference([record], out)
    assert count == 0
    assert out.read_text(encoding="utf-8") == ""


def test_policy_preference_uses_best_and_lowest_reward_rejected(tmp_path):
    record = make_record()
    out = tmp_path / "policy_preference.jsonl"
    count = export_policy_preference([record], out)
    rows = read_jsonl(out)
    assert count == 1
    assert rows[0]["chosen"] == "A2_offer_value_comparison"
    assert rows[0]["rejected"] == "A1_silent_observe"
    assert rows[0]["reward_gap"] > 0
    assert rows[0]["chosen_json"]["action"] == "A2_offer_value_comparison"


def test_build_policy_preference_row_returns_none_without_strictly_lower_reward():
    record = make_record()
    record = record.model_copy(
        update={
            "reward_by_action": {
                "A1_silent_observe": 0.8,
                "A2_offer_value_comparison": 0.8,
                "A4_open_with_question": 0.8,
            }
        }
    )
    assert build_policy_preference_row(record) is None

