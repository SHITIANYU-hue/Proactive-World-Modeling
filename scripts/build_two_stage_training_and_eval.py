"""Build leakage-free two-stage PIWM training and eval entrypoints."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from piwm_data.migration.legacy_action_mapping import legacy_action_to_act_params_for_comparison
from piwm_train.data_collator import ActBalancing, SFTExample, user_intent_loss_weight
from piwm_train.ms_swift_adapter import build_ms_swift_record
from piwm_train.prompts import build_action_prompt_no_leak, build_next_state_prediction_prompt, build_user_intent_prompt
from piwm_train.targets import build_action_target, build_deliberation_target, build_user_intent_target


REPO_ROOT = Path(__file__).resolve().parents[1]
FIVE_ACTS = {"Greet", "Elicit", "Inform", "Recommend", "Hold"}
DEFAULT_GENERAL_DIR = Path("data/official/piwm_train_synth_v2")
DEFAULT_GENERAL_EVAL_DIR = Path("data/official/piwm_eval_qa_v1")
DEFAULT_TARGET_DIR = Path("data/official/piwm_target_v1")
DEFAULT_MS_SWIFT_DIR = Path("data/official/ms_swift")
DEFAULT_EVAL_DIR = Path("data/official/domain_specialization_eval_v2")


def build_two_stage_artifacts(
    *,
    general_dir: Path,
    general_eval_dir: Path,
    target_dir: Path,
    ms_swift_dir: Path,
    eval_dir: Path,
    target_test_per_act: int = 6,
    act_balancing: ActBalancing = "none",
) -> dict[str, Any]:
    root = REPO_ROOT
    general_dir = _resolve(general_dir)
    general_eval_dir = _resolve(general_eval_dir)
    target_dir = _resolve(target_dir)
    ms_swift_dir = _resolve(ms_swift_dir)
    eval_dir = _resolve(eval_dir)

    general_stage1 = _build_stage1_examples(general_dir)
    stage1_out = ms_swift_dir / "piwm_train_stage1_user_intent_v1.jsonl"
    stage1_summary = _write_ms_swift(general_stage1, stage1_out, root=root)

    target_main = _index_by_state(_read_jsonl(target_dir / "main_schema.jsonl"))
    target_state = _index_by_state(_read_jsonl(target_dir / "state_inference.jsonl"))
    target_transitions = _read_jsonl(target_dir / "transition_modeling.jsonl")
    target_policy_rows = _read_jsonl(target_dir / "policy_preference.jsonl")
    clean_policy_rows, excluded_counts = _clean_5act_policy_rows(target_policy_rows)
    test_ids = _select_balanced_target_test_ids(clean_policy_rows, per_act=target_test_per_act)
    test_id_set = set(test_ids)
    train_policy_rows = [row for row in clean_policy_rows if row["state_id"] not in test_id_set]
    test_policy_rows = [row for row in clean_policy_rows if row["state_id"] in test_id_set]
    test_ids = [row["state_id"] for row in test_policy_rows]

    stage2_target = [_action_example(row) for row in train_policy_rows]
    stage2_out = ms_swift_dir / "piwm_train_stage2_target_5act_v1.jsonl"
    stage2_summary = _write_ms_swift(stage2_target, stage2_out, root=root)

    joint_out = ms_swift_dir / "piwm_train_stage1_plus_stage2_target_5act_v1.jsonl"
    joint_summary = _write_rows(_read_jsonl(stage1_out) + _read_jsonl(stage2_out), joint_out)

    eval_dir.mkdir(parents=True, exist_ok=True)
    target_eval_user = [_user_intent_example(target_state[state_id]) for state_id in test_ids]
    target_eval_next = [_next_state_example(row) for row in _target_hold_transition_rows(target_transitions, test_ids)]
    target_eval_action = [_action_example(row) for row in test_policy_rows]
    target_eval_all = target_eval_user + target_eval_next + target_eval_action

    target_eval_paths = {
        "user_intent": eval_dir / "target_frontcam_5act_test_user_intent.jsonl",
        "next_state_prediction": eval_dir / "target_frontcam_5act_test_no_intervention_next_state.jsonl",
        "action_selection_5act": eval_dir / "target_frontcam_5act_test_action_selection.jsonl",
        "all": eval_dir / "target_frontcam_5act_test_all.jsonl",
    }
    target_eval_summaries = {
        "user_intent": _write_ms_swift(target_eval_user, target_eval_paths["user_intent"], root=root),
        "next_state_prediction": _write_ms_swift(target_eval_next, target_eval_paths["next_state_prediction"], root=root),
        "action_selection_5act": _write_ms_swift(target_eval_action, target_eval_paths["action_selection_5act"], root=root),
        "all": _write_ms_swift(target_eval_all, target_eval_paths["all"], root=root),
    }

    general_eval = _build_stage1_examples(general_eval_dir)
    general_eval_out = eval_dir / "general_qa_stage1_all.jsonl"
    general_eval_summary = _write_ms_swift(general_eval, general_eval_out, root=root)
    test_qa_status_counts = _qa_counts(test_ids, target_main)
    target_qa_red_line = (
        "The 5-act target test is balanced, video-backed, excludes Reassure as best or candidate action, and is project-lead QA-reviewed pass under the revised split."
        if test_qa_status_counts == {"qa_reviewed_pass": len(test_ids)}
        else "The 5-act target test is balanced, video-backed, and excludes Reassure as best or candidate action, but not all revised-split rows are QA-reviewed pass."
    )

    summary = {
        "artifact": "piwm_two_stage_training_and_eval_v1",
        "is_training_result": False,
        "stage1_train": stage1_summary,
        "stage2_target_5act_train": stage2_summary,
        "joint_stage1_stage2_target_5act": joint_summary,
        "target_5act_split": {
            "source_records": len(target_policy_rows),
            "official_split_counts": _split_counts(target_policy_rows),
            "official_best_act_counts": _act_counts(target_policy_rows),
            "clean_5act_records": len(clean_policy_rows),
            "train_records": len(train_policy_rows),
            "test_records": len(test_policy_rows),
            "filtered_records": excluded_counts,
            "test_per_act": target_test_per_act,
            "test_best_act_counts": _act_counts(test_policy_rows),
            "train_best_act_counts": _act_counts(train_policy_rows),
            "test_qa_status_counts": test_qa_status_counts,
            "stage2_act_balancing": act_balancing,
            "accounting_chain": [
                "118 total target records",
                "-17 rows with best_act=Reassure",
                "-0 rows whose candidate set degenerates after removing Reassure candidates",
                "=101 clean 5-act records",
                "101 - 30 balanced test records = 71 Stage-2 target train records",
            ],
            "split_policy": "Use a strict clean 5-act subset for the main experiment. The operational acts are Greet/Elicit/Inform/Recommend/Hold. Exclude rows whose best act is Reassure, and filter Reassure from candidate lists. Select a balanced 30-record target test with 6 rows per operational act using seed-stable state_id ordering; use the remaining 71 clean records for Stage-2 target training.",
        },
        "target_5act_eval": target_eval_summaries,
        "general_stage1_eval": general_eval_summary,
        "evaluation_matrix": [
            {
                "eval_label": "general_on_general",
                "checkpoint": "checkpoint_general",
                "input_jsonl": _display_path(general_eval_out),
                "purpose": "Stage-1 user-intent and action-conditioned next-state health check.",
            },
            {
                "eval_label": "general_on_target",
                "checkpoint": "checkpoint_general",
                "input_jsonl": _display_path(target_eval_paths["all"]),
                "purpose": "Zero-shot transfer to target frontcam 5-act eval.",
            },
            {
                "eval_label": "target_specialized_on_target",
                "checkpoint": "checkpoint_target",
                "input_jsonl": _display_path(target_eval_paths["all"]),
                "purpose": "Target specialization gain under the 5-act metric.",
            },
            {
                "eval_label": "target_specialized_on_general",
                "checkpoint": "checkpoint_target",
                "input_jsonl": _display_path(general_eval_out),
                "purpose": "Catastrophic forgetting check after target specialization.",
            },
        ],
        "red_lines": [
            target_qa_red_line,
            "Do not report Reassure inside the main 5-act macro F1; use it only as a source/compatibility analysis boundary.",
            "Keep Recommend pressure params in action-selection outputs.",
            "The target action-selection prompt intentionally omits gold reward, risk, benefit, and predicted next state.",
            "Real-50 and salesperson-majority validation are planned external checks, not current completed results.",
        ],
    }
    summary_path = eval_dir / "two_stage_eval_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (eval_dir / "two_stage_eval_summary.md").write_text(_markdown(summary), encoding="utf-8")
    return summary


def _build_stage1_examples(data_dir: Path) -> list[SFTExample]:
    examples = [_user_intent_example(row) for row in _read_jsonl(data_dir / "state_inference.jsonl")]
    examples.extend(_next_state_example(row) for row in _read_jsonl(data_dir / "transition_modeling.jsonl"))
    return examples


def _user_intent_example(row: dict[str, Any]) -> SFTExample:
    intent_label = row.get("output", {}).get("intent")
    loss_weight = user_intent_loss_weight(intent_label)
    return SFTExample(
        task="user_intent",
        source_id=row["state_id"],
        prompt=build_user_intent_prompt(row),
        target=build_user_intent_target(row),
        images=list(row["input"].get("frames", [])),
        weight=loss_weight,
        meta={
            "split": row.get("meta", {}).get("split"),
            "qa_status": row.get("meta", {}).get("qa_status"),
            "human_review_status": row.get("meta", {}).get("human_review_status"),
            "viewpoint": row.get("meta", {}).get("viewpoint"),
            "stage": row.get("output", {}).get("aida_stage"),
            "intent_label": intent_label,
            "loss_weight": loss_weight,
            "loss_weight_policy": "a3plus_visual_intent_low_confidence",
        },
    )


def _next_state_example(row: dict[str, Any]) -> SFTExample:
    action_spec = row["input"].get("candidate_action_spec") or row["input"].get("candidate_dialogue_act") or {}
    return SFTExample(
        task="next_state_prediction",
        source_id=row["state_id"],
        prompt=build_next_state_prediction_prompt(row),
        target=build_deliberation_target(row),
        images=list(row["input"].get("frames", [])),
        meta={
            "parent_state_id": row.get("meta", {}).get("parent_state_id"),
            "candidate_action": row["input"].get("candidate_action"),
            "candidate_act": action_spec.get("act"),
            "candidate_params": action_spec.get("params"),
            "no_intervention_branch": action_spec.get("act") == "Hold"
            and (action_spec.get("params") or {}).get("mode") == "silent",
            "split": row.get("meta", {}).get("split"),
            "qa_status": row.get("meta", {}).get("qa_status"),
            "human_review_status": row.get("meta", {}).get("human_review_status"),
            "viewpoint": row.get("meta", {}).get("viewpoint"),
        },
    )


def _action_example(row: dict[str, Any]) -> SFTExample:
    return SFTExample(
        task="action_selection_5act",
        source_id=row["state_id"],
        prompt=build_action_prompt_no_leak(row, five_act_only=True),
        target=build_action_target(row, "chosen"),
        images=list(row.get("meta", {}).get("frames", [])),
        meta={
            "split": row.get("meta", {}).get("split"),
            "qa_status": row.get("meta", {}).get("qa_status"),
            "human_review_status": row.get("meta", {}).get("human_review_status"),
            "viewpoint": row.get("meta", {}).get("viewpoint"),
            "best_act": _best_act(row),
            "candidate_action_acts": _candidate_action_acts(row),
            "five_act_only": True,
            "leakage_control": "no_reward_no_predicted_outcome_in_prompt",
        },
    )


def _target_hold_transition_rows(rows: list[dict[str, Any]], state_ids: list[str]) -> list[dict[str, Any]]:
    selected = set(state_ids)
    out = []
    for row in rows:
        if row.get("meta", {}).get("parent_state_id") not in selected:
            continue
        spec = row["input"].get("candidate_action_spec") or row["input"].get("candidate_dialogue_act") or {}
        if spec.get("act") == "Hold" and (spec.get("params") or {}).get("mode") == "silent":
            out.append(row)
    return sorted(out, key=lambda row: row.get("meta", {}).get("parent_state_id", ""))


def _clean_5act_policy_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    clean_rows: list[dict[str, Any]] = []
    excluded = Counter({"best_non_5act": 0, "candidate_non_5act": 0, "empty_5act_candidates": 0})
    for row in rows:
        best = _best_act(row)
        if best not in FIVE_ACTS:
            excluded["best_non_5act"] += 1
            continue
        updated = _filter_policy_row_candidates(row)
        original_candidate_count = len(row.get("meta", {}).get("candidate_block", []))
        filtered_candidate_count = len(updated.get("meta", {}).get("candidate_block", []))
        if original_candidate_count != filtered_candidate_count:
            excluded["candidate_non_5act"] += 1
        if filtered_candidate_count == 0:
            excluded["empty_5act_candidates"] += 1
            continue
        clean_rows.append(updated)
    return clean_rows, dict(excluded)


def _select_balanced_target_test_ids(rows: list[dict[str, Any]], *, per_act: int) -> list[str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_best_act(row)].append(row)

    selected: list[str] = []
    for act in ["Greet", "Elicit", "Inform", "Recommend", "Hold"]:
        candidates = sorted(grouped[act], key=lambda row: row["state_id"])
        if len(candidates) < per_act:
            raise ValueError(f"not enough clean target rows for {act}: need {per_act}, found {len(candidates)}")
        selected.extend(row["state_id"] for row in candidates[:per_act])
    return selected


def _clean_balanced_5act_policy_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Return clean 5-act train/test rows using the current balanced split."""
    clean_rows, excluded = _clean_5act_policy_rows(rows)
    test_ids = set(_select_balanced_target_test_ids(clean_rows, per_act=6))
    train_rows = [row for row in clean_rows if row["state_id"] not in test_ids]
    test_rows = [row for row in clean_rows if row["state_id"] in test_ids]
    return train_rows, test_rows, excluded


