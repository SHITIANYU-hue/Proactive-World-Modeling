"""Pydantic schemas for PIWM data artifacts."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from . import rules

AIDAStage = Literal["attention", "interest", "desire", "action"]
Viewpoint = Literal["salesperson_observable", "surveillance_oblique", "third_party_side", "first_person_pov"]
ProactiveScore = Literal[1, 2, 3, 4, 5]


class Persona(BaseModel):
    type: str
    description: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in rules.PERSONA_TYPES:
            raise ValueError(f"invalid persona type: {value}")
        return value


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


class ActionOutcome(BaseModel):
    next_state: str
    next_aida_stage: AIDAStage
    next_bdi: BDISummary
    reward: float = Field(ge=-1.0, le=1.0)
    reward_components: RewardComponents
    risk: Literal["low", "medium", "high"]
    benefit: Literal["low", "medium", "high"]
    rationale: Optional[str] = None

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
    next_state_by_action: dict[str, ActionOutcome]
    reward_by_action: dict[str, float]
    continuations: dict[str, ActionContinuation] = Field(default_factory=dict)
    rationale: Optional[str] = None
    provenance: list[Provenance]
    is_anchor: bool = False

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
        invalid = [action for action in value if action not in rules.ACTIONS]
        if invalid:
            raise ValueError(f"invalid action(s): {invalid}")
        return value

    @field_validator("best_action")
    @classmethod
    def validate_best_action_enum(cls, value: str) -> str:
        if value not in rules.ACTIONS:
            raise ValueError(f"invalid best action: {value}")
        return value

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "MainSchemaRecord":
        candidate_set = set(self.candidate_actions)
        next_state_keys = set(self.next_state_by_action)
        reward_keys = set(self.reward_by_action)
        if self.best_action not in candidate_set:
            raise ValueError("best_action must be in candidate_actions")
        if not next_state_keys.issuperset(candidate_set):
            raise ValueError("next_state_by_action keys must include all candidate_actions")
        if reward_keys != next_state_keys:
            raise ValueError("reward_by_action keys must match next_state_by_action keys")
        for action, outcome in self.next_state_by_action.items():
            if self.reward_by_action[action] != outcome.reward:
                raise ValueError(f"reward_by_action[{action}] must equal next_state_by_action[{action}].reward")
        for action, continuation in self.continuations.items():
            if action not in candidate_set:
                raise ValueError(f"continuation action {action} not in candidate_actions")
            if continuation.candidate_action != action:
                raise ValueError(f"continuation key {action} must match continuation.candidate_action")
            if continuation.parent_state_id != self.state_id:
                raise ValueError(f"continuation {continuation.continuation_id} parent_state_id mismatch")
            if continuation.continuation_viewpoint != self.viewpoint:
                raise ValueError(f"continuation {continuation.continuation_id} viewpoint mismatch parent")
        return self
