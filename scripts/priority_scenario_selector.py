"""Select high-value PIWM scenarios when Kling budget is limited.

This script does not call Kling. It ranks the full controlled scenario space by
World Model supervision value, then writes a limited manifest for prompt
construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from piwm_data import rules
from scripts import scenario_sampler

DEFAULT_OUT = Path("data/scenario_manifest_priority64.jsonl")
DEFAULT_ALL_OUT = Path("data/scenario_manifest_priority_all.jsonl")
DEFAULT_STATS_OUT = Path("data/_scenario_stats_priority64.json")
DEFAULT_LIMIT = 64
DEFAULT_SEED = 20260430
DEFAULT_VIEWPOINT_RATIO = [0.75, 0.25]

HIGH_VALUE_STATES = {
    "high_hesitation": 1.2,
    "active_evaluation": 1.0,
    "ready_to_decide": 1.0,
    "early_browsing": 0.8,
}

UNSTABLE_CUE_PENALTY = {
    "brief_glance_walking_past": 0.8,
    "approaching_counter": 0.3,
}


def annotate_priority(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``scenario`` with priority metrics and score."""
    row = dict(scenario)
    state = row["derived"]["state_subtype"]
    aida_stage = row["aida_stage"]
    persona_type = row["persona_type"]
    candidate_actions = list(row["derived"]["candidate_actions"])
    outcomes = {
        action: rules.derive_action_outcome(state, aida_stage, persona_type, action)
        for action in candidate_actions
    }
    rewards = {action: float(outcome["reward"]) for action, outcome in outcomes.items()}
    next_states = {action: outcome["next_state"] for action, outcome in outcomes.items()}
    risks = {action: outcome["risk"] for action, outcome in outcomes.items()}
    reward_values = list(rewards.values())
    reward_gap = max(reward_values) - min(reward_values) if reward_values else 0.0
    worst_action = min(
        candidate_actions,
        key=lambda action: (rewards[action], rules.ACTIONS.index(action)),
    )
    best_action = row["derived"]["best_action"]

    metrics = {
        "reward_gap": round(reward_gap, 4),
        "best_action": best_action,
        "best_reward": rewards[best_action],
        "worst_action": worst_action,
        "worst_reward": rewards[worst_action],
        "has_negative_reward": any(reward < 0 for reward in reward_values),
        "n_negative_reward_actions": sum(1 for reward in reward_values if reward < 0),
        "n_unique_next_states": len(set(next_states.values())),
        "strict_next_state_contrast": len(set(next_states.values())) > 1,
        "has_strong_recommend": "A3_strong_recommend" in candidate_actions,
        "has_silent_observe": "A1_silent_observe" in candidate_actions,
        "worst_risk": risks[worst_action],
    }
    score, reasons = _priority_score(row, metrics)
    row["priority"] = {
        "score": round(score, 4),
        "reasons": reasons,
        "metrics": metrics,
    }
    return row


