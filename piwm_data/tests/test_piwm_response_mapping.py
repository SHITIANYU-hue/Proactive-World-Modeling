from piwm_data import rules
from piwm_data.migration.piwm_response_mapping import (
    PIWM_RESPONSE_ID_TO_V2_ACTION,
    piwm_response_to_action_key,
    piwm_response_to_action_spec,
)
from piwm_data.schemas import ActionOutcome, FrameRef, MainSchemaRecord, Persona, Provenance


def test_piwm_response_mapping_is_complete_and_unique():
    assert set(PIWM_RESPONSE_ID_TO_V2_ACTION) == {
        "greet_open",
        "greet_close",
        "elicit_need_focus_open",
        "inform_comparison_brief",
        "inform_demo_brief",
        "inform_attributes_brief",
        "inform_price_brief",
        "recommend_soft",
        "recommend_firm",
        "reassure_time_wait",
        "reassure_decision",
        "hold_silent",
        "hold_ambient",
    }

    keys = []
    for response_id in PIWM_RESPONSE_ID_TO_V2_ACTION:
        spec = piwm_response_to_action_spec(response_id)
        rules.validate_dialogue_act(spec["act"], spec["params"])
        keys.append(piwm_response_to_action_key(response_id))

    assert len(keys) == len(set(keys))


def test_main_schema_accepts_v2_native_action_keys_for_target_frontcam():
    best_spec = piwm_response_to_action_spec("elicit_need_focus_open")
    hold_spec = piwm_response_to_action_spec("hold_silent")
    best_key = piwm_response_to_action_key("elicit_need_focus_open")
    hold_key = piwm_response_to_action_key("hold_silent")
    outcome = ActionOutcome(
        next_state="active_evaluation",
        next_aida_stage="interest",
        next_bdi={"belief": "the terminal can help", "desire": "clarify the choice", "intention": "answer the prompt"},
        reward=0.21,
        reward_components={"delta_stage": 0.25, "delta_mental": 0.3, "action_cost": 0.2, "alpha": 0.4, "beta": 0.5, "gamma": 0.2, "final_reward": 0.21},
        risk="medium",
        benefit="high",
        dialogue_act=best_spec["act"],
        act_params=best_spec["params"],
    )
    hold_outcome = ActionOutcome(
        next_state="active_evaluation",
        next_aida_stage="interest",
        next_bdi={"belief": "space remains available", "desire": "continue browsing", "intention": "keep observing"},
        reward=0.0,
        reward_components={"delta_stage": 0.0, "delta_mental": 0.0, "action_cost": 0.0, "alpha": 0.4, "beta": 0.5, "gamma": 0.2, "final_reward": 0.0},
        risk="low",
        benefit="low",
        dialogue_act=hold_spec["act"],
        act_params=hold_spec["params"],
    )

    record = MainSchemaRecord(
        state_id="target_piwm_test",
        images=[FrameRef(index=0, relative_path="data/official/piwm_target_v1/frames/piwm_test/000.jpg")],
        product_category="smart_vending_retail",
        split="train",
        visual_state={
            "summary": "顾客在设备前停留并看向屏幕。",
            "engagement_pattern": "顾客保持停留。",
            "gaze_and_attention": "视线看向屏幕。",
            "body_and_hands": "身体正面朝向设备。",
        },
        observable_cues=["long_dwell_with_price_check"],
        viewpoint="target_frontcam",
        persona=Persona(type="browser_low_intent", description="casual target shopper"),
        aida_stage="interest",
        latent_state="active_evaluation",
        intent="explore_options",
        bdi={"belief": "the product may fit", "desire": "compare options", "intention": "keep checking"},
        proactive_score=3,
        candidate_actions=[hold_key, best_key],
        best_action=best_key,
        candidate_action_specs=[hold_spec, best_spec],
        best_action_spec=best_spec,
        best_action_realization={
            "utterance": "您今天想先看价格、功能，还是适合什么场景？",
            "physical_action": "智能售货柜显示选项气泡。",
            "timing": "顾客停留看屏幕时触发。",
        },
        dialogue_act=best_spec["act"],
        act_params=best_spec["params"],
        next_state_by_action={hold_key: hold_outcome, best_key: outcome},
        next_state_by_action_v2={hold_key: hold_outcome, best_key: outcome},
        reward_by_action={hold_key: 0.0, best_key: 0.21},
        provenance=[Provenance(field_name="candidate_action_specs", source="annotation_override", rule_version=rules.RULE_VERSION)],
    )

    assert record.viewpoint == "target_frontcam"
    assert record.best_action == best_key
    assert record.best_action_spec.act == "Elicit"
