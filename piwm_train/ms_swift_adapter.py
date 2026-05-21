"""Export PIWM SFT examples to the ms-swift multimodal messages format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from . import config
from .data_collator import SFTExample, build_sft_examples
from .prompts import PIWM_SYSTEM_PROMPT

SWIFT_JSONL = "ms_swift_sft.jsonl"
SWIFT_SUMMARY = "ms_swift_sft_summary.json"
MS_SWIFT_IMAGE_TOKEN = "<image>"


def build_ms_swift_record(example: SFTExample, *, root: Path | None = None, validate_images: bool = True) -> dict:
    """Convert one internal SFT example into ms-swift messages JSONL shape."""
    images = [_resolve_image(path, root, validate=validate_images) for path in example.images] if root is not None else list(example.images)
    image_prefix = MS_SWIFT_IMAGE_TOKEN * len(images)
    prompt = example.prompt.replace(config.IMAGE_PLACEHOLDER, "").strip()
    user_content = f"{image_prefix}{prompt}" if image_prefix else prompt
    return {
        "messages": [
            {"role": "system", "content": PIWM_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": example.target},
        ],
        "images": images,
        "task": example.task,
        "source_id": example.source_id,
        "weight": example.weight,
        "loss_weight": example.weight,
        "meta": example.meta,
    }


def example_to_swift_row(example: SFTExample, *, root: Path, validate_images: bool = True) -> dict:
    return build_ms_swift_record(example, root=root, validate_images=validate_images)


def export_ms_swift_jsonl(
    data_dir: Path,
    output_jsonl: Path,
    *,
    root: Path | None = None,
    max_examples: int | None = None,
    include_perception: bool = True,
    include_deliberation: bool = True,
    include_continuation: bool = True,
    include_future_verification: bool = True,
    include_action: bool = False,
    include_user_intent: bool = False,
    action_prompt_mode: str = "outcome",
    five_act_only: bool = False,
    act_balancing: str = "inverse_freq",
    validate_images: bool = True,
) -> dict:
    root = (root or Path.cwd()).resolve()
    examples = build_sft_examples(
        data_dir,
        include_user_intent=include_user_intent,
        include_perception=include_perception,
        include_deliberation=include_deliberation,
        include_continuation=include_continuation,
        include_future_verification=include_future_verification,
        include_action=include_action,
        action_prompt_mode=action_prompt_mode,  # type: ignore[arg-type]
        five_act_only=five_act_only,
        act_balancing=act_balancing,  # type: ignore[arg-type]
    )
    if max_examples is not None:
        examples = examples[:max_examples]

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    task_counts: dict[str, int] = {}
    image_path_count = 0
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for example in examples:
            row = example_to_swift_row(example, root=root, validate_images=validate_images)
            task_counts[example.task] = task_counts.get(example.task, 0) + 1
            image_path_count += len(row["images"])
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "artifact": "ms_swift_sft_jsonl",
        "is_training_result": False,
        "data_dir": str(data_dir),
        "output_jsonl": str(output_jsonl),
        "n_examples": len(examples),
        "task_counts": task_counts,
        "image_path_count": image_path_count,
        "task_includes": {
            "user_intent": include_user_intent,
            "perception": include_perception,
            "deliberation": include_deliberation,
            "continuation": include_continuation,
            "future_verification": include_future_verification,
            "action_selection": include_action,
        },
        "action_prompt_mode": action_prompt_mode,
        "five_act_only": five_act_only,
        "act_balancing": act_balancing,
        "format": "ms-swift messages + images",
    }
    summary_path = output_jsonl.with_name(f"{output_jsonl.stem}_summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def _resolve_image(path: str, root: Path, *, validate: bool = True) -> str:
    image_path = Path(path)
    if not image_path.is_absolute():
        image_path = root / image_path
    if validate and not image_path.exists():
        raise FileNotFoundError(f"image not found: {image_path}")
    return image_path.resolve().as_posix()


def _iter_preview(path: Path, limit: int) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index >= limit:
                break
            if line.strip():
                yield json.loads(line)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root used to resolve relative frame paths.")
    parser.add_argument("--max-examples", type=int, default=None)
    parser.add_argument("--no-perception", action="store_true", help="Exclude state_inference rows.")
    parser.add_argument("--include-user-intent", action="store_true", help="Include leakage-free Stage-1 user-intent rows.")
    parser.add_argument("--no-deliberation", action="store_true", help="Exclude transition_modeling rows.")
    parser.add_argument("--no-continuation", action="store_true", help="Exclude world_model_continuation rows.")
    parser.add_argument("--no-future-verification", action="store_true", help="Exclude future_verification rows when continuation is enabled.")
    parser.add_argument("--include-action", action="store_true", help="Include policy_preference chosen-action rows as SFT action-selection examples.")
    parser.add_argument("--action-prompt-mode", choices=["outcome", "no_leak"], default="outcome")
    parser.add_argument("--five-act-only", action="store_true", help="Export action-selection rows with the five-act no-Reassure policy task name and prompt filter.")
    parser.add_argument("--act-balancing", choices=["none", "inverse_freq", "oversample_minority"], default="inverse_freq", help="Balance action-selection examples by best act before export.")
    parser.add_argument("--allow-missing-images", action="store_true", help="Do not validate image paths while exporting; useful when writing remote absolute paths locally.")
    parser.add_argument("--preview", type=int, default=0, help="Print the first N exported rows after writing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = export_ms_swift_jsonl(
        args.data_dir,
        args.output_jsonl,
        root=args.root,
        max_examples=args.max_examples,
        include_perception=not args.no_perception,
        include_user_intent=args.include_user_intent,
        include_deliberation=not args.no_deliberation,
        include_continuation=not args.no_continuation,
        include_future_verification=not args.no_future_verification,
        include_action=args.include_action,
        action_prompt_mode=args.action_prompt_mode,
        five_act_only=args.five_act_only,
        act_balancing=args.act_balancing,
        validate_images=not args.allow_missing_images,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.preview:
        for row in _iter_preview(args.output_jsonl, args.preview):
            print(json.dumps(row, ensure_ascii=False, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
