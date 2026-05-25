#!/usr/bin/env python3
"""Build the GuidanceSalesBench dataset bundle.

The default bundle is lightweight and keeps large media in their canonical
source locations. Pass --include-media to materialize target frames and the
available real-shooting videos into the output directory for dataset upload.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPERATIONAL_ACTS = ["Greet", "Elicit", "Inform", "Recommend", "Hold"]

GENERAL_FILES = [
    "_stats.json",
    "main_schema.jsonl",
    "state_inference.jsonl",
    "state_inference_with_cue.jsonl",
    "transition_modeling.jsonl",
    "policy_preference.jsonl",
    "world_model_continuation.jsonl",
]

GENERAL_SPLIT_FILES = [
    "general_split_seed42.json",
    "general_train_parents.txt",
    "general_val_parents.txt",
]

GENERAL_STAGE1_FILES = [
    "user_intent_train.jsonl",
    "user_intent_train_summary.json",
    "user_intent_val.jsonl",
    "user_intent_val_summary.json",
    "next_state_prediction_train.jsonl",
    "next_state_prediction_train_summary.json",
    "next_state_prediction_val.jsonl",
    "next_state_prediction_val_summary.json",
]

TARGET_FRONTCAM_FILES = [
    "_stats.json",
    "main_schema.jsonl",
    "frame_index.jsonl",
    "state_inference.jsonl",
    "state_inference_with_cue.jsonl",
    "transition_modeling.jsonl",
    "policy_preference.jsonl",
    "world_model_continuation.jsonl",
    "split_rebalance_5act_summary.json",
    "split_rebalance_5act_summary.md",
]

TARGET_SPLIT_FILES = {
    "target_frontcam_5act_test_all.jsonl": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_all.jsonl",
    "target_frontcam_5act_test_all_summary.json": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_all_summary.json",
    "target_frontcam_5act_test_action_selection.jsonl": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_action_selection.jsonl",
    "target_frontcam_5act_test_action_selection_summary.json": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_action_selection_summary.json",
    "target_frontcam_5act_test_user_intent.jsonl": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_user_intent.jsonl",
    "target_frontcam_5act_test_user_intent_summary.json": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_user_intent_summary.json",
    "target_frontcam_5act_test_no_intervention_next_state.jsonl": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_no_intervention_next_state.jsonl",
    "target_frontcam_5act_test_no_intervention_next_state_summary.json": "data/official/domain_specialization_eval_v2/target_frontcam_5act_test_no_intervention_next_state_summary.json",
}

TARGET_TRAIN_FILES = {
    "stage2_target_5act_train_71.jsonl": "data/official/ms_swift/piwm_train_stage2_target_5act_v1.jsonl",
    "stage2_target_5act_greet_aug_v2_86.jsonl": "data/official/ms_swift/piwm_train_stage2_target_5act_greet_aug_v2.jsonl",
    "stage2_target_v2_balanced_190.jsonl": "data/official/ms_swift/piwm_train_stage2_target_v2_balanced.jsonl",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_text_normalized(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    text = src.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def best_act(record: dict[str, Any]) -> str | None:
    spec = record.get("best_action_spec")
    if isinstance(spec, dict) and spec.get("act"):
        return str(spec["act"])
    value = record.get("best_action")
    if not value:
        return None
    value = str(value)
    return value[:1].upper() + value[1:] if value.islower() else value


def jsonl_best_act_counts(path: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in iter_jsonl(path):
        act = best_act(record)
        if act:
            counts[act] += 1
    return dict(sorted(counts.items()))


def copy_general(root: Path, out: Path) -> dict[str, Any]:
    src = root / "data/official/piwm_train_synth_v2"
    dst = out / "general"
    for name in GENERAL_FILES:
        copy_file(src / name, dst / name)
    for name in GENERAL_SPLIT_FILES:
        copy_file(src / name, dst / "splits" / name)
    for name in GENERAL_STAGE1_FILES:
        copy_file(src / name, dst / "sft_stage1" / name)

    stats = read_json(src / "_stats.json")
    files = {}
    for name in GENERAL_FILES:
        files[name] = line_count(src / name) if name.endswith(".jsonl") else None
    for name in GENERAL_STAGE1_FILES:
        files[f"sft_stage1/{name}"] = line_count(src / name) if name.endswith(".jsonl") else None
    write_text(
        dst / "README.md",
        """# GuidanceSalesBench / general

Synthetic general-domain PIWM data exported from `data/official/piwm_train_synth_v2`.

