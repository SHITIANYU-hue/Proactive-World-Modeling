"""Export PIWM main schema records into the three training JSONL formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from . import rules
from .schemas import MainSchemaRecord

WORTH_DOING_THRESHOLD = 0.0


def export_state_inference(records: Iterable[MainSchemaRecord], out: Path) -> int:
    rows = [_state_inference_row(record) for record in records]
    return _write_jsonl(rows, out)


def export_transition_modeling(records: Iterable[MainSchemaRecord], out: Path) -> int:
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.extend(_transition_rows(record))
    return _write_jsonl(rows, out)


def export_policy_preference(records: Iterable[MainSchemaRecord], out: Path) -> int:
    rows = []
    for record in records:
        row = build_policy_preference_row(record)
        if row is not None:
            rows.append(row)
    return _write_jsonl(rows, out)


def build_policy_preference_row(record: MainSchemaRecord) -> dict[str, Any] | None:
    if len(record.candidate_actions) < 2:
        return None

    best_action = record.best_action
    best_reward = record.reward_by_action[best_action]
    rejected_pool = [
        action
        for action in record.candidate_actions
        if record.reward_by_action[action] < best_reward
    ]
    if not rejected_pool:
        return None

    rejected = min(
        rejected_pool,
        key=lambda action: (
            record.reward_by_action[action],
            rules.ACTIONS.index(action),
        ),
    )
    rejected_reward = record.reward_by_action[rejected]
    return {
        "state_id": record.state_id,
        "prompt": _policy_prompt(record),
        "chosen": best_action,
        "rejected": rejected,
        "chosen_json": {
            "action": best_action,
            "rationale": _outcome_rationale(record, best_action),
        },
        "rejected_json": {
            "action": rejected,
            "rationale": _outcome_rationale(record, rejected),
        },
        "reward_gap": best_reward - rejected_reward,
        "meta": {
            "frames": _frame_paths(record),
            "is_anchor": record.is_anchor,
            "rule_version": rules.RULE_VERSION,
        },
    }


def count_policy_preference_skipped_no_pair(records: Iterable[MainSchemaRecord]) -> int:
    return sum(1 for record in records if build_policy_preference_row(record) is None)


def _state_inference_row(record: MainSchemaRecord) -> dict[str, Any]:
    return {
        "state_id": record.state_id,
        "input": {
            "frames": _frame_paths(record),
            "observable_cues": record.observable_cues,
            "persona_summary": _persona_summary(record),
            "history_summary": None,
        },
        "output": {
            "current_state": record.latent_state,
            "intent": record.intent,
            "proactive_score": record.proactive_score,
            "candidate_actions": record.candidate_actions,
            "best_action": record.best_action,
            "rationale": record.rationale,
        },
        "meta": {
            "aida_stage": record.aida_stage,
            "is_anchor": record.is_anchor,
            "rule_version": rules.RULE_VERSION,
        },
    }


def _transition_rows(record: MainSchemaRecord) -> list[dict[str, Any]]:
    rows = []
    for action in record.candidate_actions:
        outcome = record.next_state_by_action[action]
        rows.append(
            {
                "state_id": f"{record.state_id}#{action}",
                "input": {
                    "frames": _frame_paths(record),
                    "current_state_summary": {
                        "state": record.latent_state,
                        "intent": record.intent,
                        "persona_type": record.persona.type,
                    },
                    "candidate_action": action,
                },
                "output": {
                    "next_state": outcome.next_state,
                    "risk": outcome.risk,
                    "benefit": outcome.benefit,
                    "reward": outcome.reward,
                    "worth_doing": outcome.reward > WORTH_DOING_THRESHOLD,
                    "rationale": outcome.rationale,
                },
                "meta": {
                    "parent_state_id": record.state_id,
                    "is_anchor": record.is_anchor,
                    "rule_version": rules.RULE_VERSION,
                },
            }
        )
    return rows


def _policy_prompt(record: MainSchemaRecord) -> str:
    candidates = ", ".join(record.candidate_actions)
    return (
        f"顾客状态：{record.latent_state}；"
        f"意图：{record.intent}；"
        f"persona：{record.persona.type}；"
        f"候选动作：[{candidates}]。请选择最合适的动作并给出理由。"
    )


def _persona_summary(record: MainSchemaRecord) -> str:
    if record.persona.description:
        return f"{record.persona.type}: {record.persona.description}"
    return record.persona.type


def _outcome_rationale(record: MainSchemaRecord, action: str) -> str | None:
    outcome = record.next_state_by_action[action]
    return outcome.rationale or record.rationale


def _frame_paths(record: MainSchemaRecord) -> list[str]:
    return [frame.relative_path for frame in record.images]


def _write_jsonl(rows: list[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
    return len(rows)

