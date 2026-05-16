"""Mapping from lightweight piwm response ids to PIWM v2.2 action specs.

The lightweight guochenmeinian/piwm repository uses ``response_id`` as its
unique action key. The main PIWM repository uses canonical ``(act, params)``
objects plus a stable ``action_spec_key``. This file is intentionally explicit:
no fuzzy inference is allowed in the target-domain import path.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from piwm_data import rules


PIWM_RESPONSE_ID_TO_V2_ACTION: dict[str, dict[str, Any]] = {
    "greet_open": {"act": "Greet", "params": {"phase": "open"}},
    "greet_close": {"act": "Greet", "params": {"phase": "close"}},
    "elicit_need_focus_open": {"act": "Elicit", "params": {"openness": "open", "slot": "need_focus"}},
    "inform_comparison_brief": {"act": "Inform", "params": {"content_type": "comparison", "depth": "brief"}},
    "inform_demo_brief": {"act": "Inform", "params": {"content_type": "demo", "depth": "brief"}},
    "inform_attributes_brief": {"act": "Inform", "params": {"content_type": "attributes", "depth": "brief"}},
    "inform_price_brief": {"act": "Inform", "params": {"content_type": "price", "depth": "brief"}},
    "recommend_soft": {"act": "Recommend", "params": {"target": "item", "pressure": "soft"}},
    "recommend_firm": {"act": "Recommend", "params": {"target": "item", "pressure": "firm"}},
    "reassure_time_wait": {
        "act": "Reassure",
        "params": {
            "focus": "time",
            "supporting_acts": [{"type": "Hold", "params": {"mode": "ambient"}}],
        },
    },
    "reassure_decision": {"act": "Reassure", "params": {"focus": "decision"}},
    "hold_silent": {"act": "Hold", "params": {"mode": "silent"}},
    "hold_ambient": {"act": "Hold", "params": {"mode": "ambient"}},
}


def piwm_response_to_action_spec(response_id: str) -> dict[str, Any]:
    """Return the canonical v2.2 action spec for a lightweight piwm response."""

    if response_id not in PIWM_RESPONSE_ID_TO_V2_ACTION:
        raise ValueError(f"unknown piwm response_id: {response_id}")
    spec = deepcopy(PIWM_RESPONSE_ID_TO_V2_ACTION[response_id])
    spec["params"] = rules.merge_supporting_acts(spec.get("params", {}))
    rules.validate_dialogue_act(spec["act"], spec["params"])
    return spec


def piwm_response_to_action_key(response_id: str) -> str:
    """Return the main-repo stable v2.2 action key for a response id."""

    spec = piwm_response_to_action_spec(response_id)
    return rules.action_spec_key(spec["act"], spec["params"])
