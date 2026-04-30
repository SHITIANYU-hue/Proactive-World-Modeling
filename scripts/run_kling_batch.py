"""Run a controlled Kling generation batch for PIWM prompt indexes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from scripts import extract_frames, qa_gate

DEFAULT_PROMPT_INDEX = Path("Archive_prompts_viewpoint_review/_prompt_index.jsonl")
DEFAULT_OUT_ROOT = Path("Archive_generated_viewpoint_review")
DEFAULT_SUMMARY = Path("Archive_generated_viewpoint_review/_batch_summary.json")


def run_batch(
    prompt_index: Path,
    out_root: Path,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
    reuse_existing: bool = False,
    continue_on_error: bool = True,
    model: str = "kling-v3.0-t2v",
    duration: int = 10,
    mode: str = "pro",
) -> dict[str, Any]:
    rows = _read_jsonl(prompt_index)
    out_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    if not dry_run and not reuse_existing:
        _require_kling_env()

    for row in rows:
        result = _run_one(
            row,
            out_root=out_root,
            dry_run=dry_run,
            overwrite=overwrite,
            reuse_existing=reuse_existing,
            model=model,
            duration=duration,
            mode=mode,
        )
        results.append(result)
        if result["status"] == "error" and not continue_on_error:
            break

    summary = _summarize(results)
    summary["prompt_index"] = prompt_index.as_posix()
    summary["out_root"] = out_root.as_posix()
    summary["dry_run"] = dry_run
    summary["results"] = results
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a PIWM mixed-view Kling batch.")
    parser.add_argument("--prompt-index", type=Path, default=DEFAULT_PROMPT_INDEX)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse existing session video.mp4 files without calling Kling.",
    )
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--model", default="kling-v3.0-t2v")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--mode", default="pro")
    args = parser.parse_args(argv)

    summary = run_batch(
        args.prompt_index,
        args.out_root,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        reuse_existing=args.reuse_existing,
        continue_on_error=not args.stop_on_error,
        model=args.model,
        duration=args.duration,
        mode=args.mode,
    )
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, ensure_ascii=False, indent=2))
    return 0 if summary["n_error"] == 0 else 1


def _run_one(
    row: dict[str, Any],
    *,
    out_root: Path,
    dry_run: bool,
    overwrite: bool,
    reuse_existing: bool,
    model: str,
    duration: int,
    mode: str,
) -> dict[str, Any]:
    session_id = row["session_id"]
    prompt_path = Path(row["prompt_path"])
    session_dir = out_root / session_id
    base = {
        "session_id": session_id,
        "viewpoint": row.get("viewpoint"),
        "target_cue": row.get("target_cue"),
        "prompt_path": prompt_path.as_posix(),
        "session_dir": session_dir.as_posix(),
    }
    try:
        if reuse_existing and not dry_run and (session_dir / "video.mp4").exists():
            if not (session_dir / "prompt.json").exists():
                session_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(prompt_path, session_dir / "prompt.json")
            generation_path = session_dir / "kling_generation.json"
            if generation_path.exists():
                generation_payload = json.loads(generation_path.read_text(encoding="utf-8"))
            else:
                generation_payload = {"video_path": (session_dir / "video.mp4").as_posix(), "reused_existing": True}
            extraction = extract_frames.extract_frames_for_session(session_dir, overwrite=overwrite)
            _write_manual_review_template(session_dir)
            report = qa_gate.run_qa_for_session(session_dir, overwrite=True)
            return {
                **base,
                "status": "reused_existing_qa_report_written",
                "generation": generation_payload,
                "extraction": extraction,
                "qa_overall_pass": report["overall_pass"],
                "qa_manual_review_required": report["manual_review_required"],
                "qa_viewpoint_pass": report["viewpoint_pass"],
                "qa_rejection_reason": report["rejection_reason"],
            }

        command = [
            "node",
            "kling/generate_session.js",
            "--prompt",
            prompt_path.as_posix(),
            "--out-root",
            out_root.as_posix(),
            "--model",
            model,
            "--duration",
            str(duration),
            "--mode",
            mode,
        ]
        if overwrite:
            command.append("--overwrite")
        if dry_run:
            command.append("--dry-run")

        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        generation_payload = _loads_last_json(completed.stdout)
        result = {
            **base,
            "status": "dry_run" if dry_run else "generated",
            "generation": generation_payload,
        }
        if dry_run:
            return result

        extraction = extract_frames.extract_frames_for_session(session_dir, overwrite=overwrite)
        _write_manual_review_template(session_dir)
        report = qa_gate.run_qa_for_session(session_dir, overwrite=True)
        return {
            **result,
            "status": "qa_report_written",
            "extraction": extraction,
            "qa_overall_pass": report["overall_pass"],
            "qa_manual_review_required": report["manual_review_required"],
            "qa_viewpoint_pass": report["viewpoint_pass"],
            "qa_rejection_reason": report["rejection_reason"],
        }
    except Exception as exc:  # noqa: BLE001 - batch summary should preserve failure and continue.
        return {**base, "status": "error", "error": str(exc)}


def _write_manual_review_template(session_dir: Path) -> None:
    prompt_path = session_dir / "prompt.json"
    if not prompt_path.exists():
        return
    prompt = json.loads(prompt_path.read_text(encoding="utf-8"))
    viewpoint = prompt.get("viewpoint", "salesperson_observable")
    required_fields = qa_gate.VIEWPOINT_REQUIRED_VISIBILITY.get(viewpoint, [])
    template_path = session_dir / "qa_manual_review.template.json"
    if template_path.exists():
        return
    template = {
        "cue_visible_in_video": None,
        "cue_visible_in_sampled_frames": None,
        "physical_consistency_pass": None,
        "extra_subjects": None,
        "viewpoint_pass": None,
        "required_visibility": {field: None for field in required_fields},
        "reviewer_notes": "",
    }
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(result["status"] for result in results)
    by_viewpoint: dict[str, Counter[str]] = defaultdict(Counter)
    for result in results:
        viewpoint = result.get("viewpoint") or "unknown"
        by_viewpoint[viewpoint]["n"] += 1
        if result.get("qa_overall_pass") is True:
            by_viewpoint[viewpoint]["qa_pass"] += 1
        if result.get("qa_manual_review_required") is True:
            by_viewpoint[viewpoint]["manual_review_required"] += 1
        if result.get("status") == "error":
            by_viewpoint[viewpoint]["error"] += 1
    return {
        "n_sessions": len(results),
        "n_error": status_counts["error"],
        "status_counts": dict(sorted(status_counts.items())),
        "viewpoint_counts": {
            viewpoint: dict(counter)
            for viewpoint, counter in sorted(by_viewpoint.items())
        },
    }


def _require_kling_env() -> None:
    missing = [
        name
        for name in ("KLINGAI_ACCESS_KEY", "KLINGAI_SECRET_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(f"missing Kling environment variable(s): {', '.join(missing)}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _loads_last_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.rfind("{")
        if start == -1:
            return {"raw_stdout": text}
        try:
            return json.loads(text[start:])
        except json.JSONDecodeError:
            return {"raw_stdout": text}


if __name__ == "__main__":
    raise SystemExit(main())
