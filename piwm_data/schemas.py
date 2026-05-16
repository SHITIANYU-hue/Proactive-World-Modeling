"""Pydantic schemas for PIWM data artifacts."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from . import rules

AIDAStage = Literal["attention", "interest", "desire", "action"]
Viewpoint = Literal[
    "salesperson_observable",
    "surveillance_oblique",
    "third_party_side",
    "first_person_pov",
    "target_frontcam",
]
ProactiveScore = Literal[1, 2, 3, 4, 5]
IntentTier = Literal["low_intent_browsing", "exploring", "ready_to_buy"]
OutcomeType = Literal["success", "failure"]
CompatibilityTier = Literal["green", "yellow", "red"]
ShootingClipVersion = Literal["A", "B"]
ShootingCustomerState = Literal[
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


class Persona(BaseModel):
    type: str
    description: Optional[str] = None
    intent_tier: Optional[IntentTier] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in rules.PERSONA_TYPES:
            raise ValueError(f"invalid persona type: {value}")
        return value

    @model_validator(mode="after")
    def fill_intent_tier(self) -> "Persona":
        if self.intent_tier is None:
            self.intent_tier = rules.derive_intent_tier(self.type)
        return self


class FrameRef(BaseModel):
    index: int
    relative_path: str
    timestamp_sec: Optional[float] = None


class ContinuationRole(str, Enum):
    BEST = "best"
    WORST = "worst"
    NEUTRAL = "neutral"


class ReactionFrameRef(FrameRef):
    role: Literal["reaction_onset", "reaction_peak", "reaction_settle"]


class BDISummary(BaseModel):
    belief: str = Field(min_length=1)
    desire: str = Field(min_length=1)
    intention: str = Field(min_length=1)


class VisualEvidenceItem(BaseModel):
    channel: Literal[
        "gaze",
        "hands",
        "body_orientation",
        "movement",
        "product_relation",
        "price_or_value_attention",
        "social_context",
    ]
    observation: str = Field(min_length=1)
    supports: list[str] = Field(default_factory=list)
    source: Literal["cue_template", "manual_annotation", "qa_review"] = "cue_template"


class FineGrainedVisualState(BaseModel):
    """Human-readable visual facts observed before symbolic labels are assigned."""

    summary: str = Field(min_length=1)
    engagement_pattern: str = Field(min_length=1)
    gaze_and_attention: str = Field(min_length=1)
    body_and_hands: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_axes(cls, data):
        if not isinstance(data, dict):
            return data
        if "engagement_pattern" not in data:
            parts = [data.get("product_relation"), data.get("movement")]
            data["engagement_pattern"] = " ".join(part for part in parts if part) or data.get("summary", "")
        if "gaze_and_attention" not in data:
            data["gaze_and_attention"] = data.get("gaze") or data.get("summary", "")
        if "body_and_hands" not in data:
            parts = [data.get("body_orientation"), data.get("hands")]
            data["body_and_hands"] = " ".join(part for part in parts if part) or data.get("summary", "")
        return data


class ActionRealization(BaseModel):
    """Concrete salesperson behavior paired with an abstract action label."""

    utterance: str = Field(min_length=1)
    physical_action: str = Field(min_length=1)
    timing: str = Field(min_length=1)
    rationale: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_intervention_plan(cls, data):
        if not isinstance(data, dict):
            return data
        if "utterance" not in data and "customer_facing_utterance_zh" in data:
            data["utterance"] = data["customer_facing_utterance_zh"]
        if "physical_action" not in data and "physical_action_zh" in data:
            data["physical_action"] = data["physical_action_zh"]
        if "timing" not in data and "timing_zh" in data:
            data["timing"] = data["timing_zh"]
        if "rationale" not in data and "rationale_zh" in data:
            data["rationale"] = data["rationale_zh"]
        return data


class TerminalRealization(BaseModel):
    """Concrete terminal behavior generated from a v2 dialogue act."""

    surface_text: str = ""
    screen: dict[str, Any] = Field(default_factory=dict)
    voice_style: str = Field(min_length=1)
    light: str = Field(min_length=1)
    cabinet_motion: Optional[str] = None
    duration_ms: int = Field(ge=0)
    dialogue_act: str
    act_params: dict[str, Any] = Field(default_factory=dict)
    co_acts: list[dict[str, Any]] = Field(default_factory=list)
    legacy_action: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def migrate_supporting_acts(cls, data):
        if not isinstance(data, dict):
            return data
        params = rules.merge_supporting_acts(data.get("act_params", {}), data.get("co_acts", []))
        data["act_params"] = params
        data.setdefault("co_acts", rules.legacy_co_acts_from_params(params))
        if not data["co_acts"]:
            data["co_acts"] = rules.legacy_co_acts_from_params(params)
        return data

    @field_validator("dialogue_act")
    @classmethod
    def validate_dialogue_act_name(cls, value: str) -> str:
        if value not in rules.DIALOGUE_ACTS:
            raise ValueError(f"invalid dialogue act: {value}")
        return value

    @model_validator(mode="after")
    def validate_dialogue_act_params(self) -> "TerminalRealization":
        rules.validate_dialogue_act(self.dialogue_act, self.act_params)
        for co_act in self.co_acts:
            rules.validate_dialogue_act(co_act["act"], co_act.get("params"))
        return self


class VisibleReaction(BaseModel):
    engagement_pattern_change: str = Field(min_length=1)
    gaze_and_attention_change: str = Field(min_length=1)
    body_and_hands_change: str = Field(min_length=1)
    reaction_type: Optional[str] = None


class ShootingClipAssets(BaseModel):
    fpv_video_path: Optional[str] = None
    hero_video_path: Optional[str] = None
    ui_recording_path: Optional[str] = None
    audio_path: Optional[str] = None
    transcript_path: Optional[str] = None
    raw_material_path: Optional[str] = None


class ShootingClipQA(BaseModel):
    overall_pass: bool = False
    start_state_visible: bool = False
    terminal_response_visible: bool = False
    audio_transcript_clear: bool = False
    future_reaction_visible: bool = False
    ab_start_state_consistent: bool = False
    viewpoint_pass: bool = False
    no_sensitive_info: bool = False
    label_complete: bool = False
    notes: str = ""


class ShootingClipRecord(BaseModel):
    """Real-shooting clip manifest row aligned with the v2 action contract."""

    clip_id: str
    group_id: str
    shooting_state: ShootingCustomerState
    state_name_zh: Optional[str] = None
    version: ShootingClipVersion
    product_category: str
    persona_type: str
    response_type_zh: Optional[str] = None
    legacy_action: Optional[str] = None
    t_state: Optional[str] = None
    dialogue_act: Optional[str] = None
    act_params: dict[str, Any] = Field(default_factory=dict)
    co_acts: list[dict[str, Any]] = Field(default_factory=list)
    terminal_realization: Optional[TerminalRealization] = None
    visual_state: Optional[FineGrainedVisualState] = None
    visible_reaction: Optional[VisibleReaction] = None
    expected_reaction: Optional[str] = None
    requires_hero_view: bool = False
    post_compose_ui: bool = False
    assets: ShootingClipAssets = Field(default_factory=ShootingClipAssets)
    qa: ShootingClipQA = Field(default_factory=ShootingClipQA)

    @model_validator(mode="before")
    @classmethod
    def fill_from_shooting_prior(cls, data):
        if not isinstance(data, dict):
            return data
        state = data.get("shooting_state")
        version = data.get("version")
        if state and version:
            prior = rules.shooting_state_response_prior(state, version)
            data.setdefault("state_name_zh", prior["state_name_zh"])
            data.setdefault("response_type_zh", prior["response_type_zh"])
            data.setdefault("legacy_action", prior.get("legacy_action"))
            data.setdefault("t_state", prior.get("t_state"))
            data.setdefault("dialogue_act", prior["act"])
            data.setdefault("act_params", prior["params"])
            data["act_params"] = rules.merge_supporting_acts(data.get("act_params", {}), data.get("co_acts", prior.get("co_acts", [])))
            if not data.get("co_acts"):
                data["co_acts"] = rules.legacy_co_acts_from_params(data["act_params"])
            data.setdefault("expected_reaction", prior["expected_reaction"])
            data.setdefault("requires_hero_view", prior["requires_hero_view"])
            if "terminal_realization" not in data:
                data["terminal_realization"] = rules.derive_terminal_realization_from_act(
                    data["dialogue_act"],
                    data.get("act_params", {}),
                    data.get("co_acts", []),
                    data.get("legacy_action"),
                )
        return data

    @field_validator("product_category")
    @classmethod
    def validate_clip_product_category(cls, value: str) -> str:
        if value not in rules.PRODUCT_CATEGORIES:
            raise ValueError(f"invalid product category: {value}")
        return value

    @field_validator("persona_type")
    @classmethod
    def validate_clip_persona_type(cls, value: str) -> str:
        if value not in rules.PERSONA_TYPES:
            raise ValueError(f"invalid persona type: {value}")
        return value

    @model_validator(mode="after")
    def validate_action_contract(self) -> "ShootingClipRecord":
        if self.dialogue_act:
            rules.validate_dialogue_act(self.dialogue_act, self.act_params)
        for co_act in self.co_acts:
            rules.validate_dialogue_act(co_act["act"], co_act.get("params"))
        if self.response_type_zh:
            response_spec = rules.response_type_to_act(self.response_type_zh)
            if response_spec["act"] != self.dialogue_act:
                raise ValueError("response_type_zh does not match dialogue_act")
            if response_spec.get("params", {}) != rules.merge_supporting_acts(self.act_params, self.co_acts):
                raise ValueError("response_type_zh does not match act_params")
        if self.t_state:
            t_spec = rules.t_state_to_act(self.t_state)
            if t_spec["act"] != self.dialogue_act:
                raise ValueError("t_state does not match dialogue_act")
            if t_spec.get("params", {}) != rules.merge_supporting_acts(self.act_params, self.co_acts):
                raise ValueError("t_state does not match act_params")
        if self.terminal_realization and self.terminal_realization.dialogue_act != self.dialogue_act:
            raise ValueError("terminal_realization.dialogue_act must match dialogue_act")
        return self


class RewardComponents(BaseModel):
    delta_stage: float = Field(ge=-1.0, le=1.0)
    delta_mental: float = Field(ge=-3.0, le=3.0)
    action_cost: float = Field(ge=0.0, le=1.0)
    alpha: float = Field(default=0.4, ge=0.0)
    beta: float = Field(default=0.5, ge=0.0)
    gamma: float = Field(default=0.1, ge=0.0)
    final_reward: float = Field(ge=-1.0, le=1.0)

    @model_validator(mode="after")
    def validate_formula(self) -> "RewardComponents":
        expected = self.alpha * self.delta_stage + self.beta * self.delta_mental - self.gamma * self.action_cost
        if abs(expected - self.final_reward) > 1e-6:
            raise ValueError("reward_components must satisfy alpha*delta_stage + beta*delta_mental - gamma*action_cost")
        return self


class CandidateAction(BaseModel):
    """Canonical v2 action object.

    Old A-labels are allowed only as migration input and are normalized here to
    the canonical ``act`` / ``params`` shape.
    """

    act: str
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_input(cls, data):
        if isinstance(data, str):
            return _candidate_action_payload_from_legacy(data)
        if not isinstance(data, dict):
            return data
        item = dict(data)
        if "act" not in item and "dialogue_act" in item:
            item["act"] = item["dialogue_act"]
        if "params" not in item and "act_params" in item:
            item["params"] = item["act_params"]
        item["params"] = rules.merge_supporting_acts(item.get("params", {}), item.get("co_acts", []))
        return item

    @field_validator("act")
    @classmethod
    def validate_act(cls, value: str) -> str:
        if value not in rules.DIALOGUE_ACTS:
            raise ValueError(f"invalid dialogue act: {value}")
        return value

    @model_validator(mode="after")
    def validate_params(self) -> "CandidateAction":
        rules.validate_dialogue_act(self.act, self.params)
        return self


class ActionOutcome(BaseModel):
    next_state: str
    next_aida_stage: AIDAStage
    next_bdi: BDISummary
    reward: float = Field(ge=-1.0, le=1.0)
    reward_components: RewardComponents
    risk: Literal["low", "medium", "high"]
    benefit: Literal["low", "medium", "high"]
    rationale: Optional[str] = None
    dialogue_act: Optional[str] = None
    act_params: dict[str, Any] = Field(default_factory=dict)
    intent_tier: Optional[IntentTier] = None
    risk_tags: list[str] = Field(default_factory=list)
    failure_mode: Optional[str] = None
    outcome_type: OutcomeType = "success"

    @field_validator("next_state")
    @classmethod
    def validate_next_state(cls, value: str) -> str:
        if value not in rules.LATENT_STATES:
            raise ValueError(f"invalid latent state: {value}")
        return value

    @model_validator(mode="after")
    def validate_reward_consistency(self) -> "ActionOutcome":
        if abs(self.reward_components.final_reward - self.reward) > 1e-6:
            raise ValueError("reward_components.final_reward must equal reward")
        if self.dialogue_act is not None:
            rules.validate_dialogue_act(self.dialogue_act, self.act_params)
        if self.outcome_type == "failure" and not self.failure_mode:
            raise ValueError("failure outcomes require failure_mode")
        return self


class Provenance(BaseModel):
    field_name: str
    source: Literal["prompt_json", "rule_derived", "annotation_override", "anchor_override"]
    rule_version: Optional[str] = None


class ActionContinuation(BaseModel):
    continuation_id: str
    parent_state_id: str
    candidate_action: str
    continuation_role: ContinuationRole
    continuation_viewpoint: Viewpoint
    video_relative_path: str
    frames: list[ReactionFrameRef] = Field(min_length=2)
    duration_seconds: int = Field(default=5, ge=4, le=8)
    expected_next_state: str
    expected_next_aida_stage: AIDAStage
    expected_reward: float = Field(ge=-1.0, le=1.0)
    expected_risk: Literal["low", "medium", "high"]
    expected_benefit: Literal["low", "medium", "high"]
    reaction_template_id: str
    qa_overall_pass: bool
    reaction_visible: bool
    reaction_matches_expected_state: bool
    pre_action_continuity_pass: bool

    @field_validator("candidate_action")
    @classmethod
    def validate_candidate_action(cls, value: str) -> str:
        if value not in rules.ACTIONS:
            raise ValueError(f"invalid candidate action: {value}")
        return value

    @field_validator("expected_next_state")
    @classmethod
    def validate_expected_next_state(cls, value: str) -> str:
        if value not in rules.LATENT_STATES:
            raise ValueError(f"invalid expected next state: {value}")
        return value


class MainSchemaRecord(BaseModel):
    state_id: str
    images: list[FrameRef] = Field(min_length=1)
    product_category: str
    split: Optional[str] = None
    visual_state: FineGrainedVisualState
    observable_cues: list[str]
    viewpoint: Viewpoint = rules.DEFAULT_VIEWPOINT
    persona: Persona
    aida_stage: AIDAStage
    latent_state: str
    intent: str
    bdi: BDISummary
    proactive_score: ProactiveScore
    candidate_actions: list[str] = Field(min_length=2)
    best_action: str
    candidate_action_specs: list[CandidateAction] = Field(default_factory=list)
    best_action_spec: Optional[CandidateAction] = None
    best_action_realization: ActionRealization
    dialogue_act: Optional[str] = None
    act_params: dict[str, Any] = Field(default_factory=dict)
    co_acts: list[dict[str, Any]] = Field(default_factory=list)
    realization: Optional[TerminalRealization] = None
    next_state_by_action: dict[str, ActionOutcome]
    next_state_by_action_v2: dict[str, ActionOutcome] = Field(default_factory=dict)
    reward_by_action: dict[str, float]
    continuations: dict[str, ActionContinuation] = Field(default_factory=dict)
    rationale: Optional[str] = None
    compatibility_tier: CompatibilityTier = "green"
    legacy_mismatch_flags: list[str] = Field(default_factory=list)
    provenance: list[Provenance]
    is_anchor: bool = False

    @model_validator(mode="before")
    @classmethod
    def fill_detailed_defaults(cls, data):
        if not isinstance(data, dict):
            return data
        cues = list(data.get("observable_cues") or [])
        product_category = data.get("product_category")
        viewpoint = data.get("viewpoint", rules.DEFAULT_VIEWPOINT)
        state = data.get("latent_state")
        persona = data.get("persona") or {}
        persona_type = persona.get("type") if isinstance(persona, dict) else getattr(persona, "type", None)
        candidate_actions = list(data.get("candidate_actions") or [])
        best_action = data.get("best_action")
        legacy_mismatch_flags = list(data.get("legacy_mismatch_flags") or [])

        if "visual_state" not in data and cues:
            data["visual_state"] = rules.derive_visual_state(cues, product_category, viewpoint)
        valid_candidate_actions = [action for action in candidate_actions if action in rules.ACTIONS]
        if valid_candidate_actions and not data.get("candidate_action_specs"):
            data["candidate_action_specs"] = [
                _candidate_action_payload_from_legacy(action)
                for action in valid_candidate_actions
            ]
        if best_action in rules.ACTIONS and not data.get("best_action_spec"):
            data["best_action_spec"] = _candidate_action_payload_from_legacy(best_action)
        if not data.get("next_state_by_action_v2") and data.get("next_state_by_action"):
            data["next_state_by_action_v2"] = _next_state_by_action_v2_payload(
                candidate_actions=candidate_actions,
                candidate_action_specs=data.get("candidate_action_specs") or [],
                next_state_by_action=data.get("next_state_by_action") or {},
            )
        legacy_mismatch_flags.extend(
            _action_spec_mismatch_flags(
                candidate_actions=candidate_actions,
                candidate_action_specs=data.get("candidate_action_specs") or [],
                best_action=best_action,
                best_action_spec=data.get("best_action_spec"),
            )
        )
        if _intent_tier_visual_mismatch(persona_type, cues):
            legacy_mismatch_flags.append("intent_tier_visual_mismatch")
        if legacy_mismatch_flags:
            data["legacy_mismatch_flags"] = sorted(set(legacy_mismatch_flags))
            data.setdefault("compatibility_tier", _compatibility_tier_from_flags(legacy_mismatch_flags))
        if "best_action_realization" not in data and "best_intervention" in data:
            data["best_action_realization"] = data["best_intervention"]
        if "best_action_realization" not in data and best_action:
            if best_action in rules.ACTIONS and state in rules.LATENT_STATES and persona_type:
                data["best_action_realization"] = rules.derive_action_realization(
                    best_action,
                    state,
                    persona_type,
                    product_category,
                    cues,
                )
        if best_action in rules.ACTIONS:
            act_spec = rules.legacy_action_to_act(best_action)
            data.setdefault("dialogue_act", act_spec["act"])
            data.setdefault("act_params", act_spec["params"])
            data["act_params"] = rules.merge_supporting_acts(data.get("act_params", {}), data.get("co_acts", act_spec.get("co_acts", [])))
            if not data.get("co_acts"):
                data["co_acts"] = rules.legacy_co_acts_from_params(data["act_params"])
            if "realization" not in data and state in rules.LATENT_STATES and persona_type:
                data["realization"] = rules.derive_terminal_realization(
                    best_action,
                    state,
                    persona_type,
                    product_category,
                    cues,
                )
        return data

    @field_validator("observable_cues")
    @classmethod
    def validate_observable_cues(cls, value: list[str]) -> list[str]:
        invalid = [cue for cue in value if cue not in rules.CUES]
        if invalid:
            raise ValueError(f"invalid cue(s): {invalid}")
        return value

    @field_validator("product_category")
    @classmethod
    def validate_product_category(cls, value: str) -> str:
        if value not in rules.PRODUCT_CATEGORIES:
            raise ValueError(f"invalid product category: {value}")
        return value

    @field_validator("split")
    @classmethod
    def validate_split(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in rules.SPLITS:
            raise ValueError(f"invalid split: {value}")
        return value

    @field_validator("latent_state")
    @classmethod
    def validate_latent_state(cls, value: str) -> str:
        if value not in rules.LATENT_STATES:
            raise ValueError(f"invalid latent state: {value}")
        return value

    @field_validator("intent")
    @classmethod
    def validate_intent(cls, value: str) -> str:
        if value not in rules.INTENTS:
            raise ValueError(f"invalid intent: {value}")
        return value

    @field_validator("candidate_actions")
    @classmethod
    def validate_candidate_actions(cls, value: list[str]) -> list[str]:
        invalid = [action for action in value if not action or not isinstance(action, str)]
        if invalid:
            raise ValueError(f"invalid empty action key(s): {invalid}")
        return value

    @field_validator("best_action")
    @classmethod
    def validate_best_action_enum(cls, value: str) -> str:
        if not value:
            raise ValueError("best_action must be a non-empty action key")
        return value

    @field_validator("dialogue_act")
    @classmethod
    def validate_dialogue_act_enum(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in rules.DIALOGUE_ACTS:
            raise ValueError(f"invalid dialogue act: {value}")
        return value

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "MainSchemaRecord":
        candidate_set = set(self.candidate_actions)
        next_state_keys = set(self.next_state_by_action)
        reward_keys = set(self.reward_by_action)
        if self.best_action not in candidate_set:
            raise ValueError("best_action must be in candidate_actions")
        if self.candidate_action_specs and len(self.candidate_action_specs) != len(self.candidate_actions):
            raise ValueError("candidate_action_specs must align with candidate_actions")
        if self.candidate_action_specs:
            for action, spec in zip(self.candidate_actions, self.candidate_action_specs):
                if action in rules.ACTIONS:
                    continue
                expected = rules.action_spec_key(spec.act, spec.params)
                if action != expected:
                    raise ValueError(f"v2-native candidate action key {action} must match action spec key {expected}")
        if not next_state_keys.issuperset(candidate_set):
            raise ValueError("next_state_by_action keys must include all candidate_actions")
        if reward_keys != next_state_keys:
            raise ValueError("reward_by_action keys must match next_state_by_action keys")
        for action, outcome in self.next_state_by_action.items():
            if self.reward_by_action[action] != outcome.reward:
                raise ValueError(f"reward_by_action[{action}] must equal next_state_by_action[{action}].reward")
        if self.next_state_by_action_v2 and self.candidate_action_specs:
            expected_v2_keys = {
                rules.action_spec_key(spec.act, spec.params)
                for spec in self.candidate_action_specs
            }
            if not set(self.next_state_by_action_v2).issuperset(expected_v2_keys):
                raise ValueError("next_state_by_action_v2 keys must include all candidate_action_specs")
            for action, spec in zip(self.candidate_actions, self.candidate_action_specs):
                key = rules.action_spec_key(spec.act, spec.params)
                if action in self.next_state_by_action and key in self.next_state_by_action_v2:
                    if self.next_state_by_action[action].reward != self.next_state_by_action_v2[key].reward:
                        raise ValueError(f"next_state_by_action_v2[{key}] must match legacy outcome reward for {action}")
        for action, continuation in self.continuations.items():
            if action not in candidate_set:
                raise ValueError(f"continuation action {action} not in candidate_actions")
            if continuation.candidate_action != action:
                raise ValueError(f"continuation key {action} must match continuation.candidate_action")
            if continuation.parent_state_id != self.state_id:
                raise ValueError(f"continuation {continuation.continuation_id} parent_state_id mismatch")
            if continuation.continuation_viewpoint != self.viewpoint:
                raise ValueError(f"continuation {continuation.continuation_id} viewpoint mismatch parent")
        if self.dialogue_act:
            rules.validate_dialogue_act(self.dialogue_act, self.act_params)
        for co_act in self.co_acts:
            rules.validate_dialogue_act(co_act["act"], co_act.get("params"))
        return self


def _candidate_action_payload_from_legacy(action: str) -> dict[str, Any]:
    spec = rules.legacy_action_to_act(action)
    return {"act": spec["act"], "params": spec["params"]}


def _normalize_candidate_action_payload(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, CandidateAction):
        return value.model_dump()
    if isinstance(value, str):
        return _candidate_action_payload_from_legacy(value)
    if not isinstance(value, dict):
        return None
    act = value.get("act") or value.get("dialogue_act")
    params = value.get("params") if "params" in value else value.get("act_params", {})
    if not act:
        return None
    return {"act": act, "params": rules.merge_supporting_acts(params or {}, value.get("co_acts", []))}


def _next_state_by_action_v2_payload(
    candidate_actions: list[str],
    candidate_action_specs: list[Any],
    next_state_by_action: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for action, spec in zip(candidate_actions, candidate_action_specs):
        normalized = _normalize_candidate_action_payload(spec)
        if action not in next_state_by_action or normalized is None:
            continue
        key = rules.action_spec_key(normalized["act"], normalized["params"])
        payload[key] = next_state_by_action[action]
    return payload


def _action_spec_equal(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    if left is None or right is None:
        return left is right
    return left.get("act") == right.get("act") and rules.merge_supporting_acts(left.get("params", {})) == rules.merge_supporting_acts(right.get("params", {}))


def _action_spec_mismatch_flags(
    candidate_actions: list[str],
    candidate_action_specs: list[Any],
    best_action: str | None,
    best_action_spec: Any,
) -> list[str]:
    flags: list[str] = []
    if candidate_actions and candidate_action_specs:
        if len(candidate_actions) != len(candidate_action_specs):
            flags.append("candidate_action_specs_count_mismatch")
        else:
            for action, spec in zip(candidate_actions, candidate_action_specs):
                if action not in rules.ACTIONS:
                    continue
                if not _action_spec_equal(_candidate_action_payload_from_legacy(action), _normalize_candidate_action_payload(spec)):
                    flags.append("candidate_action_specs_mismatch")
                    break
    if best_action in rules.ACTIONS and best_action_spec is not None:
        if not _action_spec_equal(_candidate_action_payload_from_legacy(best_action), _normalize_candidate_action_payload(best_action_spec)):
            flags.append("best_action_spec_mismatch")
    return flags


_HIGH_ENGAGEMENT_CUES = {
    "long_dwell_with_price_check",
    "repeated_product_handling",
    "comparing_two_products",
    "looking_around_for_help",
    "checking_phone_likely_research",
    "trying_on_or_testing",
    "asking_companion_opinion",
    "approaching_counter",
}


def _intent_tier_visual_mismatch(persona_type: str | None, cues: list[str]) -> bool:
    if not persona_type:
        return False
    if rules.derive_intent_tier(persona_type) != "low_intent_browsing":
        return False
    return any(cue in _HIGH_ENGAGEMENT_CUES for cue in cues)


def _compatibility_tier_from_flags(flags: list[str]) -> CompatibilityTier:
    severe = {"intent_tier_visual_mismatch", "latent_state_mismatch"}
    if any(flag in severe for flag in flags):
        return "red"
    if flags:
        return "yellow"
    return "green"
