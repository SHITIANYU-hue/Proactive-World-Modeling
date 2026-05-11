from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from piwm_infer.baselines import api_status


ROOT = Path(__file__).resolve().parents[2]


def test_missing_api_key_returns_api_unavailable() -> None:
    status = api_status("gpt4v", env={})
    assert status["status"] == "api_unavailable"
    assert status["api_key_env"] == "OPENAI_API_KEY"
    assert "Missing OPENAI_API_KEY" in status["reason"]


def test_run_zero_shot_baseline_writes_offline_artifact(tmp_path: Path) -> None:
    out = tmp_path / "pilot24_zero_shot_baselines.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.run_zero_shot_baseline",
            "--data-dir",
            str(ROOT / "data/official/piwm_world_model_v1"),
            "--out",
            str(out),
            "--models",
            "rule_oracle",
            "gpt4v",
            "--limit",
            "3",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["artifact"] == "pilot24_zero_shot_baselines"
    assert payload["is_training_result"] is False
    assert payload["training_result"] is False
    assert payload["n_state_inference_rows"] == 3
    assert payload["n_policy_preference_rows"] == 3
    assert payload["n_main_schema_rows"] == 3

    by_model = {record["model"]: record for record in payload["models"]}
    assert by_model["gpt4v"]["status"] == "api_unavailable"
    assert by_model["rule_oracle"]["status"] == "ok"
    assert by_model["rule_oracle"]["is_training_result"] is False
    assert by_model["rule_oracle"]["not_real_model_result"] is True
    assert by_model["rule_oracle"]["metrics"]["n_records"] == 3
    assert by_model["rule_oracle"]["metrics"]["n_policy_pairs"] == 3
    assert len(by_model["rule_oracle"]["outputs"]) == 3
    assert set(by_model["rule_oracle"]["outputs"][0]) == {
        "state_id",
        "predicted",
        "gold",
        "policy_gold",
        "correct",
    }
