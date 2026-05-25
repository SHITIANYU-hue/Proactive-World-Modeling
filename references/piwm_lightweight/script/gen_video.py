#!/usr/bin/env python3
"""Generate videos from pre-rendered prompt files via Kling API."""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = REPO_ROOT / "data" / "prompts"
VIDEO_DIR = REPO_ROOT / "data" / "videos" / "synth"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_kling_token() -> str:
    static_token = os.environ.get("KLING_API_KEY")
    if static_token:
        return static_token

    access_key = os.environ.get("KLING_ACCESS_KEY")
    secret_key = os.environ.get("KLING_SECRET_KEY")
    if not access_key or not secret_key:
        raise RuntimeError("Set KLING_API_KEY or KLING_ACCESS_KEY + KLING_SECRET_KEY")

    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": access_key,
        "exp": now + 1800,
        "nbf": now - 5,
    }

    signing_input = ".".join(
        [
            _b64url(json.dumps(header, separators=(",", ":"), ensure_ascii=True).encode("utf-8")),
            _b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _extract_task_id(data: dict) -> str | None:
    for key in ("task_id", "id"):
        if data.get(key):
            return str(data[key])
    nested = data.get("data", {})
    if isinstance(nested, dict):
        for key in ("task_id", "id"):
            if nested.get(key):
                return str(nested[key])
    return None


def _extract_video_url(data: dict, expected_task_id: str | None = None, expected_external_task_id: str | None = None) -> str | None:
    if data.get("video_url"):
        return str(data["video_url"])
    nested = data.get("data", {})
    if isinstance(nested, list) and nested:
        for item in nested:
            if isinstance(item, dict):
                if expected_task_id and str(item.get("task_id", "")) != str(expected_task_id):
                    continue
                if expected_external_task_id:
                    task_info = item.get("task_info", {})
                    if isinstance(task_info, dict) and task_info.get("external_task_id") != expected_external_task_id:
                        continue
                video_url = _extract_video_url(
                    {"data": item},
                    expected_task_id=expected_task_id,
                    expected_external_task_id=expected_external_task_id,
                )
                if video_url:
                    return video_url
    if isinstance(nested, dict):
        if nested.get("video_url"):
            return str(nested["video_url"])
        task_result = nested.get("task_result")
        if isinstance(task_result, dict):
            if task_result.get("video_url"):
                return str(task_result["video_url"])
            videos = task_result.get("videos")
            if isinstance(videos, list) and videos:
                first = videos[0]
                if isinstance(first, dict):
                    if first.get("video_url"):
                        return str(first["video_url"])
                    if first.get("url"):
                        return str(first["url"])
            if task_result.get("url"):
                return str(task_result["url"])
        resource = nested.get("resource")
        if isinstance(resource, dict) and resource.get("video_url"):
            return str(resource["video_url"])
        videos = nested.get("videos")
        if isinstance(videos, list) and videos:
            first = videos[0]
            if isinstance(first, dict) and first.get("video_url"):
                return str(first["video_url"])
            if isinstance(first, dict) and first.get("url"):
                return str(first["url"])
    return None


def _is_terminal_failure(data: dict) -> bool:
    text = json.dumps(data, ensure_ascii=False).lower()
    return any(token in text for token in ["failed", "\"status\":\"fail\"", "\"status\":\"error\""])


def _is_still_processing(data: dict) -> bool:
    text = json.dumps(data, ensure_ascii=False).lower()
    return any(token in text for token in ["submitted", "processing", "pending", "running", "queue"])


def call_kling(prompt: str, session_id: str, output_dir: str, model: str = "kling-v2-6") -> str:
    import requests

    base_url = os.environ.get("KLING_BASE_URL", "https://api-singapore.klingai.com").rstrip("/")
    endpoint = f"{base_url}/v1/videos/text2video"
    token = _make_kling_token()
    mode = os.environ.get("KLING_VIDEO_MODE", "std")
    aspect_ratio = os.environ.get("KLING_ASPECT_RATIO", "16:9")
    duration = os.environ.get("KLING_DURATION", "10")
    sound = os.environ.get("KLING_SOUND", "off")
    payload = {
        "model_name": model,
        "prompt": prompt,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "mode": mode,
        "sound": sound,
        "external_task_id": f"{session_id}-{uuid.uuid4().hex[:8]}",
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = None
    for attempt in range(6):
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=600)
        if resp.status_code != 429:
            break
        wait_seconds = int(os.environ.get("KLING_RATE_LIMIT_WAIT", "180"))
        print(
            f"[kling] create task rate-limited for {session_id}; "
            f"waiting {wait_seconds}s before retry {attempt + 1}/6",
            file=sys.stderr,
        )
        time.sleep(wait_seconds)
    assert resp is not None
    resp.raise_for_status()
    data = resp.json()

    external_task_id = payload["external_task_id"]
    video_url = _extract_video_url(data, expected_external_task_id=external_task_id)
    task_id = _extract_task_id(data)

    if not video_url and not task_id:
        raise RuntimeError(f"Unexpected create-task response: {data}")

    if not video_url and task_id:
        query_candidates = [
            f"{base_url}/v1/videos/text2video/{task_id}",
            f"{base_url}/v1/videos/text2video?task_id={task_id}",
            f"{base_url}/v1/videos/text2video?external_task_id={payload['external_task_id']}",
        ]
        deadline = time.time() + 60 * 20
        last_data = data
        while time.time() < deadline:
            time.sleep(15)
            for query_url in query_candidates:
                try:
                    poll = requests.get(query_url, headers=headers, timeout=600)
                except requests.RequestException:
                    continue
                if poll.status_code == 404:
                    continue
                poll.raise_for_status()
                last_data = poll.json()
                video_url = _extract_video_url(
                    last_data,
                    expected_task_id=task_id,
                    expected_external_task_id=external_task_id,
                )
                if video_url:
                    break
                if _is_terminal_failure(last_data):
                    raise RuntimeError(f"Kling task failed: {last_data}")
            if video_url:
                break
            if not _is_still_processing(last_data):
                raise RuntimeError(f"Kling task returned no video_url: {last_data}")
        if not video_url:
            raise RuntimeError(f"Kling polling timed out: {last_data}")

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{session_id}.mp4")
    with requests.get(video_url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    return out_path


def find_missing_videos() -> list[Path]:
    """Prompt files that do not yet have a generated video."""
    return [
        path
        for path in sorted(PROMPT_DIR.glob("piwm_*.md"))
        if not (VIDEO_DIR / f"{path.stem}.mp4").exists()
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Generate videos from saved prompt files via Kling API. "
                    "Run without arguments to batch-process prompts without videos."
    )
    parser.add_argument(
        "prompt", nargs="?",
        help="Prompt markdown path (use - for stdin). Omit to batch-process data/prompts/*.md."
    )
    parser.add_argument("--video-dir", default=str(VIDEO_DIR))
    parser.add_argument("--kling-model", default="kling-v3")
    parser.add_argument("--dry-run", action="store_true",
                        help="Batch: list prompt files that would be sent. Single: print prompt metadata only.")
    args = parser.parse_args()

    # ── batch mode ──
    if args.prompt is None:
        pending = find_missing_videos()
        if not pending:
            print("All prompts already have videos.", file=sys.stderr)
            return
        print(f"{'[dry-run] would process' if args.dry_run else 'Processing'} "
              f"{len(pending)} file(s):", file=sys.stderr)
        for f in pending:
            print(f"  {f.name}", file=sys.stderr)
        if args.dry_run:
            return
        failed = []
        for f in pending:
            prompt = f.read_text(encoding="utf-8")
            try:
                video_path = call_kling(prompt, f.stem, args.video_dir, args.kling_model)
                print(f"  ✓ saved {video_path}", file=sys.stderr)
            except Exception as e:
                print(f"  ✗ {f.name}: {e}", file=sys.stderr)
                failed.append(f.name)
        if failed:
            print(f"\n{len(failed)} failed: {', '.join(failed)}", file=sys.stderr)
        return

    # ── single-file mode ──
    if args.prompt == "-":
        prompt = sys.stdin.read()
        session_id = "stdin_prompt"
    else:
        prompt_path = Path(args.prompt)
        prompt = prompt_path.read_text(encoding="utf-8")
        session_id = prompt_path.stem

    if args.dry_run:
        print(f"Would generate video for {session_id} using {args.kling_model}")
        return

    video_path = call_kling(prompt, session_id, args.video_dir, args.kling_model)
    print(f"Video saved to {video_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
