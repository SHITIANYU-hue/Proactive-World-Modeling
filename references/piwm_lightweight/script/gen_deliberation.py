#!/usr/bin/env python3
"""Deliberation: predict action-conditioned outcomes with LLM-assigned 1-5 scores."""

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
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
LABELED_DIR = REPO_ROOT / "data" / "labeled"

MAX_RETRIES = 2
BASELINE = "hold"
STAGE_ORDER = {"attention": 0, "interest": 1, "desire": 2, "action": 3}

def target_act_class(target_act: str) -> str:
    """'Greet:open' → 'greet', 'Hold:ambient' → 'hold', etc."""
    return target_act.split(":")[0].lower() if target_act else ""

CLASS_DESCRIPTIONS: dict[str, str] = {
    "hold":      "静默或低打扰退出——屏幕保持极简状态，不主动发言。适用于顾客已经顺畅自主浏览或操作，不需要干预。",
    "greet":     "开场问候（open）或收尾致谢（close）——适用于顾客刚进入交互范围的轻唤醒，或交易完成后的礼貌收尾。",
    "elicit":    "提问引导——主动询问顾客关注方向（价格/功能/场景）或预算，帮助其聚焦需求。适用于需求尚不明确的阶段。",
    "inform":    "提供信息——展示比较卡、功能演示、商品参数或价格，填补顾客的信息缺口。适用于顾客有明确信息需求时。",
    "recommend": "推荐或安抚——给出方向性推荐（温和或明确），或降低决策压力（如「不用马上定」「慢慢看」），推动顾客收束选择。适用于顾客已有偏好或需要心理减压时。",
}

AIDA_ALLOWED_CLASSES: dict[str, list[str]] = {
    "attention": ["hold", "greet", "elicit", "inform"],
    "interest":  ["hold", "elicit", "inform", "recommend"],
    "desire":    ["hold", "inform", "recommend"],
    "action":    ["hold", "greet", "recommend"],
}


def get_allowed_classes(aida_stage: str) -> list[str]:
    return AIDA_ALLOWED_CLASSES.get(aida_stage, AIDA_ALLOWED_CLASSES["interest"])


def build_allowed_class_desc(allowed: list[str]) -> str:
    return "\n".join(f"- **{cls}**：{CLASS_DESCRIPTIONS.get(cls, cls)}" for cls in allowed)


EXPERT_PROMPT = """你是一个 BDI 认知建模 + 零售行为领域的专家标注员，对 AIDA 购买阶段理论和顾客心理状态迁移有深入理解。

# 背景
智能零售设备内置摄像头持续观察顾客，可主动选择交互动作。
任务：针对当前顾客状态，从下方允许的动作类别（5-class）中选出候选，然后逐一预测 ActionOutcome。

# 当前 AIDA 阶段
{aida_stage}

# 当前阶段允许的动作类别
{allowed_class_desc}

候选选择规则：
- 阶段有 4 个可选类别时，输出 3 个（必须包含 hold）
- 阶段只有 3 个可选类别时，全部输出（必须包含 hold）
- 候选不能重复
- 只能使用上方列出的类别

# 推理方法（每个候选走完整链路）
1. **BDI 因果链**：该动作→更新顾客哪个 belief？激活/抑制哪个 desire？intention 更靠近购买还是后退？
2. **AIDA 迁移**：基于 BDI 变化推断 next_aida_stage
3. **评分**：综合以上推理，给出该动作的 score（1–5 整数），评分标准见下方

# 评分标准（score）
5 — 最优：直接命中当前顾客最关键摩擦点，对购买进程推进最明显
4 — 较优：正向推进，但不是当前状态最契合的选择
3 — 中性：轻微正向影响或无显著效果
2 — 偏弱：帮助有限，时机或方向略偏
1 — 不合适：打断顾客节奏，或明显误判当前需求

评分约束：
- 有且只有一个候选的 score=5，该候选即为 best_action
- 其余候选的 score 范围是 1–4，可以有并列分值

# 动作选择边界
- `greet` 只在顾客刚进入范围尚未开始浏览（open），或交易完成后（close）使用；顾客已在主动浏览时不给高分。
- `elicit` 只在需求模糊、不知道关注哪一类时给高分；顾客已锁定商品时不合适。
- `inform` 只在顾客有具体信息缺口（要比较、要看参数、要确认价格）时给高分；不要在需求仍模糊时展示信息。
- `recommend` 只在顾客已有偏向或需要降压时给高分；不要在需求完全不明确时直接推荐。
- 若顾客当前节奏顺畅、无求助信号，`hold` 可能是最优解，不要为了"显得有帮助"强行干预。

# 一致性约束（输出必须满足）
- next_bdi.intention 必须与 next_aida_stage 语义一致
- 不要在 next_bdi 里写动作名称或内部标签（如 recommend、inform、Greet:open 等）

# 顾客 Manifest
{manifest_json}
{best_action_constraint}

# 输出格式（只输出 JSON，不附加解释或 Markdown）
{{
  "candidate_actions": ["hold", "class_2", "class_3"],
  "outcomes": {{
    "hold": {{
      "next_aida_stage": "...",
      "next_bdi": {{"belief": "...", "desire": "...", "intention": "..."}},
      "score": 2
    }},
    "class_2": {{
      "next_aida_stage": "...",
      "next_bdi": {{"belief": "...", "desire": "...", "intention": "..."}},
      "score": 5
    }},
    "class_3": {{
      "next_aida_stage": "...",
      "next_bdi": {{"belief": "...", "desire": "...", "intention": "..."}},
      "score": 1
    }}
  }},
  "best_action": "class_2"
}}"""

