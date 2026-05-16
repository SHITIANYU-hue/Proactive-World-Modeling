"""Pure bootstrap rules for the PIWM data pipeline.

All enum strings and numeric rule values in this file are copied from
data_pipeline_spec.md v1. Do not change them without changing the spec.
"""

from __future__ import annotations

import json
import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

from .migration.legacy_action_mapping import (
    LEGACY_ACTION_TO_ACT_PARAMS,
    act_params_to_legacy_for_comparison,
    legacy_to_v2,
)

RULE_VERSION = "v1.0"
ACTION_SCHEMA_VERSION = "dialogue_act_human_salesperson_v2.2"

PRODUCT_CATEGORIES = [
    "luxury_watch",
    "electronics_phone",
    "electronics_laptop",
    "cosmetics_skincare",
    "apparel_premium",
    "home_appliance",
    "jewelry",
    "footwear",
    "smart_vending_retail",
]

PERSONA_TYPES = [
    "price_sensitive_cautious",
    "first_time_high_consideration",
    "experienced_brand_loyal",
    "browser_low_intent",
    "gift_buyer_uncertain",
    "price_insensitive_decisive",
]

PERSONA_TO_INTENT_TIER: dict[str, str] = {
    "price_sensitive_cautious": "exploring",
    "first_time_high_consideration": "exploring",
    "experienced_brand_loyal": "ready_to_buy",
    "browser_low_intent": "low_intent_browsing",
    "gift_buyer_uncertain": "exploring",
    "price_insensitive_decisive": "ready_to_buy",
}

HIGH_PUSH_SENSITIVITY_PERSONAS = {
    "price_sensitive_cautious",
    "first_time_high_consideration",
    "gift_buyer_uncertain",
    "browser_low_intent",
}

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

DIALOGUE_ACTS = [
    "Greet",
    "Elicit",
    "Inform",
    "Recommend",
    "Reassure",
    "Hold",
]

DIALOGUE_ACT_DIMENSION: dict[str, str] = {
    "Greet": "Social Obligations",
    "Elicit": "Task",
    "Inform": "Task",
    "Recommend": "Task",
    "Reassure": "Allo-Feedback",
    "Hold": "Turn Management",
}

DIALOGUE_ACT_PARAM_VALUES: dict[str, dict[str, list[str]]] = {
    "Greet": {"phase": ["open", "close"]},
    "Elicit": {"openness": ["open", "closed"], "slot": ["need_focus", "budget", "usage", "companion_opinion"]},
    "Inform": {"content_type": ["comparison", "demo", "attributes", "price"], "depth": ["brief", "detailed"]},
    "Recommend": {"target": ["item", "action"], "pressure": ["soft", "firm"]},
    "Reassure": {"focus": ["time", "decision", "alternatives"]},
    "Hold": {"mode": ["silent", "ambient"]},
}

SUPPORTING_ACTS_PARAM = "supporting_acts"

TASK_DIALOGUE_ACTS = {"Elicit", "Inform", "Recommend"}

# Compatibility map from the pre-v2 salesperson/action labels to the v2
# dialogue-act layer.  Existing datasets keep their A* labels; new code can
# read the v2 act/params without re-labeling old records.
LEGACY_ACTION_TO_DIALOGUE_ACT: dict[str, dict[str, Any]] = deepcopy(LEGACY_ACTION_TO_ACT_PARAMS)

T_STATE_TO_DIALOGUE_ACT: dict[str, dict[str, Any]] = {
    "T1_SILENT_OBSERVE": LEGACY_ACTION_TO_DIALOGUE_ACT["A1_silent_observe"],
    "T2_VALUE_COMPARE": LEGACY_ACTION_TO_DIALOGUE_ACT["A2_offer_value_comparison"],
    "T3_STRONG_RECOMMEND": LEGACY_ACTION_TO_DIALOGUE_ACT["A3_strong_recommend"],
    "T4_OPEN_QUESTION": LEGACY_ACTION_TO_DIALOGUE_ACT["A4_open_with_question"],
    "T5_DEMO": LEGACY_ACTION_TO_DIALOGUE_ACT["A5_provide_demonstration"],
    "T6_ACK_WAIT": LEGACY_ACTION_TO_DIALOGUE_ACT["A6_acknowledge_and_wait"],
    "T7_DISENGAGE": LEGACY_ACTION_TO_DIALOGUE_ACT["A7_disengage"],
    "T_TRANSACT": {
        "act": "Greet",
        "params": {"phase": "close"},
        "co_acts": [],
    },
}

SHOOTING_RESPONSE_TO_DIALOGUE_ACT: dict[str, dict[str, Any]] = {
    "招呼问候": {"act": "Greet", "params": {"phase": "close"}, "co_acts": []},
    "提问探询": LEGACY_ACTION_TO_DIALOGUE_ACT["A4_open_with_question"],
    "提供信息-比较两件": LEGACY_ACTION_TO_DIALOGUE_ACT["A2_offer_value_comparison"],
    "提供信息-演示一件": LEGACY_ACTION_TO_DIALOGUE_ACT["A5_provide_demonstration"],
    "提供信息-罗列参数价格": {"act": "Inform", "params": {"content_type": "attributes", "depth": "brief"}, "co_acts": []},
    "建议推荐-力度温和": {"act": "Recommend", "params": {"target": "item", "pressure": "soft"}, "co_acts": []},
    "建议推荐-力度强势": LEGACY_ACTION_TO_DIALOGUE_ACT["A3_strong_recommend"],
    "安抚降压": LEGACY_ACTION_TO_DIALOGUE_ACT["A6_acknowledge_and_wait"],
    "暂不打扰-完全静默": LEGACY_ACTION_TO_DIALOGUE_ACT["A1_silent_observe"],
    "暂不打扰-背景退出": LEGACY_ACTION_TO_DIALOGUE_ACT["A7_disengage"],
}

S05_AB_DIALOGUE_ACTS: dict[str, dict[str, Any]] = {
    "G001_S05_A": {
        "shooting_state": "S05_BROWSE_UNC",
        "version": "A",
        "response_type_zh": "提供信息-比较两件",
        "legacy_action": "A2_offer_value_comparison",
        "t_state": "T2_VALUE_COMPARE",
        **LEGACY_ACTION_TO_DIALOGUE_ACT["A2_offer_value_comparison"],
    },
    "G001_S05_B": {
        "shooting_state": "S05_BROWSE_UNC",
        "version": "B",
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        **LEGACY_ACTION_TO_DIALOGUE_ACT["A3_strong_recommend"],
    },
}

SHOOTING_CUSTOMER_STATES = [
    "S01_PASSBY",
    "S02_APPROACH",
    "S03_HOVER",
    "S04_BROWSE_POS",
    "S05_BROWSE_UNC",
    "S06_BROWSE_NEG",
    "S07_OPERATE",
    "S08_CLOSE_LOOK",
    "S09_RETRY_FAIL",
    "S10_HELP_SEEK",
    "S11_WALKAWAY",
    "S12_EXIT_POST",
]

SHOOTING_STATE_DISPLAY_ZH: dict[str, str] = {
    "S01_PASSBY": "路过无关注",
    "S02_APPROACH": "有兴趣未停稳",
    "S03_HOVER": "停下观望",
    "S04_BROWSE_POS": "积极挑选",
    "S05_BROWSE_UNC": "犹豫比较",
    "S06_BROWSE_NEG": "失望降温",
    "S07_OPERATE": "主动操作",
    "S08_CLOSE_LOOK": "凑近细看",
    "S09_RETRY_FAIL": "反复失败",
    "S10_HELP_SEEK": "寻求帮助",
    "S11_WALKAWAY": "放弃倾向",
    "S12_EXIT_POST": "购买后离开",
}

SHOOTING_CORE_STATES = {"S03_HOVER", "S05_BROWSE_UNC", "S07_OPERATE", "S11_WALKAWAY"}

