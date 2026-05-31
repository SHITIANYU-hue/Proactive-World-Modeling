#!/usr/bin/env python3
"""Resumable Hugging Face dataset uploader for PIWM artifacts."""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi


REPO_ID = "GameFreshMan/PIWM"
REPO_TYPE = "dataset"
STAGE = Path("local_artifacts/hf_upload_stage_20260531")
LOG_PREFIX = "[hf-sync]"
UPLOAD_TIMEOUT_SECONDS = 900
BATCH_MAX_FILES = 100
BATCH_MAX_BYTES = 50 * 1024 * 1024


class UploadTimeout(TimeoutError):
    pass


def _timeout_handler(signum: int, frame: object) -> None:
    raise UploadTimeout(f"upload timed out after {UPLOAD_TIMEOUT_SECONDS}s")


def retry_sleep_seconds(exc: Exception, failed_rounds: int) -> int:
    text = str(exc)
    if "Retry after " in text and " seconds" in text:
        tail = text.split("Retry after ", 1)[1].split(" seconds", 1)[0]
        if tail.strip().isdigit():
            return max(60, int(tail.strip()) + 30)
    if "in " in text and " minutes" in text:
        tail = text.rsplit("in ", 1)[1].split(" minutes", 1)[0]
        if tail.strip().isdigit():
            return max(60, int(tail.strip()) * 60 + 60)
    return min(3600, 60 * max(1, failed_rounds))


def make_batch(missing: list[tuple[str, Path, int]]) -> list[tuple[str, Path, int]]:
    batch: list[tuple[str, Path, int]] = []
    total = 0
    for item in missing:
        _, _, size = item
        if batch and (len(batch) >= BATCH_MAX_FILES or total + size > BATCH_MAX_BYTES):
            break
        batch.append(item)
        total += size
    return batch


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
    signal.signal(signal.SIGALRM, _timeout_handler)
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

        batch = make_batch(missing)
        batch_bytes = sum(size for _, _, size in batch)
        print(
            f"{LOG_PREFIX} upload_batch files={len(batch)} bytes={batch_bytes} "
            f"first={batch[0][0]}",
            flush=True,
        )
        try:
            signal.alarm(UPLOAD_TIMEOUT_SECONDS)
            api.create_commit(
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                operations=[
                    CommitOperationAdd(path_in_repo=rel, path_or_fileobj=str(path))
                    for rel, path, _ in batch
                ],
                commit_message=f"Upload PIWM dataset artifacts ({len(batch)} files)",
            )
            signal.alarm(0)
            uploaded += len(batch)
            failed_rounds = 0
            print(f"{LOG_PREFIX} uploaded_batch files={len(batch)}", flush=True)
        except Exception as exc:
            signal.alarm(0)
            failed_rounds += 1
            sleep_s = retry_sleep_seconds(exc, failed_rounds)
            print(
                f"{LOG_PREFIX} upload_batch failed: {type(exc).__name__}: {exc}; "
                f"sleep={sleep_s}s",
                flush=True,
            )
            time.sleep(sleep_s)


if __name__ == "__main__":
    raise SystemExit(main())