RETRY_PROMPT = """上一轮输出存在以下问题，请逐条修正后重新输出完整 JSON：

{errors}

只输出修正后的 JSON，不附加解释。"""


def validate_outcomes(current_aida: str, candidates: list[str], outcomes: dict) -> list[str]:
    errors = []
    allowed = set(get_allowed_classes(current_aida))
    n_allowed = len(allowed)
    expected_n = 3 if n_allowed >= 4 else n_allowed
    required_outcome_keys = {"next_aida_stage", "next_bdi", "score"}
    required_bdi_keys = {"belief", "desire", "intention"}

    if len(candidates) != expected_n:
        errors.append(f"候选数量应为 {expected_n}，当前为 {len(candidates)}")
    if len(candidates) != len(set(candidates)):
        errors.append("候选类别不能重复")
    if BASELINE not in candidates:
        errors.append(f"缺少基线候选 {BASELINE!r}")
    for cls in candidates:
        if cls not in allowed:
            errors.append(f"[{cls}] 不属于 {current_aida} 阶段允许的类别 {sorted(allowed)}")
    for cls in candidates:
        if cls not in outcomes:
            errors.append(f"缺少候选的 outcome：{cls}")

    for cls, oc in outcomes.items():
        missing = sorted(required_outcome_keys - set(oc))
        if missing:
            errors.append(f"[{cls}] outcome 缺少字段：{', '.join(missing)}")
            continue

        next_bdi = oc.get("next_bdi", {})
        if not isinstance(next_bdi, dict):
            errors.append(f"[{cls}] next_bdi 必须是对象")
            continue
        missing_bdi = sorted(required_bdi_keys - set(next_bdi))
        if missing_bdi:
            errors.append(f"[{cls}] next_bdi 缺少字段：{', '.join(missing_bdi)}")

        next_stage = oc.get("next_aida_stage", "")
        if next_stage not in STAGE_ORDER:
            errors.append(f"[{cls}] next_aida_stage={next_stage!r} 不合法，必须是 {list(STAGE_ORDER)}")

        score = oc.get("score")
        if isinstance(score, float) and score == int(score):
            score = int(score)
        if not isinstance(score, int) or not (1 <= score <= 5):
            errors.append(f"[{cls}] score={score!r} 不合法，必须是 1–5 的整数")

        label_leaks = ["target_act", "response_id", "Recommend:", "Inform:", "Elicit:", "Hold:", "Greet:"]
        bdi_text = " ".join(str(next_bdi.get(k, "")) for k in ("belief", "desire", "intention"))
        for marker in label_leaks:
            if marker in bdi_text:
                errors.append(f"[{cls}] next_bdi 泄漏内部标签：{marker!r}")

    fives = [
        cls for cls, oc in outcomes.items()
        if isinstance(oc.get("score"), (int, float)) and int(oc["score"]) == 5
    ]
    if len(fives) == 0:
        errors.append("没有候选的 score=5，必须有且只有一个")
    elif len(fives) > 1:
        errors.append(f"有多个候选 score=5：{fives}，只能有一个")

    return errors


def clean_outcomes(outcomes: dict) -> dict:
    clean = {}
    for cls, oc in outcomes.items():
        score = oc["score"]
        if isinstance(score, float):
            score = int(score)
        clean[cls] = {
            "next_aida_stage": oc["next_aida_stage"],
            "next_bdi": oc["next_bdi"],
            "score": score,
        }
    return clean