SHOOTING_STATE_RESPONSE_PRIOR: dict[tuple[str, str], dict[str, Any]] = {
    ("S01_PASSBY", "A"): {
        "response_type_zh": "暂不打扰-完全静默",
        "legacy_action": "A1_silent_observe",
        "t_state": "T1_SILENT_OBSERVE",
        "expected_reaction": "自然路过，不被打扰",
    },
    ("S01_PASSBY", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "防御加速离开",
    },
    ("S02_APPROACH", "A"): {
        "response_type_zh": "安抚降压",
        "legacy_action": "A6_acknowledge_and_wait",
        "t_state": "T6_ACK_WAIT",
        "expected_reaction": "愿意停下看",
    },
    ("S02_APPROACH", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "立刻后撤",
    },
    ("S03_HOVER", "A"): {
        "response_type_zh": "提问探询",
        "legacy_action": "A4_open_with_question",
        "t_state": "T4_OPEN_QUESTION",
        "expected_reaction": "视线落屏，进入互动",
    },
    ("S03_HOVER", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "视线回避，结束停留",
    },
    ("S04_BROWSE_POS", "A"): {
        "response_type_zh": "提供信息-演示一件",
        "legacy_action": "A5_provide_demonstration",
        "t_state": "T5_DEMO",
        "expected_reaction": "持续看演示，热度延续",
    },
    ("S04_BROWSE_POS", "B"): {
        "response_type_zh": "暂不打扰-背景退出",
        "legacy_action": "A7_disengage",
        "t_state": "T7_DISENGAGE",
        "expected_reaction": "失去支持，热度下降",
    },
    ("S05_BROWSE_UNC", "A"): {
        "response_type_zh": "提供信息-比较两件",
        "legacy_action": "A2_offer_value_comparison",
        "t_state": "T2_VALUE_COMPARE",
        "expected_reaction": "进入澄清，犹豫缓解",
    },
    ("S05_BROWSE_UNC", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "压力上升，更犹豫",
    },
    ("S06_BROWSE_NEG", "A"): {
        "response_type_zh": "提供信息-比较两件",
        "legacy_action": "A2_offer_value_comparison",
        "t_state": "T2_VALUE_COMPARE",
        "expected_reaction": "重回评估，负面减弱",
    },
    ("S06_BROWSE_NEG", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "抵触增强，准备走",
    },
    ("S07_OPERATE", "A"): {
        "response_type_zh": "提供信息-演示一件",
        "legacy_action": "A5_provide_demonstration",
        "t_state": "T5_DEMO",
        "expected_reaction": "继续验证，信心提升",
    },
    ("S07_OPERATE", "B"): {
        "response_type_zh": "暂不打扰-背景退出",
        "legacy_action": "A7_disengage",
        "t_state": "T7_DISENGAGE",
        "expected_reaction": "操作中断，意向下降",
    },
    ("S08_CLOSE_LOOK", "A"): {
        "response_type_zh": "提供信息-比较两件",
        "legacy_action": "A2_offer_value_comparison",
        "t_state": "T2_VALUE_COMPARE",
        "expected_reaction": "看完更接近决策",
    },
    ("S08_CLOSE_LOOK", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "向后撤离，防御",
    },
    ("S09_RETRY_FAIL", "A"): {
        "response_type_zh": "提问探询",
        "legacy_action": "A4_open_with_question",
        "t_state": "T4_OPEN_QUESTION",
        "expected_reaction": "情绪稳定，重新评估",
    },
    ("S09_RETRY_FAIL", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "挫败放大，转向放弃",
    },
    ("S10_HELP_SEEK", "A"): {
        "response_type_zh": "提供信息-演示一件",
        "legacy_action": "A5_provide_demonstration",
        "t_state": "T5_DEMO",
        "expected_reaction": "获得帮助，回到评估",
    },
    ("S10_HELP_SEEK", "B"): {
        "response_type_zh": "暂不打扰-背景退出",
        "legacy_action": "A7_disengage",
        "t_state": "T7_DISENGAGE",
        "expected_reaction": "求助失败，放弃",
    },
    ("S11_WALKAWAY", "A"): {
        "response_type_zh": "安抚降压",
        "legacy_action": "A6_acknowledge_and_wait",
        "t_state": "T6_ACK_WAIT",
        "expected_reaction": "退出速度放缓，短暂停留",
    },
    ("S11_WALKAWAY", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "明显加速离开",
    },
    ("S12_EXIT_POST", "A"): {
        "response_type_zh": "招呼问候",
        "legacy_action": None,
        "t_state": "T_TRANSACT",
        "expected_reaction": "自然离开，体验闭合",
    },
    ("S12_EXIT_POST", "B"): {
        "response_type_zh": "建议推荐-力度强势",
        "legacy_action": "A3_strong_recommend",
        "t_state": "T3_STRONG_RECOMMEND",
        "expected_reaction": "购后仍被打扰，体验差",
    },
}

ACTION_VISIBLE_BEHAVIOR: dict[str, str] = {
    "A1_silent_observe": "no salesperson appears, no staff enters, and no one speaks; the shopper remains alone with the product and decides what to do without intervention",
    "A2_offer_value_comparison": "a salesperson appears at the side and gestures toward two product options as if comparing features",
    "A3_strong_recommend": "a salesperson approaches firmly and gestures toward one specific product with an assertive recommending pose",
    "A4_open_with_question": "a salesperson appears at a respectful distance with an open posture as if asking a brief question",
    "A5_provide_demonstration": "a salesperson appears and operates the product to demonstrate a feature",
    "A6_acknowledge_and_wait": "a salesperson briefly acknowledges the shopper with a small nod and steps back to a non-intrusive distance",
    "A7_disengage": "a salesperson visibly steps away from the shopper, returns to the background, and stops interacting so the shopper is clearly left alone",
    "A8_offer_companion_invite": "a salesperson invites a companion or assistant to join the conversation with an open hand gesture",
}

PRODUCT_CATEGORY_ZH: dict[str, str] = {
    "luxury_watch": "腕表",
    "electronics_phone": "手机",
    "electronics_laptop": "电脑",
    "cosmetics_skincare": "护肤品",
    "apparel_premium": "服装",
    "home_appliance": "家电",
    "jewelry": "珠宝",
    "footwear": "鞋类商品",
    "smart_vending_retail": "智能售货柜商品",
}

PRODUCT_ACTION_PROFILES: dict[str, dict[str, str]] = {
    "luxury_watch": {
        "scene": "腕表柜台",
        "decision_focus": "表盘大小、表带材质、上手比例和佩戴场合",
        "comparison_focus": "表盘尺寸、表带材质、品牌质感、保修和价格差异",
        "demo_focus": "表扣开合、表带贴合度和表盘细节",
        "open_question": "佩戴场合、表盘大小，还是表带材质",
        "value_frame": "材质、工艺、保修和适合佩戴的场合",
    },
    "electronics_phone": {
        "scene": "手机陈列区",
        "decision_focus": "屏幕手感、拍照、电池、存储和价格差异",
        "comparison_focus": "拍照、续航、存储容量、屏幕尺寸和以旧换新价格",
        "demo_focus": "拍照样张、屏幕滑动流畅度或手持重量",
        "open_question": "拍照、续航、存储，还是预算",
        "value_frame": "配置差异、使用年限、售后和实际到手价",
    },
    "electronics_laptop": {
        "scene": "电脑陈列区",
        "decision_focus": "屏幕尺寸、键盘手感、性能配置、重量和价格差异",
        "comparison_focus": "处理器/内存配置、屏幕尺寸、重量、续航和售后",
        "demo_focus": "屏幕显示、键盘触感、机身重量或接口布局",
        "open_question": "办公学习、剪辑设计、便携性，还是预算",
        "value_frame": "配置、便携性、保修和未来几年使用成本",
    },
    "cosmetics_skincare": {
        "scene": "护肤品陈列区",
        "decision_focus": "肤质适配、成分功效、质地和价格容量",
        "comparison_focus": "肤质适配、主打成分、质地、容量和单次使用成本",
        "demo_focus": "质地、吸收速度、气味和试用肤感",
        "open_question": "肤质、功效诉求、质地，还是预算",
        "value_frame": "成分、容量、使用周期和肤质匹配度",
    },
    "apparel_premium": {
        "scene": "服装陈列区",
        "decision_focus": "版型、面料、颜色、尺码和搭配场景",
        "comparison_focus": "版型、面料、颜色、尺码、护理方式和价格差异",
        "demo_focus": "面料手感、垂坠感、版型线条或搭配效果",
        "open_question": "版型、面料、颜色搭配，还是尺码",
        "value_frame": "面料、剪裁、适用场合和搭配频率",
    },
    "home_appliance": {
        "scene": "家电展示区",
        "decision_focus": "尺寸、核心功能、能耗、噪音和售后安装",
        "comparison_focus": "尺寸、功率/能耗、核心功能、安装条件和售后",
        "demo_focus": "关键功能、操作步骤、噪音或空间占用",
        "open_question": "使用空间、核心功能、能耗，还是安装售后",
        "value_frame": "功能覆盖、能耗、安装条件和长期使用成本",
    },
    "jewelry": {
        "scene": "珠宝柜台",
        "decision_focus": "佩戴效果、材质、光泽、尺寸和送礼场景",
        "comparison_focus": "材质、大小、光泽、佩戴效果、证书和价格差异",
        "demo_focus": "上身比例、光泽变化、扣合方式或证书信息",
        "open_question": "自戴/送礼、材质、大小，还是预算",
        "value_frame": "材质、证书、佩戴场景和送礼适配度",
    },
    "footwear": {
        "scene": "鞋类商品区",
        "decision_focus": "尺码、脚感、支撑、鞋型和价格差异",
        "comparison_focus": "尺码脚感、鞋底支撑、材质、适用场景和价格差异",
        "demo_focus": "鞋底弯折、脚跟包裹、鞋面软硬或尺码贴合",
        "open_question": "尺码脚感、通勤场景、支撑性，还是价格",
        "value_frame": "脚感、材质、耐穿度和使用场景",
    },
    "smart_vending_retail": {
        "scene": "智能售货柜前置摄像头视角",
        "decision_focus": "屏幕信息、商品价格、功能差异、购买步骤和取货确认",
        "comparison_focus": "价格、功能、适合场景、库存状态和购买路径",
        "demo_focus": "屏幕交互、商品亮点和取货流程",
        "open_question": "价格、功能、场景，还是购买步骤",
        "value_frame": "价格、功能、适用场景、库存和取货便利性",
    },
}

