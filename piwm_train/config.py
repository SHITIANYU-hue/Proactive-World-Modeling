"""Constants for PIWM training and parsing targets.

Keep all structured-output tag literals in this module. Prompt, target, and
parser code should import these constants instead of duplicating raw tag
strings.
"""

from __future__ import annotations

from dataclasses import dataclass

from piwm_data import rules

MODEL_NAME = "Qwen/Qwen3-VL-8B-Instruct"
FALLBACK_MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"
LORA_RANK = 16
LORA_ALPHA = 32
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]

IMAGE_PLACEHOLDER = "<|image_pad|>"
REWARD_FORMAT = "{:.2f}"

# Perception tags.
TAG_STAGE_OPEN = "<stage>"
TAG_STAGE_CLOSE = "</stage>"
TAG_BELIEF_OPEN = "<belief>"
TAG_BELIEF_CLOSE = "</belief>"
TAG_DESIRE_OPEN = "<desire>"
TAG_DESIRE_CLOSE = "</desire>"
TAG_INTENTION_OPEN = "<intention>"
TAG_INTENTION_CLOSE = "</intention>"
TAG_SCORE_OPEN = "<score>"
TAG_SCORE_CLOSE = "</score>"
TAG_CANDS_OPEN = "<cands>"
TAG_CANDS_CLOSE = "</cands>"

# Deliberation tags.
TAG_NEXT_STAGE_OPEN = "<next_stage>"
TAG_NEXT_STAGE_CLOSE = "</next_stage>"
TAG_NEXT_BELIEF_OPEN = "<next_belief>"
TAG_NEXT_BELIEF_CLOSE = "</next_belief>"
TAG_NEXT_DESIRE_OPEN = "<next_desire>"
TAG_NEXT_DESIRE_CLOSE = "</next_desire>"
TAG_NEXT_INTENTION_OPEN = "<next_intention>"
TAG_NEXT_INTENTION_CLOSE = "</next_intention>"
TAG_RISK_OPEN = "<risk>"
TAG_RISK_CLOSE = "</risk>"
TAG_BENEFIT_OPEN = "<benefit>"
TAG_BENEFIT_CLOSE = "</benefit>"
TAG_REWARD_OPEN = "<reward>"
TAG_REWARD_CLOSE = "</reward>"

# Continuation-caption tags.
TAG_REACTION_CAPTION_OPEN = "<reaction_caption>"
TAG_REACTION_CAPTION_CLOSE = "</reaction_caption>"

# Action tags.
TAG_RATIONALE_OPEN = "<rationale>"
TAG_RATIONALE_CLOSE = "</rationale>"
TAG_CHOSEN_OPEN = "<chosen>"
TAG_CHOSEN_CLOSE = "</chosen>"

VALID_AIDA_STAGES = tuple(rules.AIDA_STAGES)
VALID_RISKS = ("low", "medium", "high")
VALID_BENEFITS = ("low", "medium", "high")
VALID_ACTIONS = tuple(rules.ACTIONS)


@dataclass(frozen=True)
class TagPair:
    open: str
    close: str
    name: str


PERCEPTION_TAGS = (
    TagPair(TAG_STAGE_OPEN, TAG_STAGE_CLOSE, "stage"),
    TagPair(TAG_BELIEF_OPEN, TAG_BELIEF_CLOSE, "belief"),
    TagPair(TAG_DESIRE_OPEN, TAG_DESIRE_CLOSE, "desire"),
    TagPair(TAG_INTENTION_OPEN, TAG_INTENTION_CLOSE, "intention"),
    TagPair(TAG_SCORE_OPEN, TAG_SCORE_CLOSE, "score"),
    TagPair(TAG_CANDS_OPEN, TAG_CANDS_CLOSE, "cands"),
)

DELIBERATION_TAGS = (
    TagPair(TAG_NEXT_STAGE_OPEN, TAG_NEXT_STAGE_CLOSE, "next_stage"),
    TagPair(TAG_NEXT_BELIEF_OPEN, TAG_NEXT_BELIEF_CLOSE, "next_belief"),
    TagPair(TAG_NEXT_DESIRE_OPEN, TAG_NEXT_DESIRE_CLOSE, "next_desire"),
    TagPair(TAG_NEXT_INTENTION_OPEN, TAG_NEXT_INTENTION_CLOSE, "next_intention"),
    TagPair(TAG_RISK_OPEN, TAG_RISK_CLOSE, "risk"),
    TagPair(TAG_BENEFIT_OPEN, TAG_BENEFIT_CLOSE, "benefit"),
    TagPair(TAG_REWARD_OPEN, TAG_REWARD_CLOSE, "reward"),
)

CONTINUATION_TAGS = (
    TagPair(TAG_REACTION_CAPTION_OPEN, TAG_REACTION_CAPTION_CLOSE, "reaction_caption"),
)

ACTION_TAGS = (
    TagPair(TAG_RATIONALE_OPEN, TAG_RATIONALE_CLOSE, "rationale"),
    TagPair(TAG_CHOSEN_OPEN, TAG_CHOSEN_CLOSE, "chosen"),
)


def tag_instruction_lines(tag_pairs: tuple[TagPair, ...]) -> str:
    """Return one empty tag pair per line for prompt format instructions."""
    return "\n".join(f"{tag.open}...{tag.close}" for tag in tag_pairs)
