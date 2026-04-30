"""Build QA contact sheets and manual-review templates for generated PIWM archives."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

from piwm_data import rules
from scripts.qa_gate import DEFAULT_MANUAL_REVIEW, VIEWPOINT_REQUIRED_VISIBILITY

SHEET_VERSION = "priority_contact_sheet_v1"
DEFAULT_MAX_SESSIONS_PER_SHEET = 12
DEFAULT_FRAME_WIDTH = 240
PANEL_PADDING = 12
TEXT_LINES = 4
TEXT_LINE_HEIGHT = 16
FRAME_GAP = 8


def build_contact_sheet_index(
    archive_root: Path,
    output_dir: Path,
    *,
    max_sessions_per_sheet: int = DEFAULT_MAX_SESSIONS_PER_SHEET,
    frame_width: int = DEFAULT_FRAME_WIDTH,
    write_session_templates: bool = False,
) -> dict[str, Any]:
    """Create sheet images, JSON/Markdown indexes, and empty manual QA templates."""

    output_dir.mkdir(parents=True, exist_ok=True)
    template_dir = output_dir / "qa_manual_review_templates"
    template_dir.mkdir(parents=True, exist_ok=True)

    sessions = [_session_record(path, archive_root, template_dir) for path in _session_dirs(archive_root)]
    for session in sessions:
        template = _manual_review_template(session["viewpoint"])
        template_path = Path(session["manual_review_template"])
        _write_json(template_path, template)
        if write_session_templates:
            archive_template_path = Path(session["session_dir"]) / "qa_manual_review.template.json"
            _write_json(archive_template_path, template)
            session["archive_manual_review_template"] = archive_template_path.as_posix()

    sheet_records = _write_contact_sheets(
        sessions,
        output_dir,
        max_sessions_per_sheet=max_sessions_per_sheet,
        frame_width=frame_width,
    )

    index = {
        "sheet_version": SHEET_VERSION,
        "archive_root": archive_root.as_posix(),
        "output_dir": output_dir.as_posix(),
        "n_sessions": len(sessions),
        "n_sessions_with_frames": sum(1 for item in sessions if item["n_existing_frames"] > 0),
        "n_sessions_missing_prompt": sum(1 for item in sessions if not item["prompt_exists"]),
        "n_sessions_missing_manifest": sum(1 for item in sessions if not item["frame_manifest_exists"]),
        "n_sessions_missing_frames": sum(1 for item in sessions if item["n_missing_frames"] > 0),
        "sheets": sheet_records,
        "sessions": sessions,
    }
    _write_json(output_dir / "contact_sheet_index.json", index)
    (output_dir / "contact_sheet_index.md").write_text(_markdown_index(index), encoding="utf-8")
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create PIWM QA contact sheets and manual review templates.")
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-sessions-per-sheet", type=int, default=DEFAULT_MAX_SESSIONS_PER_SHEET)
    parser.add_argument("--frame-width", type=int, default=DEFAULT_FRAME_WIDTH)
    parser.add_argument(
        "--write-session-templates",
        action="store_true",
        help="Also write qa_manual_review.template.json next to each archive session.",
    )
    args = parser.parse_args(argv)

    index = build_contact_sheet_index(
        args.archive_root,
        args.output_dir,
        max_sessions_per_sheet=args.max_sessions_per_sheet,
        frame_width=args.frame_width,
        write_session_templates=args.write_session_templates,
    )
    summary = {
        "n_sessions": index["n_sessions"],
        "n_sheets": len(index["sheets"]),
        "index_json": (args.output_dir / "contact_sheet_index.json").as_posix(),
        "index_md": (args.output_dir / "contact_sheet_index.md").as_posix(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _session_record(session_dir: Path, archive_root: Path, template_dir: Path) -> dict[str, Any]:
    prompt_path = session_dir / "prompt.json"
    manifest_path = session_dir / "frame_manifest.json"
    prompt = _read_json_or_empty(prompt_path)
    manifest = _read_json_or_empty(manifest_path)
    viewpoint = prompt.get("viewpoint") or manifest.get("viewpoint") or rules.DEFAULT_VIEWPOINT
    if viewpoint not in rules.VIEWPOINTS:
        viewpoint = rules.DEFAULT_VIEWPOINT

    frame_entries = manifest.get("sampled_frames") if isinstance(manifest.get("sampled_frames"), list) else []
    frames = []
    for entry in frame_entries:
        rel_path = str(entry.get("path", ""))
        frame_path = session_dir / rel_path
        frames.append(
            {
                "index": entry.get("index"),
                "role": entry.get("role"),
                "timestamp_sec": entry.get("timestamp_sec"),
                "path": frame_path.as_posix(),
                "relative_path": rel_path,
                "exists": frame_path.exists(),
            }
        )
    existing_frames = [item for item in frames if item["exists"]]
    session_id = str(prompt.get("session_id") or session_dir.name)
    return {
        "session_id": session_id,
        "session_dir": session_dir.as_posix(),
        "archive_relative_dir": _relative_posix(session_dir, archive_root),
        "prompt_exists": prompt_path.exists(),
        "frame_manifest_exists": manifest_path.exists(),
        "video_exists": (session_dir / "video.mp4").exists(),
        "manual_review_target": (session_dir / DEFAULT_MANUAL_REVIEW).as_posix(),
        "manual_review_template": (template_dir / f"{session_id}.qa_manual_review.json").as_posix(),
        "viewpoint": viewpoint,
        "target_cue": prompt.get("target_cue"),
        "product_category": prompt.get("product_category"),
        "persona_type": _persona_type(prompt.get("persona")),
        "split": prompt.get("split"),
        "frames": frames,
        "n_frames": len(frames),
        "n_existing_frames": len(existing_frames),
        "n_missing_frames": len(frames) - len(existing_frames),
    }


def _write_contact_sheets(
    sessions: list[dict[str, Any]],
    output_dir: Path,
    *,
    max_sessions_per_sheet: int,
    frame_width: int,
) -> list[dict[str, Any]]:
    if not sessions:
        return []
    if max_sessions_per_sheet <= 0:
        raise ValueError("--max-sessions-per-sheet must be positive")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required to render contact sheets. Install pillow or run an empty-report smoke.") from exc

    sheet_records = []
    font = ImageFont.load_default()
    chunks = list(_chunks(sessions, max_sessions_per_sheet))
    for sheet_index, chunk in enumerate(chunks):
        max_frames = max([item["n_frames"] for item in chunk] + [3])
        panel_width = PANEL_PADDING * 2 + max_frames * frame_width + max(0, max_frames - 1) * FRAME_GAP
        frame_height = max(1, round(frame_width * 9 / 16))
        panel_height = PANEL_PADDING * 2 + TEXT_LINES * TEXT_LINE_HEIGHT + frame_height
        image = Image.new("RGB", (panel_width, panel_height * len(chunk)), "white")
        draw = ImageDraw.Draw(image)

        for row, session in enumerate(chunk):
            top = row * panel_height
            draw.rectangle([0, top, panel_width - 1, top + panel_height - 1], outline=(210, 210, 210))
            lines = [
                f"{session['session_id']} | {session['viewpoint']} | cue={session.get('target_cue') or 'unknown'}",
                f"product={session.get('product_category') or 'unknown'} | persona={session.get('persona_type') or 'unknown'}",
                f"frames={session['n_existing_frames']}/{session['n_frames']} | review -> {session['manual_review_target']}",
                f"template={Path(session['manual_review_template']).name}",
            ]
            for i, line in enumerate(lines):
                draw.text((PANEL_PADDING, top + PANEL_PADDING + i * TEXT_LINE_HEIGHT), line[:180], fill=(20, 20, 20), font=font)

            frame_top = top + PANEL_PADDING + TEXT_LINES * TEXT_LINE_HEIGHT
            for col, frame in enumerate(session["frames"]):
                left = PANEL_PADDING + col * (frame_width + FRAME_GAP)
                box = (left, frame_top, left + frame_width, frame_top + frame_height)
                if frame["exists"]:
                    with Image.open(frame["path"]) as frame_image:
                        thumb = _letterbox(frame_image.convert("RGB"), (frame_width, frame_height))
                    image.paste(thumb, (left, frame_top))
                else:
                    draw.rectangle(box, fill=(245, 245, 245), outline=(180, 180, 180))
                    draw.text((left + 8, frame_top + 8), "missing", fill=(160, 0, 0), font=font)
                label = f"{frame.get('index')} {frame.get('role') or ''} @{frame.get('timestamp_sec')}s"
                draw.text((left + 4, frame_top + frame_height - TEXT_LINE_HEIGHT), label[:40], fill=(255, 255, 255), font=font)

        sheet_path = output_dir / f"contact_sheet_{sheet_index:02d}.jpg"
        image.save(sheet_path, quality=90)
        for session in chunk:
            session["contact_sheet"] = sheet_path.as_posix()
        sheet_records.append(
            {
                "sheet_index": sheet_index,
                "path": sheet_path.as_posix(),
                "n_sessions": len(chunk),
                "session_ids": [item["session_id"] for item in chunk],
            }
        )
    return sheet_records


def _manual_review_template(viewpoint: str) -> dict[str, Any]:
    required_fields = VIEWPOINT_REQUIRED_VISIBILITY.get(viewpoint, VIEWPOINT_REQUIRED_VISIBILITY[rules.DEFAULT_VIEWPOINT])
    return {
        "cue_visible_in_video": None,
        "cue_visible_in_sampled_frames": None,
        "physical_consistency_pass": None,
        "extra_subjects": None,
        "viewpoint_pass": None,
        "required_visibility": {field: None for field in required_fields},
        "reviewer_notes": "",
    }


def _markdown_index(index: dict[str, Any]) -> str:
    lines = [
        "# PIWM QA Contact Sheet Index",
        "",
        f"- archive_root: `{index['archive_root']}`",
        f"- output_dir: `{index['output_dir']}`",
        f"- sessions: {index['n_sessions']}",
        f"- sessions_with_frames: {index['n_sessions_with_frames']}",
        f"- sessions_missing_frames: {index['n_sessions_missing_frames']}",
        "",
        "## Sheets",
        "",
    ]
    if not index["sheets"]:
        lines.append("No sessions found; no contact sheet images were rendered.")
    else:
        for sheet in index["sheets"]:
            path = Path(sheet["path"])
            lines.extend([f"### Sheet {sheet['sheet_index']:02d}", "", f"![{path.name}]({path.name})", ""])

    lines.extend(
        [
            "## Review Rows",
            "",
            "| session | viewpoint | cue | frames | template | qa target | sheet |",
            "|---|---|---|---:|---|---|---|",
        ]
    )
    for session in index["sessions"]:
        template_rel = _relative_posix(Path(session["manual_review_template"]), Path(index["output_dir"]))
        sheet_rel = _relative_posix(Path(session.get("contact_sheet", "")), Path(index["output_dir"])) if session.get("contact_sheet") else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{session['session_id']}`",
                    f"`{session['viewpoint']}`",
                    f"`{session.get('target_cue') or ''}`",
                    f"{session['n_existing_frames']}/{session['n_frames']}",
                    f"`{template_rel}`",
                    f"`{session['manual_review_target']}`",
                    f"`{sheet_rel}`",
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _letterbox(image: Any, size: tuple[int, int]) -> Any:
    from PIL import Image

    target_w, target_h = size
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (20, 20, 20))
    left = math.floor((target_w - image.width) / 2)
    top = math.floor((target_h - image.height) / 2)
    canvas.paste(image, (left, top))
    return canvas


def _session_dirs(archive_root: Path) -> list[Path]:
    if not archive_root.exists():
        return []
    return [path for path in sorted(archive_root.iterdir()) if path.is_dir() and not path.name.startswith("_")]


def _read_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _chunks(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _persona_type(persona: Any) -> str | None:
    if isinstance(persona, dict):
        value = persona.get("type")
        return str(value) if value is not None else None
    if persona is not None:
        return str(persona)
    return None


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
