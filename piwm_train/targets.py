"""Build structured target strings from PIWM training JSONL rows."""

from __future__ import annotations

from typing import Literal

from . import config


def build_perception_target(record: dict) -> str:
    """Build a perception target from one ``state_inference.jsonl`` row."""
    out = record["output"]
    bdi = out["bdi"]
    return "\n".join(
        [
            f"{config.TAG_STAGE_OPEN}{out['aida_stage']}{config.TAG_STAGE_CLOSE}",
            f"{config.TAG_BELIEF_OPEN}{bdi['belief']}{config.TAG_BELIEF_CLOSE}",
            f"{config.TAG_DESIRE_OPEN}{bdi['desire']}{config.TAG_DESIRE_CLOSE}",
            f"{config.TAG_INTENTION_OPEN}{bdi['intention']}{config.TAG_INTENTION_CLOSE}",
            f"{config.TAG_SCORE_OPEN}{int(out['proactive_score'])}{config.TAG_SCORE_CLOSE}",
            f"{config.TAG_CANDS_OPEN}{', '.join(out['candidate_actions'])}{config.TAG_CANDS_CLOSE}",
        ]
    )


def build_deliberation_target(record: dict) -> str:
    """Build a deliberation target from one ``transition_modeling.jsonl`` row."""
    out = record["output"]
    next_bdi = out["next_bdi"]
    return "\n".join(
        [
            f"{config.TAG_NEXT_STAGE_OPEN}{out['next_aida_stage']}{config.TAG_NEXT_STAGE_CLOSE}",
            f"{config.TAG_NEXT_BELIEF_OPEN}{next_bdi['belief']}{config.TAG_NEXT_BELIEF_CLOSE}",
            f"{config.TAG_NEXT_DESIRE_OPEN}{next_bdi['desire']}{config.TAG_NEXT_DESIRE_CLOSE}",
            f"{config.TAG_NEXT_INTENTION_OPEN}{next_bdi['intention']}{config.TAG_NEXT_INTENTION_CLOSE}",
            f"{config.TAG_RISK_OPEN}{out['risk']}{config.TAG_RISK_CLOSE}",
            f"{config.TAG_BENEFIT_OPEN}{out['benefit']}{config.TAG_BENEFIT_CLOSE}",
            f"{config.TAG_REWARD_OPEN}{config.REWARD_FORMAT.format(float(out['reward']))}{config.TAG_REWARD_CLOSE}",
        ]
    )


def build_continuation_caption_target(record: dict) -> str:
    """Build the Phase-7 visual-continuation caption target."""
    caption = record["output"]["reaction_caption"]
    return f"{config.TAG_REACTION_CAPTION_OPEN}{caption}{config.TAG_REACTION_CAPTION_CLOSE}"


def build_action_target(record: dict, side: Literal["chosen", "rejected"]) -> str:
    """Build a chosen or rejected action target from one preference row."""
    block = record[f"{side}_json"]
    return "\n".join(
        [
            f"{config.TAG_RATIONALE_OPEN}{block['rationale']}{config.TAG_RATIONALE_CLOSE}",
            f"{config.TAG_CHOSEN_OPEN}{block['action']}{config.TAG_CHOSEN_CLOSE}",
        ]
    )


def build_sft_target(record: dict, task: Literal["perception", "deliberation", "continuation_caption"]) -> str:
    """Dispatch target construction for SFT rows."""
    if task == "perception":
        return build_perception_target(record)
    if task == "deliberation":
        return build_deliberation_target(record)
    if task == "continuation_caption":
        return build_continuation_caption_target(record)
    raise ValueError(f"unknown SFT task: {task}")

