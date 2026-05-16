"""Export PIWM main schema records into the three training JSONL formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from . import reaction_templates, rules
from .schemas import ActionRealization, MainSchemaRecord

WORTH_DOING_THRESHOLD = 0.0


def main_schema_record_payload(record: MainSchemaRecord) -> dict[str, Any]:
    """Return the canonical v2.2 main-schema payload.

    The in-memory Pydantic model still accepts v2 ``co_acts`` for compatibility.
    New serialized data uses ``act_params.supporting_acts`` and moves old
    top-level co-acts to ``legacy_co_acts`` only when non-empty.
    """

    payload = record.model_dump(mode="json")
    payload["schema_version"] = rules.ACTION_SCHEMA_VERSION
    payload["actor_profile"] = _actor_profile(record)
    if record.viewpoint == "target_frontcam":
        payload["view_class"] = "target_frontcam"
    payload["act_params"] = rules.merge_supporting_acts(payload.get("act_params", {}), payload.get("co_acts", []))
    legacy_co_acts = payload.pop("co_acts", [])
    if legacy_co_acts:
        payload["legacy_co_acts"] = legacy_co_acts
    if payload.get("realization"):
        payload["realization"] = _terminal_realization_payload(payload["realization"])
    return payload


def export_state_inference(
    records: Iterable[MainSchemaRecord],
    out: Path,
    include_observable_cues: bool = False,
) -> int:
    rows = [
        _state_inference_row(record, include_observable_cues=include_observable_cues)
        for record in records
    ]
    return _write_jsonl(rows, out)


def export_state_inference_with_cue(records: Iterable[MainSchemaRecord], out: Path) -> int:
    return export_state_inference(records, out, include_observable_cues=True)


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


def export_world_model_continuation(records: Iterable[MainSchemaRecord], out: Path) -> int:
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.extend(_world_model_continuation_rows(record))
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
            record.candidate_actions.index(action),
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
            "action_spec": _candidate_spec_for_action(record, best_action),
            "dialogue_act": _dialogue_act_for_action(record, best_action),
            "rationale": _outcome_rationale(record, best_action),
            "action_realization": _action_realization(record, best_action).model_dump(),
            "terminal_realization": _terminal_realization(record, best_action),
        },
        "rejected_json": {
            "action": rejected,
            "action_spec": _candidate_spec_for_action(record, rejected),
            "dialogue_act": _dialogue_act_for_action(record, rejected),
            "rationale": _outcome_rationale(record, rejected),
            "action_realization": _action_realization(record, rejected).model_dump(),
            "terminal_realization": _terminal_realization(record, rejected),
        },
        "reward_gap": best_reward - rejected_reward,
        "meta": {
            "product_category": record.product_category,
            "split": record.split,
            "viewpoint": record.viewpoint,
            "actor_profile": _actor_profile(record),
            "frames": _frame_paths(record),
            "is_anchor": record.is_anchor,
            "rule_version": rules.RULE_VERSION,
            "state_summary": _state_summary(record),
            "candidate_block": _candidate_block(record),
            "compatibility_tier": record.compatibility_tier,
            "legacy_mismatch_flags": record.legacy_mismatch_flags,
        },
    }


def count_policy_preference_skipped_no_pair(records: Iterable[MainSchemaRecord]) -> int:
    return sum(1 for record in records if build_policy_preference_row(record) is None)


def _state_inference_row(record: MainSchemaRecord, include_observable_cues: bool = False) -> dict[str, Any]:
    input_payload: dict[str, Any] = {
        "frames": _frame_paths(record),
        "persona_summary": _persona_summary(record),
        "history_summary": None,
    }
    if include_observable_cues:
        input_payload["observable_cues"] = record.observable_cues
    return {
        "state_id": record.state_id,
        "input": input_payload,
        "output": {
            "visual_state": record.visual_state.model_dump(),
            "aida_stage": record.aida_stage,
            "state_subtype": record.latent_state,
            "current_state": record.latent_state,
            "intent": record.intent,
            "bdi": record.bdi.model_dump(),
            "proactive_score": record.proactive_score,
            "candidate_actions": record.candidate_actions,
            "best_action": record.best_action,
            "candidate_action_specs": _candidate_action_specs_payload(record),
            "best_action_spec": _best_action_spec_payload(record),
            "intent_tier": record.persona.intent_tier,
            "dialogue_act": record.dialogue_act,
            "act_params": rules.merge_supporting_acts(record.act_params, record.co_acts),
            "best_action_realization": record.best_action_realization.model_dump(),
            "terminal_realization": _terminal_realization_payload(record.realization) if record.realization else None,
            "legacy_co_acts": record.co_acts,
            "rationale": record.rationale,
        },
        "meta": {
            "product_category": record.product_category,
            "split": record.split,
            "viewpoint": record.viewpoint,
            "actor_profile": _actor_profile(record),
            "observable_cues": record.observable_cues,
            "visual_only_input": not include_observable_cues,
            "aida_stage": record.aida_stage,
            "deprecated_calibration_fields": ["proactive_score"],
            "compatibility_tier": record.compatibility_tier,
            "legacy_mismatch_flags": record.legacy_mismatch_flags,
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
                    "current_state_summary": _state_summary(record),
                    "candidate_action": action,
                    "candidate_action_key": _candidate_action_key_for_action(record, action),
                    "candidate_action_spec": _candidate_spec_for_action(record, action),
                    "candidate_dialogue_act": _dialogue_act_for_action(record, action),
                    "candidate_action_realization": _action_realization(record, action).model_dump(),
                    "candidate_terminal_realization": _terminal_realization(record, action),
                },
                "output": {
                    "next_aida_stage": outcome.next_aida_stage,
                    "next_state_subtype": outcome.next_state,
                    "next_state": outcome.next_state,
                    "next_bdi": outcome.next_bdi.model_dump(),
                    "risk": outcome.risk,
                    "benefit": outcome.benefit,
                    "reward": outcome.reward,
                    "reward_components": outcome.reward_components.model_dump(),
                    "worth_doing": outcome.reward > WORTH_DOING_THRESHOLD,
                    "rationale": outcome.rationale,
                    "dialogue_act": outcome.dialogue_act,
                    "act_params": outcome.act_params,
                    "intent_tier": outcome.intent_tier,
                    "risk_tags": outcome.risk_tags,
                    "failure_mode": outcome.failure_mode,
                    "outcome_type": outcome.outcome_type,
                },
                "meta": {
                    "product_category": record.product_category,
                    "split": record.split,
                    "viewpoint": record.viewpoint,
                    "actor_profile": _actor_profile(record),
                    "parent_state_id": record.state_id,
                    "compatibility_tier": record.compatibility_tier,
                    "legacy_mismatch_flags": record.legacy_mismatch_flags,
                    "is_anchor": record.is_anchor,
                    "rule_version": rules.RULE_VERSION,
                },
            }
        )
    return rows


def _world_model_continuation_rows(record: MainSchemaRecord) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for action in record.candidate_actions:
        continuation = record.continuations.get(action)
        if continuation is None or continuation.qa_overall_pass is not True:
            continue
        outcome = record.next_state_by_action[action]
        template = reaction_templates.REACTION_TEMPLATES[continuation.reaction_template_id]
        rows.append(
            {
                "state_id": continuation.continuation_id,
                "input": {
                    "current_frames": _frame_paths(record),
                    "candidate_action": action,
                    "candidate_action_key": _candidate_action_key_for_action(record, action),
                    "candidate_action_spec": _candidate_spec_for_action(record, action),
                    "current_state_summary": _state_summary(record),
                },
                "output": {
                    "next_aida_stage": outcome.next_aida_stage,
                    "next_state_subtype": outcome.next_state,
                    "next_state": outcome.next_state,
                    "reward": outcome.reward,
                    "risk": outcome.risk,
                    "benefit": outcome.benefit,
                    "reaction_caption": template["reaction_caption"],
                    "visible_reaction": reaction_templates.visible_reaction_axes(template),
                    "dialogue_act": outcome.dialogue_act,
                    "act_params": outcome.act_params,
                    "intent_tier": outcome.intent_tier,
                    "risk_tags": outcome.risk_tags,
                    "failure_mode": outcome.failure_mode,
                    "outcome_type": outcome.outcome_type,
                    "continuation_frames": [
                        frame.model_dump()
                        for frame in continuation.frames
                    ],
                },
                "meta": {
                    "product_category": record.product_category,
                    "split": record.split,
                    "viewpoint": record.viewpoint,
                    "actor_profile": _actor_profile(record),
                    "continuation_role": continuation.continuation_role.value,
                    "reaction_template_id": continuation.reaction_template_id,
                    "parent_state_id": record.state_id,
                    "compatibility_tier": record.compatibility_tier,
                    "legacy_mismatch_flags": record.legacy_mismatch_flags,
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
        f"视觉观察：{record.visual_state.summary}；"
        f"persona：{record.persona.type}；"
        f"候选动作：[{candidates}]。请选择最合适的动作并给出理由。"
    )


def _state_summary(record: MainSchemaRecord) -> dict[str, Any]:
    return {
        "aida_stage": record.aida_stage,
        "product_category": record.product_category,
        "state_subtype": record.latent_state,
        "state": record.latent_state,
        "visual_state": record.visual_state.model_dump(),
        "intent": record.intent,
        "intent_tier": record.persona.intent_tier,
        "bdi": record.bdi.model_dump(),
        "proactive_score": record.proactive_score,
        "candidate_action_specs": _candidate_action_specs_payload(record),
        "best_action_spec": _best_action_spec_payload(record),
        "persona_type": record.persona.type,
        "observable_cues": record.observable_cues,
        "dialogue_act": record.dialogue_act,
        "act_params": rules.merge_supporting_acts(record.act_params, record.co_acts),
        "terminal_realization": _terminal_realization_payload(record.realization) if record.realization else None,
        "legacy_co_acts": record.co_acts,
        "compatibility_tier": record.compatibility_tier,
        "legacy_mismatch_flags": record.legacy_mismatch_flags,
    }


def _candidate_block(record: MainSchemaRecord) -> list[dict[str, Any]]:
    return [
        {
            "action": action,
            "action_key": _candidate_action_key_for_action(record, action),
            "reward": record.reward_by_action[action],
            "next_state": record.next_state_by_action[action].next_state,
            "next_aida_stage": record.next_state_by_action[action].next_aida_stage,
            "risk": record.next_state_by_action[action].risk,
            "benefit": record.next_state_by_action[action].benefit,
            "action_spec": _candidate_spec_for_action(record, action),
            "dialogue_act": _dialogue_act_for_action(record, action),
            "risk_tags": record.next_state_by_action[action].risk_tags,
            "failure_mode": record.next_state_by_action[action].failure_mode,
            "outcome_type": record.next_state_by_action[action].outcome_type,
            "action_realization": _action_realization(record, action).model_dump(),
            "terminal_realization": _terminal_realization(record, action),
        }
        for action in record.candidate_actions
    ]


def _persona_summary(record: MainSchemaRecord) -> str:
    if record.persona.description:
        return f"{record.persona.type}: {record.persona.description}"
    return record.persona.type


def _outcome_rationale(record: MainSchemaRecord, action: str) -> str | None:
    outcome = record.next_state_by_action[action]
    return outcome.rationale or record.rationale


def _action_realization(record: MainSchemaRecord, action: str) -> ActionRealization:
    if action == record.best_action:
        return record.best_action_realization
    if action not in rules.ACTIONS:
        terminal = _terminal_realization(record, action)
        surface_text = terminal.get("surface_text") or "（静默）"
        return ActionRealization(
            utterance=surface_text,
            physical_action="智能售货柜按屏幕、语音、灯效执行该候选响应。",
            timing="设备前置摄像头检测到当前顾客状态后触发。",
            rationale=f"target terminal realization for {action}",
        )
    return ActionRealization(
        **rules.derive_action_realization(
            action,
            record.latent_state,
            record.persona.type,
            record.product_category,
            record.observable_cues,
        )
    )


def _act_spec(action: str) -> dict[str, Any]:
    spec = rules.legacy_action_to_act(action)
    return {
        "act": spec["act"],
        "params": spec["params"],
        "legacy_co_acts": spec.get("co_acts", []),
    }


def _dialogue_act_for_action(record: MainSchemaRecord, action: str) -> dict[str, Any]:
    spec = _candidate_spec_for_action(record, action)
    params = rules.merge_supporting_acts(spec.get("params", {}))
    return {
        "act": spec["act"],
        "params": params,
        "legacy_co_acts": rules.legacy_co_acts_from_params(params),
    }


def _candidate_action_specs_payload(record: MainSchemaRecord) -> list[dict[str, Any]]:
    if record.candidate_action_specs:
        return [spec.model_dump(mode="json") for spec in record.candidate_action_specs]
    return [
        {"act": spec["act"], "params": rules.merge_supporting_acts(spec.get("params"), spec.get("co_acts"))}
        for spec in (rules.legacy_action_to_act(action) for action in record.candidate_actions)
    ]


def _best_action_spec_payload(record: MainSchemaRecord) -> dict[str, Any]:
    if record.best_action_spec is not None:
        return record.best_action_spec.model_dump(mode="json")
    spec = rules.legacy_action_to_act(record.best_action)
    return {"act": spec["act"], "params": rules.merge_supporting_acts(spec.get("params"), spec.get("co_acts"))}


def _candidate_spec_for_action(record: MainSchemaRecord, action: str) -> dict[str, Any]:
    if action in record.candidate_actions and record.candidate_action_specs:
        index = record.candidate_actions.index(action)
        return record.candidate_action_specs[index].model_dump(mode="json")
    if action not in rules.ACTIONS:
        raise ValueError(f"missing candidate_action_specs for v2 action key: {action}")
    spec = rules.legacy_action_to_act(action)
    return {"act": spec["act"], "params": rules.merge_supporting_acts(spec.get("params"), spec.get("co_acts"))}


def _candidate_action_key_for_action(record: MainSchemaRecord, action: str) -> str:
    spec = _candidate_spec_for_action(record, action)
    return rules.action_spec_key(spec["act"], spec.get("params", {}))


def _terminal_realization(record: MainSchemaRecord, action: str) -> dict[str, Any]:
    if action == record.best_action and record.realization is not None:
        return _terminal_realization_payload(record.realization)
    if action not in rules.ACTIONS:
        spec = _candidate_spec_for_action(record, action)
        return _terminal_realization_payload(
            rules.derive_terminal_realization_from_act(spec["act"], spec.get("params", {}))
        )
    return _terminal_realization_payload(rules.derive_terminal_realization(
        action,
        record.latent_state,
        record.persona.type,
        record.product_category,
        record.observable_cues,
    ))


def _terminal_realization_payload(realization: Any) -> dict[str, Any]:
    if hasattr(realization, "model_dump"):
        payload = realization.model_dump()
    else:
        payload = dict(realization)
    payload["act_params"] = rules.merge_supporting_acts(payload.get("act_params", {}), payload.get("co_acts", []))
    legacy_co_acts = payload.pop("co_acts", [])
    if legacy_co_acts:
        payload["legacy_co_acts"] = legacy_co_acts
    return payload


def _frame_paths(record: MainSchemaRecord) -> list[str]:
    return [frame.relative_path for frame in record.images]


def _actor_profile(record: MainSchemaRecord) -> str:
    if record.viewpoint == "target_frontcam":
        return "target_terminal_logic"
    return "human_salesperson_logic"


def _write_jsonl(rows: list[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
    return len(rows)
