#!/usr/bin/env python3
"""
gen_scores.py — Add LLM 1-5 scores to existing labeled JSONs.

Reads data/labeled/piwm_NNN.json, sends manifest + existing outcomes to the
LLM for scoring only (no BDI or next_stage regeneration), writes scores back.

Usage:
  python script/gen_scores.py --dry-run
  python script/gen_scores.py
  python script/gen_scores.py data/labeled/piwm_001.json
"""

import argparse
import json
import sys
from pathlib import Path
from openai import OpenAI

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
LABELED_DIR = REPO_ROOT / "data" / "labeled"
MAX_RETRIES = 2

SCORE_PROMPT = """你是一个零售行为专家，正在对智能零售终端的候选动作进行质量评分。

# 评分标准（score，1–5 整数）
5 — 最优：直接命中当前顾客最关键摩擦点，对购买进程推进最明显
4 — 较优：正向推进，但不是当前状态最契合的选择
3 — 中性：轻微正向影响或无显著效果
2 — 偏弱：帮助有限，时机或方向略偏
1 — 不合适：打断顾客节奏，或明显误判当前需求

# 评分约束
- 有且只有一个候选的 score=5（即 best_action）
- 其余候选的 score 范围是 1–4，可以有并列分值

# 顾客当前状态
{state_json}

# 候选动作及预测结果
{outcomes_json}

根据以上信息，为每个候选动作打分。只输出 JSON，格式如下：
{{"scores": {{"action_1": 5, "action_2": 3, "action_3": 1}}}}"""

RETRY_PROMPT = """上一轮输出存在以下问题，请修正后重新输出：

{errors}

只输出修正后的 JSON。"""

STATE_FIELDS = ["aida_stage", "bdi", "observable_behavior", "facial_expression", "body_posture"]


def validate_scores(candidates: list[str], scores: dict) -> list[str]:
    errors = []
    for act in candidates:
        if act not in scores:
            errors.append(f"缺少候选 {act!r} 的评分")
            continue
        s = scores[act]
        if isinstance(s, float) and s == int(s):
            s = int(s)
        if not isinstance(s, int) or not (1 <= s <= 5):
            errors.append(f"[{act}] score={s!r} 不合法，必须是 1–5 的整数")
    fives = [a for a, s in scores.items() if int(s) == 5]
    if len(fives) == 0:
        errors.append("没有候选的 score=5，必须有且只有一个")
    elif len(fives) > 1:
        errors.append(f"有多个候选 score=5：{fives}，只能有一个")
    return errors


def score_record(record: dict, model: str = "gpt-4.1") -> dict[str, int]:
    client = OpenAI()
    candidates = record["candidate_actions"]
    outcomes = record["outcomes"]

    state = {k: record[k] for k in STATE_FIELDS if k in record}
    outcomes_for_prompt = {
        act: {
            "next_aida_stage": outcomes[act]["next_aida_stage"],
            "next_bdi": outcomes[act]["next_bdi"],
        }
        for act in candidates
    }

    prompt = SCORE_PROMPT.format(
        state_json=json.dumps(state, ensure_ascii=False, indent=2),
        outcomes_json=json.dumps(outcomes_for_prompt, ensure_ascii=False, indent=2),
    )

    messages = [{"role": "user", "content": prompt}]

    for attempt in range(MAX_RETRIES + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        scores = parsed.get("scores", {})

        # Normalize float scores
        scores = {k: int(v) if isinstance(v, float) else v for k, v in scores.items()}

        errors = validate_scores(candidates, scores)
        if not errors:
            return scores

        if attempt < MAX_RETRIES:
            error_text = "\n".join(f"- {e}" for e in errors)
            print(f"  [retry {attempt + 1}] {len(errors)} errors", file=sys.stderr)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": RETRY_PROMPT.format(errors=error_text)})
        else:
            raise ValueError(f"scoring failed after {MAX_RETRIES} retries:\n" +
                             "\n".join(f"- {e}" for e in errors))

    return scores


def needs_scoring(record: dict) -> bool:
    outcomes = record.get("outcomes", {})
    candidates = record.get("candidate_actions", [])
    return any("score" not in outcomes.get(act, {}) for act in candidates)


def process_file(path: Path, model: str, dry_run: bool) -> bool:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not needs_scoring(record):
        return False
    if dry_run:
        return True
    scores = score_record(record, model=model)
    for act, s in scores.items():
        if act in record["outcomes"]:
            record["outcomes"][act]["score"] = s
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Add LLM 1-5 scores to labeled JSONs.")
    parser.add_argument("paths", nargs="*",
                        help="Labeled JSON files. Defaults to all data/labeled/piwm_*.json missing scores.")
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files that need scoring, no API calls.")
    args = parser.parse_args()

    if args.paths:
        paths = [Path(p) for p in args.paths]
    else:
        paths = [
            p for p in sorted(LABELED_DIR.glob("piwm_*.json"))
            if needs_scoring(json.loads(p.read_text(encoding="utf-8")))
        ]

    if not paths:
        print("All labeled files already have scores.", file=sys.stderr)
        return

    print(f"{'[dry-run] ' if args.dry_run else ''}Processing {len(paths)} file(s):", file=sys.stderr)
    for p in paths:
        print(f"  {p.name}", file=sys.stderr)

    if args.dry_run:
        return

    for path in paths:
        try:
            changed = process_file(path, model=args.model, dry_run=False)
            if changed:
                print(f"  ✓ {path.name}", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ {path.name}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
