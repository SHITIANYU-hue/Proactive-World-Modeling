"""Archive session loader for the PIWM data pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Optional

from pydantic import ValidationError

from . import rules
from .schemas import ActionOutcome, FrameRef, MainSchemaRecord, Persona, Provenance


class MissingRequiredFieldError(ValueError):
    pass


class InvalidEnumValueError(ValueError):
    pass


class FrameNotFoundError(ValueError):
    pass


REQUIRED_PROMPT_FIELDS = ["session_id", "product_category", "persona", "aida_stage", "target_cue"]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def load_session(session_dir: Path) -> MainSchemaRecord:
    prompt_path = session_dir / "prompt.json"
    if not prompt_path.exists():
        raise MissingRequiredFieldError("missing required file: prompt.json")

    prompt = _read_json(prompt_path)
    _require_prompt_fields(prompt)
    _validate_prompt_enums(prompt)

    frames = _load_frames(session_dir / "frames")
    persona = _load_persona(session_dir, prompt)
    target_cue = prompt["target_cue"]
    aida_stage = prompt["aida_stage"]

    latent_state = rules.derive_latent_state([target_cue])
    intent = rules.derive_intent(persona.type, latent_state)
    proactive_score = rules.derive_proactive_score(latent_state)
    candidate_actions = rules.derive_candidate_actions(latent_state, aida_stage)
    next_state_by_action = {
        action: ActionOutcome(**rules.derive_transition(latent_state, action))
        for action in candidate_actions
    }
    reward_by_action = {
        action: outcome.reward for action, outcome in next_state_by_action.items()
    }
    best_action = rules.pick_best_action(latent_state, candidate_actions)

    record = MainSchemaRecord(
        state_id=prompt["session_id"],
        images=frames,
        observable_cues=[target_cue],
        persona=persona,
        aida_stage=aida_stage,
        latent_state=latent_state,
        intent=intent,
        proactive_score=proactive_score,
        candidate_actions=candidate_actions,
        best_action=best_action,
        next_state_by_action=next_state_by_action,
        reward_by_action=reward_by_action,
        rationale=None,
        provenance=_rule_provenance(
            [
                "latent_state",
                "intent",
                "proactive_score",
                "candidate_actions",
                "next_state_by_action",
                "reward_by_action",
                "best_action",
            ]
        ),
        is_anchor=False,
    )

    annotation_path = session_dir / "piwm_annotation.json"
    if annotation_path.exists():
        record = _apply_annotation(record, _read_json(annotation_path), "annotation_override")

    anchor_dir = session_dir / "anchor"
    anchor_annotation_path = anchor_dir / "piwm_annotation.json"
    if anchor_dir.exists():
        record = record.model_copy(update={"is_anchor": True})
    if anchor_annotation_path.exists():
        record = _apply_annotation(record, _read_json(anchor_annotation_path), "anchor_override")

    return record


def iter_archive(archive_root: Path, limit: Optional[int] = None) -> Iterator[MainSchemaRecord]:
    session_dirs = [
        path
        for path in sorted(archive_root.iterdir())
        if path.is_dir() and not path.name.startswith("_")
    ]
    if limit is not None:
        session_dirs = session_dirs[:limit]
    for session_dir in session_dirs:
        yield load_session(session_dir)


def sample_frames(frames: list[FrameRef], n: int) -> list[FrameRef]:
    if n == 0 or len(frames) <= n:
        return frames
    step = (len(frames) - 1) / (n - 1)
    indices = [round(i * step) for i in range(n)]
    return [frames[i] for i in indices]


def _load_frames(frames_dir: Path) -> list[FrameRef]:
    if not frames_dir.exists():
        raise FrameNotFoundError(f"missing frames directory: {frames_dir}")
    paths = sorted(path for path in frames_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    if not paths:
        raise FrameNotFoundError(f"no image frames found in: {frames_dir}")
    return [
        FrameRef(index=index, relative_path=_relative_path(path), timestamp_sec=None)
        for index, path in enumerate(paths)
    ]


def _load_persona(session_dir: Path, prompt: dict[str, Any]) -> Persona:
    persona_path = session_dir / "persona.json"
    persona_data = _read_json(persona_path) if persona_path.exists() else prompt["persona"]
    if not isinstance(persona_data, dict):
        raise MissingRequiredFieldError("persona must be an object")
    if "type" not in persona_data:
        raise MissingRequiredFieldError("persona.type")
    if persona_data["type"] not in rules.PERSONA_TYPES:
        raise InvalidEnumValueError(f"persona.type={persona_data['type']}")
    return Persona(**persona_data)


def _require_prompt_fields(prompt: dict[str, Any]) -> None:
    for field in REQUIRED_PROMPT_FIELDS:
        if field not in prompt:
            raise MissingRequiredFieldError(field)
    if not isinstance(prompt["persona"], dict):
        raise MissingRequiredFieldError("persona")
    if "type" not in prompt["persona"]:
        raise MissingRequiredFieldError("persona.type")


def _validate_prompt_enums(prompt: dict[str, Any]) -> None:
    if prompt["product_category"] not in rules.PRODUCT_CATEGORIES:
        raise InvalidEnumValueError(f"product_category={prompt['product_category']}")
    if prompt["persona"]["type"] not in rules.PERSONA_TYPES:
        raise InvalidEnumValueError(f"persona.type={prompt['persona']['type']}")
    if prompt["aida_stage"] not in ("attention", "interest", "desire", "action"):
        raise InvalidEnumValueError(f"aida_stage={prompt['aida_stage']}")
    if prompt["target_cue"] not in rules.CUES:
        raise InvalidEnumValueError(f"target_cue={prompt['target_cue']}")


def _apply_annotation(
    record: MainSchemaRecord,
    annotation: dict[str, Any],
    source: str,
) -> MainSchemaRecord:
    data = record.model_dump()
    changed_fields: list[str] = []

    for field in ("intent", "proactive_score", "best_action", "rationale", "candidate_actions"):
        if field in annotation:
            data[field] = annotation[field]
            changed_fields.append(field)

    if "next_state_by_action" in annotation:
        existing = dict(data["next_state_by_action"])
        for action, partial in annotation["next_state_by_action"].items():
            base = existing.get(action)
            if base is None:
                base = rules.derive_transition(data["latent_state"], action)
            if isinstance(base, ActionOutcome):
                base = base.model_dump()
            merged = dict(base)
            merged.update(partial)
            existing[action] = merged
        data["next_state_by_action"] = existing
        data["reward_by_action"] = {
            action: outcome["reward"] if isinstance(outcome, dict) else outcome.reward
            for action, outcome in existing.items()
        }
        changed_fields.extend(["next_state_by_action", "reward_by_action"])

    data["provenance"] = list(data.get("provenance", [])) + [
        Provenance(field_name=field, source=source, rule_version=rules.RULE_VERSION).model_dump()
        for field in changed_fields
    ]
    try:
        return MainSchemaRecord(**data)
    except ValidationError as exc:
        raise InvalidEnumValueError(str(exc)) from exc


def _rule_provenance(fields: list[str]) -> list[Provenance]:
    return [
        Provenance(field_name=field, source="rule_derived", rule_version=rules.RULE_VERSION)
        for field in fields
    ]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()

