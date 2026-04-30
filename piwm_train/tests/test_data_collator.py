from __future__ import annotations

import json
from pathlib import Path

import pytest

from piwm_train import config
from piwm_train.data_collator import (
    SFTExample,
    batch_examples,
    build_dpo_examples,
    build_sft_examples,
    write_dpo_jsonl,
    write_sft_jsonl,
)


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data/piwm_dataset_pilot30"
DATA_DIR_WITH_CONTINUATIONS = ROOT / "data/piwm_dataset_pilot30_with_continuations"


def test_build_sft_examples_from_pilot30_without_continuation() -> None:
    examples = build_sft_examples(DATA_DIR, include_continuation=True)
    task_counts = {task: sum(1 for example in examples if example.task == task) for task in ["perception", "deliberation", "continuation_caption"]}
    assert task_counts["perception"] == 24
    assert task_counts["deliberation"] == 66
    assert task_counts["continuation_caption"] == 0
    assert all(isinstance(example, SFTExample) for example in examples)


def test_build_sft_examples_from_pilot30_with_continuations() -> None:
    examples = build_sft_examples(DATA_DIR_WITH_CONTINUATIONS, include_continuation=True)
    task_counts = {task: sum(1 for example in examples if example.task == task) for task in ["perception", "deliberation", "continuation_caption"]}
    assert task_counts == {
        "perception": 24,
        "deliberation": 66,
        "continuation_caption": 44,
    }
    first_continuation = next(example for example in examples if example.task == "continuation_caption")
    assert first_continuation.images
    assert first_continuation.meta["continuation_frames"]


def test_perception_examples_include_recap_by_default() -> None:
    example = next(example for example in build_sft_examples(DATA_DIR) if example.task == "perception")
    assert "[recap]" in example.target
    assert example.target.count(config.TAG_STAGE_OPEN) == 2
    assert example.target.count(config.TAG_INTENTION_OPEN) == 2


def test_build_dpo_examples_from_pilot30() -> None:
    examples = build_dpo_examples(DATA_DIR)
    assert len(examples) == 24
    first = examples[0]
    assert config.TAG_CHOSEN_OPEN in first.chosen
    assert config.TAG_CHOSEN_OPEN in first.rejected
    assert first.images


def test_batch_examples_requires_positive_batch_size() -> None:
    with pytest.raises(ValueError):
        list(batch_examples([], 0))


def test_batch_examples_chunks() -> None:
    examples = build_dpo_examples(DATA_DIR)[:5]
    batches = list(batch_examples(examples, 2))
    assert [len(batch) for batch in batches] == [2, 2, 1]


def test_write_training_jsonl_roundtrip(tmp_path: Path) -> None:
    sft = build_sft_examples(DATA_DIR)[:2]
    dpo = build_dpo_examples(DATA_DIR)[:2]
    sft_out = tmp_path / "sft.jsonl"
    dpo_out = tmp_path / "dpo.jsonl"
    assert write_sft_jsonl(sft, sft_out) == 2
    assert write_dpo_jsonl(dpo, dpo_out) == 2
    first_sft = json.loads(sft_out.read_text(encoding="utf-8").splitlines()[0])
    first_dpo = json.loads(dpo_out.read_text(encoding="utf-8").splitlines()[0])
    assert first_sft["prompt"]
    assert first_sft["target"]
    assert first_dpo["chosen"]
    assert first_dpo["rejected"]
