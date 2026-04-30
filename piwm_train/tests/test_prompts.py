from __future__ import annotations

import json
from pathlib import Path

from piwm_train import config
from piwm_train.prompts import (
    PIWM_SYSTEM_PROMPT,
    build_action_prompt,
    build_continuation_caption_prompt,
    build_deliberation_prompt,
    build_perception_prompt,
    format_candidate_block,
)


ROOT = Path(__file__).resolve().parents[2]


def _first_jsonl(path: str) -> dict:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.loads(next(line for line in handle if line.strip()))


def test_perception_prompt_has_image_placeholders_and_tags() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/state_inference.jsonl")
    prompt = build_perception_prompt(row)
    assert prompt.count(config.IMAGE_PLACEHOLDER) == 3
    assert config.TAG_STAGE_OPEN in prompt
    assert config.TAG_CANDS_CLOSE in prompt


def test_deliberation_prompt_contains_candidate_action_only_once_contextually() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/transition_modeling.jsonl")
    prompt = build_deliberation_prompt(row)
    assert row["input"]["candidate_action"] in prompt
    assert config.TAG_NEXT_STAGE_OPEN in prompt
    assert "candidate interventions:" not in prompt


def test_format_candidate_block_from_list() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/policy_preference.jsonl")
    block = format_candidate_block(row["meta"]["candidate_block"])
    assert row["chosen"] in block
    assert "reward=0.20" in block
    assert "predicted_next_stage=" in block


def test_action_prompt_uses_candidate_block() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30/policy_preference.jsonl")
    prompt = build_action_prompt(row)
    assert row["chosen"] in prompt
    assert config.TAG_RATIONALE_OPEN in prompt
    assert config.TAG_CHOSEN_CLOSE in prompt


def test_continuation_caption_prompt_shape() -> None:
    transition = _first_jsonl("data/piwm_dataset_pilot30/transition_modeling.jsonl")
    row = {
        "input": {
            "current_frames": transition["input"]["frames"],
            "candidate_action": transition["input"]["candidate_action"],
            "current_state_summary": transition["input"]["current_state_summary"],
        }
    }
    prompt = build_continuation_caption_prompt(row)
    assert prompt.count(config.IMAGE_PLACEHOLDER) == 3
    assert config.TAG_REACTION_CAPTION_OPEN in prompt
    assert "next 5 seconds" in prompt


def test_system_prompt_mentions_structured_tags() -> None:
    assert "structured tag format" in PIWM_SYSTEM_PROMPT

