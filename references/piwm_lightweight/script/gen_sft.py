#!/usr/bin/env python3
"""
gen_sft.py — Convert data/labeled/ to ms-swift training JSONL.

Reads each data/labeled/piwm_NNN.json and produces:
  data/sft/stage1.jsonl   — state identification
  data/sft/stage2.jsonl   — action selection
  data/sft/joint.jsonl    — stage1 + stage2 combined

Frames are extracted from data/videos/synth/piwm_NNN.mp4 if not already present.

Usage:
  python script/gen_sft.py
  python script/gen_sft.py --dry-run
  python script/gen_sft.py --stage 1
  python script/gen_sft.py --stage 2
  python script/gen_sft.py --overwrite-frames
"""

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent
LABELED_DIR = REPO / "data" / "labeled"
VIDEO_DIR = REPO / "data" / "videos" / "synth"
FRAMES_DIR = REPO / "data" / "frames"
SFT_DIR = REPO / "data" / "sft"

TIMESTAMPS = [0, 2, 5, 8, 10]

STATE_FIELDS = ["aida_stage", "bdi", "observable_behavior", "facial_expression", "body_posture"]

STAGE1_SYSTEM = (
    "你是一个用于智能零售终端的顾客状态预测模型（Stage-1）。\n\n"
    "输入：顾客与终端交互前的 5 帧关键帧，时间戳分别为 0s / 2s / 5s / 8s / 10s。\n\n"
    "输出一个 JSON 对象，字段：aida_stage（attention/interest/desire/action）、"
    "bdi（belief/desire/intention）、observable_behavior、facial_expression、body_posture。\n\n"
    "约束：只依据可见线索，不臆造商品或身份；不输出机器动作；只输出合法 JSON。"
)

STAGE2_SYSTEM = (
    "你是一个用于智能零售终端的动作选择模型（Stage-2）。\n\n"
    "输入：5 帧关键帧 + 当前顾客 state（JSON）+ 候选动作列表（已按 aida_stage 过滤）。\n\n"
    "对每个候选动作预测顾客下一步 state（next_aida_stage + next_bdi），并打分（score 1–5，"
    "best_action 固定为 5）。最后给出 best_action。\n\n"
    "约束：outcomes 覆盖所有候选；best_action 必须来自候选列表；next_bdi 用自然语言，"
    "不含动作名或内部标签；不输出 preference_score 或 delta 值；只输出合法 JSON。"
)


def extract_frames(session_id: str, overwrite: bool = False) -> None:
    video = VIDEO_DIR / f"{session_id}.mp4"
    if not video.exists():
        print(f"  [skip] video not found: {video}")
        return
    out_dir = FRAMES_DIR / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for ts in TIMESTAMPS:
        out = out_dir / f"t{ts:02d}.jpg"
        if out.exists() and not overwrite:
            continue
        subprocess.run(
            ["ffmpeg", "-ss", str(ts), "-i", str(video),
             "-frames:v", "1", "-q:v", "2", str(out), "-y"],
            capture_output=True, check=True,
        )


def frame_paths(session_id: str) -> list[str]:
    d = FRAMES_DIR / session_id
    return [str(d.relative_to(REPO) / f"t{ts:02d}.jpg") for ts in TIMESTAMPS]


