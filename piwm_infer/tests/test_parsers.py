from __future__ import annotations

import pytest

from piwm_infer.parsers import (
    MalformedOutputError,
    parse_action_output,
    parse_continuation_caption_output,
    parse_deliberation_output,
    parse_future_verification_output,
    parse_perception_output,
)
from piwm_train import config


VALID_PERCEPTION = "\n".join(
    [
        f"{config.TAG_STAGE_OPEN}interest{config.TAG_STAGE_CLOSE}",
        f"{config.TAG_VISUAL_SUMMARY_OPEN}customer keeps comparing products{config.TAG_VISUAL_SUMMARY_CLOSE}",
        f"{config.TAG_ENGAGEMENT_PATTERN_OPEN}customer stays near the display and keeps comparing{config.TAG_ENGAGEMENT_PATTERN_CLOSE}",
        f"{config.TAG_GAZE_AND_ATTENTION_OPEN}gaze stays on the display{config.TAG_GAZE_AND_ATTENTION_CLOSE}",
        f"{config.TAG_BODY_AND_HANDS_OPEN}body faces the display and hands remain near the product{config.TAG_BODY_AND_HANDS_CLOSE}",
        f"{config.TAG_BELIEF_OPEN}the offer may be useful{config.TAG_BELIEF_CLOSE}",
        f"{config.TAG_DESIRE_OPEN}compare the options{config.TAG_DESIRE_CLOSE}",
        f"{config.TAG_INTENTION_OPEN}keep evaluating{config.TAG_INTENTION_CLOSE}",
        f"{config.TAG_SCORE_OPEN}3{config.TAG_SCORE_CLOSE}",
        f"{config.TAG_CANDS_OPEN}A1_silent_observe, A4_open_with_question{config.TAG_CANDS_CLOSE}",
        f"{config.TAG_INTERVENTION_ACTION_OPEN}stand aside and ask one open question{config.TAG_INTERVENTION_ACTION_CLOSE}",
        f"{config.TAG_INTERVENTION_UTTERANCE_OPEN}What are you mainly comparing today?{config.TAG_INTERVENTION_UTTERANCE_CLOSE}",
    ]
)


def test_parse_perception_output_success() -> None:
    parsed = parse_perception_output(VALID_PERCEPTION)
    assert parsed["aida_stage"] == "interest"
    assert parsed["visual_state"]["gaze_and_attention"] == "gaze stays on the display"
    assert parsed["proactive_score"] == 3
    assert parsed["candidate_actions"] == ["A1_silent_observe", "A4_open_with_question"]
    assert parsed["best_action_realization"]["utterance"] == "What are you mainly comparing today?"


def test_parse_perception_missing_tag_raises() -> None:
    with pytest.raises(MalformedOutputError):
        parse_perception_output(VALID_PERCEPTION.replace(config.TAG_CANDS_OPEN, ""))


def test_parse_perception_invalid_stage_raises() -> None:
    with pytest.raises(MalformedOutputError):
        parse_perception_output(VALID_PERCEPTION.replace("interest", "commitment", 1))


def test_parse_deliberation_output_success_with_extra_text() -> None:
    raw = "\n".join(
        [
            "extra preface",
            f"{config.TAG_NEXT_STAGE_OPEN}desire{config.TAG_NEXT_STAGE_CLOSE}",
            f"{config.TAG_NEXT_BELIEF_OPEN}the salesperson can help{config.TAG_NEXT_BELIEF_CLOSE}",
            f"{config.TAG_NEXT_DESIRE_OPEN}get reassurance{config.TAG_NEXT_DESIRE_CLOSE}",
            f"{config.TAG_NEXT_INTENTION_OPEN}ask a question{config.TAG_NEXT_INTENTION_CLOSE}",
            f"{config.TAG_RISK_OPEN}low{config.TAG_RISK_CLOSE}",
            f"{config.TAG_BENEFIT_OPEN}high{config.TAG_BENEFIT_CLOSE}",
            f"{config.TAG_REWARD_OPEN}0.80{config.TAG_REWARD_CLOSE}",
            "extra suffix",
        ]
    )
    parsed = parse_deliberation_output(raw)
    assert parsed["reward"] == 0.8
    assert parsed["risk"] == "low"


def test_parse_deliberation_bad_reward_format_raises() -> None:
    raw = "\n".join(
        [
            f"{config.TAG_NEXT_STAGE_OPEN}desire{config.TAG_NEXT_STAGE_CLOSE}",
            f"{config.TAG_NEXT_BELIEF_OPEN}belief{config.TAG_NEXT_BELIEF_CLOSE}",
            f"{config.TAG_NEXT_DESIRE_OPEN}desire{config.TAG_NEXT_DESIRE_CLOSE}",
            f"{config.TAG_NEXT_INTENTION_OPEN}intention{config.TAG_NEXT_INTENTION_CLOSE}",
            f"{config.TAG_RISK_OPEN}low{config.TAG_RISK_CLOSE}",
            f"{config.TAG_BENEFIT_OPEN}high{config.TAG_BENEFIT_CLOSE}",
            f"{config.TAG_REWARD_OPEN}0.800{config.TAG_REWARD_CLOSE}",
        ]
    )
    with pytest.raises(MalformedOutputError):
        parse_deliberation_output(raw)


