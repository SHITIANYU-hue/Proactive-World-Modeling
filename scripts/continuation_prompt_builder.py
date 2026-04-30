"""Build action-conditioned continuation prompts for PIWM parent sessions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from piwm_data import reaction_templates, rules
from piwm_data.schemas import ContinuationRole, MainSchemaRecord
from scripts.prompt_builder import PRODUCT_SCENES, VIEWPOINT_CAMERA, VIEWPOINT_NEGATIVE, forbidden_label_hits


CONTINUATION_FRAME_SAMPLING_PLAN = [
    {"index": 0, "timestamp_sec": 1.0, "role": "reaction_onset"},
    {"index": 1, "timestamp_sec": 3.0, "role": "reaction_peak"},
    {"index": 2, "timestamp_sec": 5.0, "role": "reaction_settle"},
]


def build_continuation_prompt(
    parent_record: MainSchemaRecord,
    candidate_action: str,
    continuation_role: ContinuationRole | str,
) -> dict[str, Any]:
    continuation_role = ContinuationRole(continuation_role)
    if candidate_action not in parent_record.candidate_actions:
        raise ValueError(f"candidate_action not in parent candidate_actions: {candidate_action}")
    outcome = parent_record.next_state_by_action[candidate_action]
    template_id, template = reaction_templates.template_for_next_state(outcome.next_state)
    scene = _scene_for_parent(parent_record)
    action_event = rules.ACTION_VISIBLE_BEHAVIOR[candidate_action]
    store_setting = PRODUCT_SCENES[parent_record.product_category]["store"]
    continuity_prefix = (
        f"Continuing from the previous shot in the same store setting ({store_setting}), "
        "the same single shopper is in the same position with the same products visible. "
        "No cuts, no scene change, no new people enter."
    )
    timeline = [
        {"time": "0-1s", "event": f"{continuity_prefix} {action_event}."},
        {"time": "1-2s", "event": template["physical_change"] + "."},
        {"time": "2-4s", "event": f"{template['head_gaze']}. {template['hands']}."},
        {"time": "4-5s", "event": template["movement"] + "."},
    ]
    sections = {
        "camera": _continuation_camera(parent_record.viewpoint),
        "scene": scene,
        "continuity": continuity_prefix,
        "action_event": action_event,
        "reaction_timeline": timeline,
        "negative": _continuation_negative(parent_record.viewpoint),
    }
    prompt = _join_continuation_sections(sections)
    return {
        "continuation_id": f"{parent_record.state_id}#{continuation_role.value}_{candidate_action}",
        "parent_state_id": parent_record.state_id,
        "candidate_action": candidate_action,
        "continuation_role": continuation_role.value,
        "continuation_viewpoint": parent_record.viewpoint,
        "product_category": parent_record.product_category,
        "duration_seconds": template["duration_window_sec"][1],
        "expected_next_state": outcome.next_state,
        "expected_next_aida_stage": outcome.next_aida_stage,
        "expected_reward": outcome.reward,
        "expected_risk": outcome.risk,
        "expected_benefit": outcome.benefit,
        "reaction_template_id": template_id,
        "frame_sampling_plan": CONTINUATION_FRAME_SAMPLING_PLAN,
        "kling_prompt_sections": sections,
        "kling_prompt": prompt,
        "forbidden_label_hits": forbidden_label_hits(prompt),
    }


def build_best_worst_prompts(parent_record: MainSchemaRecord) -> list[dict[str, Any]]:
    best = parent_record.best_action
    worst = min(
        (action for action in parent_record.candidate_actions if action != best),
        key=lambda action: (
            parent_record.reward_by_action[action],
            rules.ACTIONS.index(action),
        ),
        default=None,
    )
    prompts = [build_continuation_prompt(parent_record, best, ContinuationRole.BEST)]
    if worst is not None:
        prompts.append(build_continuation_prompt(parent_record, worst, ContinuationRole.WORST))
    return prompts


def write_continuation_prompts(
    records: Iterable[MainSchemaRecord],
    out_root: Path,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    for record in records:
        for prompt_json in build_best_worst_prompts(record):
            out_dir = out_root / record.state_id / "continuations" / _continuation_dir_name(prompt_json)
            out_path = out_dir / "continuation_prompt.json"
            if out_path.exists() and not overwrite:
                raise FileExistsError(f"continuation_prompt.json exists: {out_path}. Use --overwrite to replace it.")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(prompt_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            written.append(
                {
                    "continuation_id": prompt_json["continuation_id"],
                    "parent_state_id": prompt_json["parent_state_id"],
                    "candidate_action": prompt_json["candidate_action"],
                    "continuation_role": prompt_json["continuation_role"],
                    "continuation_viewpoint": prompt_json["continuation_viewpoint"],
                    "expected_next_state": prompt_json["expected_next_state"],
                    "expected_reward": prompt_json["expected_reward"],
                    "reaction_template_id": prompt_json["reaction_template_id"],
                    "prompt_path": out_path.as_posix(),
                    "prompt_chars": len(prompt_json["kling_prompt"]),
                    "forbidden_label_hits": prompt_json["forbidden_label_hits"],
                }
            )
    return written


def load_main_schema_jsonl(path: Path) -> list[MainSchemaRecord]:
    records: list[MainSchemaRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(MainSchemaRecord.model_validate_json(line))
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build action-continuation Kling prompt files.")
    parser.add_argument("--main-schema", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--index-out", type=Path, default=None)
    args = parser.parse_args(argv)

    records = load_main_schema_jsonl(args.main_schema)
    if args.limit is not None:
        records = records[: args.limit]
    written = write_continuation_prompts(records, args.out_root, overwrite=args.overwrite)
    index_out = args.index_out or args.out_root / "_continuation_prompt_index.jsonl"
    _write_jsonl(written, index_out)
    stats = {
        "n_continuation_prompts": len(written),
        "n_with_forbidden_label_hits": sum(1 for row in written if row["forbidden_label_hits"]),
        "out_root": args.out_root.as_posix(),
        "index_out": index_out.as_posix(),
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def _continuation_camera(viewpoint: str) -> str:
    return VIEWPOINT_CAMERA[viewpoint].replace("10-second", "5-second")


def _scene_for_parent(parent_record: MainSchemaRecord) -> str:
    product = PRODUCT_SCENES[parent_record.product_category]
    return f"{product['store']}; visible product setup: {product['product']}."


def _continuation_negative(viewpoint: str) -> str:
    return (
        f"{VIEWPOINT_NEGATIVE[viewpoint]}, no scene change, no new shoppers, no costume change, "
        "no product swap, no inconsistent reaction, no enum-like text, no floating labels, no UI overlays"
    )


def _join_continuation_sections(sections: dict[str, Any]) -> str:
    timeline = "\n".join(f"- {entry['time']}: {entry['event']}" for entry in sections["reaction_timeline"])
    return (
        f"Camera: {sections['camera']}\n"
        f"Scene: {sections['scene']}\n"
        f"Continuity: {sections['continuity']}\n"
        f"Visible intervention: {sections['action_event']}\n"
        f"Reaction timeline:\n{timeline}\n"
        f"Negative constraints: {sections['negative']}"
    )


def _continuation_dir_name(prompt_json: dict[str, Any]) -> str:
    return f"{prompt_json['continuation_role']}_{prompt_json['candidate_action']}"


def _write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count


if __name__ == "__main__":
    raise SystemExit(main())