ACTION_DISPLAY_NAME_ZH: dict[str, str] = {
    "A1_silent_observe": "继续观察",
    "A2_offer_value_comparison": "提供价值对比",
    "A3_strong_recommend": "强推荐",
    "A4_open_with_question": "开放式询问",
    "A5_provide_demonstration": "产品演示",
    "A6_acknowledge_and_wait": "礼貌确认后等待",
    "A7_disengage": "主动退开",
    "A8_offer_companion_invite": "邀请同伴参与",
}

ACTION_AVOID_TEMPLATES: dict[str, str] = {
    "A1_silent_observe": "不要突然靠近、不要报价、不要直接推荐具体款。",
    "A2_offer_value_comparison": "不要说“这款最适合您”或直接推动下单。",
    "A3_strong_recommend": "不要连续强调“就买这款”，不要压缩顾客比较时间。",
    "A4_open_with_question": "不要一上来讲完整卖点，不要连续提问。",
    "A5_provide_demonstration": "不要把演示变成长篇介绍。",
    "A6_acknowledge_and_wait": "不要继续追问，不要跟随顾客移动。",
    "A7_disengage": "不要补充卖点，不要试图挽留。",
    "A8_offer_companion_invite": "不要让同伴感觉被强行拉入销售。",
}

ACTION_FALLBACK_TEMPLATES: dict[str, str] = {
    "A1_silent_observe": "如果顾客看向导购或主动询问，再进入开放式询问。",
    "A2_offer_value_comparison": "如果顾客后退或视线回避，立刻收短话术，改为“我就在旁边，需要时叫我”。",
    "A3_strong_recommend": "一旦顾客表情或身体后撤，立即降级为开放问题或退出。",
    "A4_open_with_question": "如果顾客只简短回应，停止追问，给出等待空间。",
    "A5_provide_demonstration": "如果顾客兴趣下降，立刻停止演示并退回观察。",
    "A6_acknowledge_and_wait": "如果顾客主动看向导购，再进入开放式询问。",
    "A7_disengage": "如果顾客重新停留并看向导购，再重新评估状态。",
    "A8_offer_companion_invite": "如果顾客或同伴回避，立刻停止邀请。",
}

CUE_VISUAL_STATE_TEMPLATES: dict[str, dict[str, Any]] = {
    "long_dwell_with_price_check": {
        "summary": "顾客持续停留在商品区域，并反复关注价格或价值信息，表现为有兴趣但仍在犹豫。",
        "product_relation": "顾客和商品保持稳定关系，不是快速经过；注意力围绕商品和价格区域。",
        "gaze": "视线持续落在商品、价签或附近陈列区域，呈现反复查看而非一次性扫视。",
        "hands": "手部没有快速离开商品区域，可能停在商品附近或保持比较姿态。",
        "body_orientation": "身体朝向商品区域，姿态相对停留，没有明显转身离开。",
        "movement": "移动速度较慢或基本停留，缺少快速离场动作。",
        "price_or_value_attention": "价格/价值信息是当前犹豫的主要线索。",
        "uncertainty_signals": ["停留时间较长", "反复查看价格或商品", "没有立即购买动作"],
    },
    "repeated_product_handling": {
        "summary": "顾客反复接触或摆弄商品，说明正在主动评估商品细节。",
        "product_relation": "顾客与商品有持续直接互动。",
        "gaze": "视线主要集中在商品细节和手部操作位置。",
        "hands": "手部反复拿起、放下、调整或触摸商品。",
        "body_orientation": "身体保持靠近商品，姿态显示评估意愿。",
        "movement": "移动较少，动作集中在商品操作上。",
        "price_or_value_attention": None,
        "uncertainty_signals": ["反复操作商品", "需要更多功能或体验确认"],
    },
    "comparing_two_products": {
        "summary": "顾客在两个商品之间来回比较，说明已经进入备选项评估。",
        "product_relation": "顾客注意力在两个具体选项之间切换。",
        "gaze": "视线在两个商品或对应价签之间来回移动。",
        "hands": "手部可能指向、拿起或靠近两个备选商品。",
        "body_orientation": "身体朝向两个备选商品之间的区域。",
        "movement": "移动围绕两个商品点位展开，不是离开式移动。",
        "price_or_value_attention": "可能同时比较价格、功能、外观或品牌价值。",
        "uncertainty_signals": ["备选项未收敛", "需要差异解释"],
    },
    "looking_around_for_help": {
        "summary": "顾客在商品区域停留并向周围寻找帮助，可能已经接近需要导购介入。",
        "product_relation": "顾客仍处在商品或柜台附近。",
        "gaze": "视线从商品转向周围空间或导购可能出现的位置。",
        "hands": "手部动作相对暂停，像是在等待回应。",
        "body_orientation": "身体仍面向商品或柜台，但头部/视线外转。",
        "movement": "移动不明显，更多是原地寻找帮助。",
        "price_or_value_attention": None,
        "uncertainty_signals": ["主动寻找外部帮助", "需要确认或提问"],
    },
    "checking_phone_likely_research": {
        "summary": "顾客在商品区域查看手机，可能正在做价格、评价或规格研究。",
        "product_relation": "顾客没有离开商品区域，手机行为与商品决策同时发生。",
        "gaze": "视线在手机和商品区域之间切换。",
        "hands": "至少一只手持手机或操作手机。",
        "body_orientation": "身体仍靠近商品，说明手机查询服务于当前商品判断。",
        "movement": "移动较少，处在查询和比较状态。",
        "price_or_value_attention": "可能在核对价格、评价、规格或替代选项。",
        "uncertainty_signals": ["需要外部信息验证", "可能对价格或评价有疑虑"],
    },
    "brief_glance_walking_past": {
        "summary": "顾客短暂扫视商品但持续移动，当前兴趣较弱。",
        "product_relation": "顾客与商品只有短暂视觉接触，没有形成稳定停留。",
        "gaze": "视线短暂扫过商品区域，很快离开。",
        "hands": "手部没有接触商品。",
        "body_orientation": "身体主要沿行走方向前进，没有明显转向商品。",
        "movement": "持续走过，缺少停留。",
        "price_or_value_attention": None,
        "uncertainty_signals": ["兴趣弱", "不适合高压介入"],
    },
    "trying_on_or_testing": {
        "summary": "顾客正在试用或测试商品，说明已经进入体验式评估。",
        "product_relation": "顾客和商品发生直接体验关系。",
        "gaze": "视线集中在试用效果、镜面反馈或商品反应上。",
        "hands": "手部正在操作、试穿或测试商品。",
        "body_orientation": "身体靠近商品并配合测试动作。",
        "movement": "动作与试用过程相关，停留意愿较强。",
        "price_or_value_attention": None,
        "uncertainty_signals": ["需要体验确认", "可能等待功能说明"],
    },
    "asking_companion_opinion": {
        "summary": "顾客向同伴寻求意见，说明决策受到社交反馈影响。",
        "product_relation": "顾客仍围绕商品做判断。",
        "gaze": "视线在商品和同伴之间切换。",
        "hands": "手部可能指向商品或把商品展示给同伴。",
        "body_orientation": "身体在商品与同伴之间形成互动姿态。",
        "movement": "移动不大，重点是沟通和确认。",
        "price_or_value_attention": None,
        "social_context": "同伴意见是当前决策的重要输入。",
        "uncertainty_signals": ["需要第三方确认", "自己尚未完全决定"],
    },
    "no_eye_contact_avoidant": {
        "summary": "顾客避免眼神接触或身体回避，说明当前不适合主动推进。",
        "product_relation": "顾客与商品或导购的互动关系较弱。",
        "gaze": "视线回避导购或交流区域。",
        "hands": "手部不主动展示需求，可能收回或保持封闭。",
        "body_orientation": "身体可能偏离商品或导购方向。",
        "movement": "可能有离开或减少互动的趋势。",
        "price_or_value_attention": None,
        "uncertainty_signals": ["回避互动", "进一步介入风险较高"],
    },
    "approaching_counter": {
        "summary": "顾客主动走向柜台或服务区域，说明接近明确咨询或决策时刻。",
        "product_relation": "顾客从浏览转向服务/结算区域。",
        "gaze": "视线朝向柜台、导购或服务点。",
        "hands": "手部可能携带商品、指向柜台或准备询问。",
        "body_orientation": "身体朝柜台方向前进。",
        "movement": "移动方向明确，正在接近服务点。",
        "price_or_value_attention": None,
        "uncertainty_signals": ["需要确认", "可能准备询问或购买"],
    },
}

AIDA_INTERVENTION_READINESS_ZH: dict[int, str] = {
    1: "不建议主动打扰；保持距离观察。",
    2: "只适合低存在感观察或礼貌点头，不进入推销。",
    3: "可以轻度介入，但应以开放问题或演示为主。",
    4: "建议主动但低压力介入，重点降低犹豫和决策成本。",
    5: "可以明确介入，帮助顾客完成确认或收口。",
}

