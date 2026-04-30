from __future__ import annotations

import json
from pathlib import Path

from piwm_train import sft


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data/piwm_dataset_pilot30"
DATA_DIR_WITH_CONTINUATIONS = ROOT / "data/piwm_dataset_pilot30_with_continuations"


def test_sft_dry_run_writes_smoke_artifacts(tmp_path: Path) -> None:
    exit_code = sft.main(["--data-dir", str(DATA_DIR), "--output-dir", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    smoke_jsonl = tmp_path / "sft_train_smoke.jsonl"
    summary_json = tmp_path / "sft_smoke_summary.json"
    assert smoke_jsonl.exists()
    assert summary_json.exists()

    rows = [json.loads(line) for line in smoke_jsonl.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_json.read_text(encoding="utf-8"))

    assert summary["mode"] == "dry-run"
    assert "not a training result" in summary["note"]
    assert summary["n_examples"] == len(rows) == 90
    assert summary["task_counts"] == {
        "continuation_caption": 0,
        "deliberation": 66,
        "perception": 24,
    }
    assert summary["image_path_count"] > 0
    assert summary["has_continuation_examples"] is False
    assert rows[0]["prompt"]
    assert rows[0]["target"]
    assert rows[0]["images"]


def test_sft_dry_run_function_returns_summary(tmp_path: Path) -> None:
    summary = sft.run_dry_run(DATA_DIR, tmp_path)

    assert summary["n_examples"] == 90
    assert summary["task_counts"]["perception"] == 24
    assert (tmp_path / sft.SMOKE_JSONL).exists()
    assert (tmp_path / sft.SMOKE_SUMMARY).exists()


def test_sft_dry_run_includes_continuation_head_when_available(tmp_path: Path) -> None:
    summary = sft.run_dry_run(DATA_DIR_WITH_CONTINUATIONS, tmp_path)

    assert summary["n_examples"] == 134
    assert summary["task_counts"] == {
        "continuation_caption": 44,
        "deliberation": 66,
        "perception": 24,
    }
    assert summary["has_continuation_examples"] is True
