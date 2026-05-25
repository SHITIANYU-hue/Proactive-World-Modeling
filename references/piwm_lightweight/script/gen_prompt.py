#!/usr/bin/env python3
"""Render pre-interaction 10s video prompts from manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
PROMPT_DIR = REPO_ROOT / "data" / "prompts"

PROMPT_TEMPLATE = """# Goal
生成一段 10 秒、写实自然、单镜头的视频。视频内容是智能零售设备前置摄像头捕捉到的顾客当前状态片段。

# Camera And Framing
- 视角：设备正面上方前置摄像头，朝外拍摄顾客
- 镜头：固定机位，轻微俯视，不平移，不旋转，不推拉，不变焦
- 构图：顾客位于画面中央附近，头部、面部、上半身、双手持续清晰可见
- 画面：真实商用摄像头质感，光线稳定，无遮挡，无镜头漂移
- 禁止出现机器本体、机器边框、商品、货架、屏幕 UI、价格标签、文字叠层

# Subject Continuity
- 顾客外观在 10 秒内完全一致，不换脸、不换衣、不增减配饰
- 只有一名顾客，无其他人进入画面
- 动作幅度克制，表情自然，不做戏剧化表演
- 顾客的犹豫应表现为细微确认、短暂停顿、轻度迟疑，不要演成明显困惑、茫然失措或夸张纠结

# Character
{persona_visual}
人物背景：{persona}

# Internal State Reference
这些状态只用于约束行为气质，不应直接以文字、符号或 UI 出现在画面里。
- 购买阶段：{aida_stage}
- Belief：{belief}
- Desire：{desire}
- Intention：{intention}

# Observable Performance
- 主要可见行为：{observable_behavior}
- 面部状态：{facial_expression}
- 身体姿态：{body_posture}

# 10-Second Timeline
- 0–2 秒：{t_0_2}
- 2–5 秒：{t_2_5}
- 5–8 秒：{t_5_8}
- 8–10 秒：{t_8_10}

# Motion Quality
- {entry_policy}
- 所有头部、视线、停顿、前倾、手部变化都应缓慢、连续、符合真实顾客行为
- 视线变化要自然，可短暂停留后再移动，不能高频乱跳
- {interaction_policy}
- {display_policy}

