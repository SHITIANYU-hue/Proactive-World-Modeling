#!/usr/bin/env python3
"""Comprehensive quality check for the PIWM pipeline."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "data" / "seed"
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
LABELED_DIR = REPO_ROOT / "data" / "labeled"

STAGE_ORDER = {"attention": 0, "interest": 1, "desire": 2, "action": 3}
AIDA_ALLOWED = {
    "attention": {"hold", "greet", "elicit", "inform"},
    "interest":  {"hold", "elicit", "inform", "recommend"},
    "desire":    {"hold", "inform", "recommend"},
    "action":    {"hold", "greet", "recommend"},
}
ALL_CLASSES = {"hold", "greet", "elicit", "inform", "recommend"}


def seed_stage(text: str) -> str | None:
    m = re.match(r"(attention|interest|desire|action)\s*[阶段 ]+", text)
    return m.group(1) if m else None


def seed_target_act(text: str) -> str | None:
    m = re.search(r"target_act=(\w+):", text)
    return m.group(1).lower() if m else None


def manifest_target_class(target_act: str) -> str | None:
    if not target_act:
        return None
    return target_act.split(":")[0].lower()


def load_all():
    records = {}
    for sid in range(1, 201):
        name = f"piwm_{sid:03d}"
        seed_path = SEED_DIR / f"{name}.txt"
        manifest_path = MANIFEST_DIR / f"{name}.json"
        labeled_path = LABELED_DIR / f"{name}.json"

        seed_text = seed_path.read_text(encoding="utf-8").strip() if seed_path.exists() else None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        labeled = json.loads(labeled_path.read_text(encoding="utf-8")) if labeled_path.exists() else None

        records[name] = {
            "seed_text": seed_text,
            "manifest": manifest,
            "labeled": labeled,
        }
    return records


def check_pipeline_alignment(records):
    issues = defaultdict(list)

    for name, r in records.items():
        seed_text = r["seed_text"]
        manifest = r["manifest"]
        labeled = r["labeled"]

        if not seed_text or not manifest or not labeled:
            issues["missing_files"].append(f"{name}: seed={bool(seed_text)}, manifest={bool(manifest)}, labeled={bool(labeled)}")
            continue

        # 1. Stage alignment: seed vs manifest
        s_stage = seed_stage(seed_text)
        m_stage = manifest.get("aida_stage", "")
        if s_stage and s_stage != m_stage:
            issues["stage_seed_manifest"].append(f"{name}: seed={s_stage}, manifest={m_stage}")

        # 2. target_act alignment: seed → manifest → labeled best_action
        s_target = seed_target_act(seed_text)
        m_target = manifest_target_class(manifest.get("target_act", ""))
        l_best = labeled.get("best_action", "")

        if s_target:
            if m_target and s_target != m_target:
                issues["target_seed_manifest"].append(f"{name}: seed={s_target}, manifest={m_target}")
            if s_target != l_best:
                issues["target_seed_labeled"].append(f"{name}: seed={s_target}, labeled_best={l_best}")
        elif m_target:
            if m_target != l_best:
                issues["target_manifest_labeled"].append(f"{name}: manifest={m_target}, labeled_best={l_best}")

    return issues


def check_scores(records):
    issues = []
    score_dist = Counter()
    hold_score_dist = Counter()
    class_score_dist = defaultdict(Counter)

    for name, r in records.items():
        labeled = r.get("labeled")
        if not labeled:
            continue

        candidates = labeled.get("candidate_actions", [])
        outcomes = labeled.get("outcomes", {})
        best = labeled.get("best_action", "")

        fives = [c for c in candidates if outcomes.get(c, {}).get("score") == 5]
        if len(fives) != 1:
            issues.append(f"{name}: score=5 count is {len(fives)} (expected 1), fives={fives}")
        if fives and fives[0] != best:
            issues.append(f"{name}: score=5 on {fives[0]} but best_action={best}")
        if best not in candidates:
            issues.append(f"{name}: best_action={best} not in candidates={candidates}")

        for c in candidates:
            sc = outcomes.get(c, {}).get("score")
            if sc is None:
                issues.append(f"{name}: [{c}] missing score")
            else:
                score_dist[sc] += 1
                class_score_dist[c][sc] += 1
                if c == "hold":
                    hold_score_dist[sc] += 1

    return issues, score_dist, hold_score_dist, class_score_dist


def check_trajectories(records):
    issues = []
    stage_trans = Counter()

    for name, r in records.items():
        labeled = r.get("labeled")
        if not labeled:
            continue

        cur_stage = labeled.get("aida_stage", "")
        best = labeled.get("best_action", "")
        outcomes = labeled.get("outcomes", {})

        if best in outcomes:
            next_stage = outcomes[best].get("next_aida_stage", "")
            stage_trans[(cur_stage, next_stage)] += 1

            # Sanity: next stage should not skip more than 1 step forward
            if cur_stage in STAGE_ORDER and next_stage in STAGE_ORDER:
                delta = STAGE_ORDER[next_stage] - STAGE_ORDER[cur_stage]
                if delta > 1:
                    issues.append(f"{name}: [{best}] stage jump {cur_stage}→{next_stage} (delta={delta})")
                if delta < -1:
                    issues.append(f"{name}: [{best}] stage regression {cur_stage}→{next_stage} (delta={delta})")

        # Check all candidates have valid next_aida_stage
        for c, oc in outcomes.items():
            ns = oc.get("next_aida_stage", "")
            if ns not in STAGE_ORDER:
                issues.append(f"{name}: [{c}] invalid next_aida_stage={ns!r}")

    return issues, stage_trans


def check_allowed_classes(records):
    issues = []

    for name, r in records.items():
        manifest = r.get("manifest")
        labeled = r.get("labeled")
        if not manifest or not labeled:
            continue

        stage = manifest.get("aida_stage", "")
        allowed = AIDA_ALLOWED.get(stage, set())
        candidates = labeled.get("candidate_actions", [])

        for c in candidates:
            if c not in allowed:
                issues.append(f"{name}: [{c}] not allowed in stage={stage}")

    return issues


def distribution_summary(records):
    stage_dist = Counter()
    best_dist = Counter()
    stage_best = defaultdict(Counter)

    for name, r in records.items():
        labeled = r.get("labeled")
        if not labeled:
            continue
        stage = labeled.get("aida_stage", "")
        best = labeled.get("best_action", "")
        stage_dist[stage] += 1
        best_dist[best] += 1
        stage_best[stage][best] += 1

    return stage_dist, best_dist, stage_best


def main():
    print("Loading all 200 records…")
    records = load_all()

    # Check files exist
    missing = sum(
        1 for r in records.values()
        if not r["seed_text"] or not r["manifest"] or not r["labeled"]
    )
    print(f"  Records with all 3 files: {200 - missing}/200\n")

    # === 1. Pipeline alignment ===
    print("=" * 60)
    print("1. PIPELINE ALIGNMENT (seed → manifest → labeled)")
    print("=" * 60)
    alignment_issues = check_pipeline_alignment(records)
    for check_name, items in sorted(alignment_issues.items()):
        print(f"\n[{check_name}] {len(items)} issue(s):")
        for item in sorted(items):
            print(f"  {item}")
    if not alignment_issues:
        print("  ✓ No alignment issues")

    # === 2. Allowed classes ===
    print("\n" + "=" * 60)
    print("2. ALLOWED CLASSES PER STAGE")
    print("=" * 60)
    class_issues = check_allowed_classes(records)
    if class_issues:
        for item in class_issues:
            print(f"  {item}")
    else:
        print("  ✓ All candidate actions are within allowed sets")

    # === 3. Score validity ===
    print("\n" + "=" * 60)
    print("3. SCORE VALIDITY & DISTRIBUTION")
    print("=" * 60)
    score_issues, score_dist, hold_score_dist, class_score_dist = check_scores(records)
    if score_issues:
        print(f"\n  {len(score_issues)} issue(s):")
        for item in score_issues:
            print(f"  {item}")
    else:
        print("  ✓ All score constraints satisfied")

    print("\n  Overall score distribution (across all candidates in all samples):")
    for sc in range(1, 6):
        bar = "█" * score_dist[sc]
        print(f"    {sc}: {score_dist[sc]:4d}  {bar}")

    print("\n  hold score distribution:")
    for sc in range(1, 6):
        bar = "█" * hold_score_dist[sc]
        print(f"    {sc}: {hold_score_dist[sc]:4d}  {bar}")

    print("\n  Per-class average score:")
    for cls in sorted(class_score_dist):
        dist = class_score_dist[cls]
        total = sum(dist.values())
        avg = sum(k * v for k, v in dist.items()) / total if total else 0
        print(f"    {cls:12s}: n={total:4d}  avg={avg:.2f}  dist={dict(sorted(dist.items()))}")

    # === 4. Trajectory coherence ===
    print("\n" + "=" * 60)
    print("4. TRAJECTORY COHERENCE")
    print("=" * 60)
    traj_issues, stage_trans = check_trajectories(records)
    if traj_issues:
        print(f"\n  {len(traj_issues)} trajectory issue(s):")
        for item in traj_issues:
            print(f"  {item}")
    else:
        print("  ✓ No trajectory anomalies")

    print("\n  Stage transitions (best_action outcome):")
    for (src, dst), cnt in sorted(stage_trans.items()):
        arrow = "→"
        print(f"    {src:10s} {arrow} {dst:10s}: {cnt:3d}")

    # === 5. Distribution summary ===
    print("\n" + "=" * 60)
    print("5. OVERALL DISTRIBUTION")
    print("=" * 60)
    stage_dist, best_dist, stage_best = distribution_summary(records)

    print("\n  AIDA stage distribution:")
    for stage in ["attention", "interest", "desire", "action"]:
        bar = "█" * stage_dist[stage]
        print(f"    {stage:10s}: {stage_dist[stage]:3d}  {bar}")

    print("\n  Best action distribution:")
    for cls in sorted(best_dist):
        bar = "█" * best_dist[cls]
        print(f"    {cls:12s}: {best_dist[cls]:3d}  {bar}")

    print("\n  Per-stage best action breakdown:")
    for stage in ["attention", "interest", "desire", "action"]:
        d = stage_best[stage]
        allowed = AIDA_ALLOWED[stage]
        row = "  ".join(f"{cls}={d[cls]}" for cls in sorted(allowed))
        print(f"    {stage:10s}: {row}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_issues = (
        sum(len(v) for v in alignment_issues.values()) +
        len(class_issues) + len(score_issues) + len(traj_issues)
    )
    print(f"  Total issues found: {total_issues}")


if __name__ == "__main__":
    main()
