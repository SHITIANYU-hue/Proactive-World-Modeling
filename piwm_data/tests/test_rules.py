from piwm_data import rules


def test_each_cue_prior_maps_to_expected_state():
    for cue, expected_state in rules.CUE_TO_STATE_PRIOR.items():
        assert rules.derive_latent_state([cue]) == expected_state


def test_multi_cue_priority_ready_to_decide_is_strongest():
    assert rules.derive_latent_state(["no_eye_contact_avoidant", "approaching_counter"]) == "ready_to_decide"
    assert rules.derive_latent_state(["brief_glance_walking_past", "looking_around_for_help"]) == "ready_to_decide"


def test_multi_cue_priority_active_evaluation_before_long_dwell():
    assert rules.derive_latent_state(["long_dwell_with_price_check", "comparing_two_products"]) == "active_evaluation"


def test_multi_cue_priority_long_dwell_before_disengaged():
    assert rules.derive_latent_state(["no_eye_contact_avoidant", "long_dwell_with_price_check"]) == "high_hesitation"


def test_low_intensity_cues_map_to_early_browsing():
    assert rules.derive_latent_state(["brief_glance_walking_past"]) == "early_browsing"


def test_derive_intent_hits_persona_state_mapping():
    assert rules.derive_intent("price_sensitive_cautious", "high_hesitation") == "compare_value_for_money"


def test_derive_intent_uses_state_fallback():
    assert rules.derive_intent("browser_low_intent", "active_evaluation") == "explore_options"


def test_pick_best_action_uses_highest_reward():
    assert (
        rules.pick_best_action(
            "high_hesitation",
            ["A1_silent_observe", "A2_offer_value_comparison", "A4_open_with_question"],
        )
        == "A2_offer_value_comparison"
    )


def test_pick_best_action_tie_breaks_by_lower_risk(monkeypatch):
    monkeypatch.setitem(
        rules.TRANSITION_TABLE,
        ("early_browsing", "A1_silent_observe"),
        {"next_state": "early_browsing", "reward": 0.5, "risk": "medium", "benefit": "high"},
    )
    monkeypatch.setitem(
        rules.TRANSITION_TABLE,
        ("early_browsing", "A6_acknowledge_and_wait"),
        {"next_state": "early_browsing", "reward": 0.5, "risk": "low", "benefit": "low"},
    )
    assert (
        rules.pick_best_action("early_browsing", ["A1_silent_observe", "A6_acknowledge_and_wait"])
        == "A6_acknowledge_and_wait"
    )


def test_pick_best_action_tie_breaks_by_higher_benefit(monkeypatch):
    monkeypatch.setitem(
        rules.TRANSITION_TABLE,
        ("early_browsing", "A1_silent_observe"),
        {"next_state": "early_browsing", "reward": 0.5, "risk": "low", "benefit": "medium"},
    )
    monkeypatch.setitem(
        rules.TRANSITION_TABLE,
        ("early_browsing", "A6_acknowledge_and_wait"),
        {"next_state": "early_browsing", "reward": 0.5, "risk": "low", "benefit": "high"},
    )
    assert (
        rules.pick_best_action("early_browsing", ["A1_silent_observe", "A6_acknowledge_and_wait"])
        == "A6_acknowledge_and_wait"
    )


def test_pick_best_action_tie_breaks_by_global_action_order():
    assert (
        rules.pick_best_action("early_browsing", ["A6_acknowledge_and_wait", "A1_silent_observe"])
        == "A1_silent_observe"
    )

