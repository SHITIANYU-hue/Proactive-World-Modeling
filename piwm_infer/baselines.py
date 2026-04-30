"""Zero-shot and deterministic baseline helpers for PIWM pilot artifacts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from piwm_data import rules


API_BASELINES: dict[str, str] = {
    "gpt4v": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "qwen_vl": "DASHSCOPE_API_KEY",
}

LOCAL_BASELINES = {"rule_oracle"}


@dataclass(frozen=True)
class BaselinePrediction:
    """Structured prediction for one pilot record."""

    aida_stage: str
    state_subtype: str
    intent: str
    proactive_score: int
    candidate_actions: list[str]
    chosen_action: str
    rationale: str


def is_local_baseline(model: str) -> bool:
    return model in LOCAL_BASELINES


def api_key_env_for(model: str) -> str | None:
    return API_BASELINES.get(model)


def api_status(model: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Return a non-throwing API availability record for an external model."""

    key_name = api_key_env_for(model)
    if key_name is None:
        return {
            "model": model,
            "status": "unsupported_model",
            "reason": "No baseline adapter is registered for this model.",
        }

    env_map = os.environ if env is None else env
    if not env_map.get(key_name):
        return {
            "model": model,
            "status": "api_unavailable",
            "api_key_env": key_name,
            "reason": f"Missing {key_name}; no network request was attempted.",
        }

    return {
        "model": model,
        "status": "api_unavailable",
        "api_key_env": key_name,
        "reason": "API invocation is intentionally not implemented in the offline smoke runner.",
    }


def predict_rule_oracle(state_row: dict[str, Any], policy_row: dict[str, Any] | None = None) -> BaselinePrediction:
    """Metadata-assisted deterministic baseline for smoke numbers.

    This is not a model result. It uses observable cue metadata plus public
    bootstrap rules to create a stable lower-cost baseline artifact.
    """

    meta = _dict(state_row.get("meta"))
    input_obj = _dict(state_row.get("input"))
    cues = _string_list(meta.get("observable_cues"))
    state = _state_from_cues(cues)
    stage = rules.STATE_TO_AIDA_STAGE_PRIOR.get(state, "attention")
    persona_type = _persona_type(input_obj.get("persona_summary"))
    intent = rules.PERSONA_STATE_TO_INTENT.get(
        (persona_type, state),
        rules.STATE_FALLBACK_INTENT.get(state, "no_clear_intent"),
    )
    score = rules.STATE_TO_PROACTIVE_SCORE.get(state, 1)
    candidates = _candidate_actions(state_row, state, stage)
    chosen = _choose_action(candidates, policy_row, state, persona_type)
    return BaselinePrediction(
        aida_stage=stage,
        state_subtype=state,
        intent=intent,
        proactive_score=score,
        candidate_actions=candidates,
        chosen_action=chosen,
        rationale=(
            "Deterministic metadata-assisted rule_oracle: infer state from "
            "observable_cues, derive intent/candidates from bootstrap priors, "
            "then choose by policy pair when available or by static action prior."
        ),
    )


def prediction_to_record(
    state_id: str,
    prediction: BaselinePrediction,
    gold: dict[str, Any],
    policy_gold: dict[str, Any] | None,
) -> dict[str, Any]:
    predicted = {
        "aida_stage": prediction.aida_stage,
        "state_subtype": prediction.state_subtype,
        "intent": prediction.intent,
        "proactive_score": prediction.proactive_score,
        "candidate_actions": prediction.candidate_actions,
        "chosen_action": prediction.chosen_action,
        "rationale": prediction.rationale,
    }
    return {
        "state_id": state_id,
        "predicted": predicted,
        "gold": gold,
        "policy_gold": policy_gold,
        "correct": {
            "aida_stage": prediction.aida_stage == gold.get("aida_stage"),
            "state_subtype": prediction.state_subtype == gold.get("state_subtype"),
            "intent": prediction.intent == gold.get("intent"),
            "chosen_action": prediction.chosen_action == gold.get("best_action"),
            "policy_pair": (
                None
                if policy_gold is None
                else prediction.chosen_action == policy_gold.get("chosen")
            ),
        },
    }


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    policy_records = [row for row in records if row["correct"]["policy_pair"] is not None]
    return {
        "n_records": n,
        "n_policy_pairs": len(policy_records),
        "aida_stage_accuracy": _ratio(records, "aida_stage"),
        "state_subtype_accuracy": _ratio(records, "state_subtype"),
        "intent_accuracy": _ratio(records, "intent"),
        "strategy_accuracy_vs_best_action": _ratio(records, "chosen_action"),
        "policy_pair_accuracy": (
            None
            if not policy_records
            else sum(1 for row in policy_records if row["correct"]["policy_pair"]) / len(policy_records)
        ),
    }


def _ratio(records: list[dict[str, Any]], field: str) -> float | None:
    if not records:
        return None
    return sum(1 for row in records if row["correct"][field]) / len(records)


def _state_from_cues(cues: list[str]) -> str:
    for cue in cues:
        state = rules.CUE_TO_STATE_PRIOR.get(cue)
        if state is not None:
            return state
    return "early_browsing"


def _persona_type(persona_summary: Any) -> str:
    if not isinstance(persona_summary, str) or ":" not in persona_summary:
        return "browser_low_intent"
    candidate = persona_summary.split(":", 1)[0].strip()
    return candidate if candidate in rules.PERSONA_TYPES else "browser_low_intent"


def _candidate_actions(state_row: dict[str, Any], state: str, stage: str) -> list[str]:
    input_candidates = _string_list(_dict(state_row.get("output")).get("candidate_actions"))
    if input_candidates:
        return input_candidates
    return list(rules.STATE_AIDA_TO_CANDIDATES.get((state, stage), rules.DEFAULT_CANDIDATES))


def _choose_action(
    candidates: list[str],
    policy_row: dict[str, Any] | None,
    state: str,
    persona_type: str,
) -> str:
    if policy_row is not None:
        chosen = policy_row.get("chosen")
        if isinstance(chosen, str) and chosen in candidates:
            return chosen

    priority = _action_priority(state, persona_type)
    for action in priority:
        if action in candidates:
            return action
    return candidates[0] if candidates else rules.DEFAULT_CANDIDATES[0]


def _action_priority(state: str, persona_type: str) -> list[str]:
    if state in {"disengaged", "defensive_withdrawal"}:
        return ["A7_disengage", "A6_acknowledge_and_wait", "A1_silent_observe"]
    if persona_type == "price_sensitive_cautious":
        return ["A2_offer_value_comparison", "A4_open_with_question", "A6_acknowledge_and_wait", "A1_silent_observe"]
    if state == "ready_to_decide":
        return ["A4_open_with_question", "A3_strong_recommend", "A6_acknowledge_and_wait", "A1_silent_observe"]
    if state in {"high_hesitation", "continued_hesitation"}:
        return ["A4_open_with_question", "A2_offer_value_comparison", "A6_acknowledge_and_wait", "A1_silent_observe"]
    return ["A4_open_with_question", "A5_provide_demonstration", "A2_offer_value_comparison", "A6_acknowledge_and_wait", "A1_silent_observe"]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
