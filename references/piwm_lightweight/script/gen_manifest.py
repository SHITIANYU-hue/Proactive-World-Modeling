#!/usr/bin/env python3
"""Step 1: Generate Manifest JSON via GPT."""

import argparse
import json
import os
import re
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
SEED_DIR = REPO_ROOT / "data" / "seed"
SESSION_PREFIX = "piwm_"
SESSION_START = 201  # next after piwm_001–200

PROMPT_TEMPLATE = """你是一个有 10 年产业经验的数据合成专家，熟悉零售行为、消费者心理、AIDA 购买阶段、BDI（belief / desire / intention）建模，以及面向视频生成的数据设计。

你的任务是：
为"智能售货机 / 智能冰箱前置摄像头视角下的顾客行为视频生成"构造一条高质量、结构一致、可直接填入视频生成 Prompt Template 的结构化数据。

# 总目标
请围绕一个顾客在零售设备前停留、观察、比较、犹豫的短时片段，生成一条完整样本。
该样本将被用于后续视频生成，因此你输出的字段必须：
- 内部语义一致
- 符合零售场景常识
- 符合 AIDA 阶段定义
- 能通过外显行为、表情和姿态体现出来
- 能自然映射为一个 10 秒视频片段

# 生成流程
请按以下顺序思考并生成：

1. 先生成"人物层"：
- persona：一句话顾客画像（角色身份 + 当下情境，例如"下班路过便利区的年轻上班族"）
- persona_visual：用于视频生成的外观描述，包含：年龄段、性别、发型、服装（颜色/款式）、随身物品
  示例："25 岁左右的女性，扎马尾，穿深蓝色西装外套和白衬衫，单肩背一个黑色小包"

2. 再生成"认知层"：
- aida_stage：当前处于 attention / interest / desire / action 之一
- bdi：
  - belief：顾客当前对商品/购买情境的认知或判断
  - desire：顾客当前想达成的目标
  - intention：顾客接下来倾向采取的行为

3. 再生成"外显层（manifest）"：
这些字段必须是上面心理状态在镜头中可被观察到的体现：
- observable_behavior：可见行为特征
- facial_expression：表情状态
- body_posture：身体姿态

4. 再生成"时间线层（timeline）"：
生成一个 10 秒视频分段脚本，每段 1 句，使用人称与 persona_visual 保持一致：
- 0–2 秒
- 2–5 秒
- 5–8 秒
- 8–10 秒

# 场景约束
以下约束默认成立，不需要在生成字段中重复解释，但生成内容必须兼容这些约束：
- 视频时长 10 秒，单镜头、固定机位、无剪辑、写实自然风格
- 镜头来自智能售货机正面上方前置摄像头，轻微俯视，不晃动不变焦
- 顾客始终正面朝向镜头，面部无遮挡，双手在画面内
- 画面中不出现机器本体、商品、货架、价格标签或屏幕 UI
- 室内零售环境，无人互动，无对白，无夸张表情或动作

# 字段说明
请严格输出以下 JSON 字段：
- session_id：唯一字符串，格式 "piwm_<N>"
- persona：一句话顾客画像（身份 + 情境）
- persona_visual：外观视觉描述（年龄段、性别、发型、服装、随身物品）
- aida_stage："attention" / "interest" / "desire" / "action"
- bdi：belief / desire / intention 各一句话
- observable_behavior：镜头中可见的行为特征
- facial_expression：表情状态
- body_posture：身体姿态
- timeline：t_0_2 / t_2_5 / t_5_8 / t_8_10 各一句

# 输出格式
只输出 JSON：

{{
  "session_id": "",
  "persona": "",
  "persona_visual": "",
  "aida_stage": "",
  "bdi": {{
    "belief": "",
    "desire": "",
    "intention": ""
  }},
  "observable_behavior": "",
  "facial_expression": "",
  "body_posture": "",
  "timeline": {{
    "t_0_2": "",
    "t_2_5": "",
    "t_5_8": "",
    "t_8_10": ""
  }}
}}

# 输出要求
- 只输出 JSON，不要解释、注释、Markdown 或任务复述

当前的session_id是{session_id}{extra_note}"""


