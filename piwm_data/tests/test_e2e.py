import json
import shutil
from pathlib import Path

from piwm_data.build_dataset import main


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_session"


def test_cli_builds_all_jsonl_and_stats(tmp_path, monkeypatch):
    archive_root = tmp_path / "Archive"
    archive_root.mkdir()
    shutil.copytree(FIXTURE_ROOT / "session_test_001", archive_root / "session_test_001")
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "data" / "piwm_dataset"

    exit_code = main(
        [
            "--archive-root",
            str(archive_root),
            "--output-dir",
            str(output_dir),
            "--frame-sample",
            "3",
        ]
    )

    assert exit_code == 0
    for name in [
        "main_schema.jsonl",
        "state_inference.jsonl",
        "state_inference_with_cue.jsonl",
        "transition_modeling.jsonl",
        "policy_preference.jsonl",
        "_stats.json",
    ]:
        path = output_dir / name
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()
    assert (output_dir / "world_model_continuation.jsonl").exists()

    stats = json.loads((output_dir / "_stats.json").read_text(encoding="utf-8"))
    assert stats["n_sessions_total"] == 1
    assert stats["n_sessions_loaded"] == 1
    assert stats["n_sessions_skipped"] == 0
    assert stats["n_state_inference_rows"] == 1
    assert stats["n_state_inference_with_cue_rows"] == 1
    assert stats["n_transition_modeling_rows"] == 4
    assert stats["n_policy_preference_rows"] == 1
    assert stats["n_world_model_continuation_rows"] == 0
    assert stats["require_qa_pass"] is True
    assert stats["require_continuation"] is False
    assert stats["n_transition_parent_states"] == 1
    assert stats["avg_actions_per_state"] == 4
    assert stats["n_states_with_action_contrast"] == 1
