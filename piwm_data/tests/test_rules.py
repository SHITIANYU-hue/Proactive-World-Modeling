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


def test_derive_bdi_returns_explicit_three_part_summary():
    bdi = rules.derive_bdi(
        "price_sensitive_cautious",
        "high_hesitation",
        "compare_value_for_money",
        ["long_dwell_with_price_check"],
    )
    assert set(bdi) == {"belief", "desire", "intention"}
    assert all(bdi.values())
    assert "long_dwell_with_price_check" not in bdi["belief"]
    assert "Observable cue" not in bdi["belief"]


def test_derive_action_outcome_adds_world_model_fields():
    outcome = rules.derive_action_outcome(
        "high_hesitation",
        "interest",
        "price_sensitive_cautious",
        "A2_offer_value_comparison",
    )
    assert outcome["next_state"] == "engaged_dialogue"
    assert outcome["next_aida_stage"] == "desire"
    assert outcome["next_bdi"]["belief"]
    assert outcome["reward_components"]["final_reward"] == outcome["reward"]
    assert outcome["rationale"]


def test_reward_components_preserve_scalar_reward_formula():
    components = rules.derive_reward_components("interest", "desire", "A2_offer_value_comparison", 0.8)
    reconstructed = (
        components["alpha"] * components["delta_stage"]
        + components["beta"] * components["delta_mental"]
        - components["gamma"] * components["action_cost"]
    )
    assert abs(reconstructed - 0.8) < 1e-9


def test_pick_best_action_uses_highest_reward():
    assert (
        rules.pick_best_action(
            "high_hesitation",
            ["A1_silent_observe", "A2_offer_value_comparison", "A4_open_with_question", "A3_strong_recommend"],
        )
        == "A2_offer_value_comparison"
    )


def test_candidate_sets_include_negative_intervention_contrast():
    assert "A3_strong_recommend" in rules.derive_candidate_actions("high_hesitation", "interest")
    assert "A3_strong_recommend" in rules.derive_candidate_actions("active_evaluation", "interest")
    assert "A3_strong_recommend" in rules.derive_candidate_actions("early_browsing", "attention")
    assert "A1_silent_observe" in rules.derive_candidate_actions("ready_to_decide", "action")


def test_negative_intervention_transitions_cross_zero():
    assert rules.derive_transition("high_hesitation", "A3_strong_recommend")["reward"] < 0
    assert rules.derive_transition("active_evaluation", "A3_strong_recommend")["reward"] < 0
    assert rules.derive_transition("early_browsing", "A3_strong_recommend")["reward"] < 0
    assert rules.derive_transition("ready_to_decide", "A1_silent_observe")["reward"] < 0


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