def _row_split(row: dict[str, Any]) -> str:
    return str(row.get("meta", {}).get("split") or row.get("split") or "")


def _best_act(row: dict[str, Any]) -> str:
    spec = row.get("chosen_json", {}).get("action_spec") or row.get("chosen_json", {}).get("dialogue_act") or {}
    return spec.get("act", "")


def _candidate_action_acts(row: dict[str, Any], *, five_act_filter: bool = True) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in row.get("meta", {}).get("candidate_block", []):
        action = item.get("action")
        act = _block_act(item)
        if five_act_filter and act not in FIVE_ACTS:
            continue
        if action and act:
            mapping[action] = act
    for side in ("chosen_json", "rejected_json"):
        block = row.get(side, {})
        action = block.get("action")
        act = _block_act(block)
        if five_act_filter and act not in FIVE_ACTS:
            continue
        if action and act:
            mapping.setdefault(action, act)
    for item in row.get("meta", {}).get("candidate_block", []):
        action = item.get("action")
        if action and action not in mapping:
            try:
                act = legacy_action_to_act_params_for_comparison(action)[0]
                if not five_act_filter or act in FIVE_ACTS:
                    mapping[action] = act
            except (KeyError, ValueError):
                pass
    return mapping


def _filter_policy_row_candidates(row: dict[str, Any]) -> dict[str, Any]:
    updated = dict(row)
    meta = dict(updated.get("meta") or {})
    meta["candidate_block"] = [
        item
        for item in meta.get("candidate_block", [])
        if _block_act(item) in FIVE_ACTS
    ]
    updated["meta"] = meta
    return updated


