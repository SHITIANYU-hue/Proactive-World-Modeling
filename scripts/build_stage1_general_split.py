"""Create the seed=42 Stage-1 general train/val split and task JSONLs."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.build_two_stage_training_and_eval import (
    REPO_ROOT,
    _next_state_example,
    _read_jsonl,
    _resolve,
    _user_intent_example,
    _write_ms_swift,
)


DEFAULT_GENERAL_DIR = Path("data/official/piwm_train_synth_v2")
DEFAULT_MS_SWIFT_DIR = Path("data/official/ms_swift")
DEFAULT_SEED = 42
DEFAULT_VAL_PARENTS = 50
STAGE_ORDER = ("attention", "interest", "desire", "action")


def build_stage1_general_split(
    *,
    general_dir: Path,
    ms_swift_dir: Path = DEFAULT_MS_SWIFT_DIR,
    seed: int = DEFAULT_SEED,
    val_parent_count: int = DEFAULT_VAL_PARENTS,
) -> dict[str, Any]:
    general_dir = _resolve(general_dir)
    ms_swift_dir = _resolve(ms_swift_dir)
    state_rows = _read_jsonl(general_dir / "state_inference.jsonl")
    transition_rows = _read_jsonl(general_dir / "transition_modeling.jsonl")
    if val_parent_count <= 0 or val_parent_count >= len(state_rows):
        raise ValueError(f"val_parent_count must be in 1..{len(state_rows) - 1}, got {val_parent_count}")

    stage_to_ids = _stage_to_parent_ids(state_rows)
    val_counts = _allocate_stratified_counts(stage_to_ids, val_parent_count)
    val_ids = _sample_val_ids(stage_to_ids, val_counts, seed=seed)
    train_ids = sorted(set(row["state_id"] for row in state_rows) - set(val_ids))

    _write_parent_ids(general_dir / "general_train_parents.txt", train_ids)
    _write_parent_ids(general_dir / "general_val_parents.txt", val_ids)

    train_id_set = set(train_ids)
    val_id_set = set(val_ids)
    user_train = [_user_intent_example(row) for row in state_rows if row["state_id"] in train_id_set]
    user_val = [_user_intent_example(row) for row in state_rows if row["state_id"] in val_id_set]
    next_train = [
        _next_state_example(row)
        for row in transition_rows
        if row.get("meta", {}).get("parent_state_id") in train_id_set
    ]
    next_val = [
        _next_state_example(row)
        for row in transition_rows
        if row.get("meta", {}).get("parent_state_id") in val_id_set
    ]

    outputs = {
        "user_intent_train": _write_ms_swift(
            user_train,
            general_dir / "user_intent_train.jsonl",
            root=REPO_ROOT,
        ),
        "user_intent_val": _write_ms_swift(
            user_val,
            general_dir / "user_intent_val.jsonl",
            root=REPO_ROOT,
        ),
        "next_state_prediction_train": _write_ms_swift(
            next_train,
            general_dir / "next_state_prediction_train.jsonl",
            root=REPO_ROOT,
        ),
        "next_state_prediction_val": _write_ms_swift(
            next_val,
            general_dir / "next_state_prediction_val.jsonl",
            root=REPO_ROOT,
        ),
    }
    ms_swift_outputs = {
        "user_intent_train": _write_ms_swift(
            user_train,
            ms_swift_dir / "piwm_train_stage1_user_intent_train_v1.jsonl",
            root=REPO_ROOT,
        ),
        "user_intent_val": _write_ms_swift(
            user_val,
            ms_swift_dir / "piwm_train_stage1_user_intent_val_v1.jsonl",
            root=REPO_ROOT,
        ),
        "next_state_prediction_train": _write_ms_swift(
            next_train,
            ms_swift_dir / "piwm_train_stage1_next_state_prediction_train_v1.jsonl",
            root=REPO_ROOT,
        ),
        "next_state_prediction_val": _write_ms_swift(
            next_val,
            ms_swift_dir / "piwm_train_stage1_next_state_prediction_val_v1.jsonl",
            root=REPO_ROOT,
        ),
    }

    stage_counts = _stage_counts(state_rows)
    train_stage_counts = _stage_counts([row for row in state_rows if row["state_id"] in train_id_set])
    val_stage_counts = _stage_counts([row for row in state_rows if row["state_id"] in val_id_set])
    chi_square, p_value = _chi_square_stage_balance(stage_counts, val_stage_counts, val_parent_count)

    summary_path = general_dir / "general_split_seed42.json"
    created_at = _existing_created_at(summary_path) or datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    summary = {
        "artifact": "piwm_stage1_general_split_seed42",
        "seed": seed,
        "created_at_cst": created_at,
        "stratification": "AIDA stage",
        "parent_id_field": "state_id",
        "source": "PIWM-Train-Synth-v2 state_inference.jsonl",
        "total_parent_count": len(state_rows),
        "train_parent_count": len(train_ids),
        "val_parent_count": len(val_ids),
        "stage_counts": stage_counts,
        "train_stage_counts": train_stage_counts,
        "val_stage_counts": val_stage_counts,
        "expected_val_stage_counts": {
            stage: round(stage_counts[stage] * val_parent_count / len(state_rows), 3)
            for stage in STAGE_ORDER
        },
        "chi_square": round(chi_square, 6),
        "chi_square_df": len(STAGE_ORDER) - 1,
        "chi_square_pvalue": round(p_value, 6),
        "chi_square_pass_p_gt_0_05": p_value > 0.05,
        "outputs": outputs,
        "ms_swift_outputs": ms_swift_outputs,
        "stage1_train_examples": len(user_train) + len(next_train),
        "stage1_val_examples": len(user_val) + len(next_val),
        "task_counts": {
            "train": {
                "user_intent": len(user_train),
                "next_state_prediction": len(next_train),
            },
            "val": {
                "user_intent": len(user_val),
                "next_state_prediction": len(next_val),
            },
        },
    }
    if not summary["chi_square_pass_p_gt_0_05"]:
        raise ValueError(f"stratified split failed chi-square check: p={p_value:.6f}")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _existing_created_at(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    created_at = data.get("created_at_cst")
    return created_at if isinstance(created_at, str) and created_at else None


def _stage_to_parent_ids(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        stage = row.get("output", {}).get("aida_stage")
        if stage not in STAGE_ORDER:
            raise ValueError(f"unsupported AIDA stage for {row.get('state_id')}: {stage!r}")
        grouped[stage].append(row["state_id"])
    return {stage: sorted(grouped[stage]) for stage in STAGE_ORDER}


def _stage_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(row.get("output", {}).get("aida_stage") for row in rows)
    return {stage: counts.get(stage, 0) for stage in STAGE_ORDER}


def _allocate_stratified_counts(stage_to_ids: dict[str, list[str]], total_val: int) -> dict[str, int]:
    total = sum(len(ids) for ids in stage_to_ids.values())
    quotas = {stage: len(ids) * total_val / total for stage, ids in stage_to_ids.items()}
    counts = {stage: int(math.floor(quotas[stage])) for stage in STAGE_ORDER}
    remaining = total_val - sum(counts.values())
    ranked = sorted(STAGE_ORDER, key=lambda stage: (quotas[stage] - counts[stage], len(stage_to_ids[stage])), reverse=True)
    for stage in ranked[:remaining]:
        counts[stage] += 1
    return counts


def _sample_val_ids(stage_to_ids: dict[str, list[str]], val_counts: dict[str, int], *, seed: int) -> list[str]:
    rng = random.Random(seed)
    selected: list[str] = []
    for stage in STAGE_ORDER:
        ids = list(stage_to_ids[stage])
        rng.shuffle(ids)
        selected.extend(ids[: val_counts[stage]])
    return sorted(selected)


def _write_parent_ids(path: Path, parent_ids: list[str]) -> None:
    path.write_text("".join(f"{parent_id}\n" for parent_id in parent_ids), encoding="utf-8")


def _chi_square_stage_balance(
    full_stage_counts: dict[str, int],
    val_stage_counts: dict[str, int],
    val_total: int,
) -> tuple[float, float]:
    full_total = sum(full_stage_counts.values())
    chi_square = 0.0
    for stage in STAGE_ORDER:
        expected = full_stage_counts[stage] * val_total / full_total
        observed = val_stage_counts[stage]
        chi_square += ((observed - expected) ** 2) / expected
    return chi_square, _chi_square_survival_df3(chi_square)


def _chi_square_survival_df3(value: float) -> float:
    """Survival function for chi-square(df=3), avoiding a scipy dependency."""
    x = value / 2.0
    return math.erfc(math.sqrt(x)) + (2.0 * math.sqrt(x) * math.exp(-x) / math.sqrt(math.pi))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--general-dir", type=Path, default=DEFAULT_GENERAL_DIR)
    parser.add_argument("--ms-swift-dir", type=Path, default=DEFAULT_MS_SWIFT_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--val-parent-count", type=int, default=DEFAULT_VAL_PARENTS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_stage1_general_split(
        general_dir=args.general_dir,
        ms_swift_dir=args.ms_swift_dir,
        seed=args.seed,
        val_parent_count=args.val_parent_count,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
