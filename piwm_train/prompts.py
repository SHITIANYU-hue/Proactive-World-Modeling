"""Prompt builders for PIWM training rows."""

from __future__ import annotations

from typing import Any

from . import config

PIWM_SYSTEM_PROMPT = (
    "You are a multimodal sales-guidance agent trained on retail pedagogy. "
    "You observe customers in physical retail stores via a streaming camera "
    "and decide whether and how to intervene. Always output your reasoning "
    "in the structured tag format requested by the user prompt. Do not output "
    "free-form prose outside the requested tags."
)


def image_placeholders(n_frames: int) -> str:
    return "\n".join(config.IMAGE_PLACEHOLDER for _ in range(n_frames))


def build_perception_prompt(record: dict) -> str:
    frames = record["input"].get("frames", [])
    history = record["input"].get("history_summary") or "empty"
    return (
        "You are observing a customer in a retail store. Below are "
        f"{len(frames)} frames sampled from a streaming camera, in chronological order.\n\n"
        f"{image_placeholders(len(frames))}\n\n"
        "History summary (states inferred at earlier decision points; may be empty):\n"
        f"{history}\n\n"
        "Identify the customer's current state and decide whether the situation warrants intervention.\n\n"
        "Output the following fields, in this exact order, each on its own line:\n"
        f"{config.tag_instruction_lines(config.PERCEPTION_TAGS)}\n\n"
        "- stage must be one of: attention, interest, desire, action.\n"
        "- score must be an integer 1-5, where 1 means do not disturb and 5 means intervene immediately.\n"
        "- cands must be a comma-separated list of candidate strategy labels appropriate for the inferred stage.\n"
        "- belief, desire, and intention must be single short clauses in English."
    )


def build_deliberation_prompt(record: dict) -> str:
    frames = record["input"].get("frames", [])
    state = record["input"]["current_state_summary"]
    bdi = state["bdi"]
    action = record["input"]["candidate_action"]
    return (
        "You are observing a customer in a retail store. Below are "
        f"{len(frames)} frames sampled from a streaming camera, in chronological order.\n\n"
        f"{image_placeholders(len(frames))}\n\n"
        "The customer's current state is:\n"
        f"- stage: {state['aida_stage']}\n"
        f"- belief: {bdi['belief']}\n"
        f"- desire: {bdi['desire']}\n"
        f"- intention: {bdi['intention']}\n\n"
        f"Consider one candidate intervention: {action}\n\n"
        "Predict how this candidate intervention will change the customer's state in the next decision step. "
        "Output the following fields, in this exact order, each on its own line:\n"
        f"{config.tag_instruction_lines(config.DELIBERATION_TAGS)}\n\n"
        "- next_stage must be one of: attention, interest, desire, action.\n"
        "- risk and benefit must each be one of: low, medium, high.\n"
        "- reward must be a number in [-1.00, 1.00] with two decimal places.\n"
        "- all textual spans must be a single short clause in English."
    )


def build_continuation_caption_prompt(record: dict) -> str:
    frames = record["input"].get("current_frames", [])
    state = record["input"]["current_state_summary"]
    bdi = state["bdi"]
    action = record["input"]["candidate_action"]
    return (
        "You are observing a customer in a retail store. Below are "
        f"{len(frames)} current-state frames sampled in chronological order.\n\n"
        f"{image_placeholders(len(frames))}\n\n"
        "The customer's current state is:\n"
        f"- stage: {state['aida_stage']}\n"
        f"- belief: {bdi['belief']}\n"
        f"- desire: {bdi['desire']}\n"
        f"- intention: {bdi['intention']}\n\n"
        f"Imagine the customer's visible reaction after the salesperson chooses: {action}.\n"
        "Describe what you would see in the next 5 seconds.\n\n"
        "Output the following field, in this exact format:\n"
        f"{config.tag_instruction_lines(config.CONTINUATION_TAGS)}"
    )


def format_candidate_block(per_candidate_outputs: dict[str, dict[str, Any]] | list[dict[str, Any]]) -> str:
    if isinstance(per_candidate_outputs, list):
        rows = per_candidate_outputs
    else:
        rows = [{"action": action, **values} for action, values in per_candidate_outputs.items()]
    lines = []
    for row in rows:
        reward = config.REWARD_FORMAT.format(float(row["reward"]))
        next_stage = row.get("next_aida_stage") or row.get("predicted_next_stage") or row.get("next_stage")
        lines.append(
            f"- {row['action']}: predicted_next_stage={next_stage}, "
            f"risk={row['risk']}, benefit={row['benefit']}, reward={reward}"
        )
    return "\n".join(lines)


def build_action_prompt(record: dict) -> str:
    state = record["meta"]["state_summary"]
    bdi = state["bdi"]
    frames = record["meta"].get("frames", [])
    return (
        "You are observing a customer in a retail store. Below are "
        f"{len(frames)} frames sampled from a streaming camera, in chronological order.\n\n"
        f"{image_placeholders(len(frames))}\n\n"
        "The customer's current state is:\n"
        f"- stage: {state['aida_stage']}\n"
        f"- belief: {bdi['belief']}\n"
        f"- desire: {bdi['desire']}\n"
        f"- intention: {bdi['intention']}\n\n"
        "You have evaluated the following candidate interventions:\n\n"
        f"{format_candidate_block(record['meta']['candidate_block'])}\n\n"
        "Choose the best intervention and explain your reasoning briefly.\n\n"
        "Output the following fields, in this exact order:\n"
        f"{config.tag_instruction_lines(config.ACTION_TAGS)}\n\n"
        "- chosen must be one of the candidate labels listed above, exact string match.\n"
        "- rationale should reference the predicted next states when justifying the choice."
    )

