from __future__ import annotations

import pytest

from piwm_infer.parsers import (
    MalformedOutputError,
    parse_action_output,
    parse_continuation_caption_output,
    parse_deliberation_output,
    parse_perception_output,
)
from piwm_train import config


VALID_PERCEPTION = "\n".join(
    [
        f"{config.TAG_STAGE_OPEN}interest{config.TAG_STAGE_CLOSE}",
        f"{config.TAG_BELIEF_OPEN}the offer may be useful{config.TAG_BELIEF_CLOSE}",
        f"{config.TAG_DESIRE_OPEN}compare the options{config.TAG_DESIRE_CLOSE}",
        f"{config.TAG_INTENTION_OPEN}keep evaluating{config.TAG_INTENTION_CLOSE}",
        f"{config.TAG_SCORE_OPEN}3{config.TAG_SCORE_CLOSE}",
        f"{config.TAG_CANDS_OPEN}A1_silent_observe, A4_open_with_question{config.TAG_CANDS_CLOSE}",
    ]
)


def test_parse_perception_output_success() -> None:
    parsed = parse_perception_output(VALID_PERCEPTION)
    assert parsed["aida_stage"] == "interest"
    assert parsed["proactive_score"] == 3
    assert parsed["candidate_actions"] == ["A1_silent_observe", "A4_open_with_question"]


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
        ]
    )
    parsed = parse_action_output(raw, valid_actions={"A1_silent_observe"})
    assert parsed["chosen"] == "A1_silent_observe"


def test_parse_action_output_invalid_choice_raises() -> None:
    raw = "\n".join(
        [
            f"{config.TAG_RATIONALE_OPEN}reason{config.TAG_RATIONALE_CLOSE}",
            f"{config.TAG_CHOSEN_OPEN}A3_strong_recommend{config.TAG_CHOSEN_CLOSE}",
        ]
    )
    with pytest.raises(MalformedOutputError):
        parse_action_output(raw, valid_actions={"A1_silent_observe"})


def test_parse_continuation_caption_output_success() -> None:
    raw = f"{config.TAG_REACTION_CAPTION_OPEN}the customer steps back{config.TAG_REACTION_CAPTION_CLOSE}"
    assert parse_continuation_caption_output(raw)["reaction_caption"] == "the customer steps back"

