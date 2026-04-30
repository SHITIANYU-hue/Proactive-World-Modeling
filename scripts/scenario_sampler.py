"""Sample rule-space scenarios before Kling video generation.

This script does not call Kling. It builds a reproducible manifest of
controlled retail scenarios that can later be turned into ``prompt.json``
files by :mod:`scripts.prompt_builder`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from piwm_data import rules

DEFAULT_OUT = Path("data/scenario_manifest.jsonl")
DEFAULT_SEED = 42
DEFAULT_HOLDOUT_PRODUCTS = ["footwear"]
DEFAULT_HOLDOUT_PERSONAS = ["gift_buyer_uncertain"]
DEFAULT_VIEWPOINTS = ["salesperson_observable", "surveillance_oblique"]
DEFAULT_VIEWPOINT_RATIO = [0.8, 0.2]

PERSONA_DESCRIPTIONS = {
    "price_sensitive_cautious": "A careful shopper who repeatedly weighs price and value before engaging.",
    "first_time_high_consideration": "A first-time buyer considering a higher-stakes purchase and needing reassurance.",
    "experienced_brand_loyal": "An experienced shopper who already trusts familiar brands and compares details quickly.",
    "browser_low_intent": "A casual browser with low purchase intent who may leave if approached too strongly.",
    "gift_buyer_uncertain": "A shopper buying for someone else and unsure which option fits best.",
    "price_insensitive_decisive": "A decisive shopper who prioritizes fit and quality over price.",
}


def build_all_scenarios(
    seed: int = DEFAULT_SEED,
    holdout_products: list[str] | None = None,
    holdout_personas: list[str] | None = None,
    viewpoints: list[str] | None = None,
    viewpoint_ratio: list[float] | None = None,
) -> list[dict[str, Any]]:
    holdout_products = holdout_products if holdout_products is not None else DEFAULT_HOLDOUT_PRODUCTS
    holdout_personas = holdout_personas if holdout_personas is not None else DEFAULT_HOLDOUT_PERSONAS
    viewpoints, viewpoint_ratio = _validate_viewpoint_config(viewpoints, viewpoint_ratio)
    base_specs: list[dict[str, str]] = []
    for product in rules.PRODUCT_CATEGORIES:
        for persona in rules.PERSONA_TYPES:
            for cue in rules.CUES:
                for aida_stage in rules.AIDA_STAGES:
                    base_specs.append(
                        {
                            "product_category": product,
                            "persona_type": persona,
                            "target_cue": cue,
                            "aida_stage": aida_stage,
                        }
                    )

    viewpoint_assignments = _assign_viewpoints(base_specs, seed, viewpoints, viewpoint_ratio)
    scenarios: list[dict[str, Any]] = []
    for spec, viewpoint in zip(base_specs, viewpoint_assignments):
        scenarios.append(
            _build_scenario(
                product=spec["product_category"],
                persona_type=spec["persona_type"],
                cue=spec["target_cue"],
                aida_stage=spec["aida_stage"],
                viewpoint=viewpoint,
                seed=seed,
                holdout_products=holdout_products,
                holdout_personas=holdout_personas,
            )
        )
    return scenarios


def select_scenarios(
    scenarios: list[dict[str, Any]],
    limit: int | None,
    seed: int = DEFAULT_SEED,
    balanced_cues: bool = False,
    viewpoints: list[str] | None = None,
    viewpoint_ratio: list[float] | None = None,
) -> list[dict[str, Any]]:
    if limit is None or limit >= len(scenarios):
        return list(scenarios)
    if limit <= 0:
        return []

    rng = random.Random(seed)
    viewpoints, viewpoint_ratio = _infer_selection_viewpoints(scenarios, viewpoints, viewpoint_ratio)
    if not balanced_cues:
        selected = list(scenarios)
        rng.shuffle(selected)
        return _take_with_viewpoint_quota(selected, limit, viewpoints, viewpoint_ratio)

    by_cue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scenario in scenarios:
        by_cue[scenario["target_cue"]].append(scenario)
    for bucket in by_cue.values():
        rng.shuffle(bucket)

    by_cue_viewpoint: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for scenario in scenarios:
        by_cue_viewpoint[(scenario["target_cue"], scenario["viewpoint"])].append(scenario)
    for bucket in by_cue_viewpoint.values():
        rng.shuffle(bucket)

    selected: list[dict[str, Any]] = []
    cue_order = list(rules.CUES)
    viewpoint_sequence = _viewpoint_sequence(limit, viewpoints, viewpoint_ratio)
    while len(selected) < limit:
        progressed = False
        for cue in cue_order:
            desired_viewpoint = viewpoint_sequence[len(selected)]
            bucket = by_cue_viewpoint[(cue, desired_viewpoint)]
            if not bucket:
                bucket = by_cue[cue]
            if bucket:
                item = bucket.pop()
                if item in by_cue[item["target_cue"]]:
                    by_cue[item["target_cue"]].remove(item)
                selected.append(item)
                progressed = True
                if len(selected) == limit:
                    break
        if not progressed:
            break
    return selected


def write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count


def scenario_stats(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n_scenarios": len(scenarios),
        "split_counts": dict(sorted(Counter(item["split"] for item in scenarios).items())),
        "product_counts": dict(sorted(Counter(item["product_category"] for item in scenarios).items())),
        "persona_counts": dict(sorted(Counter(item["persona_type"] for item in scenarios).items())),
        "viewpoint_counts": dict(sorted(Counter(item["viewpoint"] for item in scenarios).items())),
        "cue_counts": dict(sorted(Counter(item["target_cue"] for item in scenarios).items())),
        "aida_counts": dict(sorted(Counter(item["aida_stage"] for item in scenarios).items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sample PIWM rule-space scenarios for prompt construction.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--balanced-cues", action="store_true")
    parser.add_argument("--holdout-product", action="append", default=None)
    parser.add_argument("--holdout-persona", action="append", default=None)
    parser.add_argument("--viewpoints", nargs="+", default=DEFAULT_VIEWPOINTS)
    parser.add_argument("--viewpoint-ratio", nargs="+", type=float, default=DEFAULT_VIEWPOINT_RATIO)
    parser.add_argument("--stats-out", type=Path, default=None)
    args = parser.parse_args(argv)

    scenarios = build_all_scenarios(
        seed=args.seed,
        holdout_products=args.holdout_product or DEFAULT_HOLDOUT_PRODUCTS,
        holdout_personas=args.holdout_persona or DEFAULT_HOLDOUT_PERSONAS,
        viewpoints=args.viewpoints,
        viewpoint_ratio=args.viewpoint_ratio,
    )
    selected = select_scenarios(
        scenarios,
        args.limit,
        seed=args.seed,
        balanced_cues=args.balanced_cues,
        viewpoints=args.viewpoints,
        viewpoint_ratio=args.viewpoint_ratio,
    )
    for index, scenario in enumerate(selected):
        scenario["sample_index"] = index

    n_written = write_jsonl(selected, args.out)
    stats = scenario_stats(selected)
    stats["n_written"] = n_written
    stats_out = args.stats_out or args.out.with_name("_scenario_stats.json")
    stats_out.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def _build_scenario(
    product: str,
    persona_type: str,
    cue: str,
    aida_stage: str,
    viewpoint: str,
    seed: int,
    holdout_products: list[str],
    holdout_personas: list[str],
) -> dict[str, Any]:
    state = rules.derive_latent_state([cue])
    intent = rules.derive_intent(persona_type, state)
    proactive_score = rules.derive_proactive_score(state)
    candidate_actions = rules.derive_candidate_actions(state, aida_stage)
    best_action = rules.pick_best_action(state, candidate_actions)
    key = {
        "product_category": product,
        "persona_type": persona_type,
        "target_cue": cue,
        "aida_stage": aida_stage,
    }
    session_key = {**key, "viewpoint": viewpoint}
    session_id = f"piwm_{_stable_digest(session_key, seed)[:10]}"
    source_rule_ids, runtime_fallbacks = _source_trace(
        cue=cue,
        persona_type=persona_type,
        state=state,
        aida_stage=aida_stage,
        candidate_actions=candidate_actions,
    )
    return {
        "session_id": session_id,
        "sample_index": None,
        "split": _assign_split(product, persona_type, key, seed, holdout_products, holdout_personas),
        "viewpoint": viewpoint,
        "product_category": product,
        "persona_type": persona_type,
        "persona": {
            "type": persona_type,
            "description": PERSONA_DESCRIPTIONS[persona_type],
        },
        "aida_stage": aida_stage,
        "target_cue": cue,
        "duration_seconds": 10,
        "training_input_mode": "multi_image_single_turn",
        "derived": {
            "state_subtype": state,
            "intent": intent,
            "proactive_score": proactive_score,
            "candidate_actions": candidate_actions,
            "best_action": best_action,
        },
        "source_rule_ids": source_rule_ids,
        "runtime_fallbacks": runtime_fallbacks,
        "sampler": {
            "version": "phase3_viewpoint_v1",
            "seed": seed,
            "holdout_products": holdout_products,
            "holdout_personas": holdout_personas,
            "viewpoint": viewpoint,
        },
    }


def _validate_viewpoint_config(
    viewpoints: list[str] | None,
    viewpoint_ratio: list[float] | None,
) -> tuple[list[str], list[float]]:
    viewpoints = list(viewpoints or DEFAULT_VIEWPOINTS)
    viewpoint_ratio = list(viewpoint_ratio or DEFAULT_VIEWPOINT_RATIO)
    if len(viewpoints) != len(viewpoint_ratio):
        raise ValueError("--viewpoints and --viewpoint-ratio must have the same length")
    invalid = [viewpoint for viewpoint in viewpoints if viewpoint not in rules.VIEWPOINTS]
    if invalid:
        raise ValueError(f"invalid viewpoint(s): {invalid}")
    if any(weight < 0 for weight in viewpoint_ratio) or sum(viewpoint_ratio) <= 0:
        raise ValueError("--viewpoint-ratio values must be non-negative and sum to a positive value")
    return viewpoints, viewpoint_ratio


def _assign_viewpoints(
    specs: list[dict[str, str]],
    seed: int,
    viewpoints: list[str],
    viewpoint_ratio: list[float],
) -> list[str]:
    quotas = _quota_by_ratio(len(specs), viewpoint_ratio)
    assignments = [viewpoints[0]] * len(specs)
    ranked_indices = sorted(
        range(len(specs)),
        key=lambda index: _stable_digest({**specs[index], "assign": "viewpoint"}, seed),
    )
    cursor = 0
    for viewpoint, quota in zip(viewpoints, quotas):
        for index in ranked_indices[cursor: cursor + quota]:
            assignments[index] = viewpoint
        cursor += quota
    return assignments


def _infer_selection_viewpoints(
    scenarios: list[dict[str, Any]],
    viewpoints: list[str] | None,
    viewpoint_ratio: list[float] | None,
) -> tuple[list[str], list[float]]:
    if viewpoints is not None and viewpoint_ratio is not None:
        return _validate_viewpoint_config(viewpoints, viewpoint_ratio)
    present = [viewpoint for viewpoint in rules.VIEWPOINTS if any(item.get("viewpoint") == viewpoint for item in scenarios)]
    if not present:
        return [rules.DEFAULT_VIEWPOINT], [1.0]
    counts = Counter(item.get("viewpoint", rules.DEFAULT_VIEWPOINT) for item in scenarios)
    return present, [float(counts[viewpoint]) for viewpoint in present]


def _take_with_viewpoint_quota(
    scenarios: list[dict[str, Any]],
    limit: int,
    viewpoints: list[str],
    viewpoint_ratio: list[float],
) -> list[dict[str, Any]]:
    quotas = dict(zip(viewpoints, _quota_by_ratio(limit, viewpoint_ratio)))
    selected: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    for scenario in scenarios:
        viewpoint = scenario.get("viewpoint", rules.DEFAULT_VIEWPOINT)
        if quotas.get(viewpoint, 0) > 0:
            selected.append(scenario)
            quotas[viewpoint] -= 1
            if len(selected) == limit:
                return selected
        else:
            remaining.append(scenario)
    return selected + remaining[: limit - len(selected)]


def _viewpoint_sequence(limit: int, viewpoints: list[str], viewpoint_ratio: list[float]) -> list[str]:
    quotas = _quota_by_ratio(limit, viewpoint_ratio)
    sequence: list[str] = []
    for viewpoint, quota in zip(viewpoints, quotas):
        sequence.extend([viewpoint] * quota)
    return sequence[:limit]


def _quota_by_ratio(total: int, ratio: list[float]) -> list[int]:
    weight_sum = sum(ratio)
    raw = [total * weight / weight_sum for weight in ratio]
    quotas = [int(value) for value in raw]
    remainder = total - sum(quotas)
    order = sorted(range(len(ratio)), key=lambda index: (raw[index] - quotas[index], ratio[index]), reverse=True)
    for index in order[:remainder]:
        quotas[index] += 1
    return quotas

def _assign_split(
    product: str,
    persona_type: str,
    key: dict[str, str],
    seed: int,
    holdout_products: list[str],
    holdout_personas: list[str],
) -> str:
    if product in holdout_products:
        return "ood_product"
    if persona_type in holdout_personas:
        return "ood_persona"
    bucket = int(_stable_digest(key, seed)[10:18], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "dev"
    return "test"


def _source_trace(
    cue: str,
    persona_type: str,
    state: str,
    aida_stage: str,
    candidate_actions: list[str],
) -> tuple[list[str], list[str]]:
    source_rule_ids: list[str] = []
    runtime_fallbacks: list[str] = []

    source_rule_ids.append(_cue_rule_id(cue))
    if (persona_type, state) in rules.PERSONA_STATE_TO_INTENT:
        source_rule_ids.append(_rule_id_from_tuple("PSI", rules.PERSONA_STATE_TO_INTENT, (persona_type, state)))
    else:
        source_rule_ids.append(_rule_id_from_key("FALLBACK", rules.STATE_FALLBACK_INTENT, state))
        runtime_fallbacks.append("persona_state_to_intent->state_fallback_intent")

    source_rule_ids.append(_rule_id_from_key("PROSCORE", rules.STATE_TO_PROACTIVE_SCORE, state))
    if (state, aida_stage) in rules.STATE_AIDA_TO_CANDIDATES:
        source_rule_ids.append(_rule_id_from_tuple("CAND", rules.STATE_AIDA_TO_CANDIDATES, (state, aida_stage)))
    else:
        runtime_fallbacks.append("state_aida_to_candidates->DEFAULT_CANDIDATES")

    for action in candidate_actions:
        if (state, action) in rules.TRANSITION_TABLE:
            source_rule_ids.append(_rule_id_from_tuple("TRANS", rules.TRANSITION_TABLE, (state, action)))
        else:
            runtime_fallbacks.append(f"transition:{state}:{action}->DEFAULT_TRANSITION")

    return sorted(dict.fromkeys(source_rule_ids)), sorted(dict.fromkeys(runtime_fallbacks))


def _cue_rule_id(cue: str) -> str:
    return f"CUE2STATE_{rules.CUES.index(cue) + 1:03d}"


def _rule_id_from_key(prefix: str, table: dict[str, Any], key: str) -> str:
    keys = list(table)
    return f"{prefix}_{keys.index(key) + 1:03d}"


def _rule_id_from_tuple(prefix: str, table: dict[tuple[str, ...], Any], key: tuple[str, ...]) -> str:
    keys = list(table)
    return f"{prefix}_{keys.index(key) + 1:03d}"


def _stable_digest(payload: dict[str, str], seed: int) -> str:
    encoded = json.dumps({"seed": seed, **payload}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
