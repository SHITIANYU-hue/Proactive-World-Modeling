"""Run Kling generation for PIWM action-continuation prompts."""

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

DEFAULT_PROMPT_INDEX = Path("Archive_continuation_prompts_pilot30/_continuation_prompt_index.jsonl")
DEFAULT_PARENT_ARCHIVE_ROOT = Path("Archive_generated_pilot30")
DEFAULT_SUMMARY = Path("Archive_generated_pilot30/_continuation_batch_summary.json")


def run_batch(
    prompt_index: Path,
    parent_archive_root: Path,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
    reuse_existing: bool = False,
    continue_on_error: bool = True,
    model: str = "kling-v3.0-t2v",
    duration: int = 5,
    mode: str = "pro",
) -> dict[str, Any]:
    rows = _read_jsonl(prompt_index)
    results: list[dict[str, Any]] = []
    if not dry_run and not reuse_existing:
        _require_kling_env()

    for row in rows:
        result = _run_one(
            row,
            parent_archive_root=parent_archive_root,
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
    summary["parent_archive_root"] = parent_archive_root.as_posix()
    summary["dry_run"] = dry_run
    summary["results"] = results
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Kling for PIWM continuation prompt indexes.")
    parser.add_argument("--prompt-index", type=Path, default=DEFAULT_PROMPT_INDEX)
    parser.add_argument("--parent-archive-root", type=Path, default=DEFAULT_PARENT_ARCHIVE_ROOT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--model", default="kling-v3.0-t2v")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--mode", default="pro")
    args = parser.parse_args(argv)

    summary = run_batch(
        args.prompt_index,
        args.parent_archive_root,
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
    parent_archive_root: Path,
    dry_run: bool,
    overwrite: bool,
    reuse_existing: bool,
    model: str,
    duration: int,
    mode: str,
) -> dict[str, Any]:
    parent_state_id = row["parent_state_id"]
    prompt_path = Path(row["prompt_path"])
    continuation_prompt = _read_json(prompt_path)
    continuation_dir = parent_archive_root / parent_state_id / "continuations" / _continuation_dir_name(continuation_prompt)
    base = {
        "continuation_id": row["continuation_id"],
        "parent_state_id": parent_state_id,
        "candidate_action": row["candidate_action"],
        "continuation_role": row["continuation_role"],
        "continuation_viewpoint": row["continuation_viewpoint"],
        "expected_next_state": row["expected_next_state"],
        "expected_reward": row["expected_reward"],
        "prompt_path": prompt_path.as_posix(),
        "continuation_dir": continuation_dir.as_posix(),
    }
    try:
        continuation_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(prompt_path, continuation_dir / "continuation_prompt.json")
        temp_prompt_path = continuation_dir / "_kling_prompt.json"
        temp_prompt_path.write_text(
            json.dumps(_kling_compatible_prompt(continuation_prompt, parent_archive_root), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if reuse_existing and not dry_run and (continuation_dir / "video.mp4").exists():
            extraction = extract_frames.extract_frames_for_session(continuation_dir, overwrite=overwrite)
            _write_manual_review_template(continuation_dir, continuation_prompt)
            report = qa_gate.run_qa_for_continuation(continuation_dir, overwrite=True)
            return {
                **base,
                "status": "reused_existing_qa_report_written",
                "generation": {"video_path": (continuation_dir / "video.mp4").as_posix(), "reused_existing": True},
                "extraction": extraction,
                "qa_overall_pass": report["overall_pass"],
                "qa_manual_review_required": report["manual_review_required"],
                "qa_rejection_reason": report["rejection_reason"],
            }

        command = [
            "node",
            "kling/generate_session.js",
            "--prompt",
            temp_prompt_path.as_posix(),
            "--out-root",
            continuation_dir.parent.as_posix(),
            "--out-session",
            continuation_dir.name,
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

        extraction = extract_frames.extract_frames_for_session(continuation_dir, overwrite=overwrite)
        _write_manual_review_template(continuation_dir, continuation_prompt)
        report = qa_gate.run_qa_for_continuation(continuation_dir, overwrite=True)
        return {
            **result,
            "status": "qa_report_written",
            "extraction": extraction,
            "qa_overall_pass": report["overall_pass"],
            "qa_manual_review_required": report["manual_review_required"],
            "qa_rejection_reason": report["rejection_reason"],
        }
    except Exception as exc:  # noqa: BLE001 - batch summaries should preserve failures.
        return {**base, "status": "error", "error": str(exc)}


def _kling_compatible_prompt(prompt: dict[str, Any], parent_archive_root: Path) -> dict[str, Any]:
    parent_prompt_path = parent_archive_root / prompt["parent_state_id"] / "prompt.json"
    parent_prompt = _read_json(parent_prompt_path)
    return {
        "session_id": _continuation_dir_name(prompt),
        "product_category": prompt["product_category"],
        "persona": parent_prompt["persona"],
        "aida_stage": parent_prompt["aida_stage"],
        "target_cue": parent_prompt["target_cue"],
        "viewpoint": prompt["continuation_viewpoint"],
        "duration_seconds": prompt.get("duration_seconds", 5),
        "training_input_mode": "action_continuation_single_turn",
        "frame_sampling_plan": prompt["frame_sampling_plan"],
        "kling_prompt": prompt["kling_prompt"],
        "kling_prompt_sections": prompt["kling_prompt_sections"],
    }


def _write_manual_review_template(continuation_dir: Path, prompt: dict[str, Any]) -> None:
    template_path = continuation_dir / "qa_manual_review.template.json"
    if template_path.exists():
        return
    viewpoint = prompt.get("continuation_viewpoint", "salesperson_observable")
    visibility_fields = qa_gate.CONTINUATION_REQUIRED_VISIBILITY.get(viewpoint, [])
    reaction_fields = qa_gate.CONTINUATION_REACTION_CHECKLIST.get(prompt.get("expected_next_state"), [])
    template = {
        "reaction_visible": None,
        "reaction_matches_expected_state": None,
        "pre_action_continuity_pass": None,
        "no_scene_change": None,
        "no_new_subjects": None,
        "viewpoint_pass": None,
        "required_visibility": {field: None for field in visibility_fields},
        "reaction_checklist": {field: None for field in reaction_fields},
        "reviewer_notes": "",
    }
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _continuation_dir_name(prompt: dict[str, Any]) -> str:
    return f"{prompt['continuation_role']}_{prompt['candidate_action']}"


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(result["status"] for result in results)
    by_viewpoint: dict[str, Counter[str]] = defaultdict(Counter)
    by_role: dict[str, Counter[str]] = defaultdict(Counter)
    for result in results:
        viewpoint = result.get("continuation_viewpoint") or "unknown"
        role = result.get("continuation_role") or "unknown"
        by_viewpoint[viewpoint]["n"] += 1
        by_role[role]["n"] += 1
        if result.get("qa_overall_pass") is True:
            by_viewpoint[viewpoint]["qa_pass"] += 1
            by_role[role]["qa_pass"] += 1
        if result.get("qa_manual_review_required") is True:
            by_viewpoint[viewpoint]["manual_review_required"] += 1
            by_role[role]["manual_review_required"] += 1
        if result.get("status") == "error":
            by_viewpoint[viewpoint]["error"] += 1
            by_role[role]["error"] += 1
    return {
        "n_continuations": len(results),
        "n_error": status_counts["error"],
        "status_counts": dict(sorted(status_counts.items())),
        "viewpoint_counts": {key: dict(value) for key, value in sorted(by_viewpoint.items())},
        "role_counts": {key: dict(value) for key, value in sorted(by_role.items())},
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _require_kling_env() -> None:
    missing = [
        name
        for name in ("KLINGAI_ACCESS_KEY", "KLINGAI_SECRET_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(f"missing Kling environment variable(s): {', '.join(missing)}")


if __name__ == "__main__":
    raise SystemExit(main())
