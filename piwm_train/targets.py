"""Build structured target strings from PIWM training JSONL rows."""

from __future__ import annotations

from typing import Literal

from . import config


def build_perception_target(record: dict) -> str:
    """Build a perception target from one ``state_inference.jsonl`` row."""
    out = record["output"]
    bdi = out["bdi"]
    visual = out.get("visual_state") or {}
    realization = out.get("best_action_realization") or out.get("best_intervention") or {}
    return "\n".join(
        [
            f"{config.TAG_STAGE_OPEN}{out['aida_stage']}{config.TAG_STAGE_CLOSE}",
            f"{config.TAG_VISUAL_SUMMARY_OPEN}{visual.get('summary', '')}{config.TAG_VISUAL_SUMMARY_CLOSE}",
            f"{config.TAG_ENGAGEMENT_PATTERN_OPEN}{visual.get('engagement_pattern', '')}{config.TAG_ENGAGEMENT_PATTERN_CLOSE}",
            f"{config.TAG_GAZE_AND_ATTENTION_OPEN}{visual.get('gaze_and_attention', visual.get('gaze', ''))}{config.TAG_GAZE_AND_ATTENTION_CLOSE}",
            f"{config.TAG_BODY_AND_HANDS_OPEN}{visual.get('body_and_hands', '')}{config.TAG_BODY_AND_HANDS_CLOSE}",
            f"{config.TAG_BELIEF_OPEN}{bdi['belief']}{config.TAG_BELIEF_CLOSE}",
            f"{config.TAG_DESIRE_OPEN}{bdi['desire']}{config.TAG_DESIRE_CLOSE}",
            f"{config.TAG_INTENTION_OPEN}{bdi['intention']}{config.TAG_INTENTION_CLOSE}",
            f"{config.TAG_SCORE_OPEN}{int(out['proactive_score'])}{config.TAG_SCORE_CLOSE}",
            f"{config.TAG_CANDS_OPEN}{', '.join(out['candidate_actions'])}{config.TAG_CANDS_CLOSE}",
            f"{config.TAG_INTERVENTION_ACTION_OPEN}{_physical_action(realization)}{config.TAG_INTERVENTION_ACTION_CLOSE}",
            f"{config.TAG_INTERVENTION_UTTERANCE_OPEN}{_utterance(realization)}{config.TAG_INTERVENTION_UTTERANCE_CLOSE}",
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


def build_future_verification_target(record: dict) -> str:
    """Build the action-conditioned future-verification target."""
    out = record["output"]
    reaction = _visible_reaction_axes(out["visible_reaction"])
    return "\n".join(
        [
            f"{config.TAG_MATCH_OPEN}{out['match']}{config.TAG_MATCH_CLOSE}",
            f"{config.TAG_EXPECTED_STATE_OPEN}{out['expected_next_state']}{config.TAG_EXPECTED_STATE_CLOSE}",
            f"{config.TAG_ENGAGEMENT_PATTERN_CHANGE_OPEN}{reaction['engagement_pattern_change']}{config.TAG_ENGAGEMENT_PATTERN_CHANGE_CLOSE}",
            f"{config.TAG_GAZE_AND_ATTENTION_CHANGE_OPEN}{reaction['gaze_and_attention_change']}{config.TAG_GAZE_AND_ATTENTION_CHANGE_CLOSE}",
            f"{config.TAG_BODY_AND_HANDS_CHANGE_OPEN}{reaction['body_and_hands_change']}{config.TAG_BODY_AND_HANDS_CHANGE_CLOSE}",
            f"{config.TAG_REASON_OPEN}{out['reason']}{config.TAG_REASON_CLOSE}",
        ]
    )


def build_action_target(record: dict, side: Literal["chosen", "rejected"]) -> str:
    """Build a chosen or rejected action target from one preference row."""
    block = record[f"{side}_json"]
    realization = block.get("action_realization") or block.get("intervention_plan") or {}
    return "\n".join(
        [
            f"{config.TAG_RATIONALE_OPEN}{block['rationale']}{config.TAG_RATIONALE_CLOSE}",
            f"{config.TAG_CHOSEN_OPEN}{block['action']}{config.TAG_CHOSEN_CLOSE}",
            f"{config.TAG_INTERVENTION_ACTION_OPEN}{_physical_action(realization)}{config.TAG_INTERVENTION_ACTION_CLOSE}",
            f"{config.TAG_INTERVENTION_UTTERANCE_OPEN}{_utterance(realization)}{config.TAG_INTERVENTION_UTTERANCE_CLOSE}",
        ]
    )


def build_sft_target(
    record: dict,
    task: Literal["perception", "deliberation", "continuation_caption", "future_verification", "action_selection"],
) -> str:
    """Dispatch target construction for SFT rows."""
    if task == "perception":
        return build_perception_target(record)
    if task == "deliberation":
        return build_deliberation_target(record)
    if task == "continuation_caption":
        return build_continuation_caption_target(record)
    if task == "future_verification":
        return build_future_verification_target(record)
    if task == "action_selection":
        return build_action_target(record, "chosen")
    raise ValueError(f"unknown SFT task: {task}")


def _physical_action(realization: dict) -> str:
    return realization.get("physical_action") or realization.get("physical_action_zh") or ""


def _utterance(realization: dict) -> str:
    return realization.get("utterance") or realization.get("customer_facing_utterance_zh") or ""


def _visible_reaction_axes(reaction: dict) -> dict[str, str]:
    """Return future-reaction fields in the compact three-axis schema.

    Older local artifacts used body/gaze/hand/movement fields. The training
    target now emits the shared visual-state axes while still accepting those
    legacy rows during migration.
    """
    if "engagement_pattern_change" in reaction:
        return {
            "engagement_pattern_change": reaction["engagement_pattern_change"],
            "gaze_and_attention_change": reaction["gaze_and_attention_change"],
            "body_and_hands_change": reaction["body_and_hands_change"],
        }
    return {
        "engagement_pattern_change": "; ".join(
            item for item in [reaction.get("movement_change", ""), reaction.get("body_change", "")] if item
        ),
        "gaze_and_attention_change": reaction.get("gaze_change", ""),
        "body_and_hands_change": "; ".join(
            item for item in [reaction.get("body_change", ""), reaction.get("hand_change", "")] if item
        ),
    }
