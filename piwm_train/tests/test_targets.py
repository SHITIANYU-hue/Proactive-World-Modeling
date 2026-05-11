from __future__ import annotations

import json
from pathlib import Path

import pytest

from piwm_data import rules
from piwm_train import config
from piwm_train.targets import (
    build_action_target,
    build_continuation_caption_target,
    build_deliberation_target,
    build_future_verification_target,
    build_perception_target,
    build_sft_target,
)


ROOT = Path(__file__).resolve().parents[2]


def _first_jsonl(path: str) -> dict:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.loads(next(line for line in handle if line.strip()))


def test_build_perception_target_contains_six_tags_once() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/state_inference.jsonl")
    target = build_perception_target(row)
    for tag in config.PERCEPTION_TAGS:
        assert target.count(tag.open) == 1
        assert target.count(tag.close) == 1
    assert f"{config.TAG_STAGE_OPEN}{row['output']['aida_stage']}{config.TAG_STAGE_CLOSE}" in target
    assert row["output"]["state_subtype"] not in {
        "attention",
        "interest",
        "desire",
        "action",
    }


def test_build_perception_target_edge_empty_candidates_allowed_as_literal() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/state_inference.jsonl")
    row["output"]["candidate_actions"] = []
    target = build_perception_target(row)
    assert f"{config.TAG_CANDS_OPEN}{config.TAG_CANDS_CLOSE}" in target


def test_build_deliberation_target_formats_reward_with_two_decimals() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/transition_modeling.jsonl")
    row["output"]["reward"] = 0.2
    target = build_deliberation_target(row)
    assert f"{config.TAG_REWARD_OPEN}0.20{config.TAG_REWARD_CLOSE}" in target
    assert f"{config.TAG_NEXT_STAGE_OPEN}{row['output']['next_aida_stage']}{config.TAG_NEXT_STAGE_CLOSE}" in target


def test_build_deliberation_target_negative_reward() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/transition_modeling.jsonl")
    row["output"]["reward"] = -0.5
    target = build_deliberation_target(row)
    assert f"{config.TAG_REWARD_OPEN}-0.50{config.TAG_REWARD_CLOSE}" in target


def test_build_continuation_caption_target() -> None:
    row = {
        "output": {
            "reaction_caption": "the customer steps back and stops touching the product",
        }
    }
    assert build_continuation_caption_target(row) == (
        f"{config.TAG_REACTION_CAPTION_OPEN}the customer steps back and stops touching the product"
        f"{config.TAG_REACTION_CAPTION_CLOSE}"
    )


def test_build_continuation_caption_target_from_shape() -> None:
    row = {
        "output": {
            "reaction_caption": "the customer keeps browsing lightly alone",
            "reward": 0.5,
        }
    }
    target = build_sft_target(row, "continuation_caption")
    assert target.count(config.TAG_REACTION_CAPTION_OPEN) == 1


def test_build_future_verification_target() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30_with_continuations_compact_v2/future_verification.jsonl")
    target = build_future_verification_target(row)
    for tag in config.FUTURE_VERIFICATION_TAGS:
        assert target.count(tag.open) == 1
        assert target.count(tag.close) == 1
    assert f"{config.TAG_MATCH_OPEN}{row['output']['match']}{config.TAG_MATCH_CLOSE}" in target
    assert f"{config.TAG_EXPECTED_STATE_OPEN}{row['output']['expected_next_state']}{config.TAG_EXPECTED_STATE_CLOSE}" in target


def test_build_sft_target_future_verification() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30_with_continuations_compact_v2/future_verification.jsonl")
    target = build_sft_target(row, "future_verification")
    assert target.count(config.TAG_REASON_OPEN) == 1


def test_build_action_target_chosen_and_rejected() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/policy_preference.jsonl")
    chosen = build_action_target(row, "chosen")
    rejected = build_action_target(row, "rejected")
    assert f"{config.TAG_CHOSEN_OPEN}{row['chosen']}{config.TAG_CHOSEN_CLOSE}" in chosen
    assert f"{config.TAG_CHOSEN_OPEN}{row['rejected']}{config.TAG_CHOSEN_CLOSE}" in rejected
    assert row["chosen"] != row["rejected"]


def test_build_sft_target_action_selection() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/policy_preference.jsonl")
    target = build_sft_target(row, "action_selection")
    assert f"{config.TAG_CHOSEN_OPEN}{row['chosen']}{config.TAG_CHOSEN_CLOSE}" in target


def test_build_sft_target_rejects_unknown_task() -> None:
    with pytest.raises(ValueError):
        build_sft_target({}, "unknown")  # type: ignore[arg-type]


def test_perception_target_candidate_actions_are_valid() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/state_inference.jsonl")
    target = build_perception_target(row)
    cands = target.split(config.TAG_CANDS_OPEN)[1].split(config.TAG_CANDS_CLOSE)[0].split(", ")
    assert all(action in rules.ACTIONS for action in cands)
