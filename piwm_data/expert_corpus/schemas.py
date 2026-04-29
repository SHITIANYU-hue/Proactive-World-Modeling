"""Pydantic schemas for the PIWM expert corpus layer.

Each rule entry in ``distilled/conditional_rules.jsonl`` is one of six rule
types. The discriminator is ``rule_type``; the typed ``key`` / ``value`` shapes
ensure the JSONL cannot drift away from runtime tables in ``piwm_data/rules.py``
without being caught by the compiler.

Provenance must be honest: the first batch is all seed rules authored by the
project, not distilled from real pedagogy text. The compiler refuses to silence
this distinction.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from .. import rules as runtime_rules

# --- Provenance --------------------------------------------------------------

SourceKind = Literal[
    "seed_rule",
    "manual_distillation",
    "pedagogy_text",
    "expert_review",
]


class Provenance(BaseModel):
    """Where this rule came from. We keep this honest."""

    source_kind: SourceKind
    source_ref: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    author: str = Field(min_length=1)
    added_at: str = Field(min_length=1)


# --- Source registries and rule-source links --------------------------------

SourceDomain = Literal["sales", "modeling"]
SourceType = Literal[
    "theory_framework",
    "open_textbook",
    "published_book",
    "research_paper",
    "manual_or_sop",
    "expert_review",
]
AuthorityLevel = Literal["canonical", "high", "medium", "pending"]
CopyrightMode = Literal[
    "public_domain",
    "open_license",
    "citation_only",
    "internal_paraphrase",
    "unknown_restricted",
]


class SourceRegistryEntry(BaseModel):
    """A source that may support sales rules or modeling decisions.

    Sales sources and modeling sources are intentionally separated. BDI-like
    modeling sources must not be used as evidence for sales rule provenance.
    """

    source_id: str = Field(min_length=1)
    domain: SourceDomain
    source_type: SourceType
    title: str = Field(min_length=1)
    citation: str = Field(min_length=1)
    url: Optional[str] = None
    authority_level: AuthorityLevel
    copyright_mode: CopyrightMode
    usable_for: list[str] = Field(min_length=1)
    notes: Optional[str] = None


RuleSupportStatus = Literal[
    "seed_only",
    "theory_anchored",
    "manual_supported",
    "expert_reviewed",
    "unsupported",
    "candidate_for_removal",
]
RuleLifecycle = Literal[
    "retained_seed",
    "modified",
    "removed",
    "new_source_backed",
]
SupportStrength = Literal["none", "low", "medium", "high"]
ReviewStatus = Literal["pending", "approved", "revise", "reject"]
RuleTypeName = Literal[
    "cue_to_state_prior",
    "persona_state_to_intent",
    "state_fallback_intent",
    "state_to_proactive_score",
    "state_aida_to_candidates",
    "transition",
]


class RuleSourceLink(BaseModel):
    """Auditable link from a rule to sales provenance.

    This is not a hard requirement to preserve all seed rules. ``lifecycle``
    records whether the rule is retained, modified, removed, or newly added.
    """

    rule_id: str = Field(min_length=1)
    rule_type: RuleTypeName
    lifecycle: RuleLifecycle
    support_status: RuleSupportStatus
    source_ids: list[str] = Field(default_factory=list)
    formalization_note: str = Field(min_length=1)
    support_strength: SupportStrength
    needs_manual_support: bool
    review_status: ReviewStatus = "pending"


class ExtractedPrinciple(BaseModel):
    """A paraphrased principle extracted from an allowed source.

    This file stores compact paraphrases only. It must not contain long
    copyrighted excerpts or be used as model-training text.
    """

    principle_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    principle: str = Field(min_length=1)
    usable_for: list[str] = Field(min_length=1)
    extraction_method: Literal["human_paraphrase", "llm_assisted_paraphrase"]
    copyright_note: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


# --- Typed key/value bodies --------------------------------------------------


class CueKey(BaseModel):
    cue: str

    def normalize(self) -> tuple[str, ...]:
        return (self.cue,)


class StateValue(BaseModel):
    state: str


class PersonaStateKey(BaseModel):
    persona: str
    state: str

    def normalize(self) -> tuple[str, ...]:
        return (self.persona, self.state)


class IntentValue(BaseModel):
    intent: str


class StateKey(BaseModel):
    state: str

    def normalize(self) -> tuple[str, ...]:
        return (self.state,)


class ScoreValue(BaseModel):
    score: int = Field(ge=1, le=5)


class StateAidaKey(BaseModel):
    state: str
    aida_stage: Literal["attention", "interest", "desire", "action"]

    def normalize(self) -> tuple[str, ...]:
        return (self.state, self.aida_stage)


class CandidateActionsValue(BaseModel):
    candidate_actions: list[str] = Field(min_length=1)


class StateActionKey(BaseModel):
    state: str
    action: str

    def normalize(self) -> tuple[str, ...]:
        return (self.state, self.action)


class TransitionValue(BaseModel):
    next_state: str
    reward: float = Field(ge=-1.0, le=1.0)
    risk: Literal["low", "medium", "high"]
    benefit: Literal["low", "medium", "high"]


# --- Discriminated rule entries ---------------------------------------------


class _BaseRule(BaseModel):
    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1, default="v1.0")
    provenance: Provenance


class CueToStateRule(_BaseRule):
    rule_type: Literal["cue_to_state_prior"]
    key: CueKey
    value: StateValue


class PersonaStateToIntentRule(_BaseRule):
    rule_type: Literal["persona_state_to_intent"]
    key: PersonaStateKey
    value: IntentValue


class StateFallbackIntentRule(_BaseRule):
    rule_type: Literal["state_fallback_intent"]
    key: StateKey
    value: IntentValue


class StateProactiveScoreRule(_BaseRule):
    rule_type: Literal["state_to_proactive_score"]
    key: StateKey
    value: ScoreValue


class StateAidaCandidatesRule(_BaseRule):
    rule_type: Literal["state_aida_to_candidates"]
    key: StateAidaKey
    value: CandidateActionsValue


class TransitionRule(_BaseRule):
    rule_type: Literal["transition"]
    key: StateActionKey
    value: TransitionValue


RuleEntry = Annotated[
    Union[
        CueToStateRule,
        PersonaStateToIntentRule,
        StateFallbackIntentRule,
        StateProactiveScoreRule,
        StateAidaCandidatesRule,
        TransitionRule,
    ],
    Field(discriminator="rule_type"),
]


# --- Enum cross-checks against runtime tables --------------------------------

_VALID_CUES = set(runtime_rules.CUES)
_VALID_STATES = set(runtime_rules.LATENT_STATES)
_VALID_PERSONAS = set(runtime_rules.PERSONA_TYPES)
_VALID_INTENTS = set(runtime_rules.INTENTS)
_VALID_ACTIONS = set(runtime_rules.ACTIONS)


class CorpusValidationError(ValueError):
    """Raised when a rule entry references an enum value not in rules.py."""


def cross_check_enums(rule: RuleEntry) -> Optional[str]:
    """Return an error string if the rule references an unknown enum, else None."""

    rt = rule.rule_type
    if rt == "cue_to_state_prior":
        if rule.key.cue not in _VALID_CUES:
            return f"unknown cue: {rule.key.cue}"
        if rule.value.state not in _VALID_STATES:
            return f"unknown state: {rule.value.state}"
    elif rt == "persona_state_to_intent":
        if rule.key.persona not in _VALID_PERSONAS:
            return f"unknown persona: {rule.key.persona}"
        if rule.key.state not in _VALID_STATES:
            return f"unknown state: {rule.key.state}"
        if rule.value.intent not in _VALID_INTENTS:
            return f"unknown intent: {rule.value.intent}"
    elif rt == "state_fallback_intent":
        if rule.key.state not in _VALID_STATES:
            return f"unknown state: {rule.key.state}"
        if rule.value.intent not in _VALID_INTENTS:
            return f"unknown intent: {rule.value.intent}"
    elif rt == "state_to_proactive_score":
        if rule.key.state not in _VALID_STATES:
            return f"unknown state: {rule.key.state}"
    elif rt == "state_aida_to_candidates":
        if rule.key.state not in _VALID_STATES:
            return f"unknown state: {rule.key.state}"
        bad = [a for a in rule.value.candidate_actions if a not in _VALID_ACTIONS]
        if bad:
            return f"unknown action(s): {bad}"
    elif rt == "transition":
        if rule.key.state not in _VALID_STATES:
            return f"unknown state: {rule.key.state}"
        if rule.key.action not in _VALID_ACTIONS:
            return f"unknown action: {rule.key.action}"
        if rule.value.next_state not in _VALID_STATES:
            return f"unknown next_state: {rule.value.next_state}"
    return None