def test_parse_action_output_success() -> None:
    raw = "\n".join(
        [
            f"{config.TAG_RATIONALE_OPEN}lower pressure is safer{config.TAG_RATIONALE_CLOSE}",
            f"{config.TAG_CHOSEN_OPEN}A1_silent_observe{config.TAG_CHOSEN_CLOSE}",
            f"{config.TAG_INTERVENTION_ACTION_OPEN}stay visible without approaching{config.TAG_INTERVENTION_ACTION_CLOSE}",
            f"{config.TAG_INTERVENTION_UTTERANCE_OPEN}I will give you space.{config.TAG_INTERVENTION_UTTERANCE_CLOSE}",
        ]
    )
    parsed = parse_action_output(raw, valid_actions={"A1_silent_observe"})
    assert parsed["chosen"] == "A1_silent_observe"
    assert parsed["intervention_utterance"] == "I will give you space."


def test_parse_action_output_invalid_choice_raises() -> None:
    raw = "\n".join(
        [
            f"{config.TAG_RATIONALE_OPEN}reason{config.TAG_RATIONALE_CLOSE}",
            f"{config.TAG_CHOSEN_OPEN}A3_strong_recommend{config.TAG_CHOSEN_CLOSE}",
            f"{config.TAG_INTERVENTION_ACTION_OPEN}point to one product{config.TAG_INTERVENTION_ACTION_CLOSE}",
            f"{config.TAG_INTERVENTION_UTTERANCE_OPEN}I recommend this one.{config.TAG_INTERVENTION_UTTERANCE_CLOSE}",
        ]
    )
    with pytest.raises(MalformedOutputError):
        parse_action_output(raw, valid_actions={"A1_silent_observe"})


def test_parse_continuation_caption_output_success() -> None:
    raw = f"{config.TAG_REACTION_CAPTION_OPEN}the customer steps back{config.TAG_REACTION_CAPTION_CLOSE}"
    assert parse_continuation_caption_output(raw)["reaction_caption"] == "the customer steps back"


def test_parse_future_verification_output_success() -> None:
    raw = "\n".join(
        [
            f"{config.TAG_MATCH_OPEN}yes{config.TAG_MATCH_CLOSE}",
            f"{config.TAG_EXPECTED_STATE_OPEN}defensive_withdrawal{config.TAG_EXPECTED_STATE_CLOSE}",
            f"{config.TAG_ENGAGEMENT_PATTERN_CHANGE_OPEN}customer steps back{config.TAG_ENGAGEMENT_PATTERN_CHANGE_CLOSE}",
            f"{config.TAG_GAZE_AND_ATTENTION_CHANGE_OPEN}gaze drops{config.TAG_GAZE_AND_ATTENTION_CHANGE_CLOSE}",
            f"{config.TAG_BODY_AND_HANDS_CHANGE_OPEN}hands retract{config.TAG_BODY_AND_HANDS_CHANGE_CLOSE}",
            f"{config.TAG_REASON_OPEN}The future matches the expected withdrawal.{config.TAG_REASON_CLOSE}",
        ]
    )
    parsed = parse_future_verification_output(raw)
    assert parsed["match"] == "yes"
    assert parsed["expected_next_state"] == "defensive_withdrawal"
    assert parsed["visible_reaction"]["body_and_hands_change"] == "hands retract"


def test_parse_future_verification_rejects_invalid_match() -> None:
    raw = "\n".join(
        [
            f"{config.TAG_MATCH_OPEN}maybe{config.TAG_MATCH_CLOSE}",
            f"{config.TAG_EXPECTED_STATE_OPEN}defensive_withdrawal{config.TAG_EXPECTED_STATE_CLOSE}",
            f"{config.TAG_ENGAGEMENT_PATTERN_CHANGE_OPEN}customer steps back{config.TAG_ENGAGEMENT_PATTERN_CHANGE_CLOSE}",
            f"{config.TAG_GAZE_AND_ATTENTION_CHANGE_OPEN}gaze drops{config.TAG_GAZE_AND_ATTENTION_CHANGE_CLOSE}",
            f"{config.TAG_BODY_AND_HANDS_CHANGE_OPEN}hands retract{config.TAG_BODY_AND_HANDS_CHANGE_CLOSE}",
            f"{config.TAG_REASON_OPEN}reason{config.TAG_REASON_CLOSE}",
        ]
    )
    with pytest.raises(MalformedOutputError):
        parse_future_verification_output(raw)
