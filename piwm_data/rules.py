"""Pure bootstrap rules for the PIWM data pipeline.

All enum strings and numeric rule values in this file are copied from
data_pipeline_spec.md v1. Do not change them without changing the spec.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

RULE_VERSION = "v1.0"

PRODUCT_CATEGORIES = [
    "luxury_watch",
    "electronics_phone",
    "electronics_laptop",
    "cosmetics_skincare",
    "apparel_premium",
    "home_appliance",
    "jewelry",
    "footwear",
]

PERSONA_TYPES = [
    "price_sensitive_cautious",
    "first_time_high_consideration",
    "experienced_brand_loyal",
    "browser_low_intent",
    "gift_buyer_uncertain",
    "price_insensitive_decisive",
]

CUES = [
    "long_dwell_with_price_check",
    "repeated_product_handling",
    "comparing_two_products",
    "looking_around_for_help",
    "checking_phone_likely_research",
    "brief_glance_walking_past",
    "trying_on_or_testing",
    "asking_companion_opinion",
    "no_eye_contact_avoidant",
    "approaching_counter",
]

LATENT_STATES = [
    "high_hesitation",
    "active_evaluation",
    "ready_to_decide",
    "early_browsing",
    "post_decision_reassurance",
    "disengaged",
    "defensive_withdrawal",
    "engaged_dialogue",
    "continued_hesitation",
]

INTENTS = [
    "compare_value_for_money",
    "seek_reassurance",
    "explore_options",
    "confirm_choice",
    "leave_without_purchase",
    "request_demonstration",
    "negotiate_price",
    "no_clear_intent",
]

ACTIONS = [
    "A1_silent_observe",
    "A2_offer_value_comparison",
    "A3_strong_recommend",
    "A4_open_with_question",
    "A5_provide_demonstration",
    "A6_acknowledge_and_wait",
    "A7_disengage",
    "A8_offer_companion_invite",
]

AIDA_STAGES = ["attention", "interest", "desire", "action"]

STATE_TO_AIDA_STAGE_PRIOR: dict[str, str] = {
    "early_browsing": "attention",
    "disengaged": "attention",
    "defensive_withdrawal": "attention",
    "high_hesitation": "interest",
    "active_evaluation": "interest",
    "continued_hesitation": "interest",
    "engaged_dialogue": "desire",
    "post_decision_reassurance": "desire",
    "ready_to_decide": "action",
}

ACTION_COST: dict[str, float] = {
    "A1_silent_observe": 0.0,
    "A2_offer_value_comparison": 0.2,
    "A3_strong_recommend": 0.3,
    "A4_open_with_question": 0.1,
    "A5_provide_demonstration": 0.2,
    "A6_acknowledge_and_wait": 0.1,
    "A7_disengage": 0.0,
    "A8_offer_companion_invite": 0.2,
}

REWARD_ALPHA = 0.4
REWARD_BETA = 0.5
REWARD_GAMMA = 0.1

CUE_TO_STATE_PRIOR: dict[str, str] = {
    "long_dwell_with_price_check": "high_hesitation",
    "repeated_product_handling": "active_evaluation",
    "comparing_two_products": "active_evaluation",
    "looking_around_for_help": "ready_to_decide",
    "checking_phone_likely_research": "active_evaluation",
    "brief_glance_walking_past": "early_browsing",
    "trying_on_or_testing": "active_evaluation",
    "asking_companion_opinion": "active_evaluation",
    "no_eye_contact_avoidant": "disengaged",
    "approaching_counter": "ready_to_decide",
}

PERSONA_STATE_TO_INTENT: dict[tuple[str, str], str] = {
    ("price_sensitive_cautious", "high_hesitation"): "compare_value_for_money",
    ("price_sensitive_cautious", "active_evaluation"): "negotiate_price",
    ("price_sensitive_cautious", "ready_to_decide"): "seek_reassurance",
    ("first_time_high_consideration", "high_hesitation"): "seek_reassurance",
    ("first_time_high_consideration", "active_evaluation"): "request_demonstration",
    ("first_time_high_consideration", "ready_to_decide"): "confirm_choice",
    ("experienced_brand_loyal", "active_evaluation"): "confirm_choice",
    ("experienced_brand_loyal", "ready_to_decide"): "confirm_choice",
    ("browser_low_intent", "early_browsing"): "explore_options",
    ("browser_low_intent", "disengaged"): "leave_without_purchase",
    ("gift_buyer_uncertain", "high_hesitation"): "seek_reassurance",
    ("gift_buyer_uncertain", "active_evaluation"): "request_demonstration",
    ("price_insensitive_decisive", "active_evaluation"): "confirm_choice",
    ("price_insensitive_decisive", "ready_to_decide"): "confirm_choice",
}

STATE_FALLBACK_INTENT: dict[str, str] = {
    "high_hesitation": "seek_reassurance",
    "active_evaluation": "explore_options",
    "ready_to_decide": "confirm_choice",
    "early_browsing": "explore_options",
    "disengaged": "leave_without_purchase",
    "defensive_withdrawal": "leave_without_purchase",
    "engaged_dialogue": "explore_options",
    "continued_hesitation": "seek_reassurance",
    "post_decision_reassurance": "confirm_choice",
}

STATE_TO_PROACTIVE_SCORE: dict[str, int] = {
    "high_hesitation": 4,
    "active_evaluation": 3,
    "ready_to_decide": 5,
    "early_browsing": 2,
    "post_decision_reassurance": 4,
    "disengaged": 1,
    "defensive_withdrawal": 1,
    "engaged_dialogue": 3,
    "continued_hesitation": 4,
}

STATE_AIDA_TO_CANDIDATES: dict[tuple[str, str], list[str]] = {
    ("high_hesitation", "interest"): [
        "A1_silent_observe",
        "A2_offer_value_comparison",
        "A4_open_with_question",
    ],
    ("high_hesitation", "desire"): [
        "A2_offer_value_comparison",
        "A4_open_with_question",
        "A6_acknowledge_and_wait",
    ],
    ("active_evaluation", "interest"): [
        "A4_open_with_question",
        "A5_provide_demonstration",
        "A1_silent_observe",
    ],
    ("active_evaluation", "desire"): [
        "A2_offer_value_comparison",
        "A5_provide_demonstration",
        "A4_open_with_question",
    ],
    ("ready_to_decide", "desire"): [
        "A2_offer_value_comparison",
        "A4_open_with_question",
        "A3_strong_recommend",
    ],
    ("ready_to_decide", "action"): [
        "A3_strong_recommend",
        "A4_open_with_question",
    ],
    ("early_browsing", "attention"): [
        "A1_silent_observe",
        "A6_acknowledge_and_wait",
    ],
    ("disengaged", "attention"): [
        "A7_disengage",
        "A1_silent_observe",
    ],
    ("defensive_withdrawal", "interest"): [
        "A7_disengage",
        "A6_acknowledge_and_wait",
    ],
}

DEFAULT_CANDIDATES = ["A1_silent_observe", "A6_acknowledge_and_wait"]

TRANSITION_TABLE: dict[tuple[str, str], dict[str, Any]] = {
    ("high_hesitation", "A1_silent_observe"): {
        "next_state": "continued_hesitation",
        "reward": 0.3,
        "risk": "low",
        "benefit": "medium",
    },
    ("high_hesitation", "A2_offer_value_comparison"): {
        "next_state": "engaged_dialogue",
        "reward": 0.8,
        "risk": "low",
        "benefit": "high",
    },
    ("high_hesitation", "A3_strong_recommend"): {
        "next_state": "defensive_withdrawal",
        "reward": -0.5,
        "risk": "high",
        "benefit": "low",
    },
    ("high_hesitation", "A4_open_with_question"): {
        "next_state": "engaged_dialogue",
        "reward": 0.6,
        "risk": "low",
        "benefit": "high",
    },
    ("high_hesitation", "A6_acknowledge_and_wait"): {
        "next_state": "continued_hesitation",
        "reward": 0.4,
        "risk": "low",
        "benefit": "medium",
    },
    ("active_evaluation", "A1_silent_observe"): {
        "next_state": "active_evaluation",
        "reward": 0.2,
        "risk": "low",
        "benefit": "low",
    },
    ("active_evaluation", "A2_offer_value_comparison"): {
        "next_state": "engaged_dialogue",
        "reward": 0.7,
        "risk": "low",
        "benefit": "high",
    },
    ("active_evaluation", "A4_open_with_question"): {
        "next_state": "engaged_dialogue",
        "reward": 0.7,
        "risk": "low",
        "benefit": "high",
    },
    ("active_evaluation", "A5_provide_demonstration"): {
        "next_state": "engaged_dialogue",
        "reward": 0.8,
        "risk": "low",
        "benefit": "high",
    },
    ("active_evaluation", "A3_strong_recommend"): {
        "next_state": "defensive_withdrawal",
        "reward": -0.3,
        "risk": "medium",
        "benefit": "low",
    },
    ("ready_to_decide", "A2_offer_value_comparison"): {
        "next_state": "engaged_dialogue",
        "reward": 0.7,
        "risk": "low",
        "benefit": "high",
    },
    ("ready_to_decide", "A3_strong_recommend"): {
        "next_state": "engaged_dialogue",
        "reward": 0.6,
        "risk": "medium",
        "benefit": "high",
    },
    ("ready_to_decide", "A4_open_with_question"): {
        "next_state": "engaged_dialogue",
        "reward": 0.8,
        "risk": "low",
        "benefit": "high",
    },
    ("ready_to_decide", "A1_silent_observe"): {
        "next_state": "disengaged",
        "reward": -0.2,
        "risk": "medium",
        "benefit": "low",
    },
    ("early_browsing", "A1_silent_observe"): {
        "next_state": "early_browsing",
        "reward": 0.5,
        "risk": "low",
        "benefit": "medium",
    },
    ("early_browsing", "A6_acknowledge_and_wait"): {
        "next_state": "early_browsing",
        "reward": 0.5,
        "risk": "low",
        "benefit": "medium",
    },
    ("early_browsing", "A3_strong_recommend"): {
        "next_state": "disengaged",
        "reward": -0.6,
        "risk": "high",
        "benefit": "low",
    },
    ("disengaged", "A7_disengage"): {
        "next_state": "disengaged",
        "reward": 0.4,
        "risk": "low",
        "benefit": "low",
    },
    ("disengaged", "A1_silent_observe"): {
        "next_state": "disengaged",
        "reward": 0.3,
        "risk": "low",
        "benefit": "low",
    },
    ("defensive_withdrawal", "A7_disengage"): {
        "next_state": "disengaged",
        "reward": 0.5,
        "risk": "low",
        "benefit": "medium",
    },
    ("defensive_withdrawal", "A6_acknowledge_and_wait"): {
        "next_state": "high_hesitation",
        "reward": 0.3,
        "risk": "low",
        "benefit": "medium",
    },
}

DEFAULT_TRANSITION = {
    "next_state": "continued_hesitation",
    "reward": 0.0,
    "risk": "medium",
    "benefit": "low",
}

_ACTIVE_EVALUATION_CUES = {
    cue for cue, state in CUE_TO_STATE_PRIOR.items() if state == "active_evaluation"
}
_RISK_RANK = {"low": 0, "medium": 1, "high": 2}
_BENEFIT_RANK = {"high": 0, "medium": 1, "low": 2}
_ACTION_ORDER = {action: index for index, action in enumerate(ACTIONS)}


def derive_latent_state(cues: list[str]) -> str:
    if "approaching_counter" in cues or "looking_around_for_help" in cues:
        return "ready_to_decide"
    if any(cue in _ACTIVE_EVALUATION_CUES for cue in cues):
        return "active_evaluation"
    if "long_dwell_with_price_check" in cues:
        return "high_hesitation"
    if "no_eye_contact_avoidant" in cues:
        return "disengaged"
    return "early_browsing"


def derive_intent(persona_type: str, state: str) -> str:
    return PERSONA_STATE_TO_INTENT.get(
        (persona_type, state),
        STATE_FALLBACK_INTENT.get(state, "no_clear_intent"),
    )


def derive_proactive_score(state: str) -> int:
    return STATE_TO_PROACTIVE_SCORE[state]


def derive_candidate_actions(state: str, aida: str) -> list[str]:
    return list(STATE_AIDA_TO_CANDIDATES.get((state, aida), DEFAULT_CANDIDATES))


def derive_transition(state: str, action: str) -> dict[str, Any]:
    return deepcopy(TRANSITION_TABLE.get((state, action), DEFAULT_TRANSITION))


def derive_bdi(
    persona_type: str,
    state: str,
    intent: str,
    cues: list[str] | None = None,
) -> dict[str, str]:
    cue_text = f" Observable cue(s): {', '.join(cues)}." if cues else ""
    belief = {
        "high_hesitation": "The offer may not yet justify its price.",
        "active_evaluation": "Several options remain worth comparing.",
        "ready_to_decide": "A suitable choice is close but still needs confirmation.",
        "early_browsing": "The category is worth a brief look, but commitment is low.",
        "post_decision_reassurance": "The selected option should be confirmed before closure.",
        "disengaged": "The current interaction is not useful enough to continue.",
        "defensive_withdrawal": "The salesperson may be applying too much pressure.",
        "engaged_dialogue": "The salesperson may help resolve the decision.",
        "continued_hesitation": "The decision remains uncertain after the last observation.",
    }.get(state, "The customer's current mental state is uncertain.")
    desire = {
        "compare_value_for_money": "find better value for money",
        "seek_reassurance": "gain reassurance before deciding",
        "explore_options": "explore available options",
        "confirm_choice": "confirm the preferred choice",
        "leave_without_purchase": "avoid further engagement",
        "request_demonstration": "see how the product works",
        "negotiate_price": "obtain a better price",
        "no_clear_intent": "keep options open",
    }.get(intent, "reduce decision uncertainty")
    intention = {
        "compare_value_for_money": "compare alternatives before deciding",
        "seek_reassurance": "look for reassurance or clarification",
        "explore_options": "continue browsing and comparing",
        "confirm_choice": "move toward confirming the choice",
        "leave_without_purchase": "leave without buying",
        "request_demonstration": "ask for a demonstration",
        "negotiate_price": "ask about price flexibility",
        "no_clear_intent": "continue observing without commitment",
    }.get(intent, "keep observing before acting")
    return {
        "belief": f"{belief} Persona: {persona_type}.{cue_text}",
        "desire": desire,
        "intention": intention,
    }


def derive_next_aida_stage(current_aida: str, next_state: str, reward: float) -> str:
    current_index = _aida_index(current_aida)
    inferred_stage = STATE_TO_AIDA_STAGE_PRIOR.get(next_state, current_aida)
    inferred_index = _aida_index(inferred_stage)
    if reward > 0:
        return AIDA_STAGES[max(current_index, inferred_index)]
    if reward < 0:
        return AIDA_STAGES[min(current_index, inferred_index)]
    return AIDA_STAGES[current_index]


def derive_reward_components(
    current_aida: str,
    next_aida_stage: str,
    action: str,
    final_reward: float,
) -> dict[str, float]:
    delta_stage = (_aida_index(next_aida_stage) - _aida_index(current_aida)) / (len(AIDA_STAGES) - 1)
    action_cost = ACTION_COST.get(action, 0.2)
    delta_mental = (final_reward - REWARD_ALPHA * delta_stage + REWARD_GAMMA * action_cost) / REWARD_BETA
    return {
        "delta_stage": delta_stage,
        "delta_mental": delta_mental,
        "action_cost": action_cost,
        "alpha": REWARD_ALPHA,
        "beta": REWARD_BETA,
        "gamma": REWARD_GAMMA,
        "final_reward": final_reward,
    }


def derive_action_outcome(
    state: str,
    aida_stage: str,
    persona_type: str,
    action: str,
) -> dict[str, Any]:
    transition = derive_transition(state, action)
    next_state = transition["next_state"]
    reward = float(transition["reward"])
    next_aida_stage = derive_next_aida_stage(aida_stage, next_state, reward)
    next_intent = derive_intent(persona_type, next_state)
    transition["next_aida_stage"] = next_aida_stage
    transition["next_bdi"] = derive_bdi(persona_type, next_state, next_intent)
    transition["reward_components"] = derive_reward_components(aida_stage, next_aida_stage, action, reward)
    return transition


def pick_best_action(state: str, candidates: list[str]) -> str:
    def key(action: str) -> tuple[float, int, int, int]:
        transition = derive_transition(state, action)
        return (
            -float(transition["reward"]),
            _RISK_RANK[transition["risk"]],
            _BENEFIT_RANK[transition["benefit"]],
            _ACTION_ORDER[action],
        )

    return min(candidates, key=key)


def _aida_index(stage: str) -> int:
    return AIDA_STAGES.index(stage) if stage in AIDA_STAGES else 0
