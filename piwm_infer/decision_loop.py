"""A small, testable PIWM inference loop for the 5-day sprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from piwm_data import rules
from piwm_infer import config as infer_config
from piwm_infer.parsers import (
    MalformedOutputError,
    parse_action_output,
    parse_continuation_caption_output,
    parse_deliberation_output,
    parse_perception_output,
)
from piwm_train.prompts import (
    build_action_prompt,
    build_continuation_caption_prompt,
    build_deliberation_prompt,
    build_perception_prompt,
)


class VLMClient(Protocol):
    def generate(self, prompt: str, *, role: str, max_new_tokens: int) -> str:
        """Return raw model text for one PIWM role."""


@dataclass
class CandidatePrediction:
    action: str
    next_aida_stage: str
    next_bdi: dict[str, str]
    risk: str
    benefit: str
    reward: float
    reaction_caption: str | None = None


@dataclass
class DecisionResult:
    state_id: str
    perception: dict
    candidates: list[str]
    per_candidate: dict[str, CandidatePrediction]
    chosen_action: str
    rationale: str
    used_fallback: bool = False
    errors: list[str] = field(default_factory=list)


class PIWMDecisionLoop:
    def __init__(
        self,
        vlm: VLMClient,
        *,
        silence_threshold: int = 1,
        fallback_action: str = infer_config.FALLBACK_ACTION_ON_PARSE_ERROR,
    ) -> None:
        self.vlm = vlm
        self.silence_threshold = silence_threshold
        self.fallback_action = fallback_action

    def decide(self, state_row: dict) -> DecisionResult:
        """Run perception, deliberation, continuation caption, and action selection."""
        state_id = state_row.get("state_id", "unknown")
        errors: list[str] = []
        try:
            perception_raw = self.vlm.generate(
                build_perception_prompt(state_row),
                role="perception",
                max_new_tokens=infer_config.MAX_NEW_TOKENS_PERCEPTION,
            )
            perception = parse_perception_output(perception_raw)
        except MalformedOutputError as exc:
            return DecisionResult(
                state_id=state_id,
                perception={},
                candidates=[self.fallback_action],
                per_candidate={},
                chosen_action=self.fallback_action,
                rationale=f"fallback after malformed perception: {exc}",
                used_fallback=True,
                errors=[str(exc)],
            )

        candidates = list(perception["candidate_actions"])
        if perception["proactive_score"] <= self.silence_threshold:
            action = self._fallback_or_first_valid(candidates)
            return DecisionResult(
                state_id=state_id,
                perception=perception,
                candidates=candidates,
                per_candidate={},
                chosen_action=action,
                rationale="proactive score below intervention threshold",
                used_fallback=True,
            )

        per_candidate: dict[str, CandidatePrediction] = {}
        for action in candidates:
            try:
                delib_row = self._deliberation_prompt_row(state_row, perception, action)
                delib_raw = self.vlm.generate(
                    build_deliberation_prompt(delib_row),
                    role=f"deliberation:{action}",
                    max_new_tokens=infer_config.MAX_NEW_TOKENS_DELIBERATION,
                )
                delib = parse_deliberation_output(delib_raw)
                continuation_row = self._continuation_prompt_row(state_row, perception, action)
                continuation_raw = self.vlm.generate(
                    build_continuation_caption_prompt(continuation_row),
                    role=f"continuation:{action}",
                    max_new_tokens=infer_config.MAX_NEW_TOKENS_CONTINUATION,
                )
                continuation = parse_continuation_caption_output(continuation_raw)
                per_candidate[action] = CandidatePrediction(
                    action=action,
                    next_aida_stage=delib["next_aida_stage"],
                    next_bdi=delib["next_bdi"],
                    risk=delib["risk"],
                    benefit=delib["benefit"],
                    reward=delib["reward"],
                    reaction_caption=continuation["reaction_caption"],
                )
            except MalformedOutputError as exc:
                errors.append(f"{action}: {exc}")

        if not per_candidate:
            return DecisionResult(
                state_id=state_id,
                perception=perception,
                candidates=candidates,
                per_candidate={},
                chosen_action=self._fallback_or_first_valid(candidates),
                rationale="fallback after all candidate predictions failed",
                used_fallback=True,
                errors=errors,
            )

        action_row = self._action_prompt_row(state_row, perception, per_candidate)
        try:
            action_raw = self.vlm.generate(
                build_action_prompt(action_row),
                role="action",
                max_new_tokens=infer_config.MAX_NEW_TOKENS_ACTION,
            )
            action = parse_action_output(action_raw, valid_actions=set(per_candidate))
            return DecisionResult(
                state_id=state_id,
                perception=perception,
                candidates=candidates,
                per_candidate=per_candidate,
                chosen_action=action["chosen"],
                rationale=action["rationale"],
                errors=errors,
            )
        except MalformedOutputError as exc:
            errors.append(str(exc))
            best = min(
                per_candidate,
                key=lambda action: (
                    -per_candidate[action].reward,
                    rules.ACTIONS.index(action),
                ),
            )
            return DecisionResult(
                state_id=state_id,
                perception=perception,
                candidates=candidates,
                per_candidate=per_candidate,
                chosen_action=best,
                rationale="fallback to highest predicted reward after malformed action output",
                used_fallback=True,
                errors=errors,
            )

    def _fallback_or_first_valid(self, candidates: list[str]) -> str:
        if self.fallback_action in candidates:
            return self.fallback_action
        return candidates[0] if candidates else self.fallback_action

    def _state_summary(self, state_row: dict, perception: dict) -> dict:
        meta = state_row.get("meta", {})
        input_payload = state_row.get("input", {})
        return {
            "aida_stage": perception["aida_stage"],
            "state_subtype": state_row.get("output", {}).get("state_subtype", "unknown"),
            "state": state_row.get("output", {}).get("current_state", "unknown"),
            "intent": state_row.get("output", {}).get("intent", "unknown"),
            "bdi": perception["bdi"],
            "proactive_score": perception["proactive_score"],
            "persona_type": input_payload.get("persona_summary", "unknown").split(":", 1)[0],
            "observable_cues": meta.get("observable_cues", []),
        }

    def _deliberation_prompt_row(self, state_row: dict, perception: dict, action: str) -> dict:
        return {
            "input": {
                "frames": state_row["input"].get("frames", []),
                "current_state_summary": self._state_summary(state_row, perception),
                "candidate_action": action,
            }
        }

    def _continuation_prompt_row(self, state_row: dict, perception: dict, action: str) -> dict:
        return {
            "input": {
                "current_frames": state_row["input"].get("frames", []),
                "current_state_summary": self._state_summary(state_row, perception),
                "candidate_action": action,
            }
        }

    def _action_prompt_row(
        self,
        state_row: dict,
        perception: dict,
        per_candidate: dict[str, CandidatePrediction],
    ) -> dict:
        return {
            "meta": {
                "frames": state_row["input"].get("frames", []),
                "state_summary": self._state_summary(state_row, perception),
                "candidate_block": [
                    {
                        "action": pred.action,
                        "next_aida_stage": pred.next_aida_stage,
                        "risk": pred.risk,
                        "benefit": pred.benefit,
                        "reward": pred.reward,
                    }
                    for pred in per_candidate.values()
                ],
            }
        }