This partition is schema v2.2 general guidance-sales supervision. It keeps the
current operational action space fixed to `Greet / Elicit / Inform / Recommend / Hold`.
`Reassure` is not an operational label here.
""",
    )
    return {
        "partition": "general",
        "source": "data/official/piwm_train_synth_v2",
        "records": stats.get("n_sessions_loaded"),
        "schema_version": stats.get("schema_version"),
        "line_counts": files,
        "best_act_counts": jsonl_best_act_counts(src / "main_schema.jsonl"),
        "media_materialized": False,
    }


def copy_target(root: Path, out: Path, include_media: bool) -> dict[str, Any]:
    src = root / "data/official/piwm_target_v1"
    dst = out / "target"
    frontcam_dst = dst / "frontcam"
    for name in TARGET_FRONTCAM_FILES:
        copy_file(src / name, frontcam_dst / name)

    prompt_src = root / "data/official/piwm_target_promptready_v1"
    prompt_dst = dst / "prompt_ready_queue"
    for src_name, dst_name in [
        ("README.md", "README.md"),
        ("_stats.json", "promptready_stats.json"),
        ("promptready_index.jsonl", "promptready_index.jsonl"),
    ]:
        copy_file(prompt_src / src_name, prompt_dst / dst_name)

    eval_counts: dict[str, int] = {}
    for dst_name, rel_src in TARGET_SPLIT_FILES.items():
        split_src = root / rel_src
        copy_file(split_src, dst / "eval_5act" / dst_name)
        eval_counts[dst_name] = line_count(split_src) if dst_name.endswith(".jsonl") else None

    train_counts: dict[str, int] = {}
    for dst_name, rel_src in TARGET_TRAIN_FILES.items():
        train_src = root / rel_src
        copy_file(train_src, dst / "training_splits" / dst_name)
        train_counts[dst_name] = line_count(train_src)

    if include_media:
        shutil.copytree(src / "frames", frontcam_dst / "frames", dirs_exist_ok=True)

    stats = read_json(src / "_stats.json")
    write_text(
        dst / "README.md",
        """# GuidanceSalesBench / target

Target-domain front-camera smart-vending data from `data/official/piwm_target_v1`.

The full source table contains historical/source compatibility labels, including
`Reassure`. Current operational training/evaluation files in `splits/` use the
fixed five-act space: `Greet / Elicit / Inform / Recommend / Hold`.
""",
    )
    return {
        "partition": "target",
        "source": "data/official/piwm_target_v1",
        "records": stats.get("n_records"),
        "frames": stats.get("n_frames"),
        "schema_version": stats.get("schema_version"),
        "source_best_act_counts": stats.get("best_act_counts"),
        "eval_5act_line_counts": eval_counts,
        "training_split_line_counts": train_counts,
        "promptready_source": "data/official/piwm_target_promptready_v1",
        "promptready_records": read_json(prompt_src / "_stats.json").get("records"),
        "media_materialized": include_media,
    }


def available_video_path(video_root: Path, metadata_video_path: str) -> Path | None:
    name = Path(metadata_video_path).name
    candidates = [video_root / name]
    if name[:1] == "0":
        candidates.append(video_root / f"{int(Path(name).stem)}.mp4")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def copy_real_shooting(root: Path, out: Path, include_media: bool) -> dict[str, Any]:
    src = root / "references/piwm_lightweight/data/eval/real"
    video_root = root / "references/piwm_lightweight/data/videos/real"
    dst = out / "real_shooting"
    eval_dst = dst / "eval_real"
    copy_file(src / "index.json", eval_dst / "index.json")

    metadata_records = []
    media_rows = []
    for meta_path in sorted(src.glob("real_*.json")):
        copy_file(meta_path, eval_dst / "metadata" / meta_path.name)
        record = read_json(meta_path)
        metadata_records.append(record)
        video_path = record.get("video_path", "")
        local_video = available_video_path(video_root, video_path)
        if include_media and local_video:
            media_dst = dst / "videos" / "real" / local_video.name
            copy_file(local_video, media_dst)
            materialized_path = str(media_dst.relative_to(out))
        else:
            materialized_path = None
        media_rows.append(
            {
                "session_id": record.get("session_id"),
                "metadata_file": f"eval_real/metadata/{meta_path.name}",
                "metadata_video_path": video_path,
                "source_video_path": str(local_video.relative_to(root)) if local_video else None,
                "hf_existing_path": (
                    f"piwm_lightweight/data/videos/real/{local_video.name}"
                    if local_video
                    else None
                ),
                "materialized_path": materialized_path,
                "video_status": "available" if local_video else "missing",
            }
        )

    with (eval_dst / "metadata_index.jsonl").open("w", encoding="utf-8") as f:
        for record in metadata_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    with (eval_dst / "media_manifest.jsonl").open("w", encoding="utf-8") as f:
        for row in media_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    protocol_src = root / "data/official/piwm_realshoot_v1"
    if protocol_src.exists():
        for name in [
            "README.md",
            "realshoot_manifest_template.json",
            "realshoot_manifest_sample.jsonl",
            "realshoot_manifest_summary.json",
        ]:
            copy_file(protocol_src / name, dst / "protocol_template" / name)

    index = read_json(src / "index.json")
    status_counts = Counter(row["video_status"] for row in media_rows)
    write_text(
        eval_dst / "README.md",
        """# GuidanceSalesBench / real_shooting

Entity-shot smart-vending evaluation metadata imported from
`guochenmeinian/piwm/data/eval/real`.

