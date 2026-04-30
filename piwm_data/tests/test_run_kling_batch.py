import json

import pytest

from scripts import run_kling_batch


def test_run_kling_batch_requires_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("KLINGAI_ACCESS_KEY", raising=False)
    monkeypatch.delenv("KLINGAI_SECRET_KEY", raising=False)
    prompt_index = tmp_path / "_prompt_index.jsonl"
    prompt_index.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing Kling environment"):
        run_kling_batch.run_batch(prompt_index, tmp_path / "out", dry_run=False)


def test_run_kling_batch_reuse_existing_does_not_require_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("KLINGAI_ACCESS_KEY", raising=False)
    monkeypatch.delenv("KLINGAI_SECRET_KEY", raising=False)
    prompt_index = tmp_path / "_prompt_index.jsonl"
    prompt_index.write_text("", encoding="utf-8")

    summary = run_kling_batch.run_batch(
        prompt_index,
        tmp_path / "out",
        dry_run=False,
        reuse_existing=True,
    )

    assert summary["n_sessions"] == 0
    assert summary["n_error"] == 0


def test_run_kling_batch_writes_manual_review_template(tmp_path):
    session_dir = tmp_path / "session_001"
    session_dir.mkdir()
    prompt = {
        "session_id": "session_001",
        "viewpoint": "surveillance_oblique",
    }
    (session_dir / "prompt.json").write_text(json.dumps(prompt), encoding="utf-8")

    run_kling_batch._write_manual_review_template(session_dir)

    template = json.loads((session_dir / "qa_manual_review.template.json").read_text(encoding="utf-8"))
    assert template["required_visibility"] == {
        "body_trajectory_visible": None,
        "dwell_visible": None,
        "hands_or_arm_movement_visible": None,
        "product_area_visible": None,
    }


def test_run_kling_batch_summary_counts_by_viewpoint():
    summary = run_kling_batch._summarize(
        [
            {
                "status": "qa_report_written",
                "viewpoint": "salesperson_observable",
                "qa_overall_pass": True,
                "qa_manual_review_required": False,
            },
            {
                "status": "qa_report_written",
                "viewpoint": "surveillance_oblique",
                "qa_overall_pass": False,
                "qa_manual_review_required": True,
            },
            {
                "status": "error",
                "viewpoint": "surveillance_oblique",
            },
        ]
    )
    assert summary["n_sessions"] == 3
    assert summary["n_error"] == 1
    assert summary["viewpoint_counts"]["salesperson_observable"]["qa_pass"] == 1
    assert summary["viewpoint_counts"]["surveillance_oblique"]["manual_review_required"] == 1
    assert summary["viewpoint_counts"]["surveillance_oblique"]["error"] == 1
