"""Validation helpers for PIWM main schema records."""

from __future__ import annotations

from pathlib import Path

from .schemas import MainSchemaRecord


def validate_main_schema(record: MainSchemaRecord) -> list[str]:
    errors: list[str] = []
    candidate_set = set(record.candidate_actions)
    next_state_keys = set(record.next_state_by_action)
    reward_keys = set(record.reward_by_action)

    if record.best_action not in candidate_set:
        errors.append("best_action must be in candidate_actions")
    if not next_state_keys.issuperset(candidate_set):
        errors.append("next_state_by_action keys must include all candidate_actions")
    if reward_keys != next_state_keys:
        errors.append("reward_by_action keys must match next_state_by_action keys")
    for action, outcome in record.next_state_by_action.items():
        reward = record.reward_by_action.get(action)
        if reward != outcome.reward:
            errors.append(f"reward mismatch for action {action}")
    return errors


def validate_image_paths(record: MainSchemaRecord, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for frame in record.images:
        if not (repo_root / frame.relative_path).exists():
            errors.append(f"missing frame path: {frame.relative_path}")
    return errors

