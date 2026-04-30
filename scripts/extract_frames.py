"""Extract sampled frames from generated PIWM video sessions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from piwm_data import rules

DEFAULT_PLAN = [
    {"index": 0, "timestamp_sec": 2.0, "role": "cue_onset"},
    {"index": 1, "timestamp_sec": 5.0, "role": "cue_peak"},
    {"index": 2, "timestamp_sec": 8.0, "role": "cue_resolution"},
]


def extract_frames_for_session(
    session_dir: Path,
    overwrite: bool = False,
    image_ext: str = ".jpg",
) -> dict[str, Any]:
    cv2 = _load_cv2()
    prompt_path = session_dir / "prompt.json"
    video_path = session_dir / "video.mp4"
    if not prompt_path.exists():
        raise FileNotFoundError(f"missing prompt.json: {prompt_path}")
    if not video_path.exists():
        raise FileNotFoundError(f"missing video.mp4: {video_path}")

    prompt = _read_json(prompt_path)
    plan = _frame_sampling_plan(prompt)
    frames_dir = session_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"failed to open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
    duration_sec = frame_count / fps if fps else 0.0
    sampled_frames: list[dict[str, Any]] = []

    try:
        for raw in plan:
            index = int(raw["index"])
            timestamp_sec = float(raw["timestamp_sec"])
            role = str(raw.get("role", f"frame_{index}"))
            if timestamp_sec < 0:
                raise ValueError(f"negative timestamp in frame_sampling_plan: {timestamp_sec}")
            filename = f"{index:03d}{image_ext}"
            out_path = frames_dir / filename
            if out_path.exists() and not overwrite:
                raise FileExistsError(f"frame exists: {out_path}. Use --overwrite to replace it.")

            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            ok, frame = cap.read()
            if not ok:
                raise ValueError(f"failed to read frame at {timestamp_sec}s from {video_path}")
            if not cv2.imwrite(str(out_path), frame):
                raise ValueError(f"failed to write frame: {out_path}")
            sampled_frames.append(
                {
                    "index": index,
                    "path": f"frames/{filename}",
                    "timestamp_sec": timestamp_sec,
                    "role": role,
                }
            )
    finally:
        cap.release()

    manifest = {
        "source_video": "video.mp4",
        "viewpoint": prompt.get("viewpoint", rules.DEFAULT_VIEWPOINT),
        "training_input_mode": prompt.get("training_input_mode", "multi_image_single_turn"),
        "frame_sampling_strategy": prompt.get("frame_sampling_strategy", "cue_timeline_plan"),
        "fps": fps,
        "frame_count": frame_count,
        "duration_sec": duration_sec,
        "sampled_frames": sampled_frames,
    }
    (session_dir / "frame_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "session_id": prompt.get("session_id", session_dir.name),
        "viewpoint": manifest["viewpoint"],
        "session_dir": session_dir.as_posix(),
        "frame_manifest": (session_dir / "frame_manifest.json").as_posix(),
        "n_sampled_frames": len(sampled_frames),
        "duration_sec": duration_sec,
        "fps": fps,
    }


def extract_frames_for_archive(archive_root: Path, overwrite: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for session_dir in _session_dirs(archive_root):
        results.append(extract_frames_for_session(session_dir, overwrite=overwrite))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract sampled PIWM frames from generated videos.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--session-dir", type=Path)
    group.add_argument("--archive-root", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--index-out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.session_dir:
        results = [extract_frames_for_session(args.session_dir, overwrite=args.overwrite)]
    else:
        results = extract_frames_for_archive(args.archive_root, overwrite=args.overwrite)

    if args.index_out:
        _write_jsonl(results, args.index_out)

    summary = {
        "n_sessions": len(results),
        "n_sampled_frames": sum(item["n_sampled_frames"] for item in results),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _frame_sampling_plan(prompt: dict[str, Any]) -> list[dict[str, Any]]:
    plan = prompt.get("frame_sampling_plan") or DEFAULT_PLAN
    if not isinstance(plan, list) or not plan:
        raise ValueError("frame_sampling_plan must be a non-empty list")
    return plan


def _session_dirs(archive_root: Path) -> list[Path]:
    if not archive_root.exists():
        return []
    return [
        path
        for path in sorted(archive_root.iterdir())
        if path.is_dir() and not path.name.startswith("_")
    ]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count


def _load_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for extract_frames.py. Install opencv-python or provide ffmpeg wrapper.") from exc
    return cv2


if __name__ == "__main__":
    raise SystemExit(main())
