"""Lightweight training-record adapters for PIWM JSONL artifacts.

The GPU collator will later tokenize these records with Qwen3-VL/Qwen2.5-VL. This
module intentionally stays dependency-free so Day-1/Day-2 tests can verify the
data contract before installing torch/transformers.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from math import ceil
from pathlib import Path
from typing import Iterable, Iterator, Literal

from piwm_data.migration.legacy_action_mapping import legacy_action_to_act_params_for_comparison

from . import config
from .prompts import (
    build_action_prompt_no_leak,
    build_action_prompt,
    build_continuation_caption_prompt,
    build_deliberation_prompt,
    build_future_verification_prompt,
    build_perception_prompt,
    build_user_intent_prompt,
)
from .targets import (
    build_action_target,
    build_continuation_caption_target,
    build_deliberation_target,
    build_future_verification_target,
    build_perception_target,
    build_user_intent_target,
)

FIVE_ACTS = {"Greet", "Elicit", "Inform", "Recommend", "Hold"}
ActBalancing = Literal["none", "inverse_freq", "oversample_minority"]

SFTTask = Literal[
    "perception",
    "user_intent",
    "deliberation",
    "next_state_prediction",
    "continuation_caption",
    "future_verification",
    "action_selection",
    "action_selection_5act",
]


def user_intent_loss_weight(intent_label: str | None) -> float:
    """Return A3+ loss weight for visual-only user-intent labels."""
    if intent_label in config.LOW_CONFIDENCE_INTENT_LABELS:
        return config.LOW_CONFIDENCE_INTENT_LOSS_WEIGHT
    return config.DEFAULT_INTENT_LOSS_WEIGHT


@dataclass
class SFTExample:
    task: SFTTask
    source_id: str
    prompt: str
    target: str
    images: list[str]
    weight: float = 1.0
    meta: dict = field(default_factory=dict)


@dataclass
class DPOExample:
    source_id: str
    prompt: str
    chosen: str
    rejected: str
    images: list[str]
    meta: dict = field(default_factory=dict)


def build_sft_examples(
    data_dir: Path,
    *,
    include_user_intent: bool = False,
    include_perception: bool = True,
    include_deliberation: bool = True,
    include_continuation: bool = True,
    include_future_verification: bool = True,
    include_action: bool = False,
    perception_recap: bool = True,
    action_prompt_mode: Literal["outcome", "no_leak"] = "outcome",
    five_act_only: bool = False,
    act_balancing: ActBalancing = "inverse_freq",
) -> list[SFTExample]:
    examples: list[SFTExample] = []
    if include_user_intent:
        for row in _read_jsonl_if_exists(data_dir / "state_inference.jsonl"):
            intent_label = row.get("output", {}).get("intent")
            loss_weight = user_intent_loss_weight(intent_label)
            examples.append(
                SFTExample(
                    task="user_intent",
                    source_id=row["state_id"],
                    prompt=build_user_intent_prompt(row),
                    target=build_user_intent_target(row),
                    images=list(row["input"].get("frames", [])),
                    weight=loss_weight,
                    meta={
                        "split": row.get("meta", {}).get("split"),
                        "viewpoint": row.get("meta", {}).get("viewpoint"),
                        "stage": row.get("output", {}).get("aida_stage"),
                        "intent_label": intent_label,
                        "loss_weight": loss_weight,
                        "loss_weight_policy": "a3plus_visual_intent_low_confidence",
                    },
                )
            )

    if include_perception:
        for row in _read_jsonl_if_exists(data_dir / "state_inference.jsonl"):
            target = build_perception_target(row)
            if perception_recap:
                target = _append_perception_recap(target, row)
            examples.append(
                SFTExample(
                    task="perception",
                    source_id=row["state_id"],
                    prompt=build_perception_prompt(row),
                    target=target,
                    images=list(row["input"].get("frames", [])),
                    meta={"split": row.get("meta", {}).get("split"), "viewpoint": row.get("meta", {}).get("viewpoint")},
                )
            )

    if include_deliberation:
        for row in _read_jsonl_if_exists(data_dir / "transition_modeling.jsonl"):
            examples.append(
                SFTExample(
                    task="deliberation",
                    source_id=row["state_id"],
                    prompt=build_deliberation_prompt(row),
                    target=build_deliberation_target(row),
                    images=list(row["input"].get("frames", [])),
                    meta={
                        "parent_state_id": row.get("meta", {}).get("parent_state_id"),
                        "candidate_action": row["input"].get("candidate_action"),
                        "split": row.get("meta", {}).get("split"),
                        "viewpoint": row.get("meta", {}).get("viewpoint"),
                    },
                )
            )

    if include_continuation:
        for row in _read_jsonl_if_exists(data_dir / "world_model_continuation.jsonl"):
            examples.append(
                SFTExample(
                    task="continuation_caption",
                    source_id=row["state_id"],
                    prompt=build_continuation_caption_prompt(row),
                    target=build_continuation_caption_target(row),
                    images=list(row["input"].get("current_frames", [])),
                    meta={
                        "parent_state_id": row.get("meta", {}).get("parent_state_id"),
                        "candidate_action": row["input"].get("candidate_action"),
                        "continuation_role": row.get("meta", {}).get("continuation_role"),
                        "continuation_frames": row["output"].get("continuation_frames", []),
                        "split": row.get("meta", {}).get("split"),
                        "viewpoint": row.get("meta", {}).get("viewpoint"),
                    },
                )
            )
        if include_future_verification:
            for row in _read_jsonl_if_exists(data_dir / "future_verification.jsonl"):
                current_frames = list(row["input"].get("current_frames", []))
                continuation_frames = list(row["input"].get("continuation_frames", []))
                examples.append(
                    SFTExample(
                        task="future_verification",
                        source_id=row["state_id"],
                        prompt=build_future_verification_prompt(row),
                        target=build_future_verification_target(row),
                        images=current_frames + continuation_frames,
                        meta={
                            "parent_state_id": row.get("meta", {}).get("parent_state_id"),
                            "continuation_id": row.get("meta", {}).get("continuation_id"),
                            "candidate_action": row["input"].get("candidate_action"),
                            "is_positive_pair": row.get("meta", {}).get("is_positive_pair"),
                            "split": row.get("meta", {}).get("split"),
                            "viewpoint": row.get("meta", {}).get("viewpoint"),
                        },
                    )
                )

    if include_action:
        action_examples: list[SFTExample] = []
        for row in _read_jsonl_if_exists(data_dir / "policy_preference.jsonl"):
            if five_act_only:
                row = _five_act_policy_row(row)
                if row is None:
                    continue
            prompt = (
                build_action_prompt_no_leak(row, five_act_only=five_act_only)
                if action_prompt_mode == "no_leak"
                else build_action_prompt(row)
            )
            task: SFTTask = "action_selection_5act" if five_act_only else "action_selection"
            action_examples.append(
                SFTExample(
                    task=task,
                    source_id=row["state_id"],
                    prompt=prompt,
                    target=build_action_target(row, "chosen"),
                    images=list(row.get("meta", {}).get("frames", [])),
                    meta={
                        "split": row.get("meta", {}).get("split"),
                        "viewpoint": row.get("meta", {}).get("viewpoint"),
                        "reward_gap": row.get("reward_gap"),
                        "best_act": _block_act(row.get("chosen_json", {})),
                        "candidate_action_acts": _candidate_action_acts(row, five_act_only=five_act_only),
                        "five_act_only": five_act_only,
                    },
                )
            )
        examples.extend(apply_action_balancing(action_examples, act_balancing))
    return examples


def apply_action_balancing(examples: list[SFTExample], mode: ActBalancing) -> list[SFTExample]:
    if not examples or mode == "none":
        return examples
    counts = Counter(example.meta.get("best_act") for example in examples if example.meta.get("best_act"))
    if not counts:
        return examples
    if mode == "inverse_freq":
        n_classes = len(counts)
        total = sum(counts.values())
        balanced: list[SFTExample] = []
        for example in examples:
            act = example.meta.get("best_act")
            weight = total / (n_classes * counts[act]) if act in counts else 1.0
            meta = {**example.meta, "act_balancing": mode}
            balanced.append(replace(example, weight=round(float(weight), 6), meta=meta))
        return balanced
    if mode == "oversample_minority":
        majority = max(counts.values())
        target_floor = ceil(majority * 0.5)
        grouped: dict[str, list[SFTExample]] = {}
        for example in examples:
            act = example.meta.get("best_act")
            if act:
                grouped.setdefault(act, []).append(example)
        balanced = [
            replace(example, meta={**example.meta, "act_balancing": mode})
            for example in examples
        ]
        for act in sorted(grouped):
            group = grouped[act]
            needed = max(0, target_floor - len(group))
            for index in range(needed):
                source = group[index % len(group)]
                balanced.append(
                    replace(
                        source,
                        meta={**source.meta, "act_balancing": mode, "oversampled": True},
                    )
                )
        return balanced
    raise ValueError(f"unsupported act_balancing mode: {mode}")


def build_dpo_examples(data_dir: Path) -> list[DPOExample]:
    examples: list[DPOExample] = []
    for row in _read_jsonl_if_exists(data_dir / "policy_preference.jsonl"):
        examples.append(
            DPOExample(
                source_id=row["state_id"],
                prompt=build_action_prompt(row),
                chosen=build_action_target(row, "chosen"),
                rejected=build_action_target(row, "rejected"),
                images=list(row.get("meta", {}).get("frames", [])),
                meta={
                    "split": row.get("meta", {}).get("split"),
                    "viewpoint": row.get("meta", {}).get("viewpoint"),
                    "reward_gap": row.get("reward_gap"),
                },
            )
        )
    return examples


def batch_examples(examples: list[SFTExample] | list[DPOExample], batch_size: int) -> Iterator[list]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(examples), batch_size):
        yield examples[start:start + batch_size]


def write_sft_jsonl(examples: Iterable[SFTExample], out: Path) -> int:
    return _write_jsonl((asdict(example) for example in examples), out)


def write_dpo_jsonl(examples: Iterable[DPOExample], out: Path) -> int:
    return _write_jsonl((asdict(example) for example in examples), out)


def _append_perception_recap(target: str, row: dict) -> str:
    out = row["output"]
    bdi = out["bdi"]
    return "\n".join(
        [
            target,
            "[recap]",
            f"{config.TAG_STAGE_OPEN}{out['aida_stage']}{config.TAG_STAGE_CLOSE}",
            f"{config.TAG_INTENTION_OPEN}{bdi['intention']}{config.TAG_INTENTION_CLOSE}",
        ]
    )


def _read_jsonl_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _five_act_policy_row(row: dict) -> dict | None:
    if _block_act(row.get("chosen_json", {})) not in FIVE_ACTS:
        return None
    updated = dict(row)
    meta = dict(updated.get("meta") or {})
    candidate_block = [
        item
        for item in meta.get("candidate_block", [])
        if _block_act(item) in FIVE_ACTS
    ]
    if not candidate_block:
        return None
    meta["candidate_block"] = candidate_block
    updated["meta"] = meta
    return updated


def _candidate_action_acts(row: dict, *, five_act_only: bool = False) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in row.get("meta", {}).get("candidate_block", []):
        action = item.get("action")
        act = _block_act(item)
        if five_act_only and act not in FIVE_ACTS:
            continue
        if action and act:
            mapping[action] = act
    for side in ("chosen_json", "rejected_json"):
        block = row.get(side, {})
        action = block.get("action")
        act = _block_act(block)
        if five_act_only and act not in FIVE_ACTS:
            continue
        if action and act:
            mapping.setdefault(action, act)
    for item in row.get("meta", {}).get("candidate_block", []):
        action = item.get("action")
        if action and action not in mapping:
            try:
                act = legacy_action_to_act_params_for_comparison(action)[0]
                if five_act_only and act not in FIVE_ACTS:
                    continue
                mapping[action] = act
            except KeyError:
                pass
    return mapping


def _block_act(block: dict) -> str | None:
    spec = block.get("dialogue_act") or block.get("action_spec") or {}
    act = spec.get("act")
    return str(act) if act else None


def _write_jsonl(rows: Iterable[dict], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count
