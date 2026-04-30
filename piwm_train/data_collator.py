"""Lightweight training-record adapters for PIWM JSONL artifacts.

The GPU collator will later tokenize these records with Qwen3-VL/Qwen2.5-VL. This
module intentionally stays dependency-free so Day-1/Day-2 tests can verify the
data contract before installing torch/transformers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Literal

from . import config
from .prompts import (
    build_action_prompt,
    build_continuation_caption_prompt,
    build_deliberation_prompt,
    build_perception_prompt,
)
from .targets import (
    build_action_target,
    build_continuation_caption_target,
    build_deliberation_target,
    build_perception_target,
)

SFTTask = Literal["perception", "deliberation", "continuation_caption"]


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
    include_continuation: bool = True,
    perception_recap: bool = True,
) -> list[SFTExample]:
    examples: list[SFTExample] = []
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
    return examples


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


def _write_jsonl(rows: Iterable[dict], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count
