"""Explicit migration from the old local Archive layout to the v1 spec layout.

This is intentionally separate from archive_loader.py. The production loader
stays strict and only accepts data_pipeline_spec.md v1 input. This helper is
for one-time migration of older local samples that used metadata.json plus
anchor/frames.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from . import rules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate old Archive sessions into PIWM v1 Archive layout.")
    parser.add_argument("--legacy-root", type=Path, default=Path("Archive"))
    parser.add_argument("--output-root", type=Path, default=Path("Archive_v1"))
    parser.add_argument("--mapping", type=Path, default=None, help="Required for migration. JSON mapping file.")
    parser.add_argument("--write-template", type=Path, default=None, help="Write a mapping template and exit.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output session directories.")
    args = parser.parse_args(argv)

    sessions = discover_legacy_sessions(args.legacy_root)
    if args.write_template:
        template = build_mapping_template(sessions)
        args.write_template.parent.mkdir(parents=True, exist_ok=True)
        args.write_template.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"template": str(args.write_template), "n_sessions": len(sessions)}, ensure_ascii=False, indent=2))
        return 0

    if args.mapping is None:
        raise SystemExit("Missing --mapping. Run with --write-template first, fill explicit enum mappings, then migrate.")

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    migrated = migrate_sessions(sessions, args.output_root, mapping, overwrite=args.overwrite)
    print(json.dumps({"output_root": str(args.output_root), "n_migrated": migrated}, ensure_ascii=False, indent=2))
    return 0


def discover_legacy_sessions(legacy_root: Path) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    for session_dir in sorted(path for path in legacy_root.iterdir() if path.is_dir() and not path.name.startswith("_")):
        metadata_path = session_dir / "metadata.json"
        anchor_log_path = session_dir / "anchor" / "anchor_log.json"
        frames_dir = session_dir / "anchor" / "frames"
        if not metadata_path.exists() or not anchor_log_path.exists() or not frames_dir.exists():
            continue
        metadata = _read_json(metadata_path)
        anchor_log = _read_json(anchor_log_path)
        sessions.append(
            {
                "session_dir": session_dir,
                "metadata": metadata,
                "anchor_log": anchor_log,
                "frames_dir": frames_dir,
                "prompt_txt": session_dir / "anchor" / "prompt.txt",
            }
        )
    return sessions


def build_mapping_template(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    template: dict[str, Any] = {
        "_comment": (
            "Fill every null value using exact enums from piwm_data.rules. "
            "The migration tool will not infer these semantic mappings."
        ),
        "_allowed": {
            "product_category": rules.PRODUCT_CATEGORIES,
            "persona_type": rules.PERSONA_TYPES,
            "aida_stage": ["attention", "interest", "desire", "action"],
            "target_cue": rules.CUES,
        },
        "sessions": {},
    }
    for session in sessions:
        metadata = session["metadata"]
        anchor_log = session["anchor_log"]
        session_id = metadata["session_id"]
        template["sessions"][session_id] = {
            "legacy_state_id": anchor_log.get("state_id"),
            "product_category": None,
            "persona_type": None,
            "aida_stage": None,
            "target_cue": None,
            "persona_description": summarize_legacy_persona(metadata.get("session_spec", {}).get("persona", {})),
        }
    return template


def migrate_sessions(
    sessions: list[dict[str, Any]],
    output_root: Path,
    mapping: dict[str, Any],
    overwrite: bool,
) -> int:
    output_root.mkdir(parents=True, exist_ok=True)
    mappings = mapping.get("sessions", {})
    migrated = 0
    for session in sessions:
        metadata = session["metadata"]
        session_id = metadata["session_id"]
        if session_id not in mappings:
            raise ValueError(f"missing mapping for session: {session_id}")
        spec = mappings[session_id]
        validate_mapping_entry(session_id, spec)
        out_dir = output_root / session_id
        if out_dir.exists():
            if not overwrite:
                raise FileExistsError(f"output session exists: {out_dir}")
            shutil.rmtree(out_dir)
        (out_dir / "frames").mkdir(parents=True)
        copy_frames(session["frames_dir"], out_dir / "frames")
        prompt = build_prompt_json(session, spec)
        (out_dir / "prompt.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        legacy_source = {
            "legacy_session_dir": str(session["session_dir"]),
            "legacy_state_id": session["anchor_log"].get("state_id"),
            "metadata": metadata,
            "anchor_log": session["anchor_log"],
        }
        (out_dir / "legacy_source.json").write_text(
            json.dumps(legacy_source, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        migrated += 1
    return migrated


def build_prompt_json(session: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    metadata = session["metadata"]
    anchor_log = session["anchor_log"]
    prompt_text = session["prompt_txt"].read_text(encoding="utf-8") if session["prompt_txt"].exists() else ""
    return {
        "session_id": metadata["session_id"],
        "product_category": spec["product_category"],
        "persona": {
            "type": spec["persona_type"],
            "description": spec.get("persona_description") or summarize_legacy_persona(
                metadata.get("session_spec", {}).get("persona", {})
            ),
        },
        "aida_stage": spec["aida_stage"],
        "target_cue": spec["target_cue"],
        "behavior_description": extract_behavior_description(prompt_text),
        "kling_prompt": prompt_text,
        "duration_seconds": _to_float(anchor_log.get("video_duration_s")),
    }


def validate_mapping_entry(session_id: str, spec: dict[str, Any]) -> None:
    required = ["product_category", "persona_type", "aida_stage", "target_cue"]
    for field in required:
        if not spec.get(field):
            raise ValueError(f"{session_id}: missing mapping field {field}")
    if spec["product_category"] not in rules.PRODUCT_CATEGORIES:
        raise ValueError(f"{session_id}: invalid product_category {spec['product_category']}")
    if spec["persona_type"] not in rules.PERSONA_TYPES:
        raise ValueError(f"{session_id}: invalid persona_type {spec['persona_type']}")
    if spec["aida_stage"] not in ("attention", "interest", "desire", "action"):
        raise ValueError(f"{session_id}: invalid aida_stage {spec['aida_stage']}")
    if spec["target_cue"] not in rules.CUES:
        raise ValueError(f"{session_id}: invalid target_cue {spec['target_cue']}")


def copy_frames(src: Path, dst: Path) -> None:
    for index, frame in enumerate(sorted(src.glob("*"))):
        if frame.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        suffix = ".jpg" if frame.suffix.lower() in {".jpg", ".jpeg"} else ".png"
        shutil.copy2(frame, dst / f"{index:03d}{suffix}")


def summarize_legacy_persona(persona: dict[str, Any]) -> str:
    parts = [
        persona.get("age_bucket"),
        persona.get("gender_expression"),
        persona.get("ethnicity"),
        f"tech={persona.get('tech_familiarity')}" if persona.get("tech_familiarity") else None,
        f"item={persona.get('carried_item')}" if persona.get("carried_item") else None,
    ]
    return "；".join(str(part) for part in parts if part)


def extract_behavior_description(prompt_text: str) -> str | None:
    marker = "行为状态："
    if marker not in prompt_text:
        return None
    start = prompt_text.index(marker) + len(marker)
    end = len(prompt_text)
    for stop in ["硬规则", "（东亚裔调校", "（非洲裔调校", "风格："]:
        idx = prompt_text.find(stop, start)
        if idx != -1:
            end = min(end, idx)
    return " ".join(prompt_text[start:end].strip().split())


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())

