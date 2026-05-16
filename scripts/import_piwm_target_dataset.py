"""Import the lightweight guochenmeinian/piwm target-domain data into PIWM v2.2."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from piwm_data import exporters, rules
from piwm_data.migration.piwm_response_mapping import (
    piwm_response_to_action_key,
    piwm_response_to_action_spec,
)
from piwm_data.schemas import (
    ActionOutcome,
    ActionRealization,
    BDISummary,
    FrameRef,
    MainSchemaRecord,
    Persona,
    Provenance,
    TerminalRealization,
)
from piwm_train.ms_swift_adapter import export_ms_swift_jsonl


DEFAULT_SAMPLE_TIMESTAMPS = [2.0, 5.0, 8.0]
TARGET_VIEWPOINT = "target_frontcam"
TARGET_PRODUCT_CATEGORY = "smart_vending_retail"


def import_piwm_target_dataset(
    piwm_root: Path,
    output_dir: Path,
    *,
    repo_root: Path,
    ms_swift_output: Path | None = None,
    overwrite_frames: bool = False,
) -> dict[str, Any]:
    records: list[MainSchemaRecord] = []
    payload_rows: list[dict[str, Any]] = []
    frame_index_rows: list[dict[str, Any]] = []

    labeled_paths = sorted((piwm_root / "data" / "labeled").glob("*.json"))
    if not labeled_paths:
        raise FileNotFoundError(f"no piwm labeled json files found under {piwm_root}")

    for ordinal, labeled_path in enumerate(labeled_paths):
        session_id = labeled_path.stem
        labeled = _read_json(labeled_path)
        manifest = _read_json(piwm_root / "data" / "manifest" / f"{session_id}.json")
        prompt_path = piwm_root / "data" / "prompts" / f"{session_id}.md"
        seed_path = piwm_root / "data" / "seed" / f"{session_id}.txt"
        video_path = piwm_root / "data" / "video" / f"{session_id}.mp4"

        frame_refs, frame_rows = _ensure_sampled_frames(
            video_path=video_path,
            output_dir=output_dir / "frames" / session_id,
            repo_root=repo_root,
            overwrite=overwrite_frames,
        )
        frame_index_rows.extend(frame_rows)

        split = "test" if ordinal >= max(0, len(labeled_paths) - 30) else "train"
        record = _build_main_schema_record(
            labeled=labeled,
            manifest=manifest,
            frame_refs=frame_refs,
            split=split,
        )
        records.append(record)

        payload = exporters.main_schema_record_payload(record)
        payload.update(
            {
                "source_dataset": "guochenmeinian/piwm",
                "source_session_id": session_id,
                "source_labeled_path": _safe_posix(labeled_path),
                "source_manifest_path": _safe_posix(piwm_root / "data" / "manifest" / f"{session_id}.json"),
                "source_prompt_path": _safe_posix(prompt_path) if prompt_path.exists() else None,
                "source_seed_path": _safe_posix(seed_path) if seed_path.exists() else None,
                "source_video_path": _safe_posix(video_path),
                "qa_status": "synthetic_unreviewed",
                "domain_role": "target_frontcam_domain",
                "target_domain": "smart_vending_retail",
                "timeline": _structured_timeline(labeled.get("timeline") or manifest.get("timeline") or {}),
            }
        )
        payload_rows.append(payload)

    _write_jsonl(payload_rows, output_dir / "main_schema.jsonl")
    _write_jsonl(frame_index_rows, output_dir / "frame_index.jsonl")
    exporters.export_state_inference(records, output_dir / "state_inference.jsonl")
    exporters.export_state_inference_with_cue(records, output_dir / "state_inference_with_cue.jsonl")
    exporters.export_transition_modeling(records, output_dir / "transition_modeling.jsonl")
    exporters.export_policy_preference(records, output_dir / "policy_preference.jsonl")
    exporters.export_world_model_continuation(records, output_dir / "world_model_continuation.jsonl")

    summary = _summary(records, output_dir, piwm_root, frame_index_rows)
    (output_dir / "_stats.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if ms_swift_output is not None:
        swift_summary = export_ms_swift_jsonl(
            output_dir,
            ms_swift_output,
            root=repo_root,
            include_continuation=False,
            include_future_verification=False,
            include_action=True,
            validate_images=True,
        )
        summary["ms_swift"] = swift_summary
        (output_dir / "_stats.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def _build_main_schema_record(
    *,
    labeled: dict[str, Any],
    manifest: dict[str, Any],
    frame_refs: list[FrameRef],
    split: str,
) -> MainSchemaRecord:
    session_id = labeled["session_id"]
    aida_stage = labeled["aida_stage"]
    persona_text = labeled.get("persona") or manifest.get("persona") or ""
    persona_type = _infer_persona_type(persona_text)
    latent_state = _infer_latent_state(aida_stage, labeled)
    observable_cues = _infer_observable_cues(aida_stage, labeled)
    intent = _infer_intent(aida_stage, labeled.get("best_action"))
    candidate_specs = [
        piwm_response_to_action_spec(response_id)
        for response_id in labeled["candidate_actions"]
    ]
    candidate_actions = [
        piwm_response_to_action_key(response_id)
        for response_id in labeled["candidate_actions"]
    ]
    best_action = piwm_response_to_action_key(labeled["best_action"])
    best_spec = piwm_response_to_action_spec(labeled["best_action"])
    next_state_by_action: dict[str, ActionOutcome] = {}
    reward_by_action: dict[str, float] = {}

    weights = labeled.get("score_weights") or {"alpha": 0.4, "beta": 0.5, "gamma": 0.2}
    for response_id, action_key in zip(labeled["candidate_actions"], candidate_actions):
        outcome = labeled["outcomes"][response_id]
        spec = piwm_response_to_action_spec(response_id)
        reward = float(outcome["preference_score"])
        next_state_by_action[action_key] = ActionOutcome(
            next_state=_infer_next_state(outcome),
            next_aida_stage=_normalize_aida_stage(outcome["next_aida_stage"]),
            next_bdi=BDISummary(**outcome["next_bdi"]),
            reward=reward,
            reward_components={
                "delta_stage": float(outcome["delta_stage"]),
                "delta_mental": float(outcome["delta_mental"]),
                "action_cost": float(outcome["action_cost"]),
                "alpha": float(weights.get("alpha", 0.4)),
                "beta": float(weights.get("beta", 0.5)),
                "gamma": float(weights.get("gamma", 0.2)),
                "final_reward": reward,
            },
            risk=_normalize_level(outcome["risk"], neutral="low"),
            benefit=_normalize_level(outcome["benefit"], neutral="low"),
            rationale=outcome.get("rationale"),
            dialogue_act=spec["act"],
            act_params=spec["params"],
            intent_tier=rules.derive_intent_tier(persona_type),
            risk_tags=_risk_tags_for_response(response_id, outcome),
            failure_mode=None,
            outcome_type="success",
        )
        reward_by_action[action_key] = reward

    realization = _terminal_realization_for_response(labeled["best_action"], labeled["realization"])
    return MainSchemaRecord(
        state_id=f"target_{session_id}",
        images=frame_refs,
        product_category=TARGET_PRODUCT_CATEGORY,
        split=split,
        visual_state={
            "summary": labeled["observable_behavior"],
            "engagement_pattern": labeled["observable_behavior"],
            "gaze_and_attention": labeled.get("facial_expression") or labeled["observable_behavior"],
            "body_and_hands": labeled.get("body_posture") or labeled["observable_behavior"],
        },
        observable_cues=observable_cues,
        viewpoint=TARGET_VIEWPOINT,
        persona=Persona(type=persona_type, description=persona_text),
        aida_stage=aida_stage,
        latent_state=latent_state,
        intent=intent,
        bdi=BDISummary(**labeled["bdi"]),
        proactive_score=rules.derive_proactive_score(latent_state),
        candidate_actions=candidate_actions,
        best_action=best_action,
        candidate_action_specs=candidate_specs,
        best_action_spec=best_spec,
        best_action_realization=_action_realization_from_terminal(realization, labeled["best_action"]),
        dialogue_act=best_spec["act"],
        act_params=best_spec["params"],
        realization=realization,
        next_state_by_action=next_state_by_action,
        next_state_by_action_v2=next_state_by_action,
        reward_by_action=reward_by_action,
        rationale="Imported from lightweight piwm target-frontcam labeled outcome scores.",
        compatibility_tier="green",
        provenance=[
            Provenance(field_name="visual_state", source="annotation_override", rule_version=rules.RULE_VERSION),
            Provenance(field_name="candidate_action_specs", source="annotation_override", rule_version=rules.RULE_VERSION),
            Provenance(field_name="next_state_by_action", source="annotation_override", rule_version=rules.RULE_VERSION),
        ],
        is_anchor=False,
    )


def _ensure_sampled_frames(
    *,
    video_path: Path,
    output_dir: Path,
    repo_root: Path,
    overwrite: bool,
) -> tuple[list[FrameRef], list[dict[str, Any]]]:
    if not video_path.exists():
        raise FileNotFoundError(f"missing piwm target video: {video_path}")
    cv2 = _load_cv2()
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path.as_posix())
    if not cap.isOpened():
        raise ValueError(f"failed to open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
    duration_sec = frame_count / fps if fps else 0.0
    timestamps = _sampling_timestamps(duration_sec)
    refs: list[FrameRef] = []
    rows: list[dict[str, Any]] = []

    try:
        for index, timestamp_sec in enumerate(timestamps):
            out_path = output_dir / f"{index:03d}.jpg"
            if overwrite or not out_path.exists():
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
                ok, frame = cap.read()
                if not ok:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, min(max(int(frame_count) - 1, 0), int(index * frame_count / 3)))
                    ok, frame = cap.read()
                if not ok:
                    raise ValueError(f"failed to read frame {index} at {timestamp_sec}s from {video_path}")
                if not cv2.imwrite(out_path.as_posix(), frame):
                    raise ValueError(f"failed to write frame: {out_path}")
            relative_path = out_path.resolve().relative_to(repo_root.resolve()).as_posix()
            refs.append(FrameRef(index=index, relative_path=relative_path, timestamp_sec=timestamp_sec))
            rows.append(
                {
                    "session_id": video_path.stem,
                    "frame_index": index,
                    "timestamp_sec": timestamp_sec,
                    "relative_path": relative_path,
                    "source_video_path": video_path.as_posix(),
                    "viewpoint": TARGET_VIEWPOINT,
                    "fps": fps,
                    "duration_sec": duration_sec,
                }
            )
    finally:
        cap.release()
    return refs, rows


def _sampling_timestamps(duration_sec: float) -> list[float]:
    if duration_sec <= 0:
        return DEFAULT_SAMPLE_TIMESTAMPS
    return [
        round(min(DEFAULT_SAMPLE_TIMESTAMPS[0], max(duration_sec * 0.25, 0.0)), 3),
        round(min(DEFAULT_SAMPLE_TIMESTAMPS[1], max(duration_sec * 0.50, 0.0)), 3),
        round(min(DEFAULT_SAMPLE_TIMESTAMPS[2], max(duration_sec - 0.1, duration_sec * 0.75, 0.0)), 3),
    ]


def _terminal_realization_for_response(response_id: str, realization: dict[str, Any]) -> TerminalRealization:
    spec = piwm_response_to_action_spec(response_id)
    payload = dict(realization)
    payload["surface_text"] = payload.get("surface_text", "")
    payload["dialogue_act"] = spec["act"]
    payload["act_params"] = spec["params"]
    payload["co_acts"] = rules.legacy_co_acts_from_params(spec["params"])
    payload["legacy_action"] = None
    return TerminalRealization(**payload)


def _action_realization_from_terminal(realization: TerminalRealization, response_id: str) -> ActionRealization:
    return ActionRealization(
        utterance=realization.surface_text or "（静默）",
        physical_action="智能售货柜通过屏幕、语音、灯效和必要的柜体反馈执行响应。",
        timing="设备前置摄像头识别到顾客当前状态后立即触发。",
        rationale=f"target terminal response imported from piwm response_id={response_id}",
    )


def _infer_persona_type(persona_text: str) -> str:
    text = persona_text or ""
    if any(token in text for token in ["无聊", "逛逛", "随便"]):
        return "browser_low_intent"
    if any(token in text for token in ["送礼", "礼物"]):
        return "gift_buyer_uncertain"
    if any(token in text for token in ["老顾客", "熟悉", "品牌"]):
        return "experienced_brand_loyal"
    if any(token in text for token in ["果断", "明确", "不差钱", "预算充足"]):
        return "price_insensitive_decisive"
    if any(token in text for token in ["价格", "预算", "谨慎", "犹豫"]):
        return "price_sensitive_cautious"
    return "first_time_high_consideration"


def _infer_observable_cues(aida_stage: str, labeled: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(labeled.get(field, ""))
        for field in ["observable_behavior", "facial_expression", "body_posture"]
    )
    if "离开" in text or "转身" in text:
        return ["brief_glance_walking_past"]
    if "扫码" in text or "支付" in text or aida_stage == "action":
        return ["approaching_counter"]
    if "比较" in text or "切换" in text:
        return ["comparing_two_products"]
    if "前倾" in text or "停留" in text:
        return ["long_dwell_with_price_check"]
    return ["brief_glance_walking_past"]


def _infer_latent_state(aida_stage: str, labeled: dict[str, Any]) -> str:
    best = labeled.get("best_action", "")
    if aida_stage == "attention":
        return "early_browsing" if best != "hold_ambient" else "disengaged"
    if aida_stage == "interest":
        return "active_evaluation"
    if aida_stage == "desire":
        return "ready_to_decide" if best.startswith("recommend") else "continued_hesitation"
    if aida_stage == "action":
        return "post_decision_reassurance"
    return "active_evaluation"


def _infer_next_state(outcome: dict[str, Any]) -> str:
    stage = _normalize_aida_stage(outcome["next_aida_stage"])
    reward = float(outcome["preference_score"])
    if outcome.get("risk") == "high" and reward < 0:
        return "defensive_withdrawal"
    if stage == "attention":
        return "early_browsing" if reward >= 0 else "disengaged"
    if stage == "interest":
        return "active_evaluation" if reward >= 0 else "continued_hesitation"
    if stage == "desire":
        return "ready_to_decide" if reward >= 0.15 else "continued_hesitation"
    if stage == "action":
        return "post_decision_reassurance"
    return "active_evaluation"


def _normalize_aida_stage(stage: str) -> str:
    if stage == "satisfaction":
        return "action"
    if stage in {"attention", "interest", "desire", "action"}:
        return stage
    raise ValueError(f"unsupported AIDA stage: {stage}")


def _infer_intent(aida_stage: str, best_action: str | None) -> str:
    if best_action in {"inform_price_brief", "inform_comparison_brief"}:
        return "compare_value_for_money"
    if best_action in {"reassure_time_wait", "reassure_decision"}:
        return "seek_reassurance"
    if best_action in {"inform_demo_brief"}:
        return "request_demonstration"
    if aida_stage == "action":
        return "confirm_choice"
    if aida_stage == "attention":
        return "no_clear_intent"
    return "explore_options"


def _risk_tags_for_response(response_id: str, outcome: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if response_id == "recommend_firm":
        tags.append("pressure_reactance")
    if response_id.startswith("inform_") and outcome.get("risk") == "medium":
        tags.append("feature_dump")
    if response_id.startswith("greet_") and outcome.get("risk") == "medium":
        tags.append("timing_intrusion")
    return tags


def _normalize_level(value: str, *, neutral: str) -> str:
    normalized = str(value).strip().lower().replace("_", " ")
    if normalized in {"very low", "low"}:
        return "low"
    if normalized in {"medium", "moderate"}:
        return "medium"
    if normalized in {"medium-high", "medium high", "high"}:
        return "high"
    if normalized == "neutral":
        return neutral
    raise ValueError(f"unsupported risk/benefit level: {value}")


def _structured_timeline(timeline: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for key, event in timeline.items():
        start, end = _parse_time_key(key)
        rows.append(
            {
                "start_sec": start,
                "end_sec": end,
                "event": event,
                "primary_signal": _primary_signal(event),
            }
        )
    return rows


def _parse_time_key(key: str) -> tuple[int, int]:
    parts = key.removeprefix("t_").split("_")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[0]), int(parts[1])
    return 0, 0


def _primary_signal(event: str) -> str:
    if "离开" in event or "转身" in event:
        return "disengage"
    if "比较" in event:
        return "compare"
    if "犹豫" in event or "思考" in event:
        return "hesitate"
    if "支付" in event or "扫码" in event:
        return "commit"
    if "走近" in event:
        return "approach"
    return "observe"


def _summary(
    records: list[MainSchemaRecord],
    output_dir: Path,
    piwm_root: Path,
    frame_index_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "artifact": "piwm_target_frontcam_v1",
        "schema_version": rules.ACTION_SCHEMA_VERSION,
        "source_repo": "guochenmeinian/piwm",
        "source_root": piwm_root.as_posix(),
        "output_dir": output_dir.as_posix(),
        "n_records": len(records),
        "n_frames": len(frame_index_rows),
        "viewpoint_counts": _counts(record.viewpoint for record in records),
        "split_counts": _counts(record.split or "unknown" for record in records),
        "best_act_counts": _counts(record.best_action_spec.act if record.best_action_spec else "unknown" for record in records),
        "best_action_key_counts": _counts(record.best_action for record in records),
        "qa_status_counts": {"synthetic_unreviewed": len(records)},
        "notes": [
            "Imported target-domain front-camera data from lightweight piwm.",
            "The final 30 samples are split=test as an unreviewed in-domain eval candidate; they still require QA before paper claims.",
        ],
    }


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(rows: list[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
    return len(rows)


def _safe_posix(path: Path) -> str:
    return path.expanduser().resolve().as_posix()


def _load_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to extract piwm target frames.") from exc
    return cv2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--piwm-root", type=Path, default=Path("../piwm"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/official/piwm_target_v1"))
    parser.add_argument("--ms-swift-output", type=Path, default=Path("data/official/ms_swift/piwm_train_target_specialization_v1.jsonl"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-ms-swift", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path.cwd().resolve()
    output_dir = args.output_dir.resolve() if args.output_dir.is_absolute() else repo_root / args.output_dir
    if args.overwrite and output_dir.exists():
        shutil.rmtree(output_dir)
    summary = import_piwm_target_dataset(
        piwm_root=(args.piwm_root.resolve() if args.piwm_root.is_absolute() else (repo_root / args.piwm_root).resolve()),
        output_dir=output_dir,
        repo_root=repo_root,
        ms_swift_output=None if args.no_ms_swift else (args.ms_swift_output.resolve() if args.ms_swift_output.is_absolute() else repo_root / args.ms_swift_output),
        overwrite_frames=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
