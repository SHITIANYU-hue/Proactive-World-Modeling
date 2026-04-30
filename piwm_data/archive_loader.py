"""Archive session loader for the PIWM data pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Optional

from pydantic import ValidationError

from . import rules
from .schemas import ActionContinuation, ActionOutcome, FrameRef, MainSchemaRecord, Persona, Provenance, ReactionFrameRef


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
    viewpoint = prompt.get("viewpoint", rules.DEFAULT_VIEWPOINT)

    latent_state = rules.derive_latent_state([target_cue])
    intent = rules.derive_intent(persona.type, latent_state)
    bdi = rules.derive_bdi(persona.type, latent_state, intent, [target_cue])
    proactive_score = rules.derive_proactive_score(latent_state)
    candidate_actions = rules.derive_candidate_actions(latent_state, aida_stage)
    next_state_by_action = {
        action: ActionOutcome(**rules.derive_action_outcome(latent_state, aida_stage, persona.type, action))
        for action in candidate_actions
    }
    reward_by_action = {
        action: outcome.reward for action, outcome in next_state_by_action.items()
    }
    best_action = rules.pick_best_action(latent_state, candidate_actions)

    record = MainSchemaRecord(
        state_id=prompt["session_id"],
        images=frames,
        product_category=prompt["product_category"],
        split=prompt.get("split"),
        observable_cues=[target_cue],
        viewpoint=viewpoint,
        persona=persona,
        aida_stage=aida_stage,
        latent_state=latent_state,
        intent=intent,
        bdi=bdi,
        proactive_score=proactive_score,
        candidate_actions=candidate_actions,
        best_action=best_action,
        next_state_by_action=next_state_by_action,
        reward_by_action=reward_by_action,
        continuations=_load_continuations(session_dir, prompt["session_id"], viewpoint, next_state_by_action),
        rationale=None,
        provenance=[
            Provenance(field_name="product_category", source="prompt_json", rule_version=rules.RULE_VERSION),
            Provenance(field_name="split", source="prompt_json", rule_version=rules.RULE_VERSION),
            Provenance(field_name="viewpoint", source="prompt_json", rule_version=rules.RULE_VERSION),
        ]
        + _rule_provenance(
            [
                "latent_state",
                "intent",
                "bdi",
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


def _load_continuations(
    session_dir: Path,
    parent_state_id: str,
    parent_viewpoint: str,
    next_state_by_action: dict[str, ActionOutcome],
) -> dict[str, ActionContinuation]:
    continuation_root = session_dir / "continuations"
    if not continuation_root.exists():
        return {}
    continuations: dict[str, ActionContinuation] = {}
    for continuation_dir in sorted(path for path in continuation_root.iterdir() if path.is_dir()):
        prompt_path = continuation_dir / "continuation_prompt.json"
        manifest_path = continuation_dir / "frame_manifest.json"
        qa_path = continuation_dir / "qa_report.json"
        video_path = continuation_dir / "video.mp4"
        if not (prompt_path.exists() and manifest_path.exists() and qa_path.exists() and video_path.exists()):
            continue
        prompt = _read_json(prompt_path)
        manifest = _read_json(manifest_path)
        qa = _read_json(qa_path)
        action = prompt["candidate_action"]
        outcome = next_state_by_action[action]
        frames = [
            ReactionFrameRef(
                index=index,
                relative_path=_relative_path(continuation_dir / entry["path"]),
                timestamp_sec=entry.get("timestamp_sec"),
                role=entry["role"],
            )
            for index, entry in enumerate(manifest.get("sampled_frames", []))
        ]
        continuations[action] = ActionContinuation(
            continuation_id=prompt["continuation_id"],
            parent_state_id=parent_state_id,
            candidate_action=action,
            continuation_role=prompt["continuation_role"],
            continuation_viewpoint=prompt.get("continuation_viewpoint", parent_viewpoint),
            video_relative_path=_relative_path(video_path),
            frames=frames,
            duration_seconds=prompt.get("duration_seconds", 5),
            expected_next_state=prompt.get("expected_next_state", outcome.next_state),
            expected_next_aida_stage=prompt.get("expected_next_aida_stage", outcome.next_aida_stage),
            expected_reward=prompt.get("expected_reward", outcome.reward),
            expected_risk=prompt.get("expected_risk", outcome.risk),
            expected_benefit=prompt.get("expected_benefit", outcome.benefit),
            reaction_template_id=prompt["reaction_template_id"],
            qa_overall_pass=qa.get("overall_pass") is True,
            reaction_visible=qa.get("reaction_visible") is True,
            reaction_matches_expected_state=qa.get("reaction_matches_expected_state") is True,
            pre_action_continuity_pass=qa.get("pre_action_continuity_pass") is True,
        )
    return continuations


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
    if prompt.get("split") is not None and prompt["split"] not in rules.SPLITS:
        raise InvalidEnumValueError(f"split={prompt['split']}")
    if prompt["target_cue"] not in rules.CUES:
        raise InvalidEnumValueError(f"target_cue={prompt['target_cue']}")
    viewpoint = prompt.get("viewpoint", rules.DEFAULT_VIEWPOINT)
    if viewpoint not in rules.VIEWPOINTS:
        raise InvalidEnumValueError(f"viewpoint={viewpoint}")


def _apply_annotation(
    record: MainSchemaRecord,
    annotation: dict[str, Any],
    source: str,
) -> MainSchemaRecord:
    data = record.model_dump()
    changed_fields: list[str] = []

    for field in ("intent", "bdi", "proactive_score", "best_action", "rationale", "candidate_actions"):
        if field in annotation:
            data[field] = annotation[field]
            changed_fields.append(field)

    if "intent" in changed_fields and "bdi" not in changed_fields:
        data["bdi"] = rules.derive_bdi(
            data["persona"]["type"],
            data["latent_state"],
            data["intent"],
            data["observable_cues"],
        )
        changed_fields.append("bdi")

    if "next_state_by_action" in annotation:
        existing = dict(data["next_state_by_action"])
        for action, partial in annotation["next_state_by_action"].items():
            base = existing.get(action)
            if base is None:
                base = rules.derive_action_outcome(data["latent_state"], data["aida_stage"], data["persona"]["type"], action)
            if isinstance(base, ActionOutcome):
                base = base.model_dump()
            merged = dict(base)
            merged.update(partial)
            merged = _complete_outcome_payload(data, action, merged, partial)
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


def _complete_outcome_payload(
    record_data: dict[str, Any],
    action: str,
    outcome: dict[str, Any],
    partial: dict[str, Any],
) -> dict[str, Any]:
    should_refresh_next = "next_state" in partial or "reward" in partial
    if should_refresh_next and "next_aida_stage" not in partial:
        outcome["next_aida_stage"] = rules.derive_next_aida_stage(
            record_data["aida_stage"],
            outcome["next_state"],
            outcome["reward"],
        )
    outcome.setdefault(
        "next_aida_stage",
        rules.derive_next_aida_stage(record_data["aida_stage"], outcome["next_state"], outcome["reward"]),
    )

    if should_refresh_next and "next_bdi" not in partial:
        next_intent = rules.derive_intent(record_data["persona"]["type"], outcome["next_state"])
        outcome["next_bdi"] = rules.derive_bdi(record_data["persona"]["type"], outcome["next_state"], next_intent)
    outcome.setdefault(
        "next_bdi",
        rules.derive_bdi(
            record_data["persona"]["type"],
            outcome["next_state"],
            rules.derive_intent(record_data["persona"]["type"], outcome["next_state"]),
        ),
    )

    if should_refresh_next and "reward_components" not in partial:
        outcome["reward_components"] = rules.derive_reward_components(
            record_data["aida_stage"],
            outcome["next_aida_stage"],
            action,
            outcome["reward"],
        )
    outcome.setdefault(
        "reward_components",
        rules.derive_reward_components(record_data["aida_stage"], outcome["next_aida_stage"], action, outcome["reward"]),
    )
    return outcome


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()
