from __future__ import annotations

import json
from pathlib import Path

from scripts import summarize_sprint_results


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_sprint_summary_marks_mock_and_missing_results(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "data/piwm_dataset_pilot30_with_continuations/_stats.json",
        {
            "n_sessions_loaded": 24,
            "n_sessions_skipped": 6,
            "n_state_inference_rows": 24,
            "n_transition_modeling_rows": 66,
            "n_world_model_continuation_rows": 44,
            "n_states_with_action_contrast": 24,
            "n_sessions_by_split": {"train": 12, "dev": 3},
            "n_sessions_by_viewpoint": {"salesperson_observable": 17},
            "timestamp_utc": "2026-04-29T21:05:35Z",
        },
    )
    _write_json(
        tmp_path / "data/piwm_results/pilot24_mock_pipeline_eval.json",
        {
            "mode": "mock",
            "model": "MockVLM",
            "is_training_result": False,
            "n_records": 24,
            "n_success": 24,
            "strategy_accuracy_vs_label": 0.125,
            "parse_failure_count": 0,
            "fallback_count": 0,
        },
    )
    _write_json(
        tmp_path / "data/piwm_results/pilot24_zero_shot_baselines.json",
        {
            "models": [
                {
                    "model": "rule_oracle",
                    "baseline_type": "deterministic_metadata_assisted",
                    "not_real_model_result": True,
                    "metrics": {
                        "n_records": 24,
                        "strategy_accuracy_vs_best_action": 1.0,
                        "intent_accuracy": 1.0,
                    },
                },
                {"model": "gpt4v"},
            ]
        },
    )

    exit_code = summarize_sprint_results.main(
        [
            "--root",
            str(tmp_path),
            "--summary-out",
            "data/piwm_results/sprint_summary.json",
            "--markdown-out",
            "docs/92_neurips_sprint_result_snapshot.md",
            "--generated-at-utc",
            "2026-04-30T00:00:00Z",
        ]
    )

    assert exit_code == 0
    payload = json.loads((tmp_path / "data/piwm_results/sprint_summary.json").read_text(encoding="utf-8"))
    assert payload["inputs"]["dataset_stats"]["status"] == "present"
    assert payload["inputs"]["mock_pipeline_eval"]["nature"] == "mock pipeline evaluation"
    assert payload["inputs"]["sft_train_summary"]["status"] == "missing"
    assert payload["inputs"]["zero_shot_baselines"]["status"] == "present"

    mock_row = next(row for row in payload["result_rows"] if row["label"] == "MockVLM pipeline eval")
    assert mock_row["result_nature"] == "mock"
    assert mock_row["is_training_result"] is False
    assert mock_row["strategy_accuracy_vs_label"] == 0.125
    assert "do not cite as a trained model result" in mock_row["notes"]

    sft_row = next(row for row in payload["result_rows"] if row["label"] == "SFT model")
    assert sft_row["status"] == "missing"
    assert sft_row["strategy_accuracy_vs_label"] == "unknown"

    oracle_row = next(row for row in payload["result_rows"] if row.get("model") == "rule_oracle")
    assert oracle_row["result_nature"] == "synthetic/rule-derived baseline"
    assert oracle_row["strategy_accuracy_vs_label"] == 1.0
    assert oracle_row["not_real_model_result"] is True

    gpt4v_row = next(row for row in payload["result_rows"] if row.get("model") == "gpt4v")
    assert gpt4v_row["status"] == "missing"
    assert gpt4v_row["strategy_accuracy_vs_label"] == "unknown"

    markdown = (tmp_path / "docs/92_neurips_sprint_result_snapshot.md").read_text(encoding="utf-8")
    assert "MockVLM pipeline eval" in markdown
    assert "missing" in markdown


def test_sprint_summary_handles_all_inputs_missing(tmp_path: Path) -> None:
    summary = summarize_sprint_results.build_summary(
        root=tmp_path,
        dataset_stats=Path("missing_stats.json"),
        mock_eval=Path("missing_mock.json"),
        sft_summary=Path("missing_sft.json"),
        zero_shot=Path("missing_zero.json"),
        generated_at_utc="2026-04-30T00:00:00Z",
    )

    assert {record["status"] for record in summary["inputs"].values()} == {"missing"}
    assert all(row["status"] == "missing" for row in summary["result_rows"])
    assert summary["result_rows"][0]["n_sessions_loaded"] == "unknown"