def select_priority_scenarios(
    scenarios: list[dict[str, Any]],
    *,
    limit: int,
    seed: int,
    viewpoints: list[str],
    viewpoint_ratio: list[float],
    min_per_cue: int | None = None,
    min_per_product: int | None = None,
    min_per_persona: int | None = None,
    min_per_minor_split: int | None = None,
    max_per_cue: int | None = None,
) -> list[dict[str, Any]]:
    """Select a limited high-priority manifest with coverage constraints."""
    annotated = [annotate_priority(scenario) for scenario in scenarios]
    ranked = _ranked(annotated, seed)
    if limit <= 0:
        return []
    limit = min(limit, len(ranked))
    min_per_cue = min_per_cue if min_per_cue is not None else (3 if limit >= 50 else 2 if limit >= 20 else 1)
    min_per_product = min_per_product if min_per_product is not None else (3 if limit >= 64 else 2 if limit >= 32 else 1)
    min_per_persona = min_per_persona if min_per_persona is not None else (4 if limit >= 64 else 2 if limit >= 32 else 1)
    min_per_minor_split = (
        min_per_minor_split
        if min_per_minor_split is not None
        else (2 if limit >= 40 else 1 if limit >= 20 else 0)
    )
    max_per_cue = max_per_cue if max_per_cue is not None else max(
        min_per_cue,
        limit // len(rules.CUES) + 3,
    )
    quotas = dict(zip(viewpoints, _quota_by_ratio(limit, viewpoint_ratio)))
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add_best(predicate: Any) -> bool:
        for scenario in ranked:
            session_id = scenario["session_id"]
            viewpoint = scenario["viewpoint"]
            if session_id in selected_ids:
                continue
            if not predicate(scenario):
                continue
            if quotas.get(viewpoint, 0) <= 0:
                continue
            selected.append(scenario)
            selected_ids.add(session_id)
            quotas[viewpoint] -= 1
            scenario["sample_index"] = len(selected) - 1
            return True
        return False

    def count(field: str, value: str) -> int:
        return sum(1 for scenario in selected if scenario[field] == value)

    def below_cue_cap(scenario: dict[str, Any]) -> bool:
        return count("target_cue", scenario["target_cue"]) < max_per_cue

    for cue in rules.CUES:
        while len(selected) < limit and count("target_cue", cue) < min_per_cue:
            if not add_best(lambda scenario, cue=cue: scenario["target_cue"] == cue):
                break

    for product in rules.PRODUCT_CATEGORIES:
        while len(selected) < limit and count("product_category", product) < min_per_product:
            if not add_best(
                lambda scenario, product=product: scenario["product_category"] == product and below_cue_cap(scenario)
            ):
                break

    for persona in rules.PERSONA_TYPES:
        while len(selected) < limit and count("persona_type", persona) < min_per_persona:
            if not add_best(
                lambda scenario, persona=persona: scenario["persona_type"] == persona and below_cue_cap(scenario)
            ):
                break

    for split in ["dev", "test", "ood_product", "ood_persona"]:
        while len(selected) < limit and count("split", split) < min_per_minor_split:
            if not add_best(
                lambda scenario, split=split: scenario["split"] == split and below_cue_cap(scenario)
            ):
                break

    while len(selected) < limit:
        if not add_best(below_cue_cap):
            break

    if len(selected) < limit:
        # Fallback: fill any shortfall without viewpoint quota, but keep ranking.
        for scenario in ranked:
            if len(selected) == limit:
                break
            if scenario["session_id"] in selected_ids:
                continue
            selected.append(scenario)
            selected_ids.add(scenario["session_id"])
            scenario["sample_index"] = len(selected) - 1

    for index, scenario in enumerate(selected):
        scenario["sample_index"] = index
    return selected


def priority_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = scenario_sampler.scenario_stats(rows)
    scores = [row["priority"]["score"] for row in rows]
    gaps = [row["priority"]["metrics"]["reward_gap"] for row in rows]
    base.update(
        {
            "priority_score": _distribution(scores),
            "reward_gap": _distribution(gaps),
            "n_negative_reward_contrast": sum(
                1 for row in rows if row["priority"]["metrics"]["has_negative_reward"]
            ),
            "n_strict_next_state_contrast": sum(
                1 for row in rows if row["priority"]["metrics"]["strict_next_state_contrast"]
            ),
            "n_with_strong_recommend": sum(
                1 for row in rows if row["priority"]["metrics"]["has_strong_recommend"]
            ),
            "n_with_silent_observe": sum(
                1 for row in rows if row["priority"]["metrics"]["has_silent_observe"]
            ),
            "worst_action_counts": dict(
                sorted(Counter(row["priority"]["metrics"]["worst_action"] for row in rows).items())
            ),
        }
    )
    return base


