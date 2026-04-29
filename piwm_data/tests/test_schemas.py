import pytest
from pydantic import ValidationError

from piwm_data import rules
from piwm_data.schemas import ActionOutcome, FrameRef, MainSchemaRecord, Persona, Provenance


def make_outcome(action: str, **overrides):
    data = rules.derive_action_outcome("high_hesitation", "interest", "price_sensitive_cautious", action)
    data.update(overrides)
    return ActionOutcome(**data)


def make_record(**overrides):
    intent = "compare_value_for_money"
    data = {
        "state_id": "session_test_001",
        "images": [FrameRef(index=0, relative_path="Archive/session_test_001/frames/000.jpg")],
        "observable_cues": ["long_dwell_with_price_check"],
        "persona": Persona(type="price_sensitive_cautious", description="测试用 persona"),
        "aida_stage": "interest",
        "latent_state": "high_hesitation",
        "intent": intent,
        "bdi": rules.derive_bdi("price_sensitive_cautious", "high_hesitation", intent, ["long_dwell_with_price_check"]),
        "proactive_score": 4,
        "candidate_actions": [
            "A1_silent_observe",
            "A2_offer_value_comparison",
            "A4_open_with_question",
        ],
        "best_action": "A2_offer_value_comparison",
        "next_state_by_action": {
            "A1_silent_observe": make_outcome("A1_silent_observe"),
            "A2_offer_value_comparison": make_outcome("A2_offer_value_comparison"),
            "A4_open_with_question": make_outcome("A4_open_with_question"),
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
    data = rules.derive_action_outcome("high_hesitation", "interest", "price_sensitive_cautious", "A1_silent_observe")
    data["next_state"] = "not_a_state"
    with pytest.raises(ValidationError):
        ActionOutcome(**data)


def test_action_outcome_rejects_reward_out_of_range():
    data = rules.derive_action_outcome("high_hesitation", "interest", "price_sensitive_cautious", "A1_silent_observe")
    data["reward"] = 1.1
    data["reward_components"] = rules.derive_reward_components("interest", data["next_aida_stage"], "A1_silent_observe", 1.1)
    with pytest.raises(ValidationError):
        ActionOutcome(**data)


def test_action_outcome_rejects_inconsistent_reward_components():
    data = rules.derive_action_outcome("high_hesitation", "interest", "price_sensitive_cautious", "A1_silent_observe")
    data["reward_components"] = rules.derive_reward_components(
        "interest",
        data["next_aida_stage"],
        "A1_silent_observe",
        0.9,
    )
    with pytest.raises(ValidationError):
        ActionOutcome(**data)


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
