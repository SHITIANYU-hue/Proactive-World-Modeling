"""Pydantic schemas for PIWM data artifacts."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from . import rules

AIDAStage = Literal["attention", "interest", "desire", "action"]
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


class ActionOutcome(BaseModel):
    next_state: str
    reward: float = Field(ge=-1.0, le=1.0)
    risk: Literal["low", "medium", "high"]
    benefit: Literal["low", "medium", "high"]
    rationale: Optional[str] = None

    @field_validator("next_state")
    @classmethod
    def validate_next_state(cls, value: str) -> str:
        if value not in rules.LATENT_STATES:
            raise ValueError(f"invalid latent state: {value}")
        return value


class Provenance(BaseModel):
    field_name: str
    source: Literal["prompt_json", "rule_derived", "annotation_override", "anchor_override"]
    rule_version: Optional[str] = None


class MainSchemaRecord(BaseModel):
    state_id: str
    images: list[FrameRef] = Field(min_length=1)
    observable_cues: list[str]
    persona: Persona
    aida_stage: AIDAStage
    latent_state: str
    intent: str
    proactive_score: ProactiveScore
    candidate_actions: list[str] = Field(min_length=2)
    best_action: str
    next_state_by_action: dict[str, ActionOutcome]
    reward_by_action: dict[str, float]
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
        return self