def write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    return scenario_sampler.write_jsonl(rows, out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select high-value PIWM scenarios before Kling generation.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--all-out", type=Path, default=DEFAULT_ALL_OUT)
    parser.add_argument("--stats-out", type=Path, default=DEFAULT_STATS_OUT)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--viewpoints", nargs="+", default=scenario_sampler.DEFAULT_VIEWPOINTS)
    parser.add_argument("--viewpoint-ratio", nargs="+", type=float, default=DEFAULT_VIEWPOINT_RATIO)
    parser.add_argument("--holdout-product", action="append", default=None)
    parser.add_argument("--holdout-persona", action="append", default=None)
    parser.add_argument("--min-per-cue", type=int, default=None)
    parser.add_argument("--min-per-product", type=int, default=None)
    parser.add_argument("--min-per-persona", type=int, default=None)
    parser.add_argument("--min-per-minor-split", type=int, default=None)
    parser.add_argument("--max-per-cue", type=int, default=None)
    args = parser.parse_args(argv)

    viewpoints, viewpoint_ratio = _validate_viewpoint_config(args.viewpoints, args.viewpoint_ratio)
    scenarios = scenario_sampler.build_all_scenarios(
        seed=args.seed,
        holdout_products=args.holdout_product or scenario_sampler.DEFAULT_HOLDOUT_PRODUCTS,
        holdout_personas=args.holdout_persona or scenario_sampler.DEFAULT_HOLDOUT_PERSONAS,
        viewpoints=viewpoints,
        viewpoint_ratio=viewpoint_ratio,
    )
    annotated_all = _ranked([annotate_priority(scenario) for scenario in scenarios], args.seed)
    selected = select_priority_scenarios(
        scenarios,
        limit=args.limit,
        seed=args.seed,
        viewpoints=viewpoints,
        viewpoint_ratio=viewpoint_ratio,
        min_per_cue=args.min_per_cue,
        min_per_product=args.min_per_product,
        min_per_persona=args.min_per_persona,
        min_per_minor_split=args.min_per_minor_split,
        max_per_cue=args.max_per_cue,
    )
    write_jsonl(annotated_all, args.all_out)
    n_written = write_jsonl(selected, args.out)
    stats = priority_stats(selected)
    stats.update(
        {
            "n_written": n_written,
            "all_out": args.all_out.as_posix(),
            "out": args.out.as_posix(),
            "selection_policy": {
                "version": "priority_world_model_v1",
                "seed": args.seed,
                "viewpoints": viewpoints,
                "viewpoint_ratio": viewpoint_ratio,
                "limit": args.limit,
            },
        }
    )
    args.stats_out.parent.mkdir(parents=True, exist_ok=True)
    args.stats_out.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def _priority_score(scenario: dict[str, Any], metrics: dict[str, Any]) -> tuple[float, list[str]]:
    state = scenario["derived"]["state_subtype"]
    cue = scenario["target_cue"]
    score = 0.0
    reasons: list[str] = []
    if metrics["has_negative_reward"]:
        score += 5.0
        reasons.append("negative_reward_contrast")
    reward_gap = float(metrics["reward_gap"])
    score += 3.0 * reward_gap
    reasons.append(f"reward_gap={reward_gap:.2f}")
    unique_next_states = int(metrics["n_unique_next_states"])
    if unique_next_states > 1:
        score += 2.0 * (unique_next_states - 1)
        reasons.append(f"strict_next_state_contrast={unique_next_states}")
    if metrics["has_strong_recommend"]:
        score += 1.5
        reasons.append("includes_A3_strong_recommend")
    if metrics["has_silent_observe"]:
        score += 0.7
        reasons.append("includes_A1_silent_observe")
    if state in HIGH_VALUE_STATES:
        score += HIGH_VALUE_STATES[state]
        reasons.append(f"high_value_state={state}")
    if metrics["worst_risk"] == "high":
        score += 1.0
        reasons.append("high_risk_worst_action")
    elif metrics["worst_risk"] == "medium":
        score += 0.4
        reasons.append("medium_risk_worst_action")
    if scenario["split"] == "train":
        score += 0.4
        reasons.append("train_split")
    elif scenario["split"] in {"dev", "test"}:
        score += 0.2
        reasons.append(f"{scenario['split']}_split")
    else:
        score += 0.3
        reasons.append(scenario["split"])
    if scenario["viewpoint"] == rules.DEFAULT_VIEWPOINT:
        score += 0.2
        reasons.append("primary_viewpoint")
    penalty = UNSTABLE_CUE_PENALTY.get(cue, 0.0)
    if penalty:
        score -= penalty
        reasons.append(f"unstable_cue_penalty={penalty:.1f}")
    return score, reasons


def _ranked(rows: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row["priority"]["score"]),
            _stable_digest(row, seed),
        ),
    )


def _validate_viewpoint_config(viewpoints: list[str], viewpoint_ratio: list[float]) -> tuple[list[str], list[float]]:
    viewpoints = list(viewpoints)
    viewpoint_ratio = list(viewpoint_ratio)
    if len(viewpoints) != len(viewpoint_ratio):
        raise ValueError("--viewpoints and --viewpoint-ratio must have the same length")
    invalid = [viewpoint for viewpoint in viewpoints if viewpoint not in rules.VIEWPOINTS]
    if invalid:
        raise ValueError(f"invalid viewpoint(s): {invalid}")
    if any(weight < 0 for weight in viewpoint_ratio) or sum(viewpoint_ratio) <= 0:
        raise ValueError("--viewpoint-ratio values must be non-negative and sum to a positive value")
    return viewpoints, viewpoint_ratio


def _quota_by_ratio(total: int, ratio: list[float]) -> list[int]:
    weight_sum = sum(ratio)
    raw = [total * weight / weight_sum for weight in ratio]
    quotas = [int(value) for value in raw]
    remainder = total - sum(quotas)
    order = sorted(range(len(ratio)), key=lambda index: (raw[index] - quotas[index], ratio[index]), reverse=True)
    for index in order[:remainder]:
        quotas[index] += 1
    return quotas


def _distribution(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "median": None, "max": None}
    return {
        "min": round(min(values), 4),
        "median": round(float(median(values)), 4),
        "max": round(max(values), 4),
    }


def _stable_digest(row: dict[str, Any], seed: int) -> str:
    payload = {
        "seed": seed,
        "session_id": row["session_id"],
        "priority_score": row["priority"]["score"],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
