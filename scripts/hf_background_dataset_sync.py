#!/usr/bin/env python3
"""Resumable Hugging Face dataset uploader for PIWM artifacts."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi


REPO_ID = "GameFreshMan/PIWM"
REPO_TYPE = "dataset"
STAGE = Path("local_artifacts/hf_upload_stage_20260531")
LOG_PREFIX = "[hf-sync]"


def iter_stage_files() -> list[tuple[str, Path, int]]:
    files: list[tuple[str, Path, int]] = []
    for path in STAGE.rglob("*"):
        if not path.is_file():
            continue
        path_str = str(path)
        if ".cache/huggingface" in path_str:
            continue
        if path.name == ".DS_Store" or path.name.startswith("._"):
            continue
        rel = path.relative_to(STAGE).as_posix()
        files.append((rel, path, path.stat().st_size))
    return files


def main() -> int:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print(f"{LOG_PREFIX} missing HF_TOKEN", flush=True)
        return 2

    if not STAGE.exists():
        print(f"{LOG_PREFIX} missing staging dir: {STAGE}", flush=True)
        return 2

    api = HfApi(token=token)
    all_files = iter_stage_files()
    print(f"{LOG_PREFIX} stage_files={len(all_files)}", flush=True)

    uploaded = 0
    failed_rounds = 0
    while True:
        try:
            repo_files = set(api.list_repo_files(REPO_ID, repo_type=REPO_TYPE))
        except Exception as exc:
            failed_rounds += 1
            print(f"{LOG_PREFIX} list_repo_files failed: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(min(300, 15 * failed_rounds))
            continue

        missing = [(rel, path, size) for rel, path, size in all_files if rel not in repo_files]
        missing.sort(key=lambda item: (-item[2], item[0]))
        remaining_bytes = sum(size for _, _, size in missing)
        print(
            f"{LOG_PREFIX} missing={len(missing)} remaining_bytes={remaining_bytes} uploaded_this_run={uploaded}",
            flush=True,
        )
        if not missing:
            print(f"{LOG_PREFIX} complete", flush=True)
            return 0

        rel, path, size = missing[0]
        print(f"{LOG_PREFIX} upload size={size} path={rel}", flush=True)
        try:
            api.upload_file(
                path_or_fileobj=str(path),
                path_in_repo=rel,
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                commit_message=f"Upload PIWM dataset artifact: {rel}",
            )
            uploaded += 1
            failed_rounds = 0
            print(f"{LOG_PREFIX} uploaded path={rel}", flush=True)
        except Exception as exc:
            failed_rounds += 1
            print(f"{LOG_PREFIX} upload failed path={rel}: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(min(300, 20 * failed_rounds))


if __name__ == "__main__":
    raise SystemExit(main())