`index.json` and `metadata/*.json` are the source metadata. `media_manifest.jsonl`
records which matching MP4 files are available in the current local/Hugging Face
media payload. Missing videos are left explicit rather than silently inferred.
""",
    )
    write_text(
        dst / "README.md",
        """# GuidanceSalesBench / real_shooting

This partition contains entity-shot smart-vending metadata in `eval_real/` and
the existing real-shooting protocol template in `protocol_template/`.

The protocol template is not counted as collected data.
""",
    )
    return {
        "partition": "real_shooting",
        "source": "references/piwm_lightweight/data/eval/real",
        "source_github": "https://github.com/guochenmeinian/piwm/tree/main/data/eval/real",
        "planned_records": index.get("total_planned"),
        "metadata_records": len(metadata_records),
        "index_available": index.get("available"),
        "video_status_counts": dict(status_counts),
        "media_materialized": include_media,
    }


def write_human_label(out: Path) -> dict[str, Any]:
    dst = out / "human_labels"
    dst.mkdir(parents=True, exist_ok=True)
    write_text(dst / "target_5act" / "annotator_a.jsonl", "")
    write_text(dst / "target_5act" / "annotator_b.jsonl", "")
    write_text(dst / "target_5act" / "annotator_c.jsonl", "")
    write_text(dst / "general_probe" / "annotator_a.jsonl", "")
    schema = {
        "label_version": "guidance_sales_bench_human_label_v0",
        "status": "empty_placeholder",
        "allowed_operational_acts": OPERATIONAL_ACTS,
        "fields": [
            {"name": "sample_id", "type": "string", "required": True},
            {"name": "partition", "type": "string", "required": True},
            {"name": "annotator_id", "type": "string", "required": True},
            {"name": "best_act", "type": "string", "required": True},
            {"name": "rationale", "type": "string", "required": False},
            {"name": "quality_flag", "type": "string", "required": False},
            {"name": "created_at", "type": "string", "required": False},
        ],
    }
    write_json(dst / "label_schema.json", schema)
    template_src = repo_root() / "data/official/annotation_pack_v2"
    if template_src.exists():
        for name in [
            "README.md",
            "annotation_template_single_annotator.csv",
            "annotation_template_three_annotators.xlsx",
        ]:
            source = template_src / name
            target = dst / "templates" / "target_5act" / name
            if name.endswith(".csv"):
                copy_text_normalized(source, target)
            else:
                copy_file(source, target)
    write_text(
        dst / "README.md",
        """# GuidanceSalesBench / human_label

Reserved partition for future human labels.

All annotator JSONL files are intentionally empty. Use `label_schema.json` and
the templates under `templates/` when human annotations are added later. Theory
labels from annotation packs are not copied here as human labels.
""",
    )
    return {
        "partition": "human_labels",
        "records": 0,
        "status": "empty_placeholder",
        "label_files": [
            "human_labels/target_5act/annotator_a.jsonl",
            "human_labels/target_5act/annotator_b.jsonl",
            "human_labels/target_5act/annotator_c.jsonl",
            "human_labels/general_probe/annotator_a.jsonl",
        ],
        "schema_file": "human_labels/label_schema.json",
    }


def write_root_docs(out: Path, manifest: dict[str, Any]) -> None:
    write_json(out / "MANIFEST.json", manifest)
    write_text(
        out / "README.md",
        """# GuidanceSalesBench

GuidanceSalesBench is the unified dataset bundle for guidance-sales proactive
intent/world-model work. It is organized into four partitions:

- `general`: schema v2.2 synthetic general-domain guidance-sales data.
- `target`: target-domain smart-vending front-camera data and current 5-act splits.
- `real_shooting`: entity-shot smart-vending evaluation metadata and media manifest.
- `human_labels`: empty placeholder for future human annotation.

The current operational act space is fixed as `Greet / Elicit / Inform /
Recommend / Hold`. `Reassure` is retained only in source/compatibility provenance
where it already exists, and is not an operational training/evaluation/inference
label in the current splits.
""",
    )


def build(output_root: Path, include_media: bool) -> dict[str, Any]:
    root = repo_root()
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    partitions = [
        copy_general(root, output_root),
        copy_target(root, output_root, include_media),
        copy_real_shooting(root, output_root, include_media),
        write_human_label(output_root),
    ]
    manifest = {
        "artifact": "GuidanceSalesBench",
        "version": "v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(output_root),
        "include_media": include_media,
        "operational_acts": OPERATIONAL_ACTS,
        "reassure_policy": "source_compatibility_only_not_operational",
        "partitions": partitions,
    }
    write_root_docs(output_root, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default="data/GuidanceSalesBench",
        help="Output directory for the GuidanceSalesBench bundle.",
    )
    parser.add_argument(
        "--include-media",
        action="store_true",
        help="Copy target frames and available real-shooting videos into the bundle.",
    )
    args = parser.parse_args()
    manifest = build(Path(args.output_root), args.include_media)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
