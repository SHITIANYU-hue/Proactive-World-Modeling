import json
import shutil
from pathlib import Path

import pytest

from scripts import make_contact_sheets


pytest.importorskip("PIL")

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_session" / "session_test_001"


def copy_fixture_archive(tmp_path: Path) -> Path:
    archive_root = tmp_path / "Archive"
    session_dir = archive_root / "session_test_001"
    shutil.copytree(FIXTURE_ROOT, session_dir)
    manifest = {
        "source_video": "video.mp4",
        "viewpoint": "salesperson_observable",
        "training_input_mode": "multi_image_single_turn",
        "frame_sampling_strategy": "fixture",
        "sampled_frames": [
            {"index": 0, "path": "frames/000.jpg", "timestamp_sec": 2.0, "role": "cue_onset"},
            {"index": 1, "path": "frames/001.jpg", "timestamp_sec": 5.0, "role": "cue_peak"},
            {"index": 2, "path": "frames/002.jpg", "timestamp_sec": 8.0, "role": "cue_resolution"},
        ],
    }
    (session_dir / "frame_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return archive_root


def test_make_contact_sheets_writes_index_sheet_and_template(tmp_path):
    archive_root = copy_fixture_archive(tmp_path)
    output_dir = tmp_path / "review"

    index = make_contact_sheets.build_contact_sheet_index(archive_root, output_dir)

    assert index["n_sessions"] == 1
    assert index["n_sessions_with_frames"] == 1
    assert len(index["sheets"]) == 1
    assert (output_dir / "contact_sheet_index.json").exists()
    assert (output_dir / "contact_sheet_index.md").exists()
    assert Path(index["sheets"][0]["path"]).exists()
    template = json.loads(Path(index["sessions"][0]["manual_review_template"]).read_text(encoding="utf-8"))
    assert template["required_visibility"]["face_visible"] is None
    assert index["sessions"][0]["manual_review_target"].endswith("qa_manual_review.json")


def test_make_contact_sheets_empty_archive_writes_empty_index(tmp_path):
    archive_root = tmp_path / "missing_archive"
    output_dir = tmp_path / "review"

    index = make_contact_sheets.build_contact_sheet_index(archive_root, output_dir)

    assert index["n_sessions"] == 0
    assert index["sheets"] == []
    assert "No sessions found" in (output_dir / "contact_sheet_index.md").read_text(encoding="utf-8")
