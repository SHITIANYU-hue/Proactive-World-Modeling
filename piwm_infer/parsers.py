"""Strict parsers for PIWM structured model outputs."""

from __future__ import annotations

import re
from typing import Iterable

from piwm_data import rules
from piwm_train import config


class MalformedOutputError(ValueError):
    """Raised when a model output does not match the required tag contract."""


def parse_perception_output(raw: str) -> dict:
    values = _extract_tags(raw, config.PERCEPTION_TAGS)
    stage = values["stage"]
    if stage not in rules.AIDA_STAGES:
        raise MalformedOutputError(f"invalid stage: {stage}")
    score = _parse_int(values["score"], field="score")
    if score < 1 or score > 5:
        raise MalformedOutputError(f"score out of range: {score}")
    candidates = _parse_candidates(values["cands"])
    return {
        "aida_stage": stage,
        "visual_state": {
            "summary": values["visual_summary"],
            "engagement_pattern": values["engagement_pattern"],
            "gaze_and_attention": values["gaze_and_attention"],
            "body_and_hands": values["body_and_hands"],
        },
        "bdi": {
            "belief": values["belief"],
            "desire": values["desire"],
            "intention": values["intention"],
        },
        "proactive_score": score,
        "candidate_actions": candidates,
        "best_action_realization": {
            "physical_action": values["intervention_action"],
            "utterance": values["intervention_utterance"],
        },
    }


def parse_deliberation_output(raw: str) -> dict:
    values = _extract_tags(raw, config.DELIBERATION_TAGS)
    next_stage = values["next_stage"]
    if next_stage not in rules.AIDA_STAGES:
        raise MalformedOutputError(f"invalid next_stage: {next_stage}")
    risk = values["risk"]
    benefit = values["benefit"]
    if risk not in config.VALID_RISKS:
        raise MalformedOutputError(f"invalid risk: {risk}")
    if benefit not in config.VALID_BENEFITS:
        raise MalformedOutputError(f"invalid benefit: {benefit}")
    reward = _parse_reward(values["reward"])
    return {
        "next_aida_stage": next_stage,
        "next_bdi": {
            "belief": values["next_belief"],
            "desire": values["next_desire"],
            "intention": values["next_intention"],
        },
        "risk": risk,
        "benefit": benefit,
        "reward": reward,
    }


def parse_continuation_caption_output(raw: str) -> dict:
    values = _extract_tags(raw, config.CONTINUATION_TAGS)
    caption = values["reaction_caption"]
    if not caption:
        raise MalformedOutputError("reaction_caption is empty")
    return {"reaction_caption": caption}


def parse_future_verification_output(raw: str) -> dict:
    values = _extract_tags(raw, config.FUTURE_VERIFICATION_TAGS)
    match = values["match"].lower()
    if match not in {"yes", "no"}:
        raise MalformedOutputError(f"match must be yes or no: {values['match']}")
    expected_state = values["expected_state"]
    if expected_state not in rules.LATENT_STATES:
        raise MalformedOutputError(f"invalid expected_state: {expected_state}")
    return {
        "match": match,
        "expected_next_state": expected_state,
        "visible_reaction": {
            "engagement_pattern_change": values["engagement_pattern_change"],
            "gaze_and_attention_change": values["gaze_and_attention_change"],
            "body_and_hands_change": values["body_and_hands_change"],
        },
        "reason": values["reason"],
    }


def parse_action_output(raw: str, valid_actions: Iterable[str] | None = None) -> dict:
    values = _extract_tags(raw, config.ACTION_TAGS)
    chosen = values["chosen"]
    valid = set(valid_actions or rules.ACTIONS)
    if chosen not in valid:
        raise MalformedOutputError(f"chosen action is not valid: {chosen}")
    return {
        "rationale": values["rationale"],
        "chosen": chosen,
        "intervention_action": values["intervention_action"],
        "intervention_utterance": values["intervention_utterance"],
    }


def _extract_tags(raw: str, tags: tuple[config.TagPair, ...]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for tag in tags:
        pattern = re.escape(tag.open) + r"(.*?)" + re.escape(tag.close)
        matches = re.findall(pattern, raw, flags=re.DOTALL)
        if len(matches) != 1:
            raise MalformedOutputError(f"expected exactly one {tag.name} tag, found {len(matches)}")
        value = matches[0].strip()
        if value == "":
            raise MalformedOutputError(f"{tag.name} tag is empty")
        parsed[tag.name] = value
    return parsed


def _parse_int(value: str, field: str) -> int:
    if not re.fullmatch(r"[+-]?\d+", value):
        raise MalformedOutputError(f"{field} is not an integer: {value}")
    return int(value)


def _parse_reward(value: str) -> float:
    if not re.fullmatch(r"-?\d+\.\d{2}", value):
        raise MalformedOutputError(f"reward must use two decimal places: {value}")
    reward = float(value)
    if reward < -1.0 or reward > 1.0:
        raise MalformedOutputError(f"reward out of range: {reward}")
    return reward


def _parse_candidates(value: str) -> list[str]:
    candidates = [item.strip() for item in value.split(",") if item.strip()]
    if not candidates:
        raise MalformedOutputError("candidate list is empty")
    invalid = [action for action in candidates if action not in rules.ACTIONS]
    if invalid:
        raise MalformedOutputError(f"invalid candidate action(s): {invalid}")
    if len(candidates) != len(set(candidates)):
        raise MalformedOutputError("candidate list contains duplicates")
    return candidates
