from __future__ import annotations

import json
from pathlib import Path

from piwm_train.data_collator import build_sft_examples
from piwm_train.ms_swift_adapter import build_ms_swift_record, main


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data/piwm_dataset_pilot30"


def test_build_ms_swift_record_uses_sft_example_target() -> None:
    example = build_sft_examples(DATA_DIR)[0]
    record = build_ms_swift_record(example)

    assert record["images"] == example.images
    assert record["messages"][0]["role"] == "system"
    assert record["messages"][1]["role"] == "user"
    assert record["messages"][1]["content"].count("<image>") == len(example.images)
    assert "<|image_pad|>" not in record["messages"][1]["content"]
    assert record["messages"][2] == {"role": "assistant", "content": example.target}
    assert record["source_id"] == example.source_id
    assert record["task"] == example.task


def test_ms_swift_export_cli_respects_max_examples(tmp_path: Path) -> None:
    output_jsonl = tmp_path / "ms_swift_sft.jsonl"

    exit_code = main(["--data-dir", str(DATA_DIR), "--output-jsonl", str(output_jsonl), "--max-examples", "2"])

    assert exit_code == 0
    rows = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert all(row["images"] for row in rows)
    assert all(row["messages"][-1]["role"] == "assistant" for row in rows)
    assert all(row["messages"][-1]["content"] for row in rows)
