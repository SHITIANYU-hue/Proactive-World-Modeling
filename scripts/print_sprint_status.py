"""Print a read-only PIWM sprint status board.

The script is intentionally dependency-free and never reads or prints
credential-bearing environment variables. It is safe to run on a local checkout
or on the remote data-disk checkout.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_JSONL_FILES = (
    "data/priority_generation_queue/scenario_manifest_priority24.jsonl",
    "data/priority_generation_queue/prompt_index_priority24.jsonl",
    "data/piwm_dataset_pilot30_with_continuations/main_schema.jsonl",
    "data/piwm_dataset_pilot30_with_continuations/state_inference.jsonl",
    "data/piwm_dataset_pilot30_with_continuations/transition_modeling.jsonl",
    "data/piwm_dataset_pilot30_with_continuations/policy_preference.jsonl",
    "data/piwm_dataset_pilot30_with_continuations/world_model_continuation.jsonl",
)

DEFAULT_RESULT_JSONS = (
    "data/priority_generation_queue/kling_batch_priority24_summary.json",
    "data/piwm_dataset_pilot30_with_continuations/_stats.json",
    "data/piwm_results/sft_train_summary.json",
    "data/piwm_results/sprint_summary.json",
    "data/piwm_results/pilot24_zero_shot_baselines.json",
    "data/piwm_results/pilot24_mock_pipeline_eval.json",
)

DEFAULT_CRITICAL_PATHS = (
    "scripts/run_kling_batch.py",
    "scripts/qa_gate.py",
    "piwm_data/build_dataset.py",
    "piwm_train/sft.py",
    "scripts/summarize_sprint_results.py",
    "Archive_prompts_priority24",
    "data/priority_generation_queue",
    "data/piwm_results",
)


@dataclass(frozen=True)
class FileStatus:
    path: str
    exists: bool
    kind: str | None = None
    bytes: int | None = None
    lines: int | None = None
    status: str | None = None
    error: str | None = None
    highlights: dict[str, Any] | None = None


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def _json_status(path: Path) -> tuple[str, str | None, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "invalid_json", str(exc), {}

    highlights: dict[str, Any] = {}
    if isinstance(payload, dict):
        for key in (
            "artifact",
            "status",
            "n_sessions",
            "n_sessions_loaded",
            "n_sessions_skipped",
            "n_overall_pass",
            "n_error",
            "mode",
            "train_loss",
            "eval_loss",
        ):
            if key in payload:
                highlights[key] = payload[key]
        if "inputs" in payload and isinstance(payload["inputs"], dict):
            highlights["inputs"] = {
                name: item.get("status")
                for name, item in payload["inputs"].items()
                if isinstance(item, dict)
            }
        if "metrics" in payload and isinstance(payload["metrics"], dict):
            highlights["metrics_keys"] = sorted(payload["metrics"].keys())
    elif isinstance(payload, list):
        highlights["items"] = len(payload)
    return "valid_json", None, highlights


def _file_status(root: Path, rel_path: str, *, count_lines: bool = False, parse_json: bool = False) -> FileStatus:
    path = root / rel_path
    if not path.exists():
        return FileStatus(path=rel_path, exists=False)
    kind = "dir" if path.is_dir() else "file"
    size = None if path.is_dir() else path.stat().st_size
    lines = _line_count(path) if count_lines and path.is_file() else None
    status = None
    error = None
    highlights = None
    if parse_json and path.is_file():
        status, error, highlights = _json_status(path)
    return FileStatus(
        path=rel_path,
        exists=True,
        kind=kind,
        bytes=size,
        lines=lines,
        status=status,
        error=error,
        highlights=highlights,
    )


def _priority_prompt_status(root: Path, prompt_root: str, prompt_index: str) -> dict[str, Any]:
    prompt_dir = root / prompt_root
    index_path = root / prompt_index
    prompt_json_count = len(list(prompt_dir.glob("*/prompt.json"))) if prompt_dir.exists() else 0
    index_rows = _line_count(index_path) if index_path.exists() else 0
    missing_prompt_paths: list[str] = []
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                prompt_path = root / row.get("prompt_path", "")
                if row.get("prompt_path") and not prompt_path.exists():
                    missing_prompt_paths.append(row["prompt_path"])
    return {
        "prompt_root": prompt_root,
        "prompt_index": prompt_index,
        "prompt_json_count": prompt_json_count,
        "index_rows": index_rows,
        "missing_prompt_paths": missing_prompt_paths[:10],
        "n_missing_prompt_paths": len(missing_prompt_paths),
    }


def _gpu_status() -> dict[str, Any]:
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return {"available": False, "status": "nvidia-smi not found"}
    try:
        proc = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "status": f"nvidia-smi failed: {type(exc).__name__}: {exc}"}
    if proc.returncode != 0:
        return {"available": False, "status": proc.stderr.strip() or f"nvidia-smi exit {proc.returncode}"}
    gpus = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 5:
            gpus.append(
                {
                    "index": parts[0],
                    "name": parts[1],
                    "memory_used_mib": parts[2],
                    "memory_total_mib": parts[3],
                    "utilization_gpu_percent": parts[4],
                }
            )
    return {"available": True, "gpus": gpus}


def collect_status(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    return {
        "root": root.as_posix(),
        "critical_paths": [
            _file_status(root, rel_path).__dict__
            for rel_path in args.critical_path
        ],
        "jsonl_counts": [
            _file_status(root, rel_path, count_lines=True).__dict__
            for rel_path in args.jsonl
        ],
        "priority_prompts": _priority_prompt_status(root, args.priority_prompt_root, args.priority_prompt_index),
        "result_jsons": [
            _file_status(root, rel_path, parse_json=True).__dict__
            for rel_path in args.result_json
        ],
        "gpu": _gpu_status(),
    }


def _print_table(title: str, rows: list[dict[str, Any]], columns: tuple[str, ...]) -> None:
    print(f"\n## {title}")
    print(" | ".join(columns))
    print(" | ".join("---" for _ in columns))
    for row in rows:
        print(" | ".join(str(row.get(column, "")) for column in columns))


def print_human(status: dict[str, Any]) -> None:
    print(f"# PIWM sprint status\nroot: {status['root']}")
    _print_table("critical paths", status["critical_paths"], ("path", "exists", "kind", "bytes"))
    _print_table("jsonl counts", status["jsonl_counts"], ("path", "exists", "lines", "bytes"))

    prompts = status["priority_prompts"]
    print("\n## priority prompts")
    for key in ("prompt_root", "prompt_index", "prompt_json_count", "index_rows", "n_missing_prompt_paths"):
        print(f"{key}: {prompts[key]}")
    if prompts["missing_prompt_paths"]:
        print("missing_prompt_paths_sample:")
        for path in prompts["missing_prompt_paths"]:
            print(f"- {path}")

    print("\n## result jsons")
    for item in status["result_jsons"]:
        print(f"- {item['path']}: exists={item['exists']} status={item.get('status')}")
        if item.get("error"):
            print(f"  error: {item['error']}")
        if item.get("highlights"):
            print(f"  highlights: {json.dumps(item['highlights'], ensure_ascii=False, sort_keys=True)}")

    print("\n## gpu")
    gpu = status["gpu"]
    if not gpu["available"]:
        print(gpu["status"])
    else:
        for item in gpu["gpus"]:
            print(
                f"gpu{item['index']} {item['name']} "
                f"mem={item['memory_used_mib']}/{item['memory_total_mib']}MiB "
                f"util={item['utilization_gpu_percent']}%"
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--priority-prompt-root", default="Archive_prompts_priority24")
    parser.add_argument("--priority-prompt-index", default="data/priority_generation_queue/prompt_index_priority24.jsonl")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--jsonl", action="append", default=list(DEFAULT_JSONL_FILES))
    parser.add_argument("--result-json", action="append", default=list(DEFAULT_RESULT_JSONS))
    parser.add_argument("--critical-path", action="append", default=list(DEFAULT_CRITICAL_PATHS))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    status = collect_status(args)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