AIDA_STAGES = ["attention", "interest", "desire", "action"]

SPLITS = ["train", "dev", "test", "ood_product", "ood_persona"]

VIEWPOINTS = [
    "salesperson_observable",
    "surveillance_oblique",
    "third_party_side",
    "first_person_pov",
    "target_frontcam",
]

DEFAULT_VIEWPOINT = "salesperson_observable"

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
        "A3_strong_recommend",
    ],
    ("high_hesitation", "desire"): [
        "A2_offer_value_comparison",
        "A4_open_with_question",
        "A6_acknowledge_and_wait",
        "A3_strong_recommend",
    ],
    ("active_evaluation", "interest"): [
        "A4_open_with_question",
        "A5_provide_demonstration",
        "A1_silent_observe",
        "A3_strong_recommend",
    ],
    ("active_evaluation", "desire"): [
        "A2_offer_value_comparison",
        "A5_provide_demonstration",
        "A4_open_with_question",
        "A3_strong_recommend",
    ],
    ("ready_to_decide", "desire"): [
        "A2_offer_value_comparison",
        "A4_open_with_question",
        "A3_strong_recommend",
    ],
    ("ready_to_decide", "action"): [
        "A3_strong_recommend",
        "A4_open_with_question",
        "A1_silent_observe",
    ],
    ("early_browsing", "attention"): [
        "A1_silent_observe",
        "A6_acknowledge_and_wait",
        "A3_strong_recommend",
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

_EXPERT_CONDITIONAL_RULES_JSONL = Path(__file__).parent / "expert_corpus" / "distilled" / "conditional_rules.jsonl"


def _load_transition_failure_meta() -> dict[tuple[str, str], dict[str, Any]]:
    """Load v2.2 failure-mode metadata without importing the compiler.

    The compiler imports this module for enum checks, so importing compiler
    objects here would create a cycle. A narrow JSONL read keeps runtime access
    to reviewed failure metadata while preserving the existing literal tables.
    """

    if not _EXPERT_CONDITIONAL_RULES_JSONL.exists():
        return {}
    meta: dict[tuple[str, str], dict[str, Any]] = {}
    for line in _EXPERT_CONDITIONAL_RULES_JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("rule_type") != "transition":
            continue
        key = row["key"]
        value = row["value"]
        item: dict[str, Any] = {}
        if "failure_mode" in value:
            item["failure_mode"] = deepcopy(value["failure_mode"])
        if "failure_mode_rationale" in value:
            item["failure_mode_rationale"] = value["failure_mode_rationale"]
        if item:
            meta[(key["state"], key["action"])] = item
    return meta


_TRANSITION_FAILURE_META = _load_transition_failure_meta()

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


def derive_intent_tier(persona_type: str) -> str:
    """Return the v2.2 persona-level intent tier prior."""

    return PERSONA_TO_INTENT_TIER.get(persona_type, "exploring")


def derive_proactive_score(state: str) -> int:
    return STATE_TO_PROACTIVE_SCORE[state]


def derive_intervention_readiness(state: str) -> str:
    return AIDA_INTERVENTION_READINESS_ZH[derive_proactive_score(state)]


def _product_profile(product_category: str | None) -> dict[str, str]:
    return PRODUCT_ACTION_PROFILES.get(
        product_category or "",
        {
            "scene": "商品陈列区",
            "decision_focus": "商品细节、价格、使用场景和个人偏好",
            "comparison_focus": "价格、材质、功能和使用场景",
            "demo_focus": "一个关键功能或可感知细节",
            "open_question": "功能、外观、价格，还是使用场景",
            "value_frame": "材质、功能、价格和适用场景",
        },
    )


def _join_sentences(*parts: str | None) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _cue_product_focus(primary: str, product: str, profile: dict[str, str]) -> str:
    if primary == "brief_glance_walking_past":
        return f"是否形成对{product}的稳定兴趣，而不是深度比较"
    if primary == "no_eye_contact_avoidant":
        return "回避互动和离开倾向，不能只按商品兴趣解释"
    if primary == "long_dwell_with_price_check":
        return f"{profile['value_frame']}是否足以支撑价格"
    if primary == "checking_phone_likely_research":
        return f"手机查询内容与{profile['value_frame']}之间的关系"
    if primary == "comparing_two_products":
        return f"两个候选项在{profile['comparison_focus']}上的差异"
    if primary == "repeated_product_handling":
        return f"{profile['decision_focus']}中需要手部确认的细节"
    if primary == "trying_on_or_testing":
        return profile["demo_focus"]
    if primary == "asking_companion_opinion":
        return f"同伴反馈如何影响{profile['decision_focus']}"
    if primary in {"looking_around_for_help", "approaching_counter"}:
        return f"顾客是否需要围绕{profile['decision_focus']}获得人工确认"
    return profile["decision_focus"]


def _engagement_product_detail(primary: str, profile: dict[str, str]) -> str:
    if primary == "brief_glance_walking_past":
        return "当前互动强度不足，不应把短暂停留误读成明确购买意图。"
    if primary == "no_eye_contact_avoidant":
        return "当前更明显的是回避互动，应优先降低打扰感，而不是推进商品介绍。"
    if primary in {"long_dwell_with_price_check", "checking_phone_likely_research"}:
        return f"停留本身更像在核对{profile['value_frame']}，而不是已经准备成交。"
    if primary in {"repeated_product_handling", "trying_on_or_testing"}:
        return f"互动已经进入体验层面，重点是{profile['demo_focus']}是否被确认。"
    if primary == "comparing_two_products":
        return f"比较行为集中在{profile['comparison_focus']}，说明选择尚未收敛。"
    if primary == "asking_companion_opinion":
        return "互动对象从商品扩展到同伴，决策节奏会受第三方反馈影响。"
    return ""


def _gaze_product_detail(primary: str, profile: dict[str, str]) -> str:
    if primary in {"long_dwell_with_price_check", "checking_phone_likely_research"}:
        return f"注意力可能在价格、评价和{profile['comparison_focus']}之间切换。"
    if primary == "comparing_two_products":
        return f"视线切换应被解释为对{profile['comparison_focus']}的对照。"
    if primary in {"trying_on_or_testing", "repeated_product_handling"}:
        return f"视线重点应落在{profile['demo_focus']}产生的可见反馈。"
    if primary == "asking_companion_opinion":
        return "视线不只看商品，也在等待同伴反应。"
    return ""


def _body_hand_product_detail(primary: str, profile: dict[str, str]) -> str:
    if primary in {"trying_on_or_testing", "repeated_product_handling"}:
        return f"手部动作应重点看是否在确认{profile['demo_focus']}。"
    if primary == "comparing_two_products":
        return "手部或身体在两个选项之间移动，说明还没有锁定单一商品。"
    if primary == "brief_glance_walking_past":
        return "没有接触动作时，不应提前进入推荐或演示。"
    if primary == "no_eye_contact_avoidant":
        return "身体和手部的封闭信号比商品兴趣更重要。"
    return ""


def derive_visual_state(
    cues: list[str],
    product_category: str | None = None,
    viewpoint: str | None = None,
) -> dict[str, Any]:
    primary = cues[0] if cues else "brief_glance_walking_past"
    template = deepcopy(CUE_VISUAL_STATE_TEMPLATES.get(primary, CUE_VISUAL_STATE_TEMPLATES["brief_glance_walking_past"]))
    product = PRODUCT_CATEGORY_ZH.get(product_category or "", "商品")
    product_profile = _product_profile(product_category)
    viewpoint_text = {
        "salesperson_observable": "导购可观察中近距离视角",
        "surveillance_oblique": "斜角监控/第三方视角",
        "third_party_side": "旁观者侧面视角",
        "first_person_pov": "导购第一人称视角",
        "target_frontcam": "设备前置摄像头单视角",
    }.get(viewpoint or "", "店内观察视角")
    summary = (
        f"{template['summary']} 当前场景是{product_profile['scene']}，"
        f"可见判断应围绕{_cue_product_focus(primary, product, product_profile)}。"
        f"视角为{viewpoint_text}。"
    )
    evidence = []
    for channel in ("product_relation", "gaze", "hands", "body_orientation", "movement", "price_or_value_attention", "social_context"):
        observation = template.get(channel)
        if observation:
            evidence.append(
                {
                    "channel": channel,
                    "observation": observation,
                    "supports": [primary],
                    "source": "cue_template",
                }
            )
    return {
        "summary": summary,
        "engagement_pattern": _join_sentences(
            template["product_relation"],
            template["movement"],
            _engagement_product_detail(primary, product_profile),
        ),
        "gaze_and_attention": _join_sentences(
            template["gaze"],
            _gaze_product_detail(primary, product_profile),
        ),
        "body_and_hands": _join_sentences(
            template["body_orientation"],
            template["hands"],
            _body_hand_product_detail(primary, product_profile),
        ),
    }


def _is_aggressive_close_action(action: str) -> bool:
    spec = legacy_action_to_act(action)
    return spec["act"] == "Recommend" and spec["params"].get("pressure") == "firm"


def derive_candidate_actions(
    state: str,
    aida: str,
    intent_tier: str | None = None,
) -> list[str]:
    candidates = list(STATE_AIDA_TO_CANDIDATES.get((state, aida), DEFAULT_CANDIDATES))
    if intent_tier == "low_intent_browsing":
        return [action for action in candidates if not _is_aggressive_close_action(action)]
    return candidates


def derive_candidate_action_specs(
    state: str,
    aida: str,
    intent_tier: str | None = None,
) -> list[dict[str, Any]]:
    """Return candidate actions as canonical v2 ``act`` / ``params`` objects."""

    specs: list[dict[str, Any]] = []
    for action in derive_candidate_actions(state, aida, intent_tier):
        spec = legacy_action_to_act(action)
        specs.append({"act": spec["act"], "params": spec["params"]})
    return specs


def derive_policy_candidate_specs(
    state: str,
    aida: str,
    intent_tier: str | None = None,
) -> list[dict[str, Any]]:
    """Return v2-native policy candidates, including soft/firm Recommend split.

    This is the canonical candidate path for v2.2 policy experiments. The legacy
    ``derive_candidate_actions`` path remains unchanged for old A-label exports.
    """

    specs = derive_candidate_action_specs(state, aida, intent_tier)
    if not any(spec["act"] == "Recommend" for spec in specs):
        return specs
    enriched: list[dict[str, Any]] = []
    for spec in specs:
        if spec["act"] == "Recommend":
            soft = {"act": "Recommend", "params": {"target": "item", "pressure": "soft"}}
            firm = {"act": "Recommend", "params": {"target": "item", "pressure": "firm"}}
            if state == "ready_to_decide" or (state == "active_evaluation" and aida == "desire"):
                _append_unique_action_spec(enriched, soft)
            _append_unique_action_spec(enriched, firm)
            continue
        _append_unique_action_spec(enriched, spec)
    return enriched


def _append_unique_action_spec(items: list[dict[str, Any]], spec: dict[str, Any]) -> None:
    key = _action_spec_key(spec["act"], spec.get("params", {}))
    if key not in {_action_spec_key(item["act"], item.get("params", {})) for item in items}:
        items.append({"act": spec["act"], "params": merge_supporting_acts(spec.get("params", {}))})


def _action_spec_key(act: str, params: dict[str, Any] | None = None) -> tuple[str, str]:
    return act, json.dumps(merge_supporting_acts(params or {}), ensure_ascii=False, sort_keys=True)


def action_spec_key(act: str, params: dict[str, Any] | None = None) -> str:
    """Return a stable JSON-safe key for a canonical v2 action spec."""

    normalized = merge_supporting_acts(params or {})
    params_json = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(params_json.encode("utf-8")).hexdigest()[:12]
    return f"{act}_{digest}"


def _normalize_supporting_act(supporting_act: dict[str, Any]) -> dict[str, Any]:
    """Return the v2.1 supporting-act shape.

    v2 used top-level ``co_acts`` entries shaped as ``{"act": ..., "params": ...}``.
    v2.1 keeps the same information under ``act_params.supporting_acts`` and uses
    ``type`` to avoid colliding with the parent ``dialogue_act`` field.
    """

    act = supporting_act.get("type") or supporting_act.get("act")
    if not act:
        raise ValueError("supporting act requires type or act")
    params = deepcopy(supporting_act.get("params") or {})
    return {"type": act, "params": params}


def normalize_supporting_acts(supporting_acts: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for supporting_act in supporting_acts or []:
        item = _normalize_supporting_act(supporting_act)
        key = (item["type"], repr(sorted(item["params"].items())))
        if key not in seen:
            normalized.append(item)
            seen.add(key)
    return normalized


def supporting_acts_from_params(params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not params:
        return []
    return normalize_supporting_acts(params.get(SUPPORTING_ACTS_PARAM) or [])


def legacy_co_acts_from_params(params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [
        {"act": supporting_act["type"], "params": deepcopy(supporting_act.get("params") or {})}
        for supporting_act in supporting_acts_from_params(params)
    ]


def merge_supporting_acts(
    params: dict[str, Any] | None = None,
    co_acts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    merged = deepcopy(params or {})
    supporting_acts = supporting_acts_from_params(merged)
    supporting_acts.extend(normalize_supporting_acts(co_acts))
    supporting_acts = normalize_supporting_acts(supporting_acts)
    if supporting_acts:
        merged[SUPPORTING_ACTS_PARAM] = supporting_acts
    else:
        merged.pop(SUPPORTING_ACTS_PARAM, None)
    return merged


def validate_dialogue_act(act: str, params: dict[str, Any] | None = None) -> None:
    if act not in DIALOGUE_ACTS:
        raise ValueError(f"invalid dialogue act: {act}")
    params = params or {}
    allowed = DIALOGUE_ACT_PARAM_VALUES.get(act, {})
    for key, value in params.items():
        if key == SUPPORTING_ACTS_PARAM:
            for supporting_act in normalize_supporting_acts(value):
                validate_dialogue_act(supporting_act["type"], supporting_act.get("params"))
            continue
        if key not in allowed:
            raise ValueError(f"invalid param for {act}: {key}")
        if str(value) not in allowed[key]:
            raise ValueError(f"invalid value for {act}.{key}: {value}")


def legacy_action_to_act(action: str) -> dict[str, Any]:
    result = legacy_to_v2(action)
    result["params"] = merge_supporting_acts(result.get("params"), result.get("co_acts"))
    result["co_acts"] = legacy_co_acts_from_params(result["params"])
    result["legacy_action"] = action
    validate_dialogue_act(result["act"], result["params"])
    return result


def t_state_to_act(t_state: str) -> dict[str, Any]:
    if t_state not in T_STATE_TO_DIALOGUE_ACT:
        raise ValueError(f"invalid T-state: {t_state}")
    result = deepcopy(T_STATE_TO_DIALOGUE_ACT[t_state])
    result["params"] = merge_supporting_acts(result.get("params"), result.get("co_acts"))
    result["co_acts"] = legacy_co_acts_from_params(result["params"])
    result["t_state"] = t_state
    validate_dialogue_act(result["act"], result["params"])
    return result


def response_type_to_act(response_type_zh: str) -> dict[str, Any]:
    if response_type_zh not in SHOOTING_RESPONSE_TO_DIALOGUE_ACT:
        raise ValueError(f"invalid shooting response type: {response_type_zh}")
    result = deepcopy(SHOOTING_RESPONSE_TO_DIALOGUE_ACT[response_type_zh])
    result["params"] = merge_supporting_acts(result.get("params"), result.get("co_acts"))
    result["co_acts"] = legacy_co_acts_from_params(result["params"])
    result["response_type_zh"] = response_type_zh
    validate_dialogue_act(result["act"], result["params"])
    return result


def shooting_state_response_prior(state: str, version: str) -> dict[str, Any]:
    key = (state, version)
    if key not in SHOOTING_STATE_RESPONSE_PRIOR:
        raise ValueError(f"invalid shooting state/version: {state}/{version}")
    prior = deepcopy(SHOOTING_STATE_RESPONSE_PRIOR[key])
    prior["shooting_state"] = state
    prior["state_name_zh"] = SHOOTING_STATE_DISPLAY_ZH[state]
    prior["version"] = version
    prior["requires_hero_view"] = state in SHOOTING_CORE_STATES
    if prior.get("t_state"):
        act_spec = t_state_to_act(prior["t_state"])
    else:
        act_spec = response_type_to_act(prior["response_type_zh"])
    prior["act"] = act_spec["act"]
    prior["params"] = act_spec["params"]
    prior["co_acts"] = legacy_co_acts_from_params(act_spec["params"])
    return prior


def act_to_legacy_action(act: str, params: dict[str, Any] | None = None) -> str:
    params = params or {}
    validate_dialogue_act(act, params)
    exact = act_params_to_legacy_for_comparison(act, params)
    if exact is not None:
        return exact
    if act == "Hold":
        return "A1_silent_observe" if params.get("mode") == "silent" else "A7_disengage"
    if act == "Elicit":
        return "A8_offer_companion_invite" if params.get("slot") == "companion_opinion" else "A4_open_with_question"
    if act == "Inform":
        return "A5_provide_demonstration" if params.get("content_type") == "demo" else "A2_offer_value_comparison"
    if act == "Recommend":
        return "A3_strong_recommend" if params.get("pressure") == "firm" else "A2_offer_value_comparison"
    if act == "Reassure":
        return "A6_acknowledge_and_wait"
    if act == "Greet":
        return "A7_disengage" if params.get("phase") == "close" else "A6_acknowledge_and_wait"
    raise ValueError(f"no legacy action for dialogue act: {act}")


def _screen_for_dialogue_act(act: str, params: dict[str, Any]) -> dict[str, Any]:
    if act == "Greet":
        return {"action": "show_message", "layout": "minimal", "text_role": "greeting"}
    if act == "Elicit":
        return {"action": "show_choice_bubbles", "choices": ["功能", "价格", "场景"], "cta": None}
    if act == "Inform" and params.get("content_type") == "demo":
        return {"action": "play_product_demo", "target": "{candidate_item}", "cta": None}
    if act == "Inform":
        return {"action": "show_comparison_or_details", "target": "{candidate_items}", "cta": None}
    if act == "Recommend":
        pressure = params.get("pressure")
        return {
            "action": "highlight_item" if pressure == "soft" else "show_fullscreen_recommendation",
            "target": "{candidate_item}",
            "cta": None if pressure == "soft" else "立即购买",
        }
    if act == "Reassure":
        return {"action": "show_hold_window", "text": "为您保留中，需要时随时叫我", "cta": None}
    if act == "Hold":
        return {"action": "idle_minimal" if params.get("mode") == "silent" else "return_to_attract_loop", "cta": None}
    return {"action": "idle_minimal", "cta": None}


def derive_terminal_realization(
    action: str,
    state: str,
    persona_type: str,
    product_category: str | None = None,
    cues: list[str] | None = None,
) -> dict[str, Any]:
    act_spec = legacy_action_to_act(action)
    act = act_spec["act"]
    params = act_spec["params"]
    product_profile = _product_profile(product_category)
    legacy_plan = derive_action_realization(action, state, persona_type, product_category, cues)
    cue = cues[0] if cues else None

    if act == "Hold" and params.get("mode") == "silent":
        surface_text = ""
        voice_style = "silent"
        light = "maintain_current_soft_breathing"
    elif action == "A2_offer_value_comparison":
        surface_text = f"我把这几款的差别帮您列清楚，您可以先看{product_profile['comparison_focus']}。"
        voice_style = "neutral"
        light = "soft_focus_on_comparison_cards"
    elif action == "A3_strong_recommend":
        surface_text = "这款最适合您，建议直接选这款。"
        voice_style = "firm"
        light = "warm_red_or_yellow_guidance"
    elif action == "A4_open_with_question":
        surface_text = f"您今天想先看{product_profile['open_question']}？"
        voice_style = "warm"
        light = "neutral_prompt_color"
    elif action == "A5_provide_demonstration":
        surface_text = f"给您看一下这款的细节：{product_profile['demo_focus']}。"
        voice_style = "neutral"
        light = "follow_demo_animation"
    elif action == "A6_acknowledge_and_wait":
        surface_text = "您慢慢看，不着急决定，需要时我再帮您说明。"
        voice_style = "calm"
        light = "dim_one_level_soft"
    elif action == "A7_disengage":
        surface_text = "不打扰您了，需要时随时叫我。"
        voice_style = "calm"
        light = "low_power_soft"
    elif action == "A8_offer_companion_invite":
        surface_text = "如果方便，也可以一起看一下，我把差别简单说清楚。"
        voice_style = "warm"
        light = "soft_secondary_focus"
    else:
        surface_text = legacy_plan["utterance"]
        voice_style = "neutral"
        light = "soft_breathing"

    cabinet_motion = None
    if action in {"A3_strong_recommend", "A5_provide_demonstration"}:
        cabinet_motion = "highlight_selected_slot"
    if cue == "approaching_counter" and action == "A7_disengage":
        cabinet_motion = "pickup_port_indicator_if_transaction_complete"

    return {
        "surface_text": surface_text,
        "screen": _screen_for_dialogue_act(act, params),
        "voice_style": voice_style,
        "light": light,
        "cabinet_motion": cabinet_motion,
        "duration_ms": 0 if voice_style == "silent" else 4000,
        "dialogue_act": act,
        "act_params": deepcopy(params),
        "co_acts": legacy_co_acts_from_params(params),
        "legacy_action": action,
        "legacy_realization": legacy_plan,
    }


def derive_terminal_realization_from_act(
    dialogue_act: str,
    act_params: dict[str, Any] | None = None,
    co_acts: list[dict[str, Any]] | None = None,
    legacy_action: str | None = None,
) -> dict[str, Any]:
    """Build a terminal realization directly from the v2 action schema."""

    params = merge_supporting_acts(act_params, co_acts)
    co_acts = legacy_co_acts_from_params(params)
    validate_dialogue_act(dialogue_act, params)

    if dialogue_act == "Hold" and params.get("mode") == "silent":
        surface_text = ""
        voice_style = "silent"
        light = "maintain_current_soft_breathing"
    elif dialogue_act == "Hold":
        surface_text = "您慢慢看，需要时我再帮您说明。"
        voice_style = "calm"
        light = "low_power_soft"
    elif dialogue_act == "Recommend":
        surface_text = "这款最适合您，建议直接选这款。" if params.get("pressure") == "firm" else "这款可以作为一个参考选项。"
        voice_style = "firm" if params.get("pressure") == "firm" else "neutral"
        light = "warm_red_or_yellow_guidance" if params.get("pressure") == "firm" else "soft_focus_on_recommendation"
    elif dialogue_act == "Elicit":
        surface_text = "您想先看价格、功能，还是使用场景？"
        voice_style = "warm"
        light = "neutral_prompt_color"
    elif dialogue_act == "Inform" and params.get("content_type") == "comparison":
        surface_text = "我把这几款的差别列在屏幕上，您可以先比较价格、功能和适合场景。"
        voice_style = "neutral"
        light = "soft_focus_on_comparison_cards"
    elif dialogue_act == "Inform" and params.get("content_type") == "demo":
        surface_text = "我给您演示一下这款的关键细节。"
        voice_style = "neutral"
        light = "follow_demo_animation"
    elif dialogue_act == "Reassure":
        surface_text = "您慢慢看，不着急决定，需要时我再帮您说明。"
        voice_style = "calm"
        light = "dim_one_level_soft"
    elif dialogue_act == "Greet" and params.get("phase") == "close":
        surface_text = "感谢惠顾，祝您使用愉快。"
        voice_style = "warm"
        light = "soft_checkout_complete"
    else:
        surface_text = "您好，需要时我可以帮您说明。"
        voice_style = "warm"
        light = "soft_breathing"

    return {
        "surface_text": surface_text,
        "screen": _screen_for_dialogue_act(dialogue_act, params),
        "voice_style": voice_style,
        "light": light,
        "cabinet_motion": "highlight_selected_slot" if legacy_action in {"A3_strong_recommend", "A5_provide_demonstration"} else None,
        "duration_ms": 0 if voice_style == "silent" else 4000,
        "dialogue_act": dialogue_act,
        "act_params": params,
        "co_acts": co_acts,
        "legacy_action": legacy_action,
    }


def derive_transition(state: str, action: str) -> dict[str, Any]:
    transition = deepcopy(TRANSITION_TABLE.get((state, action), DEFAULT_TRANSITION))
    transition.update(deepcopy(_TRANSITION_FAILURE_META.get((state, action), {})))
    return transition


def derive_bdi(
    persona_type: str,
    state: str,
    intent: str,
    cues: list[str] | None = None,
) -> dict[str, str]:
    primary_cue = cues[0] if cues else None
    belief = _cue_belief(primary_cue) or {
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
        "belief": belief,
        "desire": desire,
        "intention": intention,
    }


def _cue_belief(cue: str | None) -> str | None:
    return {
        "long_dwell_with_price_check": "The product is interesting, but its value-for-money is not yet justified.",
        "repeated_product_handling": "The product details are promising, but tactile or functional confirmation is still needed.",
        "comparing_two_products": "Two options remain close, and the decisive difference is not yet clear.",
        "looking_around_for_help": "A suitable option may be close, but staff input is needed before deciding.",
        "checking_phone_likely_research": "External prices, reviews, or specifications may change the choice.",
        "brief_glance_walking_past": "The category is only mildly interesting, and interruption may feel premature.",
        "trying_on_or_testing": "The product is promising, but fit or usage experience must be confirmed.",
        "asking_companion_opinion": "A companion's approval may influence whether the choice feels safe.",
        "no_eye_contact_avoidant": "Further engagement may feel intrusive at this moment.",
        "approaching_counter": "The shopper may be ready for service, but still needs final confirmation.",
    }.get(cue or "")


def derive_transition_rationale(
    state: str,
    action: str,
    next_state: str,
    reward: float,
    risk: str,
    benefit: str,
) -> str:
    return (
        f"Rule-derived expectation: {action} from {state} leads to {next_state} "
        f"with {risk} risk, {benefit} benefit, and reward {reward:.2f}."
    )


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


_FAILURE_CONDITION_LHS = {
    "intent_tier",
    "pressure",
    "visible_cue",
    "state",
    "push_sensitivity",
    "explicit_purchase_question",
    "private_comparison",
    "interaction_signal",
}


def _bool_token(value: bool) -> str:
    return "true" if value else "false"


def _failure_context(
    state: str,
    params: dict[str, Any],
    persona_type: str,
    intent_tier: str,
    visible_cues: list[str],
) -> dict[str, Any]:
    cues = set(visible_cues)
    explicit_purchase_question = bool(cues & {"approaching_counter", "looking_around_for_help"})
    private_comparison = "asking_companion_opinion" in cues
    interaction_signal_absent = bool(cues & {"brief_glance_walking_past", "no_eye_contact_avoidant"})
    push_sensitivity = "high" if persona_type in HIGH_PUSH_SENSITIVITY_PERSONAS else "normal"
    return {
        "intent_tier": intent_tier,
        "pressure": str(params.get("pressure", "")),
        "visible_cue": cues,
        "state": state,
        "push_sensitivity": push_sensitivity,
        "explicit_purchase_question": _bool_token(explicit_purchase_question),
        "private_comparison": _bool_token(private_comparison),
        "interaction_signal": "absent" if interaction_signal_absent else "present",
    }


def _condition_matches(condition: str, context: dict[str, Any]) -> bool:
    if "!=" in condition:
        lhs, rhs = condition.split("!=", 1)
        op = "!="
    elif "=" in condition:
        lhs, rhs = condition.split("=", 1)
        op = "="
    else:
        raise ValueError(f"invalid failure condition: {condition}")
    lhs = lhs.strip()
    rhs = rhs.strip()
    if lhs not in _FAILURE_CONDITION_LHS:
        raise ValueError(f"unknown failure condition lhs: {lhs}")
    value = context.get(lhs)
    if lhs == "visible_cue":
        matched = rhs in (value or set())
    else:
        matched = str(value) == rhs
    return matched if op == "=" else not matched


def infer_risk_tags_from_failure(failure_mode: dict[str, Any] | None) -> list[str]:
    if not failure_mode:
        return []
    text = " ".join(
        [failure_mode.get("template", "")]
        + list(failure_mode.get("trigger_conditions", []))
        + list(failure_mode.get("principle_refs", []))
    )
    tags: list[str] = []
    if "pressure" in text or "强推荐" in text or "压迫" in text:
        tags.append("pressure_reactance")
    if "closing" in text or "过早" in text:
        tags.append("premature_closing")
    if "信息" in text or "feature" in text:
        tags.append("information_overload")
    if "visible_cue" in text or "打扰" in text or "回避" in text:
        tags.append("timing_intrusion")
    return tags or ["failure_mode_triggered"]


def _transition_action_for_act(act: str, params: dict[str, Any]) -> str:
    """Map a v2 act to the closest legacy transition row.

    This is transitional until Phase 3/4 split the transition table by
    ``(act, params)`` directly. A soft recommendation should still use the
    recommendation transition family, not value-comparison.
    """

    if act == "Recommend":
        return "A3_strong_recommend"
    return act_to_legacy_action(act, params)


def derive_failure_mode(
    state: str,
    aida_stage: str,
    act: str,
    params: dict[str, Any],
    persona_type: str,
    intent_tier: str,
    visible_cues: list[str] | None = None,
) -> dict[str, Any] | None:
    """Return the triggered v2.2 failure branch, if any."""

    del aida_stage
    action = _transition_action_for_act(act, params)
    failure_mode = derive_transition(state, action).get("failure_mode")
    if not failure_mode:
        return None
    cues = list(visible_cues or [])
    context = _failure_context(state, params, persona_type, intent_tier, cues)
    if all(_condition_matches(condition, context) for condition in failure_mode["trigger_conditions"]):
        return {
            "description": failure_mode["template"],
            "triggered_by": list(failure_mode["trigger_conditions"]),
            "next_state_override": failure_mode.get("next_state_override"),
            "next_aida_override": failure_mode.get("next_aida_override"),
            "reward_override": failure_mode.get("reward_override"),
            "risk_tags": infer_risk_tags_from_failure(failure_mode),
        }
    return None


def derive_action_outcome(
    state: str,
    aida_stage: str,
    persona_type: str,
    action: str | None = None,
    *,
    act: str | None = None,
    params: dict[str, Any] | None = None,
    intent_tier: str | None = None,
    visible_cues: list[str] | None = None,
) -> dict[str, Any]:
    if action is None:
        if act is None:
            raise ValueError("derive_action_outcome requires action or act")
        action = _transition_action_for_act(act, params or {})
    act_spec = legacy_action_to_act(action)
    if act is None:
        act = act_spec["act"]
    if params is None:
        params = act_spec["params"]
    validate_dialogue_act(act, params)
    intent_tier = intent_tier or derive_intent_tier(persona_type)
    visible_cues = list(visible_cues or [])
    transition = derive_transition(state, action)
    failure = derive_failure_mode(state, aida_stage, act, params, persona_type, intent_tier, visible_cues)
    if failure:
        transition["outcome_type"] = "failure"
        transition["failure_mode"] = failure["description"]
        transition["risk_tags"] = failure["risk_tags"]
        if failure.get("next_state_override"):
            transition["next_state"] = failure["next_state_override"]
        if failure.get("reward_override") is not None:
            transition["reward"] = round(float(failure["reward_override"]), 3)
        if failure.get("next_aida_override"):
            transition["next_aida_stage"] = failure["next_aida_override"]
    else:
        raw_failure_mode = transition.get("failure_mode")
        transition["outcome_type"] = "success"
        transition["failure_mode"] = raw_failure_mode.get("template") if isinstance(raw_failure_mode, dict) else None
        transition["risk_tags"] = []
        _apply_v2_reward_calibration(transition, state, aida_stage, act, params, intent_tier)
    next_state = transition["next_state"]
    reward = float(transition["reward"])
    next_aida_stage = transition.get("next_aida_stage") or derive_next_aida_stage(aida_stage, next_state, reward)
    next_intent = derive_intent(persona_type, next_state)
    transition["dialogue_act"] = act
    transition["act_params"] = deepcopy(params)
    transition["intent_tier"] = intent_tier
    transition["next_aida_stage"] = next_aida_stage
    transition["next_bdi"] = derive_bdi(persona_type, next_state, next_intent)
    transition["reward_components"] = derive_reward_components(aida_stage, next_aida_stage, action, reward)
    transition.setdefault(
        "rationale",
        derive_transition_rationale(
            state,
            action,
            next_state,
            reward,
            transition["risk"],
            transition["benefit"],
        ),
    )
    return transition


def _apply_v2_reward_calibration(
    transition: dict[str, Any],
    state: str,
    aida_stage: str,
    act: str,
    params: dict[str, Any],
    intent_tier: str,
) -> None:
    if act == "Elicit" and params.get("openness") == "open":
        if state == "active_evaluation" and aida_stage == "interest":
            transition["reward"] = 0.83
            transition["risk"] = "low"
            transition["benefit"] = "high"
        return
    if act == "Recommend" and params.get("pressure") == "soft":
        if intent_tier == "low_intent_browsing":
            transition["reward"] = min(float(transition["reward"]), -0.2)
            transition["risk"] = "medium"
            transition["benefit"] = "low"
            return
        if state == "ready_to_decide" and aida_stage in {"desire", "action"}:
            transition["reward"] = 0.85
            transition["risk"] = "low"
            transition["benefit"] = "high"
        elif state == "active_evaluation" and aida_stage == "desire":
            transition["reward"] = 0.82
            transition["risk"] = "low"
            transition["benefit"] = "high"
        return


def _comparison_focus(profile: dict[str, str], persona_type: str, cue: str | None) -> str:
    focus = profile["comparison_focus"]
    if persona_type == "price_sensitive_cautious" or cue in {"long_dwell_with_price_check", "checking_phone_likely_research"}:
        return f"{focus}，尤其是价格差异和长期使用价值"
    if persona_type == "gift_buyer_uncertain" or cue == "asking_companion_opinion":
        return f"{focus}，尤其是送礼/他人偏好是否合适"
    if persona_type == "price_insensitive_decisive":
        return f"{focus}，优先看是否能快速确认选择"
    return focus


def _silent_timing(cue: str | None) -> str:
    if cue == "brief_glance_walking_past":
        return "顾客只是路过式扫视时，不主动开口，观察顾客是否二次回看或停下。"
    if cue == "no_eye_contact_avoidant":
        return "顾客回避眼神或身体外转时，先停止推进，至少观察 5 秒。"
    if cue == "asking_companion_opinion":
        return "顾客正在和同伴确认时，先不插话，等对话自然停顿。"
    return "现在先不主动开口，继续观察 3-5 秒。"


def _silent_physical_action(cue: str | None) -> str:
    if cue == "no_eye_contact_avoidant":
        return "后退到顾客侧后方或背景位置，视线不要持续盯着顾客，降低压迫感。"
    if cue == "brief_glance_walking_past":
        return "保持原位整理陈列或轻微侧身，不追随顾客行进方向。"
    if cue == "asking_companion_opinion":
        return "保持可见但不靠近，让顾客和同伴先完成内部讨论。"
    return "保持可见但不靠近，避免挡住顾客视线或商品区域。"


def _silent_utterance(cue: str | None) -> str:
    if cue in {"brief_glance_walking_past", "asking_companion_opinion"}:
        return "（不主动说话，只保持可被呼叫的位置。）"
    if cue == "no_eye_contact_avoidant":
        return "（不主动说话；必要时只用点头表示可提供帮助。）"
    return "（不主动说话；必要时只保持礼貌微笑。）"


def _comparison_timing(cue: str | None) -> str:
    if cue == "comparing_two_products":
        return "顾客在两个选项之间反复切换时，从侧前方低压力介入。"
    if cue in {"long_dwell_with_price_check", "checking_phone_likely_research"}:
        return "顾客停留较久并核对价格/信息时，先做对比，不直接推荐。"
    return "顾客持续停留但选择未收敛时，从侧前方低压力介入。"


def _question_timing(cue: str | None) -> str:
    if cue == "looking_around_for_help":
        return "顾客抬头寻找帮助时，可以立即用一个开放问题接住需求。"
    if cue == "approaching_counter":
        return "顾客走向服务点时，用一个问题确认她想解决的具体事项。"
    return "顾客停留但需求不明时，从开放问题开始。"


def _demonstration_timing(cue: str | None) -> str:
    if cue in {"trying_on_or_testing", "repeated_product_handling"}:
        return "顾客已经上手试用或反复触碰时，提供 10 秒以内短演示。"
    if cue == "comparing_two_products":
        return "顾客比较两个选项但无法收敛时，只演示最能区分二者的一个细节。"
    return "顾客主动评估但仍不确定时，提供短演示。"


def _acknowledge_timing(cue: str | None) -> str:
    if cue == "asking_companion_opinion":
        return "顾客和同伴讨论未结束时，只做轻度确认后等待。"
    if cue == "long_dwell_with_price_check":
        return "顾客价格犹豫明显但还没看向导购时，轻度确认后等待。"
    if cue == "no_eye_contact_avoidant":
        return "顾客回避互动但未离开时，只做最低限度确认。"
    return "顾客需要空间但不应完全消失时使用。"


def derive_action_realization(
    action: str,
    state: str,
    persona_type: str,
    product_category: str | None = None,
    cues: list[str] | None = None,
) -> dict[str, str]:
    product = PRODUCT_CATEGORY_ZH.get(product_category or "", "这件商品")
    product_profile = _product_profile(product_category)
    cue = cues[0] if cues else None
    state_phrase = {
        "high_hesitation": "顾客已经有兴趣但还在犹豫",
        "active_evaluation": "顾客正在主动比较和评估",
        "ready_to_decide": "顾客接近决策但还需要确认",
        "early_browsing": "顾客只是初步浏览",
        "disengaged": "顾客已经表现出离开或回避",
        "defensive_withdrawal": "顾客已经出现防御性退缩",
        "continued_hesitation": "顾客仍在犹豫",
        "engaged_dialogue": "顾客已经进入交流",
        "post_decision_reassurance": "顾客需要购买后的确认",
    }.get(state, "顾客状态仍不确定")
    cue_phrase = {
        "long_dwell_with_price_check": "顾客一直在看商品和价格，可能是在判断值不值得",
        "checking_phone_likely_research": "顾客正在用手机核对信息，可能在比较评价或价格",
        "comparing_two_products": "顾客在两个选项之间比较",
        "repeated_product_handling": "顾客反复接触商品，正在确认细节",
        "trying_on_or_testing": "顾客正在试用商品，需要体验确认",
        "asking_companion_opinion": "顾客在听取同伴意见",
        "looking_around_for_help": "顾客正在寻找帮助",
        "approaching_counter": "顾客正在走向服务点",
        "brief_glance_walking_past": "顾客只是短暂看了一眼",
        "no_eye_contact_avoidant": "顾客在回避交流",
    }.get(cue or "", "当前可见线索有限")
    compare_focus = _comparison_focus(product_profile, persona_type, cue)
    demo_focus = product_profile["demo_focus"]
    open_question = product_profile["open_question"]
    value_frame = product_profile["value_frame"]

    plans: dict[str, dict[str, str]] = {
        "A1_silent_observe": {
            "timing": _silent_timing(cue),
            "physical_action": _silent_physical_action(cue),
            "utterance": _silent_utterance(cue),
            "rationale": f"{cue_phrase}；此时先保留空间，比立即讲卖点更稳。",
        },
        "A2_offer_value_comparison": {
            "timing": _comparison_timing(cue),
            "physical_action": (
                f"站在顾客侧前方半步外，把两个候选{product}并排或指向对应价签，"
                f"只对比{compare_focus}，不直接替顾客下结论。"
            ),
            "utterance": (
                f"我先不替您推荐具体哪款，可以先把这几项差别摆清楚：{compare_focus}。"
                f"您看哪一点对您最重要。"
            ),
            "rationale": f"{state_phrase}；{cue_phrase}。价值对比能降低决策成本，而不是增加压力。",
        },
        "A3_strong_recommend": {
            "timing": "只在顾客明确要求推荐或已经接近购买确认时使用；当前若仍犹豫，应谨慎。",
            "physical_action": (
                f"只指向一个{product}选项，用一个理由收束选择；说完立刻给顾客退路，"
                "避免连续追问。"
            ),
            "utterance": (
                f"如果您希望我直接给建议，我会优先看这款，因为它在{value_frame}上更贴近您刚才关注的点。"
                "当然您也可以再比较一下。"
            ),
            "rationale": "强推荐能帮助临门决策，但对犹豫或价格敏感状态有较高压迫风险。",
        },
        "A4_open_with_question": {
            "timing": _question_timing(cue),
            "physical_action": "保持一臂以上距离，身体略侧开，不挡商品。",
            "utterance": f"您现在主要想先确认{open_question}？我可以按一个点帮您看，不会耽误太久。",
            "rationale": "开放问题能获得需求信息，同时保留低压力互动。",
        },
        "A5_provide_demonstration": {
            "timing": _demonstration_timing(cue),
            "physical_action": (
                f"只展示{demo_focus}中的一个最相关细节；演示后把观察权交还给顾客，"
                "不继续扩展完整卖点。"
            ),
            "utterance": f"我只演示一个最关键的地方：{demo_focus}。您看这个细节是不是符合您的使用习惯。",
            "rationale": f"{cue_phrase}。短演示能把{product}的抽象卖点变成可观察体验。",
        },
        "A6_acknowledge_and_wait": {
            "timing": _acknowledge_timing(cue),
            "physical_action": "轻微点头或短句确认后后退半步，身体侧开，保持可被呼叫的位置。",
            "utterance": f"您可以慢慢看，我就在旁边；如果要比较{compare_focus}，随时叫我就好。",
            "rationale": "该动作降低打扰感，适合犹豫但未准备交流的顾客。",
        },
        "A7_disengage": {
            "timing": "顾客已经明显回避或离开时使用。",
            "physical_action": "主动退到背景位置，不再跟随；视线转向整理陈列或其他工作，降低被盯视感。",
            "utterance": "好的，您先慢慢看，我不打扰您；需要我时招呼一声就行。",
            "rationale": "退开能避免把防御性反应进一步放大。",
        },
        "A8_offer_companion_invite": {
            "timing": "顾客明显依赖同伴意见时使用。",
            "physical_action": (
                "身体略侧开，用开放手势把同伴纳入视线范围；同时面向顾客本人，"
                "避免让同伴变成被推销对象。"
            ),
            "utterance": f"如果方便，也可以一起看一下。我可以把{compare_focus}简单说清楚，您们再自己判断。",
            "rationale": "同伴意见影响决策时，把信息同时解释给双方能减少反复确认。",
        },
    }
    plan = dict(plans[action])
    return plan


def derive_action_realizations(
    state: str,
    persona_type: str,
    product_category: str | None,
    cues: list[str],
    actions: list[str],
) -> dict[str, dict[str, str]]:
    return {
        action: derive_action_realization(action, state, persona_type, product_category, cues)
        for action in actions
    }


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


def pick_best_action_spec(
    state: str,
    aida_stage: str,
    persona_type: str,
    candidates: list[dict[str, Any]] | None = None,
    intent_tier: str | None = None,
    visible_cues: list[str] | None = None,
) -> dict[str, Any]:
    """Pick the best v2-native policy action spec by calibrated outcome reward."""

    intent_tier = intent_tier or derive_intent_tier(persona_type)
    visible_cues = list(visible_cues or [])
    candidates = candidates or derive_policy_candidate_specs(state, aida_stage, intent_tier)
    if not candidates:
        raise ValueError("pick_best_action_spec requires at least one candidate")

    def key(spec: dict[str, Any]) -> tuple[float, int, str, str]:
        outcome = derive_action_outcome(
            state,
            aida_stage,
            persona_type,
            act=spec["act"],
            params=spec.get("params", {}),
            intent_tier=intent_tier,
            visible_cues=visible_cues,
        )
        return (
            float(outcome["reward"]),
            -_RISK_RANK[outcome["risk"]],
            spec["act"],
            json.dumps(spec.get("params", {}), ensure_ascii=False, sort_keys=True),
        )

    best = max(candidates, key=key)
    return {"act": best["act"], "params": merge_supporting_acts(best.get("params", {}))}


def _aida_index(stage: str) -> int:
    return AIDA_STAGES.index(stage) if stage in AIDA_STAGES else 0
