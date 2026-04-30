from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_run_pilot_eval_mock_writes_limit_artifact(tmp_path: Path) -> None:
    out = tmp_path / "pilot3_mock_eval.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.run_pilot_eval",
            "--data-dir",
            str(ROOT / "data/piwm_dataset_pilot30"),
            "--out",
            str(out),
            "--mode",
            "mock",
            "--limit",
            "3",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["model"] == "MockVLM"
    assert payload["is_training_result"] is False
    assert payload["n_records"] == 3
    assert payload["n_success"] == 3
    assert payload["parse_failure_count"] == 0
    assert payload["fallback_count"] == 0
    assert payload["strategy_accuracy_vs_label"] == 0
    assert [record["predicted_action"] for record in payload["outputs"]] == [
        "A2_offer_value_comparison",
        "A2_offer_value_comparison",
        "A2_offer_value_comparison",
    ]
    assert set(payload["outputs"][0]) == {
        "state_id",
        "gold_action",
        "predicted_action",
        "used_fallback",
        "errors",
    }
