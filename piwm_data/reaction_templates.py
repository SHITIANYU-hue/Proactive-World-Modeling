"""Visible reaction templates for action-conditioned continuation videos."""

from __future__ import annotations

from typing import TypedDict

from . import rules


class ReactionTemplate(TypedDict):
    next_state: str
    reaction_caption: str
    physical_change: str
    head_gaze: str
    hands: str
    movement: str
    duration_window_sec: tuple[int, int]
    frame_roles: list[str]


REACTION_TEMPLATES: dict[str, ReactionTemplate] = {
    "REACT_HIGH_HESITATION_001": {
        "next_state": "high_hesitation",
        "reaction_caption": "the customer stays close to the display, keeps checking the price area, and remains visibly undecided",
        "physical_change": "customer stays near the display with a cautious, slightly closed posture",
        "head_gaze": "gaze alternates between the product and price area",
        "hands": "hands hover near the product or price placard without committing",
        "movement": "small weight shifts, no clear approach or withdrawal",
        "duration_window_sec": (4, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_ACTIVE_EVALUATION_001": {
        "next_state": "active_evaluation",
        "reaction_caption": "the customer continues examining the product, keeping attention on visible details and features",
        "physical_change": "customer continues examining the product without interruption",
        "head_gaze": "gaze stays on product details",
        "hands": "hands continue handling or pointing to features",
        "movement": "stable stance, no body re-orientation",
        "duration_window_sec": (4, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_READY_TO_DECIDE_001": {
        "next_state": "ready_to_decide",
        "reaction_caption": "the customer orients toward the service area while staying near the chosen product",
        "physical_change": "customer shifts posture toward the counter or salesperson area",
        "head_gaze": "head turns between product and service area",
        "hands": "hands settle near the product or point to the preferred option",
        "movement": "body moves slightly forward as if preparing to ask or decide",
        "duration_window_sec": (3, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_EARLY_BROWSING_001": {
        "next_state": "early_browsing",
        "reaction_caption": "the customer keeps browsing lightly alone, briefly scanning the product while staying noncommittal",
        "physical_change": "customer remains alone near the display with a light, noncommittal browsing posture",
        "head_gaze": "gaze briefly scans product and surrounding area without seeking staff",
        "hands": "hands remain relaxed with minimal product contact and no request gesture",
        "movement": "slow casual movement along the display, with no staff approaching",
        "duration_window_sec": (4, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_POST_DECISION_REASSURANCE_001": {
        "next_state": "post_decision_reassurance",
        "reaction_caption": "the customer keeps the selected product in focus and looks for final reassurance",
        "physical_change": "customer remains close to the selected option and seeks confirmation",
        "head_gaze": "gaze alternates between the selected product and salesperson area",
        "hands": "hands stay near the selected item, with a small confirming gesture",
        "movement": "slight forward lean, no withdrawal",
        "duration_window_sec": (3, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_DISENGAGED_001": {
        "next_state": "disengaged",
        "reaction_caption": "the customer turns away from the display, walks away alone, and stops interacting with the product",
        "physical_change": "customer clearly steps away from the display and turns body away from the product",
        "head_gaze": "gaze moves elsewhere in the store or toward the exit",
        "hands": "hands disengage from product entirely",
        "movement": "walks away from the product area alone, leaving the display behind",
        "duration_window_sec": (3, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_DEFENSIVE_WITHDRAWAL_001": {
        "next_state": "defensive_withdrawal",
        "reaction_caption": "the customer steps back, breaks eye contact, and retracts hands from the product",
        "physical_change": "customer steps back half a step, body turns slightly away, breaks eye contact",
        "head_gaze": "gaze drops or shifts away from salesperson area, chin lowers",
        "hands": "hands retract from the product, may briefly cross arms or move to bag or phone",
        "movement": "weight shifts to back foot, body angles away from intervention source",
        "duration_window_sec": (3, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_ENGAGED_DIALOGUE_001": {
        "next_state": "engaged_dialogue",
        "reaction_caption": "the customer turns toward the salesperson area, opens posture, and stays engaged with the product",
        "physical_change": "customer turns body toward salesperson area, makes brief eye contact, body posture opens up",
        "head_gaze": "head turns to engage, gaze alternates between salesperson area and product",
        "hands": "hands stay relaxed near or on the product, may gesture toward features",
        "movement": "weight shifts forward, leans slightly in",
        "duration_window_sec": (3, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
    "REACT_CONTINUED_HESITATION_001": {
        "next_state": "continued_hesitation",
        "reaction_caption": "the customer stays undecided, with no clear engagement or withdrawal",
        "physical_change": "customer remains in same posture, no clear engagement or withdrawal",
        "head_gaze": "gaze continues alternating between product and surroundings",
        "hands": "hands stay where they were, no clear gesture change",
        "movement": "minimal weight shift, no body re-orientation",
        "duration_window_sec": (4, 5),
        "frame_roles": ["reaction_onset", "reaction_peak", "reaction_settle"],
    },
}

NEXT_STATE_TO_TEMPLATE: dict[str, str] = {
    template["next_state"]: template_id
    for template_id, template in REACTION_TEMPLATES.items()
}


def template_for_next_state(next_state: str) -> tuple[str, ReactionTemplate]:
    template_id = NEXT_STATE_TO_TEMPLATE[next_state]
    return template_id, REACTION_TEMPLATES[template_id]


def validate_registry_complete() -> None:
    missing = sorted(set(rules.LATENT_STATES) - set(NEXT_STATE_TO_TEMPLATE))
    if missing:
        raise ValueError(f"missing reaction template(s): {missing}")


validate_registry_complete()
