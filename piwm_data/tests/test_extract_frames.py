import json
from pathlib import Path

import pytest

from scripts import extract_frames


cv2 = pytest.importorskip("cv2")


def write_test_video(path: Path, fps: int = 10, seconds: int = 3):
    import numpy as np

    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (64, 48),
    )
    assert writer.isOpened()
    for i in range(fps * seconds):
        frame = np.full((48, 64, 3), i % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()


def test_extract_frames_for_session_writes_manifest(tmp_path):
    session_dir = tmp_path / "session_001"
    session_dir.mkdir()
    prompt = {
        "session_id": "session_001",
        "viewpoint": "salesperson_observable",
        "training_input_mode": "multi_image_single_turn",
        "frame_sampling_plan": [
            {"index": 0, "timestamp_sec": 0.2, "role": "cue_onset"},
            {"index": 1, "timestamp_sec": 1.0, "role": "cue_peak"},
            {"index": 2, "timestamp_sec": 2.0, "role": "cue_resolution"},
        ],
    }
    (session_dir / "prompt.json").write_text(json.dumps(prompt), encoding="utf-8")
    write_test_video(session_dir / "video.mp4")

    result = extract_frames.extract_frames_for_session(session_dir)

    assert result["n_sampled_frames"] == 3
    assert result["viewpoint"] == "salesperson_observable"
    manifest = json.loads((session_dir / "frame_manifest.json").read_text(encoding="utf-8"))
    assert manifest["viewpoint"] == "salesperson_observable"
    assert manifest["training_input_mode"] == "multi_image_single_turn"
    assert len(manifest["sampled_frames"]) == 3
    assert (session_dir / "frames" / "000.jpg").exists()
    assert (session_dir / "frames" / "001.jpg").exists()
    assert (session_dir / "frames" / "002.jpg").exists()


def test_extract_frames_refuses_overwrite_without_flag(tmp_path):
    session_dir = tmp_path / "session_001"
    session_dir.mkdir()
    prompt = {
        "session_id": "session_001",
        "viewpoint": "salesperson_observable",
        "frame_sampling_plan": [
            {"index": 0, "timestamp_sec": 0.2, "role": "cue_onset"},
            {"index": 1, "timestamp_sec": 1.0, "role": "cue_peak"},
            {"index": 2, "timestamp_sec": 2.0, "role": "cue_resolution"},
        ],
    }
    (session_dir / "prompt.json").write_text(json.dumps(prompt), encoding="utf-8")
    write_test_video(session_dir / "video.mp4")
    extract_frames.extract_frames_for_session(session_dir)
    with pytest.raises(FileExistsError):
        extract_frames.extract_frames_for_session(session_dir)