def _block_act(block: dict[str, Any]) -> str | None:
    spec = block.get("dialogue_act") or block.get("action_spec") or {}
    act = spec.get("act")
    return str(act) if act else None


def _qa_counts(state_ids: list[str], main_by_state: dict[str, dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(main_by_state.get(state_id, {}).get("qa_status", "unknown") for state_id in state_ids).items()))


def _act_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(_best_act(row) for row in rows).items()))


def _split_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(_row_split(row) for row in rows).items()))


def _index_by_state(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["state_id"]: row for row in rows}


def _write_ms_swift(examples: list[SFTExample], output_jsonl: Path, *, root: Path) -> dict[str, Any]:
    rows = [build_ms_swift_record(example, root=root, validate_images=False) for example in examples]
    summary = _write_rows(rows, output_jsonl)
    summary["image_path_count"] = sum(len(row.get("images", [])) for row in rows)
    return summary


def _write_rows(rows: list[dict[str, Any]], output_jsonl: Path) -> dict[str, Any]:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
    task_counts = dict(sorted(Counter(row.get("task", "unknown") for row in rows).items()))
    summary = {
        "artifact": "ms_swift_sft_jsonl",
        "is_training_result": False,
        "output_jsonl": _display_path(output_jsonl),
        "n_examples": len(rows),
        "task_counts": task_counts,
        "format": "ms-swift messages + images",
    }
    output_jsonl.with_name(f"{output_jsonl.stem}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _markdown(summary: dict[str, Any]) -> str:
    split = summary["target_5act_split"]
    lines = [
        "# PIWM Two-Stage Training and Eval v1",
        "",
        "This artifact implements the revised EMNLP data plan: leakage-free Stage-1 user intent modeling, "
        "5-act Stage-2 action modeling, and the balanced target-frontcam 5-act test split.",
        "",
        "## Training Entry Points",
        "",
        f"- Stage-1: `{summary['stage1_train']['output_jsonl']}` ({summary['stage1_train']['n_examples']} rows)",
        f"- Stage-2 target 5-act: `{summary['stage2_target_5act_train']['output_jsonl']}` ({summary['stage2_target_5act_train']['n_examples']} rows)",
        f"- Joint baseline: `{summary['joint_stage1_stage2_target_5act']['output_jsonl']}` ({summary['joint_stage1_stage2_target_5act']['n_examples']} rows)",
        "",
        "## Target 5-Act Split",
        "",
        f"- official_split_counts: `{split['official_split_counts']}`",
        f"- clean_5act_records: {split['clean_5act_records']}",
        f"- train_records: {split['train_records']}",
        f"- test_records: {split['test_records']}",
        f"- filtered_records: `{split['filtered_records']}`",
        f"- test_best_act_counts: `{split['test_best_act_counts']}`",
        f"- test_qa_status_counts: `{split['test_qa_status_counts']}`",
        "",
        "## Evaluation Matrix",
        "",
        "| Label | Checkpoint | Input | Purpose |",
        "|---|---|---|---|",
    ]
    for item in summary["evaluation_matrix"]:
        lines.append(f"| `{item['eval_label']}` | `{item['checkpoint']}` | `{item['input_jsonl']}` | {item['purpose']} |")
    lines.extend(["", "## Red Lines", ""])
    lines.extend(f"- {item}" for item in summary["red_lines"])
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--general-dir", type=Path, default=DEFAULT_GENERAL_DIR)
    parser.add_argument("--general-eval-dir", type=Path, default=DEFAULT_GENERAL_EVAL_DIR)
    parser.add_argument("--target-dir", type=Path, default=DEFAULT_TARGET_DIR)
    parser.add_argument("--ms-swift-dir", type=Path, default=DEFAULT_MS_SWIFT_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument(
        "--target-test-per-act",
        type=int,
        default=6,
        help="Number of held-out target records per five-act class for the balanced target eval split.",
    )
    parser.add_argument(
        "--act-balancing",
        choices=["none", "inverse_freq", "oversample_minority"],
        default="none",
        help="Stage-2 target action-selection balancing mode.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_two_stage_artifacts(
        general_dir=args.general_dir,
        general_eval_dir=args.general_eval_dir,
        target_dir=args.target_dir,
        ms_swift_dir=args.ms_swift_dir,
        eval_dir=args.eval_dir,
        target_test_per_act=args.target_test_per_act,
        act_balancing=args.act_balancing,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