def _scores_from_preference(outcomes: dict, best_action: str) -> dict[str, int]:
    """Backward compat for old labeled data that has preference_score but no score."""
    others = sorted(
        [(act, o.get("preference_score", 0)) for act, o in outcomes.items() if act != best_action],
        key=lambda x: x[1], reverse=True,
    )
    n = len(others)
    scores: dict[str, int] = {best_action: 5}
    for i, (act, _) in enumerate(others):
        # Spread non-best across 1–4: n=1→2, n=2→3/1, n=3→4/2/1
        scores[act] = max(1, 4 - i * (3 // max(n, 1)))
    return scores


def build_stage1(record: dict) -> dict:
    sid = record["session_id"]
    state = {k: record[k] for k in STATE_FIELDS}
    image_tokens = "<image>" * len(TIMESTAMPS)
    return {
        "images": frame_paths(sid),
        "messages": [
            {"role": "system", "content": STAGE1_SYSTEM},
            {"role": "user", "content": (
                f"{image_tokens}"
                "以上为顾客与终端交互前的 5 帧关键帧（0s / 2s / 5s / 8s / 10s）。"
                "请推断当前顾客 state。"
            )},
            {"role": "assistant", "content": json.dumps(state, ensure_ascii=False)},
        ],
        "meta": {
            "source_id": sid,
            "viewpoint": record.get("viewpoint", "terminal_observable"),
            "split": "train",
            "stage": "stage1",
            "aida_stage": record["aida_stage"],
        },
    }


def build_stage2(record: dict) -> dict:
    sid = record["session_id"]
    state = {k: record[k] for k in STATE_FIELDS}
    best = record["best_action"]
    candidates = record["candidate_actions"]
    outcomes_raw = record["outcomes"]
    # New labeled data has LLM-assigned score directly; fall back for old data.
    use_preference = any("score" not in outcomes_raw[act] for act in candidates)
    fallback_scores = _scores_from_preference(outcomes_raw, best) if use_preference else {}

    outcomes_out = {}
    for act in candidates:
        raw = outcomes_raw[act]
        outcomes_out[act] = {
            "next_aida_stage": raw["next_aida_stage"],
            "next_bdi": raw["next_bdi"],
            "score": raw["score"] if "score" in raw else fallback_scores[act],
        }
    assistant = json.dumps(
        {"outcomes": outcomes_out, "best_action": best}, ensure_ascii=False
    )

    image_tokens = "<image>" * len(TIMESTAMPS)
    user_text = (
        f"{image_tokens}"
        f"# 当前顾客 state\n{json.dumps(state, ensure_ascii=False)}\n\n"
        f"# 候选动作\n{json.dumps(candidates, ensure_ascii=False)}\n\n"
        "请对每个候选动作预测顾客下一步 state 并打分（1–5），然后给出 best_action。"
    )

    return {
        "images": frame_paths(sid),
        "messages": [
            {"role": "system", "content": STAGE2_SYSTEM},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant},
        ],
        "meta": {
            "source_id": sid,
            "viewpoint": record.get("viewpoint", "terminal_observable"),
            "split": "train",
            "stage": "stage2",
            "aida_stage": record["aida_stage"],
            "candidate_actions": candidates,
        },
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ms-swift SFT JSONL from labeled data.")
    parser.add_argument("--dry-run", action="store_true", help="Print sample(s), no file output.")
    parser.add_argument("--stage", type=int, choices=[1, 2], default=None, help="Generate only Stage-1 or Stage-2.")
    parser.add_argument("--id", default=None, help="Session ID to inspect in dry-run (e.g. piwm_817).")
    parser.add_argument("--overwrite-frames", action="store_true", help="Re-extract frames even if they exist.")
    args = parser.parse_args()

    if args.id:
        labeled_files = [LABELED_DIR / f"{args.id}.json"]
    else:
        labeled_files = sorted(LABELED_DIR.glob("piwm_*.json"))
    stage1, stage2 = [], []

    for lf in labeled_files:
        record = json.loads(lf.read_text())
        sid = record["session_id"]

        if not args.dry_run:
            extract_frames(sid, overwrite=args.overwrite_frames)

        if args.stage in (None, 1):
            stage1.append(build_stage1(record))
        if args.stage in (None, 2):
            stage2.append(build_stage2(record))

    if args.dry_run:
        if stage1:
            print("=== Stage-1 sample ===")
            print(json.dumps(stage1[0], ensure_ascii=False, indent=2))
        if stage2:
            print("\n=== Stage-2 sample ===")
            print(json.dumps(stage2[0], ensure_ascii=False, indent=2))
        return

    SFT_DIR.mkdir(parents=True, exist_ok=True)

    if stage1:
        p = SFT_DIR / "stage1.jsonl"
        write_jsonl(p, stage1)
        print(f"stage1: {len(stage1):>3} records → {p}")

    if stage2:
        p = SFT_DIR / "stage2.jsonl"
        write_jsonl(p, stage2)
        print(f"stage2: {len(stage2):>3} records → {p}")

    if stage1 and stage2:
        p = SFT_DIR / "joint.jsonl"
        write_jsonl(p, stage1 + stage2)
        print(f"joint:  {len(stage1) + len(stage2):>3} records → {p}")


if __name__ == "__main__":
    main()
