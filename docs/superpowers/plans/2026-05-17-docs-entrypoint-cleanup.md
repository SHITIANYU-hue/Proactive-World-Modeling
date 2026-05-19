# PIWM Docs Entrypoint Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the PIWM documentation readable from one short entrypoint, with clear routes for data status, domain-specialization experiments, schema/action contracts, and audit reports.

**Architecture:** Keep the existing directory layout. Rewrite `docs/README.md` as the human-facing map, update `RESEARCH_LOG.md` so the active document index matches the new map, and avoid renaming or archiving files in this pass.

**Tech Stack:** Markdown documentation in the existing PIWM repository.

---

### Task 1: Rewrite `docs/README.md`

**Files:**
- Modify: `docs/README.md`

- [ ] **Step 1: Replace the long flat list with a four-route entrypoint**

Use these routes:

```text
1. 数据现状与可用入口
2. EMNLP / domain-specialization 实验
3. Schema、动作空间和生成链路契约
4. 迁移审计、验证报告和历史材料
```

- [ ] **Step 2: Preserve red-line semantics**

Keep explicit warnings that prompt-ready rows are not video-backed rows, `PIWM-Train-Synth-v2` does not mean new videos, and `PIWM-RealShoot-v1` is still a protocol/manifest rather than collected real data.

### Task 2: Update `RESEARCH_LOG.md`

**Files:**
- Modify: `RESEARCH_LOG.md`

- [ ] **Step 1: Add the current domain-specialization entrypoint**

Add `docs/current/domain_specialization_experiment_plan.md` to the active sprint table.

- [ ] **Step 2: Add a high-density update for this documentation cleanup**

Record that `docs/README.md` is now organized by reader goal rather than by a long undifferentiated list.

### Task 3: Verify documentation links and diff

**Files:**
- Read: `docs/README.md`
- Read: `RESEARCH_LOG.md`

- [ ] **Step 1: Check referenced Markdown paths exist**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
paths = [
    'docs/current/dataset_inventory.md',
    'docs/current/domain_specialization_experiment_plan.md',
    'docs/current/paper_data_section_blueprint.md',
    'docs/contracts/data_schema_v2_contract.md',
    'docs/contracts/action_space_realization_contract.md',
    'docs/contracts/data_generation_chain_v2_1_contract.md',
    'data/official/README.md',
    'data/official/DATASET_MANIFEST.json',
]
missing = [p for p in paths if not Path(p).exists()]
print('missing=', missing)
raise SystemExit(1 if missing else 0)
PY
```

- [ ] **Step 2: Review diff**

Run:

```bash
git diff -- docs/README.md RESEARCH_LOG.md docs/superpowers/plans/2026-05-17-docs-entrypoint-cleanup.md
```
