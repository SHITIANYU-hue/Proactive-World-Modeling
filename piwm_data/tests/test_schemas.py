import pytest
from pydantic import ValidationError

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
            ),
            "A2_offer_value_comparison": ActionOutcome(
                next_state="engaged_dialogue",
                reward=0.8,
                risk="low",
                benefit="high",
            ),
            "A4_open_with_question": ActionOutcome(
                next_state="engaged_dialogue",
                reward=0.6,
                risk="low",
                benefit="high",
            ),
        },
        "reward_by_action": {
            "A1_silent_observe": 0.3,
            "A2_offer_value_comparison": 0.8,
            "A4_open_with_question": 0.6,
        },
        "rationale": None,
        "provenance": [Provenance(field_name="latent_state", source="rule_derived", rule_version="v1.0")],
        "is_anchor": False,
    }
    data.update(overrides)
    return MainSchemaRecord(**data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observable_cues", ["not_a_cue"]),
        ("latent_state", "not_a_state"),
        ("intent", "not_an_intent"),
        ("candidate_actions", ["A1_silent_observe", "not_an_action"]),
        ("best_action", "not_an_action"),
        ("aida_stage", "not_a_stage"),
        ("proactive_score", 6),
    ],
)
def test_main_schema_rejects_invalid_enum_values(field, value):
    with pytest.raises(ValidationError):
        make_record(**{field: value})


def test_persona_rejects_invalid_type():
    with pytest.raises(ValidationError):
        Persona(type="not_a_persona")


def test_action_outcome_rejects_invalid_next_state():
    with pytest.raises(ValidationError):
        ActionOutcome(next_state="not_a_state", reward=0.0, risk="low", benefit="low")


def test_action_outcome_rejects_reward_out_of_range():
    with pytest.raises(ValidationError):
        ActionOutcome(next_state="high_hesitation", reward=1.1, risk="low", benefit="low")


def test_next_state_keys_must_cover_candidate_actions():
    record = make_record()
    next_state_by_action = dict(record.next_state_by_action)
    next_state_by_action.pop("A4_open_with_question")
    with pytest.raises(ValidationError):
        make_record(next_state_by_action=next_state_by_action)


def test_reward_by_action_must_match_next_state_rewards():
    reward_by_action = {
        "A1_silent_observe": 0.3,
        "A2_offer_value_comparison": 0.7,
        "A4_open_with_question": 0.6,
    }
    with pytest.raises(ValidationError):
        make_record(reward_by_action=reward_by_action)