def extract_target_act(seed_text: str) -> str | None:
    """Extract 'Greet:open', 'Hold:ambient', etc. from seed text."""
    m = re.search(r'target_act=(\w+:\w+)', seed_text)
    return m.group(1) if m else None


def render_extra_note(note: str) -> str:
    if not note:
        return ""
    return (
        "\n\n# 额外说明（用户提供的自然语言约束，请严格遵守）\n"
        f"{note}\n"
    )


def generate_manifest(
    session_id: str,
    note: str = None,
    model: str = "gpt-5.5",
    max_retries: int = 5,
) -> dict:
    import time
    client = OpenAI()

    prompt = PROMPT_TEMPLATE.format(
        session_id=session_id,
        extra_note=render_extra_note(note),
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=60,
            )
            result = json.loads(response.choices[0].message.content)
            result["session_id"] = session_id
            return result
        except Exception as e:
            wait = 2 ** attempt
            print(f"  [retry {attempt + 1}/{max_retries}] {type(e).__name__}: {e} — waiting {wait}s",
                  file=sys.stderr)
            if attempt + 1 == max_retries:
                raise
            time.sleep(wait)


def next_session_id(start: int = SESSION_START) -> str:
    """Pick next session_id by scanning MANIFEST_DIR for piwm_<N>.json with N >= start."""
    pattern = re.compile(rf"^{re.escape(SESSION_PREFIX)}(\d+)$")
    used = set()
    if MANIFEST_DIR.exists():
        for p in MANIFEST_DIR.glob(f"{SESSION_PREFIX}*.json"):
            m = pattern.match(p.stem)
            if m:
                used.add(int(m.group(1)))
    n = start
    while n in used:
        n += 1
    return f"{SESSION_PREFIX}{n}"


def find_missing_manifests() -> list[Path]:
    """Seed files in data/seed/ that don't have a manifest in data/manifest/ yet."""
    result = []
    for seed in sorted(SEED_DIR.glob("piwm_*.txt")):
        if not (MANIFEST_DIR / f"{seed.stem}.json").exists():
            result.append(seed)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Step 1: generate manifest JSON via GPT. "
                    "Run without arguments to batch-process all data/seed/ → data/manifest/."
    )
    parser.add_argument(
        "note", nargs="?",
        help='自然语言约束 (例如: "action 阶段，不犹豫"). 省略则进入批量模式，从 data/seed/ 读取'
    )
    parser.add_argument(
        "--id", dest="session_id",
        help=f"session_id (e.g. piwm_750). 单条模式缺省时自动编号"
    )
    parser.add_argument("--model", default="gpt-5.5", help="OpenAI model name")
    parser.add_argument("--dry-run", action="store_true",
                        help="批量: 列出待处理文件. 单条: 打印最终 prompt")
    parser.add_argument(
        "--output", "-o",
        help=f"输出路径 (单条模式). 缺省 {MANIFEST_DIR}/<session_id>.json，'-' 写 stdout"
    )
    args = parser.parse_args()

    # ── batch mode ──
    if args.note is None and args.session_id is None and args.output is None:
        pending = find_missing_manifests()
        if not pending:
            print("All seeds already have manifests.", file=sys.stderr)
            return
        print(f"{'[dry-run] would process' if args.dry_run else 'Processing'} "
              f"{len(pending)} seed(s):", file=sys.stderr)
        for f in pending:
            print(f"  {f.name}", file=sys.stderr)
        if args.dry_run:
            return
        for seed_path in pending:
            session_id = seed_path.stem
            note = seed_path.read_text(encoding="utf-8").strip()
            result = generate_manifest(session_id, note, args.model)
            target_act = extract_target_act(note)
            if target_act:
                result["target_act"] = target_act
            out_path = MANIFEST_DIR / f"{session_id}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ {out_path.name}", file=sys.stderr)
        return

    # ── single-file mode ──
    session_id = args.session_id or next_session_id()

    if args.dry_run:
        print(PROMPT_TEMPLATE.format(
            session_id=session_id,
            extra_note=render_extra_note(args.note),
        ))
        return

    result = generate_manifest(session_id, args.note, args.model)
    if args.note:
        target_act = extract_target_act(args.note)
        if target_act:
            result["target_act"] = target_act

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(out)
        return

    out_path = Path(args.output) if args.output else MANIFEST_DIR / f"{session_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
