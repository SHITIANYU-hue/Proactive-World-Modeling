from __future__ import annotations

import json
from pathlib import Path

import pytest

from piwm_infer.decision_loop import PIWMDecisionLoop
from piwm_train import config

from .fixtures.mock_vlm import MockVLM, default_outputs


ROOT = Path(__file__).resolve().parents[2]


def _state_row() -> dict:
    with (ROOT / "data/piwm_dataset_pilot30/state_inference.jsonl").open(encoding="utf-8") as handle:
        return json.loads(next(line for line in handle if line.strip()))


def test_decision_loop_runs_four_heads_and_selects_action() -> None:
    vlm = MockVLM()
    decision = PIWMDecisionLoop(vlm).decide(_state_row())
    assert decision.chosen_action == "A2_offer_value_comparison"
    assert decision.per_candidate["A2_offer_value_comparison"].reaction_caption == "the customer turns toward the salesperson"
    roles = [call["role"] for call in vlm.calls]
    assert roles == [
        "perception",
        "deliberation:A1_silent_observe",
        "continuation:A1_silent_observe",
        "deliberation:A2_offer_value_comparison",
        "continuation:A2_offer_value_comparison",
        "action",
    ]


def test_decision_loop_perception_parse_failure_falls_back() -> None:
    outputs = default_outputs()
    outputs["perception"] = f"{config.TAG_STAGE_OPEN}bad{config.TAG_STAGE_CLOSE}"
    decision = PIWMDecisionLoop(MockVLM(outputs)).decide(_state_row())
    assert decision.used_fallback is True
    assert decision.chosen_action == "A6_acknowledge_and_wait"
    assert decision.errors


def test_decision_loop_all_deliberation_failures_fallback_to_candidate() -> None:
    outputs = default_outputs()
    outputs["deliberation:A1_silent_observe"] = "bad"
    outputs["deliberation:A2_offer_value_comparison"] = "bad"
    decision = PIWMDecisionLoop(MockVLM(outputs)).decide(_state_row())
    assert decision.used_fallback is True
    assert decision.chosen_action == "A1_silent_observe"
    assert len(decision.errors) == 2


def test_decision_loop_action_parse_failure_fallback_to_highest_reward() -> None:
    outputs = default_outputs()
    outputs["action"] = "\n".join(
        [
            f"{config.TAG_RATIONALE_OPEN}bad choice{config.TAG_RATIONALE_CLOSE}",
            f"{config.TAG_CHOSEN_OPEN}A3_strong_recommend{config.TAG_CHOSEN_CLOSE}",
        ]
    )
    decision = PIWMDecisionLoop(MockVLM(outputs)).decide(_state_row())
    assert decision.used_fallback is True
    assert decision.chosen_action == "A2_offer_value_comparison"


def test_decision_loop_low_score_returns_silent_candidate_without_deliberation() -> None:
    outputs = default_outputs()
    outputs["perception"] = outputs["perception"].replace(
        f"{config.TAG_SCORE_OPEN}3{config.TAG_SCORE_CLOSE}",
        f"{config.TAG_SCORE_OPEN}1{config.TAG_SCORE_CLOSE}",
    )
    vlm = MockVLM(outputs)
    decision = PIWMDecisionLoop(vlm).decide(_state_row())
    assert decision.used_fallback is True
    assert decision.chosen_action == "A1_silent_observe"
    assert [call["role"] for call in vlm.calls] == ["perception"]


def test_decision_loop_raises_no_exceptions_on_fixture_batch() -> None:
    rows = []
    with (ROOT / "data/piwm_dataset_pilot30/state_inference.jsonl").open(encoding="utf-8") as handle:
        for _, line in zip(range(3), handle):
            rows.append(json.loads(line))
    loop = PIWMDecisionLoop(MockVLM())
    assert [loop.decide(row).chosen_action for row in rows] == ["A2_offer_value_comparison"] * 3

