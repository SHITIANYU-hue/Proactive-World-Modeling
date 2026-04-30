from __future__ import annotations

import json
from pathlib import Path

from piwm_train.dpo_data import build_dpo_dataset, preference_to_dpo_pair, validate_preference_record


ROOT = Path(__file__).resolve().parents[2]


def _first_jsonl(path: str) -> dict:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.loads(next(line for line in handle if line.strip()))


def test_preference_to_dpo_pair_uses_structured_action_targets() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30_with_continuations/policy_preference.jsonl")
    pair = preference_to_dpo_pair(row)
    assert "<rationale>" in pair["chosen"]
    assert "<chosen>" in pair["rejected"]
    assert pair["chosen"] != pair["rejected"]
    assert pair["images"] == row["meta"]["frames"]
    assert pair["is_training_result"] is False
    assert pair["meta"]["is_training_result"] is False


def test_validate_preference_record_catches_bad_reward_and_equal_actions() -> None:
    row = _first_jsonl("data/piwm_dataset_pilot30_with_continuations/policy_preference.jsonl")
    row["reward_gap"] = 0
    row["rejected"] = row["chosen"]
    errors = validate_preference_record(row)
    assert "reward_gap_must_be_positive" in errors
    assert "chosen_equals_rejected" in errors


def test_build_dpo_dataset_writes_summary_with_malformed_count(tmp_path: Path) -> None:
    valid = _first_jsonl("data/piwm_dataset_pilot30_with_continuations/policy_preference.jsonl")
    invalid = dict(valid)
    invalid["state_id"] = "bad-row"
    invalid["chosen"] = ""

    input_path = tmp_path / "policy_preference.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(valid, ensure_ascii=False),
                json.dumps(invalid, ensure_ascii=False),
                "{not-json}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output_jsonl = tmp_path / "dpo_train_smoke.jsonl"
    summary_json = tmp_path / "summary.json"
    summary = build_dpo_dataset(input_path, output_jsonl, summary_json)

    assert summary["is_training_result"] is False
    assert summary["total_records"] == 3
    assert summary["written_pairs"] == 1
    assert summary["malformed_count"] == 2
    assert len(output_jsonl.read_text(encoding="utf-8").splitlines()) == 1
    saved_summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert saved_summary["malformed_records"][0]["state_id"] == "bad-row"