# Negative Constraints
- 不出现售货机本体、柜门、商品、货架、二维码、付款界面、促销字幕
- 不出现镜头抖动、剪辑、转场、景别变化、夸张景深变化
- 不出现畸形手部、多余手指、面部扭曲、身体比例突变
- 不出现突然转身离开、突然贴近镜头、重复或明显舞台化的头部动作
"""


VISIBLE_TEXT_REPLACEMENTS = [
    ("视线在前方和略下方的价格信息位置之间来回移动", "视线在前方与略下方的同一区域之间来回移动"),
    ("再次看向略下方的价格信息位置", "再次看向略下方的同一区域"),
    ("前方和略下方的价格信息位置之间", "前方与略下方的同一区域之间"),
    ("价格信息位置", "前方略下方的同一区域"),
    ("价格确认区域", "前方略下方的同一区域"),
    ("价格区域", "前方略下方的区域"),
    ("参数区域", "前方略下方的区域"),
    ("说明区域", "前方略下方的区域"),
    ("偶尔把校园卡往前抬起又放低", "偶尔在胸前轻微调整校园卡"),
    ("校园卡被他稍微抬起又放低", "校园卡在胸前被轻微调整"),
    ("属性说明", "简明信息"),
    ("属性信息", "简明信息"),
    ("参数说明", "简明信息"),
    ("价格说明", "简明信息"),
    ("价格信息", "简明信息"),
    ("快步停在镜头前", "已经停留在镜头前"),
    ("往前抬起又放低", "在胸前轻微调整"),
    ("稍微抬起又放低", "在胸前轻微调整"),
    ("准备下一步操作", "继续保持观察状态"),
    ("准备继续购买", "继续保持观察状态"),
]


PAYMENT_KEYWORDS = ["支付", "扫码", "付款", "刷卡", "取货", "出货", "完成购买", "完成操作"]


def sanitize_visible_text(text: str) -> str:
    if not text:
        return ""
    result = text
    for src, dst in sorted(VISIBLE_TEXT_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        result = result.replace(src, dst)
    return result


def build_entry_policy(record: dict) -> str:
    stage = record.get("aida_stage", "")
    timeline = record.get("timeline", {})
    start_text = timeline.get("t_0_2", "")

    if stage == "attention" or any(word in start_text for word in ["路过", "走近", "经过", "进入", "快步"]):
        return "允许顾客从画面边缘自然走入或放慢脚步，但动作必须平稳，不要突然闯入、骤停或立刻表情大变"

    return "视频开始时顾客应已经处在摄像头可见范围内，默认是已停留并正在观察的片段，不要拍成从画外突然闯入、骤停、再立刻表情大变"


def build_interaction_policy(record: dict) -> str:
    stage = record.get("aida_stage", "")
    visible_text = " ".join(
        [
            record.get("observable_behavior", ""),
            record.get("body_posture", ""),
            *record.get("timeline", {}).values(),
        ]
    )
    has_payment_or_pickup = any(word in visible_text for word in PAYMENT_KEYWORDS)

    if stage == "action" and has_payment_or_pickup:
        return "允许出现与当前状态一致的轻微手机支付、刷卡、确认、等待出货或取货动作；动作应克制、真实，不要夸张贴屏、反复敲击或展示界面细节"

    return "手部不触碰画面外不存在的具体商品或按钮，不做扫码、付款、刷卡、取货等已交互动作；若手里拿着手机、卡片或钱包，只能自然握持或在胸前轻微调整，不能贴向屏幕"


def build_display_policy(record: dict) -> str:
    stage = record.get("aida_stage", "")
    visible_text = " ".join(
        [
            record.get("observable_behavior", ""),
            record.get("body_posture", ""),
            *record.get("timeline", {}).values(),
        ]
    )
    has_payment_or_pickup = any(word in visible_text for word in PAYMENT_KEYWORDS)

    if stage == "action" and has_payment_or_pickup:
        return "不展示机器主动响应或屏幕 UI 内容；即使发生支付、刷卡、等待出货或取货，也只表现顾客自然动作，不展示二维码、付款界面、价格文字或终端弹窗"

    return "不展示机器主动响应、屏幕 UI 内容、二维码、付款界面、价格文字或终端弹窗"


def render_prompt(record: dict) -> str:
    timeline = record.get("timeline", {})
    bdi = record.get("bdi", {})
    return PROMPT_TEMPLATE.format(
        persona_visual=record.get("persona_visual", ""),
        persona=record.get("persona", ""),
        aida_stage=record.get("aida_stage", ""),
        belief=bdi.get("belief", ""),
        desire=bdi.get("desire", ""),
        intention=bdi.get("intention", ""),
        observable_behavior=sanitize_visible_text(record.get("observable_behavior", "")),
        facial_expression=record.get("facial_expression", ""),
        body_posture=record.get("body_posture", ""),
        t_0_2=sanitize_visible_text(timeline.get("t_0_2", "")),
        t_2_5=sanitize_visible_text(timeline.get("t_2_5", "")),
        t_5_8=sanitize_visible_text(timeline.get("t_5_8", "")),
        t_8_10=sanitize_visible_text(timeline.get("t_8_10", "")),
        entry_policy=build_entry_policy(record),
        interaction_policy=build_interaction_policy(record),
        display_policy=build_display_policy(record),
    )


def find_prompt_sources(overwrite: bool = False) -> list[Path]:
    result = []
    for manifest in sorted(MANIFEST_DIR.glob("piwm_*.json")):
        if not overwrite and (PROMPT_DIR / f"{manifest.stem}.md").exists():
            continue
        result.append(manifest)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render pre-interaction video prompts from manifest JSON files."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        help="Manifest JSON path (use - for stdin). Omit to batch-process data/manifest/.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=f"Output path in single-file mode. Default: {PROMPT_DIR}/<id>.md. Use '-' for stdout.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing prompt files in batch mode.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Batch: list files that would be processed. Single: print prompt to stdout.",
    )
    args = parser.parse_args()

    if args.manifest is None:
        pending = find_prompt_sources(overwrite=args.overwrite)
        if not pending:
            print("All manifests already have prompts.", file=sys.stderr)
            return
        print(
            f"{'[dry-run] would process' if args.dry_run else 'Processing'} {len(pending)} file(s):",
            file=sys.stderr,
        )
        for path in pending:
            print(f"  {path.name}", file=sys.stderr)
        if args.dry_run:
            return
        for path in pending:
            record = json.loads(path.read_text(encoding="utf-8"))
            session_id = record.get("session_id", path.stem)
            prompt = render_prompt(record)
            out_path = PROMPT_DIR / f"{session_id}.md"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(prompt, encoding="utf-8")
            print(f"  saved {out_path.name}", file=sys.stderr)
        return

    if args.manifest == "-":
        record = json.load(sys.stdin)
    else:
        with open(args.manifest, "r", encoding="utf-8") as f:
            record = json.load(f)

    prompt = render_prompt(record)
    session_id = record.get("session_id", "unknown")
    if args.output == "-" or args.dry_run:
        print(prompt)
        return

    out_path = Path(args.output) if args.output else PROMPT_DIR / f"{session_id}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt, encoding="utf-8")
    print(f"Prompt saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