def deliberate(manifest: dict, model: str = "gpt-4.1") -> dict:
    client = OpenAI()
    current_aida = manifest.get("aida_stage", "interest")
    allowed = get_allowed_classes(current_aida)

    forced_best = target_act_class(manifest.get("target_act", ""))
    if forced_best and forced_best in allowed:
        constraint = (
            f"\n# Ground-Truth 约束\n"
            f"本样本的 best_action 已由人工标注确定为 **{forced_best}**，"
            f"score 必须为 5。其余候选的 score 范围 1–4，不得与 best 并列。"
        )
    else:
        constraint = ""

    prompt = EXPERT_PROMPT.format(
        aida_stage=current_aida,
        allowed_class_desc=build_allowed_class_desc(allowed),
        manifest_json=json.dumps(manifest, ensure_ascii=False, indent=2),
        best_action_constraint=constraint,
    )

    messages = [{"role": "user", "content": prompt}]
    last_candidates: list[str] = []
    last_outcomes: dict = {}

    for attempt in range(MAX_RETRIES + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)

        candidates = parsed.get("candidate_actions", [])
        outcomes = parsed.get("outcomes", {})

        errors = validate_outcomes(current_aida, candidates, outcomes)
        last_candidates, last_outcomes = candidates, outcomes

        if not errors:
            break

        if attempt < MAX_RETRIES:
            error_text = "\n".join(f"- {e}" for e in errors)
            print(f"[deliberate] attempt {attempt + 1} failed ({len(errors)} errors), retrying…",
                  file=sys.stderr)
            messages.append({"role": "assistant", "content": raw_content})
            messages.append({"role": "user", "content": RETRY_PROMPT.format(errors=error_text)})
        else:
            error_text = "\n".join(f"- {e}" for e in errors)
            raise ValueError(
                f"validation still failing after {MAX_RETRIES} retries:\n{error_text}"
            )

    if forced_best and forced_best in last_candidates:
        best_action = forced_best
        # Ensure ground-truth best has score=5 and no other does
        for cls in last_candidates:
            if cls == forced_best:
                last_outcomes[cls]["score"] = 5
            elif last_outcomes.get(cls, {}).get("score") == 5:
                last_outcomes[cls]["score"] = 4
    else:
        best_action = next(
            cls for cls in last_candidates
            if int(last_outcomes.get(cls, {}).get("score", 0)) == 5
        )

    return {
        "candidate_actions": last_candidates,
        "outcomes": clean_outcomes(last_outcomes),
        "best_action": best_action,
    }


def find_missing_labeled() -> list[Path]:
    return [
        f for f in sorted(MANIFEST_DIR.glob("piwm_*.json"))
        if not (LABELED_DIR / f.name).exists()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deliberation: predict 5-class outcomes with LLM 1-5 scores. "
                    "Run without arguments to batch-process all un-labeled manifests."
    )
    parser.add_argument("manifest", nargs="?",
                        help="Manifest JSON path (use - for stdin). Omit to batch all data/manifest/ → data/labeled/.")
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--dry-run", action="store_true",
                        help="Single file: print prompt. Batch: list files that would be processed.")
    parser.add_argument("-o", "--output",
                        help=f"Output path (single-file mode only). Default: {LABELED_DIR}/<id>.json. Use '-' for stdout.")
    args = parser.parse_args()

    if args.manifest is None:
        pending = find_missing_labeled()
        if not pending:
            print("All manifests already labeled.", file=sys.stderr)
            return
        print(f"{'[dry-run] would process' if args.dry_run else 'Processing'} "
              f"{len(pending)} file(s):", file=sys.stderr)
        for f in pending:
            print(f"  {f.name}", file=sys.stderr)
        if args.dry_run:
            return
        for f in pending:
            manifest = json.loads(f.read_text(encoding="utf-8"))
            result = deliberate(manifest, model=args.model)
            output = {**manifest, **result}
            out_path = LABELED_DIR / f.name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ {out_path.name}", file=sys.stderr)
        return

    if args.manifest == "-":
        manifest = json.load(sys.stdin)
    else:
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    if args.dry_run:
        current_aida = manifest.get("aida_stage", "interest")
        print(EXPERT_PROMPT.format(
            aida_stage=current_aida,
            allowed_class_desc=build_allowed_class_desc(get_allowed_classes(current_aida)),
            manifest_json=json.dumps(manifest, ensure_ascii=False, indent=2),
        ))
        return

    result = deliberate(manifest, model=args.model)
    output = {**manifest, **result}
    out = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(out)
        return

    out_path = (Path(args.output) if args.output
                else LABELED_DIR / f"{manifest.get('session_id', 'unknown')}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
