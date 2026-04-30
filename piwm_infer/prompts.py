"""Inference prompt builders.

The sprint keeps train and inference prompt wording aligned; this module
re-exports the shared builders from :mod:`piwm_train.prompts`.
"""

from __future__ import annotations

from piwm_train.prompts import (
    PIWM_SYSTEM_PROMPT,
    build_action_prompt,
    build_continuation_caption_prompt,
    build_deliberation_prompt,
    build_perception_prompt,
    format_candidate_block,
    image_placeholders,
)

__all__ = [
    "PIWM_SYSTEM_PROMPT",
    "build_action_prompt",
    "build_continuation_caption_prompt",
    "build_deliberation_prompt",
    "build_perception_prompt",
    "format_candidate_block",
    "image_placeholders",
]

