import json
import shutil
from pathlib import Path

from piwm_data.build_dataset import main as build_main
from scripts import qa_gate


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_session" / "session_test_001"


def copy_fixture(tmp_path):
    session_dir = tmp_path / "Archive" / "session_test_001"
    shutil.copytree(FIXTURE_ROOT, session_dir)
    return session_dir


def add_video_and_manifest(session_dir: Path):
    (session_dir / "video.mp4").write_bytes(b"fake-video")
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
    (session_dir / "frame_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_qa_gate_requires_manual_visual_review(tmp_path):
    session_dir = copy_fixture(tmp_path)
    add_video_and_manifest(session_dir)
    (session_dir / "qa_report.json").unlink()
    report = qa_gate.run_qa_for_session(session_dir)
    assert report["file_checks_pass"] is True
    assert report["viewpoint"] == "salesperson_observable"
    assert report["overall_pass"] is False
    assert report["manual_review_required"] is True
    assert "viewpoint visibility" in report["rejection_reason"]


def test_qa_gate_passes_with_manual_review(tmp_path):
    session_dir = copy_fixture(tmp_path)
    add_video_and_manifest(session_dir)
    (session_dir / "qa_report.json").unlink()
    manual = {
        "cue_visible_in_video": True,
        "cue_visible_in_sampled_frames": True,
        "physical_consistency_pass": True,
        "extra_subjects": False,
        "viewpoint_pass": True,
        "required_visibility": {
            "face_visible": True,
            "gaze_visible": True,
            "hands_visible": True,
            "product_visible": True,
            "price_area_visible": True,
        },
        "reviewer_notes": "fixture pass",
    }
    (session_dir / "qa_manual_review.json").write_text(
        json.dumps(manual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = qa_gate.run_qa_for_session(session_dir)
    assert report["overall_pass"] is True
    assert report["required_visibility"]["face_visible"] is True
    assert report["manual_review_required"] is False
    assert (session_dir / "qa_report.json").exists()


def test_build_dataset_skips_without_qa_pass(tmp_path, monkeypatch):
    session_dir = copy_fixture(tmp_path)
    (session_dir / "qa_report.json").unlink()
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "data" / "piwm_dataset"
    exit_code = build_main(
        [
            "--archive-root",
            str(tmp_path / "Archive"),
            "--output-dir",
            str(output_dir),
        ]
    )
    assert exit_code == 0
    stats = json.loads((output_dir / "_stats.json").read_text(encoding="utf-8"))
    assert stats["n_sessions_loaded"] == 0
    assert stats["skipped_reasons"] == {"QAGateNotPassedError": 1}
