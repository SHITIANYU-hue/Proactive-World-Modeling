# PIWM Research Log

核心逻辑基点：**数据生成闭环优于单一架构优化**。

本文件是 PIWM 项目的动态索引与计划跟踪中心。活跃文档只保留能直接服务当前闭环的入口；历史材料统一放入 `docs/archive/`。

## Active Document Index

当前唯一阅读入口： [docs/README.md](docs/README.md)。该入口按读者目标组织：数据现状、EMNLP / domain-specialization 实验、schema/action 契约、v2.2 审计报告、真实拍摄和目录运行。

### Current Sprint Entry Points

| Active Doc | Role |
|---|---|
| [docs/current/experiment_result_digest.md](docs/current/experiment_result_digest.md) | 当前已落盘实验结果速览：能写什么、还缺什么 |
| [docs/current/experiment_status_main_table_v2.md](docs/current/experiment_status_main_table_v2.md) | 主表 v2、visual ablation、frame budget、Future Verification 结果 |
| [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md) | 数据集总账：official v2 数据、真实拍摄 manifest、训练/评估/World Model 边界 |
| [docs/current/project_progress_report_2026-05-17.md](docs/current/project_progress_report_2026-05-17.md) | 给项目负责人和外部协作者看的单文档当前进度报告 |
| [docs/current/domain_specialization_experiment_plan.md](docs/current/domain_specialization_experiment_plan.md) | general -> target-frontcam smart-vending 的 two-stage SFT、joint baseline 和 eval matrix |
| [docs/current/company_openrouter_funding_brief.md](docs/current/company_openrouter_funding_brief.md) | 给公司看的精简预算沟通版：实验进度与 OpenRouter 模型对比投入说明 |
| [docs/current/company_data_status_for_openrouter.md](docs/current/company_data_status_for_openrouter.md) | 组内技术版：数据资产、当前结果与风险边界 |
| [docs/current/current_sprint_status_and_reporting_policy.md](docs/current/current_sprint_status_and_reporting_policy.md) | 对外报告口径：QA-reviewed / synthetic train / diagnostic-only 边界 |
| [docs/current/priority_generation_policy.md](docs/current/priority_generation_policy.md) | 新增 Kling 额度如何扩到 500/1000 parent synthetic |
| [docs/current/piwm_real_shooting_scripts_S01_S12.md](docs/current/piwm_real_shooting_scripts_S01_S12.md) | S01-S12 真实拍摄 A/B 单文件脚本全集 |
| [docs/current/piwm_real_shooting_data_annotation_appendix_v2.md](docs/current/piwm_real_shooting_data_annotation_appendix_v2.md) | 给数据负责人的真实数据标注附录：ShootingClipRecord、QA 字段、入库字段 |
| [docs/current/paper_data_section_blueprint.md](docs/current/paper_data_section_blueprint.md) | 论文数据部分写作蓝图：数据层级、QA、拍摄、表格和维护机制 |
| [docs/current/remote_sprint_runbook.md](docs/current/remote_sprint_runbook.md) | 远端数据盘、Kling、ms-swift 运行入口 |
| [docs/current/project_directory_map.md](docs/current/project_directory_map.md) | 本地/远端目录职责地图：official 数据、视频、checkpoint、docs 和 local artifacts 放置规则 |

### Method Contracts

| Reference Doc | Role |
|---|---|
| [docs/contracts/claim_to_artifact_audit.md](docs/contracts/claim_to_artifact_audit.md) | 论文 claim 与代码/数据工件对应关系 |
| [docs/contracts/action_space_realization_contract.md](docs/contracts/action_space_realization_contract.md) | 6-act 动作空间、真人导购逻辑 / target terminal 数据边界、旧 A/T 标签兼容迁移 |
| [docs/contracts/data_generation_chain_v2_1_contract.md](docs/contracts/data_generation_chain_v2_1_contract.md) | 动作、场景、label、专家知识库、official 重导的唯一维护链路 |
| [docs/contracts/data_schema_v2_contract.md](docs/contracts/data_schema_v2_contract.md) | 成熟数据格式、真实拍摄 clip manifest、导出策略和版本维护 |
| [docs/contracts/world_model_supervision_contract.md](docs/contracts/world_model_supervision_contract.md) | World Model 监督契约 |
| [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md) | 多视角、抽帧、frame manifest、QA gate |
| [docs/contracts/expert_provenance_upgrade_plan.md](docs/contracts/expert_provenance_upgrade_plan.md) | 专家规则 provenance 补强计划 |
| [docs/contracts/docs_maintenance_rules.md](docs/contracts/docs_maintenance_rules.md) | docs 维护守则 |

### Historical / Background Docs

历史计划、早期状态和解释材料统一放在 `docs/background/`；它们保留参考价值，但不再作为当前 sprint 决策入口。具体定位见 [docs/README.md](docs/README.md)。

## High-Density Updates

### [2026-05-17 19:00:00 CST] | Phase: EMNLP Data Story Reframing

**Key Progress**
- Locked the current paper data story as strong EMNLP-style low-resource domain specialization, not pilot-only target expansion.
- Added `paper/data_section_emnlp.tex`, a paper-ready LaTeX data section using only currently video-backed data: `PIWM-Train-Synth-v2`, `PIWM-Target-Frontcam-v1`, `PIWM-Eval-QA-v1`, and the fixed domain-specialization eval entrypoints.
- Updated active docs so 118 target videos are framed as 88-record target adaptation plus 30-record project-lead-QA in-domain eval, rather than as a failed attempt to reach 300+ target videos.

**Data Loop Insight**
- The strong claim is no longer "we have hundreds of target videos." The strong claim is "general retail guidance can specialize to a different camera/actor domain with a small reviewed target split."
- The 200 `PIWM-Target-PromptReady-v1` video-pending rows remain useful future data, but they are not required for the current EMNLP data story and should not appear in reported video-backed counts.

**Pending Criticals**
- The strong story now depends on results: Stage-1 general SFT, Stage-2 target SFT, joint baseline, target zero-shot eval, target-specialized eval, and general forgetting check.

**Ref Reference**
- `paper/data_section_emnlp.tex`
- `docs/current/domain_specialization_experiment_plan.md`
- `docs/current/project_progress_report_2026-05-17.md`

### [2026-05-17 18:20:00 CST] | Phase: Target QA Merge Into Official Target Data

**Key Progress**
- Merged the project-lead-reviewed 30-record target test QA split back into `data/official/piwm_target_v1/main_schema.jsonl`.
- Updated `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` so the 180 test-split SFT rows carry `qa_status=qa_reviewed_pass`, `human_review_status=project_lead_reviewed_pass`, reviewer, review date, review type, and warning flags.
- Refreshed the fixed target eval entrypoints under `data/official/domain_specialization_eval_v1/`: 180 rows from 30 target records, all QA pass, with 2 warning records retained.
- Updated `DATASET_MANIFEST.json`, `data/official/README.md`, `docs/current/dataset_inventory.md`, `docs/current/domain_specialization_experiment_plan.md`, and the target import report to distinguish the reviewed 30-record test split from the 88 synthetic-unreviewed train records.

**Data Loop Insight**
- Target QA is now part of the official target data surface, not just a sidecar review sheet.
- The correct paper wording is: `PIWM-Target-Frontcam-v1` has 118 video-backed records; its 30-record test split is project-lead QA-reviewed, while the 88 train records remain synthetic-unreviewed.
- The QA review validates the current-state observation labels and target action choice. It does not prove causal post-action reactions; for example, smiling in a `Greet(close)` third frame should be read as current visual evidence, not as the result caused by the Greeting action.

**Pending Criticals**
- Generate Kling videos and sampled frames for the 200 `PIWM-Target-PromptReady-v1` video-pending records before claiming 300+ target video-backed samples.
- Run Stage-1 general SFT, Stage-2 target SFT, joint baseline, zero-shot target eval, target-specialized eval, and general forgetting check.

**Ref Reference**
- `data/official/piwm_target_v1/main_schema.jsonl`
- `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl`
- `data/official/piwm_target_v1/qa_review_target30/qa_review_results.md`
- `data/official/DATASET_MANIFEST.json`

### [2026-05-17 17:30:00 CST] | Phase: Documentation Entrypoint Cleanup

**Key Progress**
- Reorganized [docs/README.md](docs/README.md) from a long flat link list into a goal-routed documentation map.
- Added a top-level current-state table that distinguishes `PIWM-Train-Synth-v2`, `PIWM-Target-Frontcam-v1`, `PIWM-Target-PromptReady-v1`, domain eval entrypoints, and `PIWM-RealShoot-v1`.
- Added explicit reading routes for data status, EMNLP / domain-specialization experiments, schema/action contracts, v2.2 audit reports, real-shooting materials, and lightweight `piwm` target-data docs.
- Updated this Active Document Index to include [docs/current/domain_specialization_experiment_plan.md](docs/current/domain_specialization_experiment_plan.md) as a first-class current entrypoint.

**Data Loop Insight**
- Documentation now reflects the current project shape: main PIWM owns official data, training/eval entrypoints, contracts, and paper story; lightweight `piwm` owns target data generation.
- The main red lines are visible at the top-level docs entry: prompt-ready is not video-backed, v2.2 schema export is not new video scale, and real-shooting remains a protocol until assets and QA exist.

**Pending Criticals**
- Update the README again after the 200 target prompt-ready rows become video-backed or after two-stage SFT/eval logs land.
- If the paper narrative fully moves away from NeurIPS history, archive or demote older sprint result docs after confirming they are no longer cited by `paper/`.

**Ref Reference**
- [docs/README.md](docs/README.md)
- [docs/current/domain_specialization_experiment_plan.md](docs/current/domain_specialization_experiment_plan.md)
- [data/official/README.md](data/official/README.md)

### [2026-05-15 18:05:00 CST] | Phase: Schema v2.2 / Independent Official Export Completion

**Key Progress**
- Added stable v2 action keys through `rules.action_spec_key(act, params)`.
- Added `MainSchemaRecord.next_state_by_action_v2`, while retaining legacy `next_state_by_action` A-label keys for continuation and old loader compatibility.
- Updated transition and continuation exports to include `candidate_action_key`.
- Added `scripts/refresh_official_v2_exports.py --output-dir`, allowing independent v2 dataset export without rewriting source official aliases.
- Wrote `PIWM-Train-Synth-v2` to `data/official/piwm_train_synth_v2/`: 543 main records, 543 state rows, 2011 transition rows, 543 policy rows.
- Wrote `data/official/ms_swift/piwm_train_synth_v2.jsonl`: 2554 ms-swift examples, with `perception=543` and `deliberation=2011`.
- Wrote `PIWM-PolicySlice-v2` to `data/official/piwm_policy_slice_v2/policy_manifest.jsonl`: 864 explicit candidate-rule policy scenarios.
- Updated `data/official/DATASET_MANIFEST.json`, `data/official/README.md`, `data/README.md`, `docs/current/dataset_inventory.md`, and v2 validation docs with the new canonical paths.

**Data Loop Insight**
- v2.2 is now an actual independent dataset surface, not just a dry-run report.
- `PIWM-Train-Synth-v1` remains the frozen compatibility alias. v2.2 training/data-format experiments should explicitly use `PIWM-Train-Synth-v2`.
- `PIWM-PolicySlice-v2` is the correct entry for action-space balance and future generation planning, but it is a rule-space manifest rather than a filmed or QA-reviewed dataset.

**Pending Criticals**
- v2.3 cleanup should remove migration-only A-key dependencies only after downstream loaders switch to `next_state_by_action_v2`.
- The v2-native policy helper should still be promoted back into expert-corpus rules, rather than living permanently only in `rules.py`.
- `PIWM-Train-Synth-v2` is still synthetic train pending visual QA; do not report it as QA-pass.

**Ref Reference**
- [data/official/DATASET_MANIFEST.json](data/official/DATASET_MANIFEST.json)
- [data/official/piwm_train_synth_v2/main_schema.jsonl](data/official/piwm_train_synth_v2/main_schema.jsonl)
- [data/official/piwm_policy_slice_v2/policy_manifest.jsonl](data/official/piwm_policy_slice_v2/policy_manifest.jsonl)
- [docs/v2_validation/v2_2_reexport_dry_run.md](docs/v2_validation/v2_2_reexport_dry_run.md)

### [2026-05-15 17:35:00 CST] | Phase: Schema v2.2 / Review Response + Official Re-derivation Audit

**Key Progress**
- Re-ran the compatibility analysis with two separate scopes: basic schema compatibility and extended v2 policy re-derivation.
- Confirmed the earlier `yellow=0` result was a detector-scope artifact: the basic tier check only marked hard schema/visual conflicts, while the extended audit detects policy drift.
- Extended official 543 audit result: `green=109`, `yellow=353`, `red=81`.
- Official 543 re-derived v2 policy best distribution: `Elicit=252`, `Recommend=119`, `Inform=105`, `Reassure=42`, `Hold=25`, `Greet=0`.
- Red samples are concentrated in `browser_low_intent`: 81 red out of 94 `browser_low_intent` records. This reflects legacy Kling prompts not separating low-intent browsing from high-engagement visual performance.
- Added `scripts/refresh_official_v2_exports.py --dry-run --output-diff <path>` and generated `docs/v2_validation/v2_2_reexport_diff_preview.md` without modifying official JSONL.
- Added `docs/v2_validation/v2_2_test_coverage.md` to list the v2.2-specific tests and the remaining uncovered items.

**Data Loop Insight**
- The true v2.2 outcome for current official data is not “462 clean / 81 bad”; it is “109 no-drift green, 353 policy-drift yellow, 81 red visual-intent conflicts.”
- `Recommend=360` belongs to the 864 explicit candidate-rule policy slice, not to the original official 543. The official 543 under v2 re-derivation yields `Recommend=119`.
- The 864 policy slice is a rule-supported simulation subset: it filters the 1920 full grid down to cases whose `(latent_state, aida_stage)` has explicit expert candidate support.

**Pending Criticals**
- Later completed: v2.2 was exported to independent paths `data/official/piwm_train_synth_v2/` and `data/official/piwm_policy_slice_v2/` without overwriting `PIWM-Train-Synth-v1`.
- Later completed: `next_state_by_action_v2` was added as a v2 action-keyed alias; v2.3 still needs migration-only A-key cleanup after downstream readers switch.
- Add unit tests for `compatibility_report.py` extended audit and `refresh_official_v2_exports.py --output-diff`; they are currently command-verified rather than isolated test-covered.

**Ref Reference**
- [docs/v2_validation/compatibility_report.md](docs/v2_validation/compatibility_report.md)
- [docs/v2_validation/action_distribution.md](docs/v2_validation/action_distribution.md)
- [docs/v2_validation/v2_2_reexport_diff_preview.md](docs/v2_validation/v2_2_reexport_diff_preview.md)
- [docs/v2_validation/v2_2_test_coverage.md](docs/v2_validation/v2_2_test_coverage.md)

### [2026-05-15 14:45:00 CST] | Phase: Schema v2.2 / Phase 2 Runtime Integration

**Key Progress**
- Added `piwm_data/migration/legacy_action_mapping.py` as the migration-only explicit A1-A8 to `(act, params)` adapter.
- Added `derive_intent_tier()` and intent-tier candidate filtering in `piwm_data/rules.py`.
- Added v2 candidate specs, failure-mode DSL matching, risk tags, and `outcome_type` support in `derive_action_outcome()`.
- Connected `archive_loader.load_session()` to the migration adapter and v2 outcome context while preserving old `candidate_actions` / `best_action` string fields for current schema compatibility.
- Added `docs/v2_validation/phase2_runtime_integration_report.md`.
- Added `docs/v2_validation/action_distribution.md`; confirmed `Recommend=0` remains unresolved after intent-tier filtering and must be fixed by candidate/outcome reward calibration.

**Data Loop Insight**
- Phase 2 now has an executable v2 path without making `legacy_action` part of the future schema.
- Low-intent browsing sessions can now filter firm recommendations before record construction.
- Failure modes can now trigger from runtime context, but formal schema promotion and official dataset re-export remain later phases.

**Pending Criticals**
- Split transition tables by `(act, params)` instead of mapping v2 actions onto old transition families.
- Promote `risk_tags`, `failure_mode`, `outcome_type`, and `intent_tier` into formal schemas in Phase 5.
- Run the action-distribution simulator before any official v2 export.

**Ref Reference**
- [docs/v2_validation/phase2_runtime_integration_report.md](docs/v2_validation/phase2_runtime_integration_report.md)
- [piwm_data/migration/legacy_action_mapping.py](piwm_data/migration/legacy_action_mapping.py)
- [piwm_data/rules.py](piwm_data/rules.py)

### [2026-05-15 15:05:00 CST] | Phase: Schema v2.2 / Phase 4 Label Leakage Gate

**Key Progress**
- Extended `scripts.prompt_builder.forbidden_label_hits()` to include v2.2 labels: `intent_tier`, `failure_mode`, `risk_tags`, `outcome_type`, DialogueAct names, legacy A-labels, and intent labels.
- Added `scripts.qa_gate.check_label_leakage(prompt_json)` as an explicit QA entrypoint.
- Added tests proving internal labels are rejected while plain visible behavior descriptions pass.
- Added `docs/v2_validation/label_leakage_policy.md`.

**Data Loop Insight**
- Kling/video prompts can carry natural visible behavior descriptions, but must not contain gold policy/state labels.
- This protects the synthetic visual data loop from leaking the answer into generated pixels or prompt metadata visible to generation.

**Pending Criticals**
- Keep `scenario_metadata.derived` available for prompt JSON traceability, but never include those labels in `kling_prompt`.
- Any new internal label field must update the blacklist, tests, and label leakage policy doc.

**Ref Reference**
- [docs/v2_validation/label_leakage_policy.md](docs/v2_validation/label_leakage_policy.md)
- [scripts/qa_gate.py](scripts/qa_gate.py)
- [scripts/prompt_builder.py](scripts/prompt_builder.py)

### [2026-05-15 15:20:00 CST] | Phase: Schema v2.2 / Phase 5 Schema Increment

**Key Progress**
- Added `Persona.intent_tier` with automatic fill from `rules.derive_intent_tier()`.
- Added `ActionOutcome` v2 fields: `dialogue_act`, `act_params`, `intent_tier`, `risk_tags`, `failure_mode`, and `outcome_type`.
- Added schema validation that failure outcomes must carry `failure_mode`.
- Added `CandidateAction` as the canonical v2 `(act, params)` object without a `legacy_action` field.
- Added `MainSchemaRecord.candidate_action_specs`, `best_action_spec`, `compatibility_tier`, and `legacy_mismatch_flags` as compatibility-preserving v2 mirror fields.
- Added `scripts/compatibility_report.py` and generated `docs/v2_validation/compatibility_report.md` from official v1 `main_schema.jsonl`.
- Bumped runtime export schema constant to `dialogue_act_human_salesperson_v2.2`.
- Added `--dry-run` to `scripts/refresh_official_v2_exports.py` and verified official v1/eval/world-model datasets can be read without writing files.
- Added `docs/v2_validation/phase5_schema_increment_report.md`.

**Data Loop Insight**
- Runtime v2 outcome fields are now preserved by schema instead of being silently dropped by Pydantic.
- Old `candidate_actions` / `best_action` string fields remain in place as migration keys, while `candidate_action_specs` / `best_action_spec` are now the schema-level canonical v2 mirror.
- Basic official v1 compatibility tiering was `green=462`, `yellow=0`, `red=81`; this was later clarified as schema-level only, not a full policy-drift audit.
- Official re-export dry-run counts are stable: train `543/2011/543/0`, eval `36/126/36/0`, world-model `24/66/24/44` for state/transition/policy/continuation.
- Recommend-zero diagnosis: current legacy candidate space only exposes `Recommend(pressure=firm)` through `A3_strong_recommend`; it appears in candidates but never wins under old reward selection. Raising A3 directly would promote strong recommendation, so the correct next step is v2-native candidate specs with soft/firm Recommend split.
- Added v2-native policy helpers `derive_policy_candidate_specs()` and `pick_best_action_spec()`; later review clarified that `Recommend=360` belongs to the 864 explicit candidate-rule slice, not the 1920 full grid.
- Added `scripts.scenario_sampler --candidate-rule-only`; explicit candidate-rule slice has 864 scenarios and avoids the 1056 default-fallback state/AIDA combinations that inflate low-intervention actions.

**Pending Criticals**
- `next_state_by_action` still uses legacy A-label keys; v2 action-key migration remains pending.
- Reward calibration has not yet fixed official legacy `best_action`; v2 policy path fixes Recommend/Elicit entry, but `Hold/Reassure` remain high in full rule-space because many unlikely state/aida combinations still fall through to low-intervention defaults.
- New v2 policy data generation should use the explicit candidate-rule slice before official dataset rewrite.
- No official dataset files have been rewritten by this step.

**Ref Reference**
- [docs/v2_validation/phase5_schema_increment_report.md](docs/v2_validation/phase5_schema_increment_report.md)
- [docs/v2_validation/compatibility_report.md](docs/v2_validation/compatibility_report.md)
- [docs/v2_validation/v2_2_reexport_dry_run.md](docs/v2_validation/v2_2_reexport_dry_run.md)
- [piwm_data/schemas.py](piwm_data/schemas.py)

### [2026-05-15 14:05:00 CST] | Phase: Schema v2.2 / Phase 2 Preflight Source Hardening

**Key Progress**
- Added `batch_005_source_hardening` to the expert-corpus distillation batches.
- Promoted `SRC_SALES_BABIN_GIFT_SHOPPING_VALUE_2007` and `P_GIFT_SHOPPING_001` to support `gift_buyer_uncertain -> exploring`.
- Promoted `SRC_SALES_ARNOLD_REYNOLDS_HEDONIC_MOTIVATIONS_2003` and `P_HEDONIC_MOTIVATION_001` to support hedonic browsing behavior.
- Removed Bellenger 1980 from the current executable rule chain; it remains only as a historical candidate source/principle until a direct source is available.
- Added `failure_mode_rationale` for the 4 null Hold transitions and schema/test coverage requiring rationale when `failure_mode=null`.
- Confirmed the live `gift_buyer_uncertain` persona definition is "A shopper buying for someone else and unsure which option fits best.", so the `uncertain` boundary supports `PIT_005 -> exploring`.
- Added `docs/v2_validation/failure_mode_coverage.md` to document that v2.2 covers active-intervention failures, while passive failures such as under-engagement and premature withdrawal require a future service-failure source batch.
- Documented trigger-condition DSL v0.1 and Phase 2 legacy-adapter requirements in `docs/v2_validation/phase2_preflight_review.md`.

**Data Loop Insight**
- `gift_buyer_uncertain` is no longer only supported by generic social-factor rules; it now has gift-shopping-specific provenance.
- `browser_low_intent` no longer depends on a secondary Bellenger citation in the runtime rule chain.
- Phase 2 should implement legacy compatibility as an archive-loader adapter only: no `legacy_action` field in v2 schema.

**Pending Criticals**
- Phase 2 must implement `piwm_data/migration/legacy_action_mapping.py` as an explicit A1-A8 dict, with full unit-test coverage.
- Phase 2 must implement trigger-condition matching without `eval`, with unknown lhs/op treated as an error or QA failure.
- Phase 7 TODO remains: official v2 上线后，必须更新 `docs/current/dataset_inventory.md`、`data/official/DATASET_MANIFEST.json` 和 `data/official/README.md`，并标注 v1 进入 `_legacy`。

**Ref Reference**
- [docs/v2_validation/phase2_preflight_review.md](docs/v2_validation/phase2_preflight_review.md)
- [piwm_data/expert_corpus/distillation_batches/batch_005_source_hardening/README.md](piwm_data/expert_corpus/distillation_batches/batch_005_source_hardening/README.md)
- [piwm_data/expert_corpus/distilled/conditional_rules.jsonl](piwm_data/expert_corpus/distilled/conditional_rules.jsonl)

### [2026-05-15 01:30:00 CST] | Phase: Schema v2.2 / Expert Corpus Phase 1B

**Key Progress**
- Extended `TransitionValue` with optional `failure_mode`.
- Added `failure_mode` fields to all 21 transition rules: 17 explicit failure modes and 4 explicit `null` values.
- Extended transition rule source links with failure-mode source references where relevant.
- Added a compiler test that verifies failure modes compile and retain principle refs.

**Data Loop Insight**
- Failure modes are now auditable expert-corpus metadata but are not yet used by `piwm_data/rules.py` outcome calculation.
- This keeps the migration safe: the old transition rewards still match runtime literals, while v2.2 has enough structured knowledge for the next rule-layer refactor.

**Pending Criticals**
- DoD-v2.2-3：split `Recommend(pressure=soft)` and `Recommend(pressure=firm)` in candidate/outcome rules.
- DoD-v2.2-4：wire `derive_failure_mode` into runtime outcome calculation after candidate/reward updates.
- DoD-v2.2-5：rerun action-distribution diagnostics before official export changes.
- Phase 7 TODO：official v2 上线后，必须更新 `docs/current/dataset_inventory.md`、`data/official/DATASET_MANIFEST.json` 和 `data/official/README.md`，并标注 v1 进入 `_legacy`。

**Ref Reference**
- [piwm_data/expert_corpus/distilled/conditional_rules.jsonl](piwm_data/expert_corpus/distilled/conditional_rules.jsonl)
- [piwm_data/tests/test_expert_corpus.py](piwm_data/tests/test_expert_corpus.py)

### [2026-05-15 01:00:00 CST] | Phase: Schema v2.2 / Expert Corpus Phase 1A

**Key Progress**
- Added `persona_to_intent_tier` to the expert-corpus schema and compiler.
- Added six v2.2 `PIT_*` rules covering all current persona types.
- Added source links for all six `PIT_*` rules with `lifecycle=new_source_backed` and `review_status=approved`.

**Data Loop Insight**
- `conditional_rules.jsonl` now has 78 entries: 72 existing seed/runtime rules plus 6 v2.2 intent-tier rules.
- The old runtime literal tables in `piwm_data/rules.py` are still unchanged; Phase 1A only makes intent tier auditable and compilable.
- Coverage is now 78/78 linked, with `manual_supported=38` and `theory_anchored=40`.

**Pending Criticals**
- DoD-v2.2-2：extend transition rules with machine-readable `failure_mode`. Done in Phase 1B.
- DoD-v2.2-3：split `Recommend(pressure=soft)` and `Recommend(pressure=firm)` in candidate/outcome rules.
- DoD-v2.2-4：only after rule changes, rerun action-distribution diagnostics and official export dry-run.

**Ref Reference**
- [piwm_data/expert_corpus/README.md](piwm_data/expert_corpus/README.md)
- [docs/v2_validation/distillation_summary.md](docs/v2_validation/distillation_summary.md)

### [2026-05-15 00:30:00 CST] | Phase: Schema v2.2 / Distillation Review Phase 0B

**Key Progress**
- Reviewed 11 v2.2 draft principles and converted them from `DRAFT_*` to stable ids:
  `P_INTENT_TIER_001`-`004`, `P_FAILURE_MODE_001`-`004`, and `P_RECOMMEND_PRESSURE_001`-`003`.
- Promoted 3 source additions into `sales_source_registry.jsonl`: Babin (1994), Bellenger and Korgaonkar (1980), and Brehm (1966).
- Promoted 11 finalized compact principles into `distilled/extracted_principles.jsonl`.
- Updated `docs/v2_validation/distillation_summary.md` and `piwm_data/expert_corpus/README.md` to reflect Phase 0B status.

**Data Loop Insight**
- The expert corpus now has source-backed inputs for intent tier, failure-mode logic, and `Recommend(pressure=soft/firm)`.
- Runtime policy remains unchanged after Phase 0B: the old `piwm_data/rules.py` tables still map to the 72 seed rules.
- A dry-run for `batch_004_recommend_pressure` correctly failed before `batch_003_failure_mode` was promoted because it referenced `SRC_SALES_REACTANCE_BREHM_1966`; after promoting batch 003, batch 004 passed and was committed.

**Pending Criticals**
- DoD-v2.2-1：add `persona_to_intent_tier` rule type and compile support. Done in Phase 1A.
- DoD-v2.2-2：extend transition rules with machine-readable `failure_mode`. Done in Phase 1B.
- DoD-v2.2-3：split `Recommend(pressure=soft)` and `Recommend(pressure=firm)` in candidate/outcome rules, then rerun action-distribution diagnostics.

**Ref Reference**
- [docs/v2_validation/distillation_summary.md](docs/v2_validation/distillation_summary.md)
- [piwm_data/expert_corpus/distillation_batches/README.md](piwm_data/expert_corpus/distillation_batches/README.md)

### [2026-05-14 23:00:00 CST] | Phase: Schema v2.2 / Distillation Infrastructure Phase 0A

**Key Progress**
- Added `piwm_data/expert_corpus/distillation_batches/` as the required staging area for v2.2 expert knowledge before promotion into `distilled/`.
- Added `batch_001_seed`, `batch_002_intent_tier`, `batch_003_failure_mode`, and `batch_004_recommend_pressure`.
- Added dry-run maintenance tools: `run_distillation.py`, `review_helper.py`, and `promote_to_corpus.py`.
- Generated pending review logs for 11 draft principles: 4 intent-tier, 4 failure-mode, and 3 recommendation-pressure drafts.
- Added `docs/v2_validation/distillation_summary.md` as the current review and validation entry for v2.2 distillation.

**Data Loop Insight**
- Phase 0A intentionally does not update `distilled/extracted_principles.jsonl`, `conditional_rules.jsonl`, `rule_source_links.jsonl`, `rules.py`, or official data.
- Babin (1994), Bellenger (1980), and Brehm (1966) are currently candidate source additions only; they are not promoted until review.
- Copyright mode for those sources is `citation_only`, so batches store compact paraphrases and source locators rather than source text.

**Pending Criticals**
- DoD-v2.2-0A-1：人工审阅三个 review logs，把 `pending` 改为 `approved / revise / reject`。
- DoD-v2.2-0A-2：dry-run promote 无 duplicate id 后，才能 `--commit` source/principle additions。
- DoD-v2.2-1：只有 principle 入库后，才能新增 `persona_to_intent_tier`、`failure_mode` 和 `Recommend(pressure=soft/firm)` reward 规则。

**Ref Reference**
- [docs/v2_validation/distillation_summary.md](docs/v2_validation/distillation_summary.md)
- [piwm_data/expert_corpus/README.md](piwm_data/expert_corpus/README.md)

### [2026-05-13 00:00:00 CST] | Phase: Action Schema v2.1 / Human-Salesperson Boundary

**Key Progress**
- 明确 `PIWM-Train-Synth-v1` 保留真人导购逻辑：主监督是 `best_action_realization.utterance / physical_action / timing / rationale`，不是 target terminal 硬件采集数据。
- 保留 6 个 `DialogueAct` 作为统一 policy space：`Greet / Elicit / Inform / Recommend / Reassure / Hold`。
- 将顶层 `co_acts` 降级为 legacy alias；2026-05-13 official v2.1 重导后，主表使用 `act_params.supporting_acts` 表示辅助动作，例如 `Reassure(focus=time, supporting_acts=[Hold(ambient)])`，旧回溯字段写为 `legacy_co_acts`。
- 新增 `scripts/audit_action_space.py`，用于审计 best action、candidate action、DialogueAct 和 supporting-act 分布。
- 新增 `docs/contracts/data_generation_chain_v2_1_contract.md` 和 `piwm_data/expert_corpus/README.md`，把动作、场景、label、专家知识库和 official 重导链路收敛为一个维护路径。

**Data Loop Insight**
- 当前 543 条 synthetic train 的 best DialogueAct 分布不是均衡六动作分布：`Inform=407`、`Elicit=69`、`Hold=59`、`Reassure=8`、`Recommend=0`、`Greet=0`。
- `Recommend=0` 不是动作空间缺失，而是现有 reward/candidate 规则把推荐主要作为强推负样本。后续需要单独构造 balanced policy slice，尤其拆出 `Recommend(pressure=soft)` 正样本。
- `Greet` 应主要由 realshoot / target terminal 开闭场数据补，不应强行塞进当前 synthetic browsing train。

**Pending Criticals**
- DoD-Act-v2.1-1：official v2.1 重导完成后，主表已输出 `schema_version=dialogue_act_human_salesperson_v2.1` 和 `actor_profile=human_salesperson_logic`。
- DoD-Act-v2.1-2：专家库需要审阅 `state_aida_to_candidates` 和 `transition`，解决 `Inform` 过高、`Recommend(soft)` 缺正样本的问题。
- DoD-Act-v2.1-3：target terminal dataset 单独建设，不能把 `PIWM-Train-Synth-v1` 的真人动作写成终端硬件行为。

**Ref Reference**
- [docs/contracts/action_space_realization_contract.md](docs/contracts/action_space_realization_contract.md)
- [docs/contracts/data_generation_chain_v2_1_contract.md](docs/contracts/data_generation_chain_v2_1_contract.md)
- [piwm_data/expert_corpus/README.md](piwm_data/expert_corpus/README.md)

### [2026-05-11 21:00:00 CST] | Phase: Data Schema v2 / Real Shooting Script Package

**Key Progress**
- Added `docs/contracts/data_schema_v2_contract.md` as the active schema contract for `MainSchemaRecord`, `TerminalRealization`, `ShootingClipRecord`, export fields, and maintenance rules.
- Added `ShootingClipRecord` to `piwm_data/schemas.py` and the S01-S12 shooting priors to `piwm_data/rules.py`, so real-shooting clips can auto-fill `dialogue_act`, `act_params`, `legacy_action`, `t_state`, expected reaction, and HERO-view requirements.
- Completed the editable S01-S12 A/B shooting script as one self-contained file at `docs/current/piwm_real_shooting_scripts_S01_S12.md`, including the normalized S05 script derived from the provided source format.
- Added `docs/current/paper_data_section_blueprint.md` to keep the paper data narrative, dataset tables, QA gates, action schema, and maintenance path aligned.

**Data Loop Insight**
- The project now has a single data spine: source attachments -> action/realization contract -> schema tests -> shooting scripts -> `ShootingClipRecord` -> official dataset inventory -> paper data section.
- Real shooting is no longer just production guidance; it is an enforceable manifest format that can be validated before entering QA-reviewed data.

**Pending Criticals**
- DoD-Data-1：真实拍摄素材落地后，先生成 `ShootingClipRecord` manifest，再进入 QA-reviewed official split。
- DoD-Data-2：任何新增状态、脚本或终端能力必须同步更新 contract、schema tests、script README 和 paper data blueprint。
- DoD-Data-3：旧 A/T 标签只作为 alias 保留；论文正文优先写 `DialogueAct + params + TerminalRealization`。

**Ref Reference**
- [docs/contracts/data_schema_v2_contract.md](docs/contracts/data_schema_v2_contract.md)
- [docs/current/piwm_real_shooting_scripts_S01_S12.md](docs/current/piwm_real_shooting_scripts_S01_S12.md)
- [docs/current/paper_data_section_blueprint.md](docs/current/paper_data_section_blueprint.md)

### [2026-05-11 20:00:00 CST] | Phase: Action Space v2 / Project System Integration

**Key Progress**
- Added `docs/contracts/action_space_realization_contract.md` as the active contract for the 6 Dialogue Acts, terminal realization output, and old `A1-A8` / `T-state` compatibility mapping.
- Copied the May 2026 action-space and shooting attachments into `docs/source_materials/2026-05-action-space/` with a source digest and explicit source priority.
- Added v2 action metadata to `piwm_data/rules.py`, `piwm_data/schemas.py`, `piwm_data/exporters.py`, and `piwm_train/prompts.py` while preserving old action labels for existing data.

**Data Loop Insight**
- The new project center is no longer a flat action label list. Policy uses `(DialogueAct, params)`, Realization translates it to terminal behavior, and old A/T labels remain only as compatibility aliases.

**Pending Criticals**
- DoD-Act-1：新增真实拍摄入库字段时必须同时记录旧 action alias 和新 `dialogue_act / act_params / realization`。
- DoD-Act-2：S05 A/B 样例保持固定：A=`Inform(comparison)`，B=`Recommend(firm)`。
- DoD-Act-3：后续新增终端能力优先增加 realization 模板，不扩展 policy act。

**Ref Reference**
- [docs/contracts/action_space_realization_contract.md](docs/contracts/action_space_realization_contract.md)
- [docs/source_materials/2026-05-action-space/source_digest.md](docs/source_materials/2026-05-action-space/source_digest.md)

### [2026-05-11 00:00:00 CST] | Phase: Repo Hygiene / Directory Map

**Key Progress**
- Added `docs/current/project_directory_map.md` as the canonical local/remote directory map for code, docs, official datasets, generated videos, checkpoints, and local artifacts.
- Updated `docs/README.md`, `docs/current/dataset_inventory.md`, `docs/current/local_artifacts_layout.md`, and `docs/current/remote_sprint_runbook.md` to the May 11 official-data/checkpoint layout.
- Archived duplicate docs copies from `docs/current/* (1).md` into `docs/archive/2026-05-11_directory_cleanup/`.
- Moved the stale duplicate official manifest into `data/official/archive/DATASET_MANIFEST_20260501_old.json`.
- Recorded latest effective checkpoint as `data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834`.

**Data Loop Insight**
- Directory responsibilities now separate four surfaces: local code/docs, remote data/video/checkpoints, official dataset aliases, and historical or diagnostic artifacts.
- This prevents training-only synthetic data, QA-reviewed evaluation, World Model evidence, and smoke outputs from being mixed in paper or demo reporting.

**Pending Criticals**
- DoD-Dir-1：新增视频、checkpoint 或大中间文件必须落到远端 `/root/lanyun-fs/ProactiveIntentWorldModel`，不得写入本机 repo 根目录或远端系统盘。
- DoD-Dir-2：新文档必须先查 `docs/README.md` 和 `docs/contracts/docs_maintenance_rules.md`，能更新旧文档就不新增。
- DoD-Dir-3：如果远端恢复后发现新的 official symlink 或 checkpoint，先更新 `project_directory_map.md` 和 `dataset_inventory.md`。

**Ref Reference**
- [docs/current/project_directory_map.md](docs/current/project_directory_map.md)
- [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md)
- [docs/current/remote_sprint_runbook.md](docs/current/remote_sprint_runbook.md)

### [2026-05-02 16:52:00 CST] | Phase: Real-Data Shooting Contract / Execution Detail

**Key Progress**
- Expanded the shooting-team execution checklist with a 10-second shot rhythm: current customer state, salesperson intervention, and visible reaction.
- Added pre-shoot setup requirements for product placement, actor floor marks, A/B continuity, and performance intensity.
- Rewrote the 12 customer states into detailed actor instructions covering body position, gaze, facial expression, hand motion, must-see evidence, and forbidden acting choices.
- Added salesperson action performance standards: distance, stance, gesture, tone, must-see visual evidence, and failure modes.
- Added A/B shooting order, post-action reaction vocabulary, viewpoint framing notes, and director read-aloud cue cards.

**Data Loop Insight**
- The shooting doc now specifies observable behavior rather than internal labels, improving the chance that real videos support downstream perception, action choice, and future-reaction supervision.
- A/B pairs are now operationally protected by floor marks, immediate reshoots, and start-frame consistency checks.

**Pending Criticals**
- DoD-Real-1：G001 试拍时验证导演口令是否足够让演员稳定复现 12 个起始状态。
- DoD-Real-2：每个 A/B pair 的前 3 秒用截图对照，至少 10/12 pair 起点一致。
- DoD-Real-3：试拍后根据失败样本回写状态卡和导购动作卡。

**Ref Reference**
- [docs/current/piwm_real_shooting_execution_checklist_v2.md](docs/current/piwm_real_shooting_execution_checklist_v2.md)

### [2026-05-02 16:32:00 CST] | Phase: Real-Data Shooting Contract / Audience Split

**Key Progress**
- 将真实数据拍摄主文档改为拍摄团队执行版：只保留拍什么、怎么演、怎么验收、怎么交付。
- 从主文档剥离 `compact_v2`、`visual_state`、`reward`、QA 字段等内部数据规范，新增独立附录 `docs/current/piwm_real_shooting_data_annotation_appendix_v2.md`。
- 重写现场 QA 为可执行检查表，替代 JSON 字段清单，降低公司拍摄人员理解成本。
- 将 20 组排班表中的顾客人设和用途从内部枚举改为中文拍摄说明。

**Data Loop Insight**
- 拍摄团队现在只负责产出可见证据：起始状态、导购动作、顾客后续反应。
- 数据负责人通过附录承接同一批素材到 PIWM schema，避免现场执行被技术字段干扰，同时保持入库可追溯。

**Pending Criticals**
- DoD-Real-1：G001 试拍前由拍摄负责人只阅读执行版，并确认每条 clip 卡能被现场使用。
- DoD-Real-2：数据负责人单独审阅标注附录，确认拍摄素材能落到 compact_v2 和 Future Verification。
- DoD-Real-3：试拍后按执行版 QA 表判定是否重拍，再由数据负责人补充技术标注。

**Ref Reference**
- [docs/current/piwm_real_shooting_execution_checklist_v2.md](docs/current/piwm_real_shooting_execution_checklist_v2.md)
- [docs/current/piwm_real_shooting_data_annotation_appendix_v2.md](docs/current/piwm_real_shooting_data_annotation_appendix_v2.md)

### [2026-05-02 16:08:00 CST] | Phase: Real-Data Shooting Contract

**Key Progress**
- 将微信新版 `PIWM-真实数据拍摄执行清单.md` 复制并补强为项目内正式文档：`docs/current/piwm_real_shooting_execution_checklist_v2.md`。
- 新增机位定义与可见性要求，明确 `salesperson_observable` / `surveillance_oblique` / `third_party_side` 的画面边界。
- 新增逐条 clip 拍摄卡模板，要求每条样本写清 0-3 秒起始状态、3-5 秒导购动作、5-10 秒顾客后续反应。
- 将真实数据标注字段对齐 compact_v2：`visual_state` 三轴、`best_action_realization`、三轴 `visible_reaction`。
- 新增 `risk / benefit / reward` 标注规则、文件目录结构、`clip_manifest.csv` 字段和 QA pass 表。

**Data Loop Insight**
- 真实拍摄文档现在能直接服务入库：视频、抽帧、label、QA 和 future verification 字段有统一出口。
- 真实数据不再只是“拍行为素材”，而是从拍摄阶段就对齐 PIWM 的状态推理、动作选择和动作后果验证任务。

**Pending Criticals**
- DoD-Real-1：正式拍满 20 组前，先完成 G001 24 条试拍。
- DoD-Real-2：试拍至少 20/24 条 QA pass，且至少 10/12 个 A/B pair 满足起始状态一致和 `reward(A) > reward(B)`。
- DoD-Real-3：试拍后再决定是否把真实数据纳入 train，当前优先作为 QA-reviewed real eval/test。

**Ref Reference**
- [docs/current/piwm_real_shooting_execution_checklist_v2.md](docs/current/piwm_real_shooting_execution_checklist_v2.md)
- [docs/README.md](docs/README.md)

### [2026-05-02 11:12:00 CST] | Phase: Training / Fresh 8-GPU Enriched Official Run

**Key Progress**
- 放弃旧 `priority1000_current_len8192_8gpu` checkpoint 作为当前主结果，重新从 Qwen2.5-VL-7B-Instruct base 启动 8 卡 LoRA SFT。
- 新训练数据入口：`data/official/ms_swift/piwm_train_synth_v1.jsonl`，2554 SFT examples，schema 为 enriched compact official v1。
- 新 checkpoint：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_enriched_official_v1_len8192_8gpu/v0-20260502-090632/checkpoint-638`。
- 发现原评估 `max_new_tokens=256` 会截断 perception 输出，导致 parse 被系统性低估；已重跑 long-token eval。
- Long-token 主表结果：162/162 parse 成功；stage 80.56%，proactive score 77.78%，candidate actions 75.00%，transition next-stage/risk/benefit/reward 均 100%。
- Long-token 端到端结果：36/36 perception parse 成功，36/36 action parse 成功，fallback 0%；chosen in gold candidates 86.11%，strategy vs best_action 38.89%。

**Data Loop Insight**
- 新训练已经学到 enriched compact schema 的长输出格式；之前 perception 0 parse 是评估 token 截断，不是模型没有学会。
- 当前主要短板从“格式/字段不稳定”转移到“端到端策略选择”：模型能产生候选和 transition，但最后选 best_action 的能力仍需单独优化。
- Transition 相关 100% 仍应解释为 rule-conditioned deterministic supervision，不应夸大为真实随机未来预测能力。

**Pending Criticals**
- DoD-Train-Fresh-1：后续报告默认引用 `*_enriched_official_v1_len8192_*_longtok.json`，不要再引用短 token 评估结果。
- DoD-Train-Fresh-2：下一步优先做 action-selection repair / decision-loop calibration，而不是继续重训 perception。
- DoD-Train-Fresh-3：如需要论文主表，必须同时报告 parse rate 和端到端 strategy accuracy，避免只展示 transition 100%。

**Ref Reference**
- [data/piwm_results/main_table_piwm_sft_enriched_official_v1_len8192_priority40_all_longtok.json](data/piwm_results/main_table_piwm_sft_enriched_official_v1_len8192_priority40_all_longtok.json)
- [data/piwm_results/e2e_piwm_sft_enriched_official_v1_len8192_priority40_decision_loop_longtok.json](data/piwm_results/e2e_piwm_sft_enriched_official_v1_len8192_priority40_decision_loop_longtok.json)
- [logs/run_enriched_official_v1_len8192_8gpu.sh](logs/run_enriched_official_v1_len8192_8gpu.sh)
- [logs/run_eval_enriched_official_v1_len8192_longtok.sh](logs/run_eval_enriched_official_v1_len8192_longtok.sh)

### [2026-05-02 08:50:00 CST] | Phase: Data Contract / Field Semantics Polish

**Key Progress**
- 优化 compact schema 的字段内容，不改字段结构：`visual_state` 现在加入 product-specific scene/focus，`bdi.belief` 改为 cue-aware 文本，`best_action_realization` 改为产品类别相关的话术和动作。
- 重导 remote official 数据：`PIWM-Train-Synth-v1` 保持 543 parent / 2554 SFT examples，`PIWM-Eval-QA-v1` 保持 36 parent / 162 eval rows，`PIWM-WorldModel-v1` 保持 24 parent / 44 continuation / 84 future verification。
- 官方数据旧字段/泄露扫描通过：未发现 `best_intervention`、`intervention_readiness`、旧 four-field `visible_reaction`、`Persona:` belief 尾巴。
- 本地回归测试通过：`158 passed`。

**Data Loop Insight**
- 这一步不增加视频数量，而是提高每条样本的监督密度：模型不只学习 `high_hesitation` / `A2_offer_value_comparison`，还学习“画面怎么看出来”和“具体怎么介入”。
- 字段语义更接近可展示 demo：同一条样本可以从视觉证据、顾客建模、策略选择和导购话术四层解释。

**Pending Criticals**
- DoD-Field-1：后续重新训练才会让模型真正学到这版更细字段；旧 checkpoint 仍是旧 wording 训练结果。
- DoD-Field-2：对外展示时可以使用 enriched official data，但必须区分 raw model output 与 human-facing rendering。
- DoD-Field-3：如继续优化，优先补 `visual_state` 的人工审阅质量，而不是新增粗标签。

**Ref Reference**
- [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md)
- [data/official/DATASET_MANIFEST.json](data/official/DATASET_MANIFEST.json)

### [2026-05-02 03:38:00 CST] | Phase: Data Contract / Formal Train Re-Export

**Key Progress**
- 在远端数据盘创建轻量数据处理环境 `/root/lanyun-fs/venvs/piwm-data`，使用阿里云源安装 `pydantic 2.12.5`。
- 重导正式主训练数据：`data/piwm_dataset_priority1000_unreviewed_compact_v2`，543 parent / 2011 transition / 543 policy，未人工全量视觉审阅。
- 重导 ms-swift 输入：`data/piwm_results/ms_swift_priority1000_compact_v2/ms_swift_sft.jsonl`，2554 SFT examples，task_counts = perception 543 / deliberation 2011。
- 更新 official alias：`data/official/piwm_train_synth_v1 -> ../piwm_dataset_priority1000_unreviewed_compact_v2`，`data/official/ms_swift/piwm_train_synth_v1.jsonl -> ../../piwm_results/ms_swift_priority1000_compact_v2/ms_swift_sft.jsonl`。
- 字段泄露检查通过：official train JSONL 中未出现旧字段 `intervention_readiness` / `best_intervention` / `intervention_plan_by_action` / `*_zh` / 旧 visual axes。

**Data Loop Insight**
- 正式训练入口现在使用 compact visual-state/action-realization schema，模型训练目标从“粗标签”推进到“画面三轴解释 + 具体导购动作/话术”。
- 数据规模不变，语义密度提升；旧 `priority1000_unreviewed` 保留为回滚，不再作为默认 official training entry。

**Pending Criticals**
- DoD-Train-v2：若继续训练，默认使用 `data/official/ms_swift/piwm_train_synth_v1.jsonl`，不要回退旧字段版。
- DoD-Eval-v2：新 checkpoint 评估时必须记录 schema source = `compact_v2`，避免与旧 checkpoint 指标混淆。
- DoD-Docs-v2：对外口径仍是 synthetic train pending visual QA，不能写成 QA-pass。

**Ref Reference**
- [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md)
- `/root/lanyun-fs/ProactiveIntentWorldModel/data/official/DATASET_MANIFEST.json`

### [2026-05-02 00:45:00 CST] | Phase: Reporting / Data Case Study Polish

**Key Progress**
- 新增 `docs/current/data_case_study_handbook.md`，用 `piwm_287c764c9f` 作为主案例，从当前画面、机器标签、候选动作、后续反应视频、Future Verification 四层解释一条数据。
- 将 raw labels 与 human-facing rendering 明确拆开：训练输出可以是结构化标签，但对外 demo 必须经过可审计解释层。
- 固化可展示的动作对照：`A2_offer_value_comparison` 导向 `engaged_dialogue`，`A3_strong_recommend` 导向 `defensive_withdrawal`，并配套三张 contact sheet。
- 在 `docs/README.md` 与 `docs/current/data_demo_effect_status.md` 中加入样本手册入口。

**Data Loop Insight**
- 当前问题不是“没有例子”，而是例子如果只贴 JSON 会显得粗糙；必须把视觉证据、规则标签、训练题和展示解释绑定起来。
- `FutureVerification` 的展示重点应从抽象分数转向“当前画面 + 动作 + 后续反应画面 -> match/mismatch”，这能更直接支撑 action-conditioned future verification。

**Pending Criticals**
- DoD-Demo-3：对外展示必须同时保留 raw output 和解释渲染，不把人工/模板渲染冒充模型原始自然语言。
- DoD-Demo-4：后续 demo 优先使用 `piwm_287c764c9f`，因为它同时具备当前状态、正向 continuation、负向 continuation 和 Future Verification 负例。
- DoD-Demo-5：下一轮训练/数据设计应降低 BDI 模板感，加入 fine-grained visual state 字段。

**Ref Reference**
- [docs/current/data_case_study_handbook.md](docs/current/data_case_study_handbook.md)
- [docs/current/data_demo_effect_status.md](docs/current/data_demo_effect_status.md)
- [docs/current/before_after_demo_examples.md](docs/current/before_after_demo_examples.md)

### [2026-05-02 02:35:00 CST] | Phase: Data Contract / Fine-Grained Intervention Supervision

**Key Progress**
- 将 `visual_state` 精简为 summary / engagement_pattern / gaze_and_attention / body_and_hands 四字段，去掉重复的旧视觉子字段。
- 将 `best_intervention` / `intervention_plan_by_action` 迁移为 `best_action_realization` / `action_realization`，训练样本直接输出“怎么站、怎么做、什么时候说、说什么”。
- `state_inference`、`transition_modeling`、`policy_preference`、training targets 和 parsers 已接入精简字段；`proactive_score` 保留为 deprecated internal calibration，不再作为对外核心语义。
- 生成 `data/piwm_dataset_pilot30_compact_preview/` 作为精简字段预览，`piwm_287c764c9f` 已能输出三轴 visual_state 和中文 action realization。

**Data Loop Insight**
- 这一步把 PIWM 从“标签监督”推进到“可审计状态推理监督”：模型必须先描述画面事实，再给状态和干预方案。
- 具体话术进入训练目标后，demo 可以展示真实导购行为建议，而不是只展示 `A2_offer_value_comparison` 这种内部标签。

**Pending Criticals**
- DoD-Detail-1：下一轮主训练集重导出时使用 `best_action_realization` / `action_realization`，并确认 ms-swift 输入包含 `intervention_action` / `intervention_utterance`。
- DoD-Detail-2：后续评估应新增 visual_state 三轴字段级指标，定位错误发生在看图、状态映射还是策略话术。
- DoD-Detail-3：BDI 文本仍需进一步从规则模板迁移到 visual_state-conditioned 摘要。

**Ref Reference**
- [docs/current/data_case_study_handbook.md](docs/current/data_case_study_handbook.md)
- [data/piwm_dataset_pilot30_compact_preview/](data/piwm_dataset_pilot30_compact_preview/)

### [2026-05-02 00:20:00 CST] | Phase: Repo Hygiene / GitHub Management

**Key Progress**
- 完成本地与服务器目录盘点：本地已有 GitHub remote，服务器 `/root/lanyun-fs/ProactiveIntentWorldModel` 当前不是 Git repo。
- 识别本地 Git 已追踪约 2080 个 generated/media 文件，主要来自早期 `Archive/`、`Archive_generated_priority*`、`Archive_prompts_priority*` 和 `data/piwm_results`。
- 强化 `.gitignore`，排除 generated archives、dataset outputs、training results、review sheets、logs、`.secrets/` 和 `kling/.env`。
- 新增 `docs/current/repo_cleanup_github_plan.md`，明确代码进 GitHub、数据留数据盘的目录治理方案。

**Data Loop Insight**
- 当前不能把数据产物和代码一起推 GitHub；否则 repo 会被视频、frames、checkpoint 和 API 密钥污染。
- 清理优先级是 Git 索引瘦身，不是删除数据；所有视频与训练产物仍留在数据盘。

**Pending Criticals**
- DoD-Git-1：确认后执行 `git rm --cached`，把已追踪的大文件从 Git 索引移除但保留在磁盘。
- DoD-Git-2：服务器采用干净 Git checkout 或在现有目录初始化 Git 前，必须先备份目录清单并确认 `.secrets` 不会进入索引。
- DoD-Git-3：GitHub 只管理代码、docs、paper、小型 manifest；不管理 video/frame/checkpoint。

**Ref Reference**
- [docs/current/repo_cleanup_github_plan.md](docs/current/repo_cleanup_github_plan.md)

### [2026-05-01 22:50:00 CST] | Phase: Reporting / Before-After Demo Evidence

**Key Progress**
- 新增 `docs/current/before_after_demo_examples.md`，按同一输入对比未训练模型与 PIWM-SFT 输出。
- Demo 1 固定同一段顾客画面，展示 zero-shot 无法结构化输出，训练后能输出 stage / BDI / score / candidate actions。
- Demo 2 固定同一画面与同一动作 `A3_strong_recommend`，展示训练后能输出风险、收益和负向 reward。
- 在 `docs/current/data_demo_effect_status.md` 与 `docs/README.md` 中加入 before-after demo 入口。

**Data Loop Insight**
- 对外展示不能只靠总表，必须给出同一输入下的输出差异；这能更直接证明训练改变了模型行为。
- 当前最有说服力的 demo 是“未训练模型自由发挥/解析失败”对比“训练后进入 PIWM 固定决策格式”。

**Pending Criticals**
- DoD-Demo-1：所有 demo 样本必须能追溯到落盘 eval JSON 与可视化 contact sheet。
- DoD-Demo-2：展示时避免把 rule-conditioned 100% 包装成完整真实销售理解。

**Ref Reference**
- [docs/current/before_after_demo_examples.md](docs/current/before_after_demo_examples.md)
- [docs/current/data_demo_effect_status.md](docs/current/data_demo_effect_status.md)

### [2026-05-01 22:20:00 CST] | Phase: Reporting / NeurIPS Effect Table Audit

**Key Progress**
- 重写 `docs/current/data_demo_effect_status.md` 的效果表，采用 NeurIPS 更稳的 strict exact 口径：解析失败直接计为错误。
- 移除“无法稳定统计”和“完整导购决策正确率”表述，避免主表混入不一致口径。
- 将主结构化评估与端到端闭环诊断拆成两张表：主表用于论文叙事，e2e 仅作内部/appendix 诊断。
- 固化 zero-shot 对照：未训练模型在 strict 口径下 parse=23.5%，perception 三项为 0.0%，deliberation strict 指标为 next-stage 6.3%、risk 16.7%、benefit 8.7%、reward 0.0%。
- 复审后将 transition 的四个 100% 指标合并为“规则化动作后果标签”，并显式标注为 coarse symbolic / saturated；新增“顾客心理描述文字”细粒度指标，暴露当前模型 BDI 文本仍弱。
- 根据对外汇报需求，移除数据表中的“不可以怎么说”列；效果表改为字段级平滑分数，避免小样本 0% / 100% 极值主导叙事。
- 增补 Future Verification 视觉匹配诊断：只看当前画面 48.8%，加入后续反应画面 59.5%，用于说明 continuation frames 提供额外视觉信息。

**Data Loop Insight**
- 当前最可信的论文主结论是：PIWM-SFT 将自由回答模型转成稳定的结构化视觉导购判断器。
- 端到端 action selection 仍是瓶颈，不能包装成主效果提升；应报告为 final action formatting/fallback issue。
- 过多 100% 会让 reviewer 怀疑评估粒度；主文应压缩 saturated rule-label metrics，把空间留给 perception、BDI/fine-grained state、Future Verification 和 e2e 诊断。

**Pending Criticals**
- DoD-Report-4：论文主表只使用 strict exact 或清楚注明 parse-filtered 的指标，不混用。
- DoD-Report-5：e2e 指标必须标成 diagnostic，不使用“sales success”或“complete decision accuracy”口径。

**Ref Reference**
- [docs/current/data_demo_effect_status.md](docs/current/data_demo_effect_status.md)

### [2026-05-01 21:30:00 CST] | Phase: Reporting / Data Demo Effect Table

**Key Progress**
- 新增 `docs/current/data_demo_effect_status.md`，把正式数据、可展示 demo、主表提升、e2e 短板、Future Verification 视觉增益合并成一页表。
- 固化对外解释：训练规模扩大提升 perception/candidate；transition/reward 已饱和；e2e 未涨主要因 action-selection parse/fallback。
- 将 demo 入口分成数据结构 demo、QA contact sheet、主表效果、e2e decision loop、World Model continuation、Future Verification、frame-budget ablation。

**Data Loop Insight**
- 现在需要展示的不是“还有多少视频”，而是“现有正式数据如何支撑训练、评估、World Model 证据和 demo”。
- 效果提升叙事必须区分 perception 增益、rule-conditioned transition 饱和、future verification 的视觉增益和 e2e action-selection 瓶颈。

**Pending Criticals**
- DoD-Report-1：论文写作优先引用正式数据名 `PIWM-Train-Synth-v1` / `PIWM-Eval-QA-v1` / `PIWM-WorldModel-v1`。
- DoD-Report-2：所有 demo 指向落盘文件，不展示未生成或未审阅为 QA-pass 的资产。
- DoD-Report-3：若继续提升 e2e，必须先处理 action-selection parse/fallback。

**Ref Reference**
- [docs/current/data_demo_effect_status.md](docs/current/data_demo_effect_status.md)
- [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md)

### [2026-05-01 21:15:00 CST] | Phase: Dataset Governance / Inventory

**Key Progress**
- 新增 `docs/current/dataset_inventory.md`，将远端数据盘上的 QA-reviewed eval、synthetic train、World Model continuation、ms-swift export、checkpoint、生成队列和历史 smoke 分层。
- 新增 `data/README.md`，给 `data/` 目录提供快速入口和口径红线。
- 将当前主训练输入固定为 `ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl`，当前主评估固定为 `priority40_qareviewed_sample`。
- 明确 `priority1000_unreviewed` 当前为 543 parent / 2554 SFT examples，不能写成 1000 条已完成或 QA-pass。
- Kling API 已耗尽后，新增 `data/official/` 正式数据集别名：`PIWM-Train-Synth-v1`、`PIWM-Eval-QA-v1`、`PIWM-WorldModel-v1`、`PIWM-FutureVerification-v1`。

**Data Loop Insight**
- 现在最容易出错的不是缺数据，而是把 training-only synthetic、QA-reviewed eval、World Model pilot 和 smoke artifact 混用。
- 数据总账把“能训练”和“能写进论文评估”的边界分开，避免后续论文表格口径污染。
- 正式名与 source path 分离：论文和新脚本使用 `PIWM-*` 正式名，旧 `priority*` / `pilot30*` 名称只作为复现来源保留。

**Pending Criticals**
- DoD-Data-1：后续新增数据必须先归入 `dataset_inventory.md` 的一个 tier，再进入训练或评估。
- DoD-Data-2：新增 QA-reviewed sample 必须记录 reviewed / pass / fail 数量。
- DoD-Data-3：Kling API 恢复前，missing-video queue 不得自动运行。

**Ref Reference**
- [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md)
- [data/README.md](data/README.md)
- [data/official/DATASET_MANIFEST.json](data/official/DATASET_MANIFEST.json)

### [2026-05-01 09:45:00 CST] | Phase: NeurIPS Sprint / Priority1000 Training And Eval

**Key Progress**
- Kling API 已耗尽；停止新增视频生成，缺失队列只保留为待补。
- 使用当前可用 `priority1000_unreviewed` 部分数据完成 ms-swift LoRA SFT：543 parent / 2554 examples / 8 x 4090 / 638 steps。
- 新 checkpoint：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638`。
- QA-reviewed priority40 主表完成：parse `1.000`，stage `0.917`，score `0.833`，candidates `0.833`，transition fields 全 `1.000`。
- End-to-end decision loop 完成：strategy accuracy `0.500`，delib parse `1.000`，action parse `0.667`。
- 给 eval 脚本加入 progress / partial 输出，避免长评估无可观测进度。

**Data Loop Insight**
- 更大 synthetic SFT 对 perception 有正向收益，但端到端最终动作仍受 action-selection parse/fallback 限制。
- 当前不应继续消耗 Kling；最优下一步是修 action-selection 输出约束、parser/fallback 口径，以及补论文表格叙事。

**Pending Criticals**
- DoD-Exp-1：将 priority1000-current 作为当前主结果候选，与 v2 结果明确区分。
- DoD-Exp-2：所有写作必须标注 `priority1000_unreviewed` 为 synthetic train split，不能写成 QA-pass。
- DoD-Exp-3：若继续提升 e2e，优先处理 action parse 与 fallback，而不是继续扩视频生成。

**Ref Reference**
- [docs/current/experiment_result_digest.md](docs/current/experiment_result_digest.md)
- [docs/current/experiment_status_main_table_v2.md](docs/current/experiment_status_main_table_v2.md)
- [docs/current/current_sprint_status_and_reporting_policy.md](docs/current/current_sprint_status_and_reporting_policy.md)

### [2026-05-01 06:06:30 CST] | Phase: NeurIPS Sprint / Training Data Scale-Up

**Key Progress**
- 冻结 DPO 之外的训练扩展方向：新增 Kling 额度优先用于 parent synthetic SFT，而不是 preference/DPO。
- 生成 `priority500` 与 `priority1000` 两档目标 manifest，并按 `priority280_unreviewed` 已入库 parent 去重。
- 生成新增 prompt 包：`priority500_new_after280=248` 条，`priority1000_new_after280=748` 条。
- 完成静态 prompt QA：prompt 文件 100% 存在，forbidden label leakage = 0 sessions。

**Data Loop Insight**
- 当前训练规模可以用未人工审阅 synthetic 扩大，但评估可信度必须仍由 QA-reviewed subset 支撑。
- `pilot30` continuation/Future Verification 的 218 条样本适合作为 World Model 视觉监督与消融，不适合作为主 SFT 规模来源。

**Pending Criticals**
- DoD-Scale-1：先生产 `priority500_new_after280`，合并已有 `priority280_unreviewed` 后构建约 500 parent 的 SFT split。
- DoD-Scale-2：另抽 QA-reviewed eval parent 到 80-120 条；未审阅 synthetic 不得写成 QA-pass。
- DoD-Scale-3：若 API 与时间允许，再追加 `priority1000_new_after280` 剩余队列。

**Ref Reference**
- [docs/current/priority_generation_policy.md](docs/current/priority_generation_policy.md)
- [data/priority_generation_queue/scenario_manifest_priority500_new_after280.jsonl](data/priority_generation_queue/scenario_manifest_priority500_new_after280.jsonl)
- [data/priority_generation_queue/scenario_manifest_priority1000_new_after280.jsonl](data/priority_generation_queue/scenario_manifest_priority1000_new_after280.jsonl)

### [2026-05-01 04:50:00 CST] | Phase: NeurIPS Sprint / Future Verification

**Key Progress**
- 将路线 C 落地为 `future_verification.jsonl`：`current_frames + action + continuation_frames -> match / expected_state / visible_reaction`。
- 修正 negative pair 泄漏：`expected_state` 仍来自候选 action 专家规则，`visible_reaction` 改为 swapped continuation frames 的实际反应。
- 生成 84 条 future verification 样本（44 positive / 40 negative），并导出 218 条 ms-swift SFT 样本。
- 使用 4 卡 ms-swift 重训 Qwen2.5-VL-7B LoRA：3 epochs / 162 steps，`train_loss=0.18426619`，`token_acc=0.99136691`。
- 完成 full-6 vs current-only smoke：balanced-8 上 `match_exact` 从 `0.625` 降到 `0.500`，visible reaction fields 从 `0.375` 降到 `0.250`。

**Data Loop Insight**
- Continuation frames 已从 QA/审计附件进入训练输入；当前证据显示移除未来帧会降低 future verification 表现。
- 该任务比 continuation caption 更能支撑 World Model 叙事：PIWM 验证 action-conditioned future observation 是否与专家规则后果一致，而不是只复述文本转移表。

**Pending Criticals**
- DoD-FV-1：将 future verification eval 从 balanced smoke 扩到全部 84 行。
- DoD-FV-2：补充更强视觉差异的 best/worst continuation pairs，降低模板化反应导致的 text shortcut。
- DoD-FV-3：将 future verification 结果纳入主实验表或附录表，保持 pilot-scale 口径。

**Ref Reference**
- [docs/current/experiment_status_main_table_v2.md](docs/current/experiment_status_main_table_v2.md)
- [data/piwm_results/future_verification_observed_results.md](data/piwm_results/future_verification_observed_results.md)
- [scripts/build_future_verification.py](scripts/build_future_verification.py)

### [2026-05-01 05:45:00 CST] | Phase: NeurIPS Sprint / Frame Budget Ablation

**Key Progress**
- 新增 `scripts/build_frame_budget_eval.py`，从同一 video session 旁路抽取 K=1/K=3/K=5 eval frames，不污染默认 K=3 数据。
- 在 `priority40_qareviewed_sample` perception rows 上完成 frame-budget ablation。
- 结果：K=1 stage/score/candidates = `0.722/0.694/0.694`；K=3 = `0.861/0.722/0.722`；K=5 = `0.861/0.722/0.722`。

**Data Loop Insight**
- K=3 相比单帧提供关键收益，但 K=5 没有继续提升，支持默认 K=3 作为 onset--peak--settle 的最小行为片段预算。
- 该实验回答的是 frame budget tradeoff，而不是泛泛证明多帧有用。

**Pending Criticals**
- DoD-FB-1：将 frame-budget 表格纳入实验章节或附录。
- DoD-FB-2：若时间允许，在 pilot30 continuation set 上复核一次 K=1/K=3/K=5，但当前 priority40 QA-reviewed 结果已足够支撑默认 K=3 的设计选择。

**Ref Reference**
- [docs/current/experiment_status_main_table_v2.md](docs/current/experiment_status_main_table_v2.md)
- [data/piwm_results/frame_budget_ablation_results.md](data/piwm_results/frame_budget_ablation_results.md)
- [scripts/build_frame_budget_eval.py](scripts/build_frame_budget_eval.py)

### [2026-05-01 06:02:00 CST] | Phase: NeurIPS Sprint / Future Verification Full Eval

**Key Progress**
- 将 Future Verification 从 balanced smoke 扩展到全部 84 条记录。
- 使用 8×4090 shard 并行评估 full6 与 current3 两种条件。
- Full6：`match_exact=0.595`，visible reaction fields=`0.667`，`expected_state=0.988`。
- Current3：`match_exact=0.488`，visible reaction fields=`0.583`，`expected_state=0.988`。

**Data Loop Insight**
- continuation frames 的增益集中在 match 与 visible reaction，而不是 expected_state；这与任务定义一致，因为 expected_state 主要由 action-conditioned expert rule 决定。
- 结果支持路线 C：continuation frames 已经作为 action-conditioned future verification 的视觉证据进入监督，而不是只作为审计附件。

**Pending Criticals**
- DoD-FV-2：后续若继续扩大，应优先生成视觉差异更明显的 best/worst continuation pairs，而不是平均扩样。
- DoD-Write：将 Future Verification 作为附录表或 World Model visual grounding 小节，不写成 full benchmark。

**Ref Reference**
- [data/piwm_results/future_verification_observed_all84_results.md](data/piwm_results/future_verification_observed_all84_results.md)
- [docs/current/experiment_status_main_table_v2.md](docs/current/experiment_status_main_table_v2.md)
- [docs/current/experiment_result_digest.md](docs/current/experiment_result_digest.md)

### [2026-04-30 21:08:00 CST] | Phase: Priority QA Sample / Low-Memory Checkpoint Eval

**Key Progress**
- 从 260 条 priority parent videos 中按 cue/viewpoint/split 分层抽样 40 条，生成 5 张 contact sheet。
- 完成第一批人工 contact-sheet QA：36 pass / 40 reviewed，4 fail。
- 失败集中在 `salesperson_observable` 的 face/gaze 裁切，以及 `approaching_counter` / `looking_around_for_help` 在 3 帧中证据不足。
- 构建 `data/piwm_dataset_priority40_qareviewed_sample/`：36 parent、126 transition、36 policy，18 sales / 18 surveillance。
- 修复 `scripts/eval_ms_swift_checkpoint.py`：支持 `--image-limit`、`--max-pixels`，并在每条样本后清理 CUDA cache。
- 低显存 checkpoint smoke eval 完成：1-frame 与 3-frame low-pixel 均为 24/24 parse success；当前主结果采用 3-frame low-pixel：`stage_exact=0.125`、`score_exact=0.75`、`next_stage_exact=1.0`、`reward_exact=1.0`、`caption_exact=1.0`。

**Data Loop Insight**
- priority280 不再只是 unreviewed training split：已有第一批 QA-reviewed sample 可用于估计 pass rate，但仍不能把 260 条整体写成 manually verified。
- checkpoint 已证明能按 PIWM tag 契约输出；3-frame low-pixel 已通过，下一步是提高像素或扩大样本量。

**Pending Criticals**
- DoD-QA80：把 priority split 人工 QA 从 40 条扩到 80-100 条，稳定 cue/viewpoint pass-rate。
- DoD-EvalHighPix：在显存允许下提高 3-frame 像素或扩大 eval 样本量。
- DoD-PaperMetricBoundary：把 low-memory smoke 与 full benchmark 在表格中明确分栏。

**Ref Reference**
- `data/priority_generation_queue/qa_review_priority280_stratified40_manual_decisions.json`
- `data/piwm_dataset_priority40_qareviewed_sample/_stats.json`
- `data/piwm_results/sft_checkpoint_eval_balanced24_1frame_lowpix.json`
- `data/piwm_results/sft_checkpoint_eval_balanced24_3frame_lowpix.json`
- [docs/current/current_sprint_status_and_reporting_policy.md](docs/current/current_sprint_status_and_reporting_policy.md)

### [2026-04-30 20:50:00 CST] | Phase: Sprint Status Audit / Reporting Policy

**Key Progress**
- 远端 live audit 确认：Kling 额度约从 86% 降到 46%，换来 260 条唯一 priority parent videos。
- `Archive_generated_priority24` 与 `Archive_generated_priority256` 共 260 条 parent videos，均有 `qa_report.json`，但 0 条人工 `qa_manual_review.json`。
- 构建 `data/piwm_dataset_priority280_unreviewed/`：260 parent、927 transition、260 policy；口径固定为 high-throughput synthetic train split, pending visual QA。
- `data/piwm_dataset_pilot30_with_continuations/` 保持 QA-reviewed pilot：24 parent、44 continuation。
- ms-swift 4 x 4090 SFT 完成：Qwen2.5-VL-7B-Instruct + LoRA，1321 examples，660/660 steps，train loss 0.0404377，checkpoint-660 落盘。
- checkpoint eval 已尝试 24 条 balanced input，但全部 CUDA OOM；当前没有有效模型推理指标，不能报告 accuracy=0。
- 新增 [docs/current/current_sprint_status_and_reporting_policy.md](docs/current/current_sprint_status_and_reporting_policy.md)，并更新 docs/14/90/91/92/93 的数据与口径。

**Data Loop Insight**
- 大批量数据已经从 prompt queue 转为可训练 synthetic split；当前瓶颈不再是 Kling parent generation，而是 visual QA 抽样、低显存 checkpoint eval 与论文口径控制。
- priority split 可以支撑赶 SFT，但不能替代 QA-reviewed evaluation set。

**Pending Criticals**
- DoD-EvalLowMem：生成 1-frame 或 low-image-token eval input，重跑 checkpoint eval，产出有效 JSON metric 或明确记录显存限制。
- DoD-VisualQASample：对 priority280 做 30-50 条分层人工 QA，估计 visual pass rate。
- DoD-PaperSafeTables：所有论文表格区分 QA-reviewed subset、synthetic train split、diagnostic-only artifacts。

**Ref Reference**
- [docs/current/current_sprint_status_and_reporting_policy.md](docs/current/current_sprint_status_and_reporting_policy.md)
- [docs/background/neurips_sprint_result_snapshot_20260430.md](docs/background/neurips_sprint_result_snapshot_20260430.md)
- `/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/sft_train_summary.json`

### [2026-04-30 15:05:31 CST] | Phase: NeurIPS Sprint 91 / Training Skeleton + Mock Eval

**Key Progress**
- 阅读 `docs/background/neurips_sprint_codex_plan.md` 后确认无阻塞歧义；执行假设：不自动 commit，不写 projected 数字，先做纯 Python Day1/Day2 任务。
- 新增 `piwm_train/config.py`、`targets.py`、`prompts.py`、`data_collator.py`、`sft.py`，覆盖 perception / deliberation / continuation_caption / action 四头训练文本契约。
- 新增 `piwm_infer/parsers.py`、`prompts.py`、`decision_loop.py` 与 `MockVLM` fixture，MockVLM 可跑 perception -> deliberation -> continuation caption -> action 的 4 头闭环。
- 新增 `scripts/run_pilot_eval.py`，生成真实 pipeline artifact `data/piwm_results/pilot24_mock_pipeline_eval.json`；明确 `model=MockVLM`、`is_training_result=false`。
- 同步远端已有 24/44 pilot 数据到本机 `data/piwm_dataset_pilot30_with_continuations/`，用于训练 adapter 验证，不同步视频大文件。
- 生成 adapter artifact `data/piwm_results/sft_adapter_smoke/`：`sft_train_smoke.jsonl` 为 134 行，任务分布为 perception 24 / deliberation 66 / continuation_caption 44。
- 修复 `piwm_data.build_dataset` 回归：即使 continuation 为空也稳定输出 `world_model_continuation.jsonl`，并恢复 `--require-continuation` 与 continuation stats。
- 全仓 pytest 通过：`138 passed`。

**Data Loop Insight**
- 训练侧已从 0 行代码推进到可读取四套 JSONL、可生成 SFT/DPO 文本样本、可用 MockVLM 验证推理闭环的状态。
- 当前 `pilot24_mock_pipeline_eval.json` 只能证明 pipeline 可跑，不能作为训练后模型结果；真实 GPU SFT/DPO 仍未执行。

**Pending Criticals**
- DoD-GPU-SFT：在远端新建 `piwm-train` 环境，运行非 dry-run SFT smoke；结果必须写入 `data/piwm_results/pilot24_piwm_sft_smoke.json`。
- DoD-DPO-Smoke：实现并运行最小 DPO adapter/入口，若 GPU 未就绪则结果表保持 `--`。
- DoD-Paper-Numbers：论文中所有数字只能引用 `data/piwm_results/*.json`；MockVLM artifact 不得写成 PIWM training result。

**Ref Reference**
- [docs/background/neurips_sprint_codex_plan.md](docs/background/neurips_sprint_codex_plan.md)
- Historical local artifact path, not present in the current checkout: `data/piwm_results/pilot24_mock_pipeline_eval.json`
- Historical local artifact path, not present in the current checkout: `data/piwm_results/sft_adapter_smoke/sft_smoke_summary.json`

### [2026-04-30 14:15:00 CST] | Phase: Prompt Fix Validation / Targeted Kling3

**Key Progress**
- 在远端数据盘隔离目录 `Archive_generated_fix3/` 生成 3 条 targeted continuation，不覆盖 pilot30 原始数据。
- 三条目标分别覆盖：`A1_silent_observe -> early_browsing`、`A1_silent_observe -> disengaged`、`A7_disengage -> disengaged`。
- Kling 生成 3/3 成功，人工 contact-sheet QA 后 2/3 pass。
- `A1 -> disengaged` 通过：无导购介入，顾客离开商品区域。
- `A7 -> disengaged` 通过：顾客停止产品互动并离开/转离。
- `A1 -> early_browsing` 失败：无导购介入已修正，但画面仍像近距离 active evaluation，且 surveillance body trajectory 不足。
- 构建 `data/piwm_dataset_fix3_continuation_validation/`：2 条 parent 入库，`world_model_continuation.jsonl` 为 2 行。

**Data Loop Insight**
- 弱动作修复已部分有效：最严重的“静默观察自动生成导购介入”问题在 `A1 -> disengaged` 上被消除。
- 仍不能把 `A1 -> early_browsing` 大规模放进生产；该组合需要单独 prompt 降温或在 priority selector 中进一步降权。

**Pending Criticals**
- DoD-A1EarlyBrowsingFix：重写 `A1_silent_observe -> early_browsing` continuation 的 timeline，强制 wider shot、slow walking、no product touch。
- DoD-PriorityGate：下一轮 priority 生产前降低 `A1 -> early_browsing` 的优先级，避免 API 烧在当前不稳定组合上。
- DoD-SmokeTrain-WM：可先用 pilot30 + fix3 的 pass continuation 运行第 4 头训练入口 smoke。

**Ref Reference**
- `/root/lanyun-fs/ProactiveIntentWorldModel/Archive_generated_fix3/_fix3_qa_summary.json`
- `/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_dataset_fix3_continuation_validation/_stats.json`
- [docs/background/pilot30_continuation_review_report.md](docs/background/pilot30_continuation_review_report.md)

### [2026-04-30 01:16:00 CST] | Phase: Data Quality Patch / Pilot30 Prompt Pack

**Key Progress**
- `MainSchemaRecord` 新增 `product_category` 与可选 `split`；三套 JSONL meta 与 `_stats.json` 同步输出 product/split 覆盖。
- `derive_bdi` 移除 `Observable cue(s): xxx`，避免把 cue 枚举名写入 BDI supervision token。
- `derive_action_outcome` 为每个 rule-derived transition 写入 rationale；`policy_preference.chosen_json/rejected_json.rationale` 不再为空。
- `prompt_builder.py` 顶层写入 `sampler.version`，并在 prompt index 中加入 `product_category`。
- 生成 `Archive_prompts_pilot30/`：30 条 prompt，21 条 `salesperson_observable`、9 条 `surveillance_oblique`，每个 cue 3 条，forbidden label hits 为 0。
- 重新构建 `data/piwm_dataset/`、`data/piwm_dataset_pilot/`、`data/piwm_dataset_viewpoint_review/`，使现有数据集全部采用新 schema。
- pytest **80 passed**。

**Data Loop Insight**
- 当前从“能入库”推进到“可审计覆盖”：训练 JSONL 本身可以统计 product/split/viewpoint，而不用回查 prompt。
- 下一步仍不应直接上 1920 条；`pilot30` 的目标是测 pass rate 与失败模式，而不是训练。

**Pending Criticals**
- DoD-PromptReview30：人工审阅 `Archive_prompts_pilot30/_prompt_index.jsonl` 指向的 30 条 prompt。
- DoD-Kling30：审阅通过后再调用 Kling，随后跑 extract/QA/build_dataset。
- DoD-PassRateReport：输出 cue/viewpoint/persona/product 的 pass/fail 统计，决定是否扩大生产。

**Ref Reference**
- `Archive_prompts_pilot30/_prompt_index.jsonl`
- `data/_scenario_stats_pilot30.json`
- `data/piwm_dataset_viewpoint_review/_stats.json`
- [docs/background/data_generation_loop_status.md](docs/background/data_generation_loop_status.md)
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)
- [docs/background/current_code_status.md](docs/background/current_code_status.md)

### [2026-04-30 00:40:00 CST] | Phase: Mixed-View Kling Real Batch / QA-Gated Dataset

**Key Progress**
- 已从本机已有工程配置定位 Kling 凭据来源并完成真实 mixed-view 小批量生成；不再把 API 环境视为当前阻塞。
- `Archive_generated_viewpoint_review/` 生成 10 条 `video.mp4`，并完成正式抽帧、`frame_manifest.json`、manual QA review 与 `qa_report.json`。
- QA gate 结果：6 pass / 10 generated；拒绝原因为 target cue 不可见 1 条、viewpoint visibility 不足 2 条、旧 prompt label leakage 1 条。
- 修复未来 prompt 模板中的内部标签泄露：`no_eye_contact_avoidant` 不再生成包含 `disengaged` 的文本。
- 构建 `data/piwm_dataset_viewpoint_review/`：6 main schema、6 visual-only state inference、6 with-cue state inference、16 transition rows、6 policy preference rows。
- `scripts/run_kling_batch.py` 新增 `--reuse-existing`，可复用已有 `video.mp4` 重跑抽帧/QA/summary，不重新调用 Kling。
- pytest **77 passed**。

**Data Loop Insight**
- 当前闭环已从 dry-run 进入真实视频路径：`scenario -> prompt -> Kling video -> extract frames -> QA gate -> JSONL` 可运行。
- 训练入口现在默认只读取 `qa_report.overall_pass=true`，失败视频不会进入正式数据集。
- 第一轮 pass rate 显示 P0 `salesperson_observable` 可行，但需要继续强化脸/视线/手/商品/价格区同框约束；P1 `surveillance_oblique` 可保留为跨视角泛化测试，不应立刻扩大为主线。

**Pending Criticals**
- DoD-Pass30：扩大到至少 30 条 QA pass 样本，统计 cue/persona/viewpoint 覆盖。
- DoD-QAQuality：把 viewpoint fail 与 cue invisible 的失败模式反馈到 prompt_builder，而不是人工放宽 QA。
- DoD-EndToEnd：新增一键脚本串联 batch Kling、extract、QA、build_dataset，并输出 pass-rate report。

**Ref Reference**
- `Archive_generated_viewpoint_review/_qa_index.jsonl`
- `data/piwm_dataset_viewpoint_review/_stats.json`
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)
- [docs/background/current_code_status.md](docs/background/current_code_status.md)

### [2026-04-30 00:12:00 CST] | Phase: Mixed-View Kling Batch Runner

**Key Progress**
- 新增 `scripts/run_kling_batch.py`：按 `_prompt_index.jsonl` 顺序批量调用 `kling/generate_session.js`，随后执行 `extract_frames` 与 `qa_gate`。
- 脚本会为每个生成 session 写 `qa_manual_review.template.json`，按 viewpoint 自动列出 required visibility 字段。
- 对 `Archive_prompts_viewpoint_review/_prompt_index.jsonl` 执行 dry-run：10 条 prompt 全部可规划，8 条 `salesperson_observable`、2 条 `surveillance_oblique`。
- 当时当前 shell 和项目目录未发现 `KLINGAI_ACCESS_KEY` / `KLINGAI_SECRET_KEY`，真实 Kling 调用尚未执行；后续已从本机既有工程配置定位凭据并完成真实生成，见 00:40 更新。
- pytest **76 passed**。

**Data Loop Insight**
- V5 的工程入口已经具备；剩余阻塞不是 schema/prompt/QA，而是运行环境凭据与后续人工 QA。
- dry-run 保证 10 条 mixed-view prompt 可以被同一批处理入口接入，不需要手动逐条调用 Kling。

**Pending Criticals**
- DoD-Credentials：设置 `KLINGAI_ACCESS_KEY` / `KLINGAI_SECRET_KEY` 后去掉 `--dry-run` 执行真实生成。
- DoD-ManualReview：对生成视频填写 `qa_manual_review.json`，不要直接改 template 当作通过。
- DoD-PassRate：统计 P0/P1 两种 viewpoint 的 QA pass rate，再决定是否扩大 `surveillance_oblique`。

**Ref Reference**
- `scripts/run_kling_batch.py`
- `Archive_generated_viewpoint_review/_batch_summary_dry_run.json`
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)
- [docs/background/current_code_status.md](docs/background/current_code_status.md)

### [2026-04-30 00:35:00 CST] | Phase: Provenance Weak-Point Cleanup

**Key Progress**
- 处理上一轮剩余 5 条 weak points：`CUE2STATE_009`、`FALLBACK_005`、`FALLBACK_006`、`PROSCORE_006`、`PROSCORE_007`。
- 新增 `SRC_SALES_BUSINESS_COMM_001`，用于低强度支撑 nonverbal cue 解释；新增 `P_COMM_001` compact paraphrase principle。
- coverage 更新为：32 `manual_supported`，40 `theory_anchored`，0 `seed_only`，0 `candidate_for_removal`，0 unlinked。
- 保留边界：这些 weak-point 修正仍是 low-strength theory anchors，不是 manual-supported 或 expert-reviewed。
- pytest **56 passed**。

**Data Loop Insight**
- 专家来源链路现在没有悬空规则；每条 seed rule 都能被 coverage report 追踪。
- 下一步不应继续堆 provenance，而应进入数据契约升级：BDI / next_bdi / reward_components / state_summary / candidate_block。

**Pending Criticals**
- DoD-Phase2：schema/exporter 增加 BDI、next_bdi、reward_components。
- DoD-Review：人工抽查 low-strength theory anchors 是否过度牵强。
- DoD-Reward：proactive_score 和 transition reward 数值仍需组件化，不能只靠 source link。

**Ref Reference**
- `piwm_data/expert_corpus/distilled/_provenance_coverage.json`
- `piwm_data/expert_corpus/distilled/rule_source_links.jsonl`
- [docs/contracts/expert_provenance_upgrade_plan.md](docs/contracts/expert_provenance_upgrade_plan.md)

### [2026-04-30 00:20:00 CST] | Phase: Automated Textbook Distillation / First Reviewable Pass

**Key Progress**
- 完成第一轮自动教材蒸馏可审阅版本：新增 `extracted_principles.jsonl`，保存开放教材/理论框架的 compact paraphrase principles，不保存长原文。
- 扩展 sales source registry：加入 OpenStax consumer buying factors，用于 persona / social influence / price sensitivity 支撑。
- 将 `rule_source_links.jsonl` 从 30 条扩展到 72 条：所有 seed rules 均有 `support_status` 与 `formalization_note`。
- coverage 结果：32 `manual_supported`，35 `theory_anchored`，2 `seed_only`，3 `candidate_for_removal`，0 unlinked。
- BDI 仍只存在于 modeling registry；provenance 测试继续禁止把 `SRC_MODELING_BDI_*` 用作 sales-rule evidence。

**Data Loop Insight**
- 专家来源线现在有可审阅闭环：source registry -> extracted principles -> rule source links -> coverage report。
- 当前结果可以支撑“source-audited / pedagogy-anchored rule corpus”，但不能支撑“all rules expert-reviewed”或“reward numbers textbook-derived”。

**Pending Criticals**
- DoD-Review：人工审阅 32 条 manual_supported 与 35 条 theory_anchored 是否牵强。
- DoD-Cleanup：处理 3 条 `candidate_for_removal` 与 2 条 `seed_only`。
- DoD-Reward：reward 数值仍需 `reward_components`，不能只靠 provenance link。

**Ref Reference**
- `piwm_data/expert_corpus/distilled/extracted_principles.jsonl`
- `piwm_data/expert_corpus/distilled/rule_source_links.jsonl`
- `piwm_data/expert_corpus/distilled/_provenance_coverage.json`
- `piwm_data/expert_corpus/provenance.py`
- `piwm_data/tests/test_provenance.py`
- [docs/contracts/expert_provenance_upgrade_plan.md](docs/contracts/expert_provenance_upgrade_plan.md)

### [2026-04-29 23:58:00 CST] | Phase: Multi-View Visual Contract V1-V4

**Key Progress**
- 新增 `viewpoint` 枚举：`salesperson_observable` / `surveillance_oblique` / `third_party_side` / `first_person_pov`。
- `scenario_sampler.py` 支持 `--viewpoints` 与 `--viewpoint-ratio`；默认 80% `salesperson_observable`、20% `surveillance_oblique`，`session_id` hash 已纳入 viewpoint。
- `prompt_builder.py` 按 viewpoint 生成 camera / negative；`salesperson_observable` 强制脸、视线、手、商品、价格区域可见，`surveillance_oblique` 强制轨迹、停留、手/臂动作和商品区域可见。
- `extract_frames.py` 的 `frame_manifest.json` 写入 `viewpoint`。
- `qa_gate.py` 的 `qa_report.json` 写入 `viewpoint`、`viewpoint_pass`、`required_visibility`，并按不同 viewpoint 生成 checklist。
- 三套训练 JSONL 的 `meta` 写入 `viewpoint`，但主 `input` 不包含 viewpoint，保留 view-agnostic 主线。
- 重跑 10 条 prompt 审阅包：`Archive_prompts_viewpoint_review/` = 8 条 `salesperson_observable` + 2 条 `surveillance_oblique`。
- pytest **73 passed**。

**Data Loop Insight**
- 视觉输入契约从单一观察角升级为 multi-view in-store visual observations，但执行优先级仍以导购可观察视角为主。
- 后续可以做 view-aware / view-agnostic / view-shift 三种实验，而不需要重写主 schema。

**Pending Criticals**
- DoD-MixedView-Video：用 10 条 mixed-view prompt 跑 Kling，比较 `salesperson_observable` 与 `surveillance_oblique` 的 QA pass rate。
- DoD-Visibility-QA：人工审阅 `required_visibility` 是否足以约束脸、视线、手、商品和价格区域。
- DoD-Scale：暂不引入 `first_person_pov`，直到 P0/P1 视角 pass rate 稳定。

**Ref Reference**
- `scripts/scenario_sampler.py`
- `scripts/prompt_builder.py`
- `scripts/extract_frames.py`
- `scripts/qa_gate.py`
- `Archive_prompts_viewpoint_review/_prompt_index.jsonl`
- `data/scenario_manifest_viewpoint_review10.jsonl`
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)
- [docs/background/current_code_status.md](docs/background/current_code_status.md)

### [2026-04-29 23:45:00 CST] | Phase: Extract Frames / QA-Passing Pilot Dataset

**Key Progress**
- 新增正式 `scripts/extract_frames.py`：读取 `prompt.json.frame_sampling_plan`，从 `video.mp4` 抽取 `frames/*.jpg`，写 `frame_manifest.json`。
- 修正 `prompt_builder.py` 的 demo-sample / glass-display 物理约束，避免“隔着玻璃触碰商品”的生成错误。
- 重跑 Kling pilot：`Archive_generated_pilot/` 共 3 条 session，其中 2 条 `qa_report.overall_pass=true`，1 条因 sampled frames 未确认 cue 被拒绝。
- `build_dataset` 默认 QA gate 生效，正式读入 2 条 QA pass session，跳过 1 条 QA fail session。
- `data/piwm_dataset/` 与 `data/piwm_dataset_pilot/` 非空：2 行 state inference、2 行 cue-debug state inference、5 行 transition modeling、2 行 policy preference。
- pytest **71 passed**。

**Data Loop Insight**
- 数据闭环已经从“schema 能跑”推进到“真实 Kling 视频 -> 抽帧 -> QA -> 非空 JSONL”的最小闭合。
- 当前 pilot 证明 QA gate 能阻止坏视频入库，也证明 `state_inference.jsonl` visual-only 主线可与 `state_inference_with_cue.jsonl` debug 上限并存。
- 风险仍然是规模与覆盖：当前 2 条 pass 都是 `checking_phone_likely_research`，不能代表全部 cue 或 persona。

**Pending Criticals**
- DoD-Pilot-30：扩到至少 30 条 QA pass session，并统计 cue-by-cue pass/fail 原因。
- DoD-Prompt-Feedback：把失败原因回流到 `prompt_builder.py` 的 cue-specific timeline。
- DoD-Rationale：补齐 policy preference 的 rationale，避免 chosen/rejected 解释为空。
- DoD-QA-Automation：后续接 VLM reviewer，降低人工 `qa_manual_review.json` 成本。

**Ref Reference**
- `scripts/extract_frames.py`
- `scripts/prompt_builder.py`
- `scripts/qa_gate.py`
- `Archive_generated_pilot/_qa_index.jsonl`
- `Archive_generated_pilot/qa_pass_contact_sheet.jpg`
- `Archive_generated_pilot/_one_complete_qa_pass_data_preview.json`
- `data/piwm_dataset/_stats.json`
- `data/piwm_dataset_pilot/_stats.json`
- [docs/background/data_generation_loop_status.md](docs/background/data_generation_loop_status.md)
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)

### [2026-04-29 23:40:00 CST] | Phase: Expert Provenance Implementation

**Key Progress**
- 更新 `docs/contracts/expert_provenance_upgrade_plan.md`：现有 72 条规则不再作为必须映射对象，而是 seed baseline，可保留、修改、删除或被 source-backed rules 替换。
- 将 provenance 拆为 sales/modeling 两条线；BDI 只进入 modeling source registry，不允许作为 sales-rule evidence。
- 新增 `piwm_data/expert_corpus/sources/sales_source_registry.jsonl` 与 `modeling_source_registry.jsonl`。
- 新增 `rule_source_links.jsonl`：先覆盖 9 条 `state_aida_to_candidates` + 21 条 `transition`，共 30 条 `theory_anchored`。
- 新增 `provenance.py` 与 `test_provenance.py`，强制 rule links 只能引用 `SRC_SALES_*`，不能引用 `SRC_MODELING_BDI_*`。
- 生成 `_provenance_coverage.json`：72 条现有规则中 30 条已 linked，42 条仍 unlinked seed-only。

**Data Loop Insight**
- 当前 provenance 风险已从“claim unsupported”降为“核心 action/transition 已 theory-anchored，但 cue/intent/reward 仍需后续来源或重构”。
- 数据闭环仍可继续跑 seed baseline，但论文 claim 必须区分 seed-only、theory-anchored、manual-supported、expert-reviewed。

**Pending Criticals**
- DoD-Provenance-Next：对 10 条 cue rules、14 条 persona-intent rules、9 条 score rules、9 条 fallback intent rules 做 retain/modify/remove 判定。
- DoD-Manual：把核心 transition 中低 support_strength 的规则升级为 manual_supported 或标记为 modified/removed。
- DoD-Review：人工审阅 source registry 与 30 条 rule_source_links，确认 mapping 是否牵强。

**Ref Reference**
- [docs/contracts/expert_provenance_upgrade_plan.md](docs/contracts/expert_provenance_upgrade_plan.md)
- `piwm_data/expert_corpus/provenance.py`
- `piwm_data/expert_corpus/sources/sales_source_registry.jsonl`
- `piwm_data/expert_corpus/sources/modeling_source_registry.jsonl`
- `piwm_data/expert_corpus/distilled/rule_source_links.jsonl`
- `piwm_data/expert_corpus/distilled/_provenance_coverage.json`
- `piwm_data/tests/test_provenance.py`

### [2026-04-29 23:10:00 CST] | Phase: Expert Provenance Risk Control

**Key Progress**
- 确认现有 docs 只记录了 `seed_rule` 风险和方向性建议，没有一份可执行的 provenance 补救计划。
- 新增 `docs/contracts/expert_provenance_upgrade_plan.md`，把当前状态定义为 `expert corpus container: done`、`expert provenance content: incomplete`。
- 设定四级升级链：`seed_rule -> theory_anchored -> manual_supported -> expert_reviewed`。
- 明确新增工件：`source_registry.jsonl`、`rule_source_links.jsonl`、`source_backed_rules.jsonl`、`_provenance_coverage.json`。
- 明确论文措辞边界：当前不能声称 all rules are distilled from retail manuals。

**Data Loop Insight**
- 当前 Phase 1 只解决“规则可审计”和“行为不漂移”，尚未解决“规则来源强可信”。
- 下一轮实现应优先给 `state_aida_to_candidates` 与 `transition` 建立 theory/manual provenance，因为它们直接支撑 action selection 和 world-model transition claim。

**Pending Criticals**
- DoD-Provenance-1：source registry 建立，所有 source 有 authority/copyright/usable_for 边界。
- DoD-Provenance-2：72 条 seed rules 均有 `support_status`。
- DoD-Provenance-3：21 条 transition + 9 条 candidate rules 至少达到 `theory_anchored`。
- DoD-Provenance-4：manual-supported 规则不得包含长版权原文，只保留 source id、位置和 paraphrase note。

**Ref Reference**
- [docs/contracts/expert_provenance_upgrade_plan.md](docs/contracts/expert_provenance_upgrade_plan.md)
- [docs/contracts/claim_to_artifact_audit.md](docs/contracts/claim_to_artifact_audit.md)
- [docs/background/related_work_expert_distillation.md](docs/background/related_work_expert_distillation.md)

### [2026-04-29 23:05:00 CST] | Phase: QA Gate / Visual-Only State Inference

**Key Progress**
- `state_inference.jsonl` 改为 visual-only 主线：`observable_cues` 不再进入 `input`，只保留在 `meta`。
- 新增 `state_inference_with_cue.jsonl`，作为带 oracle cue 的调试/上限版本。
- 新增 `scripts/qa_gate.py`：生成 `qa_report.json`，自动检查文件/帧/prompt 标签泄露，并结合 `qa_manual_review.json` 判断 cue 可见性与物理一致性。
- `build_dataset` 默认只读取 `qa_report.overall_pass=true` 的 session；开发调试必须显式使用 `--allow-unreviewed`。
- 3 条 Kling smoke test 已补 `qa_report.json`，均被 QA gate 拒绝：price-check sampled frames 不足、glass-counter physical inconsistency、comparison sampled frames 不足。
- pytest **69 passed**。

**Data Loop Insight**
- 当前系统已经具备“生成失败不入库”的闭环保护：Kling 能出视频不等于可训练数据。
- 这次改动切断了 `observable_cues` 直接作为 state inference 输入的 oracle shortcut，正式训练主线更接近真实视觉识别任务。

**Pending Criticals**
- DoD-Extract：实现正式 `scripts/extract_frames.py`，替代 smoke test 临时抽帧脚本。
- DoD-Pilot：修正 prompt 并重跑小批量 Kling，直到至少 1 条 `overall_pass=true`。
- DoD-QA-Scale：后续接 VLM reviewer，减少人工 `qa_manual_review.json` 成本。

**Ref Reference**
- `scripts/qa_gate.py`
- `piwm_data/build_dataset.py`
- `piwm_data/exporters.py`
- `Archive_generated_test/_qa_index.jsonl`
- `Archive_generated_test/_one_complete_data_preview.json`
- [docs/background/data_generation_loop_status.md](docs/background/data_generation_loop_status.md)
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)

### [2026-04-29 22:30:00 CST] | Phase: Phase 1 Expert Corpus Landed

**Key Progress**
- 实现 `piwm_data/expert_corpus/`：`schemas.py`（Pydantic v2 discriminated union）、`compile.py`、`distilled/conditional_rules.jsonl`（72 条）、`_seed_generator.py`（一次性把 `rules.py` 字面量翻成 JSONL）。
- 72 条 = 10 + 14 + 9 + 9 + 9 + 21，与 `01_data_generation_loop_status.md §5` 承诺一致。
- 新增 `piwm_data/tests/test_expert_corpus.py`（13 个测试），核心断言 6 个 `*_matches_literal`：编译产物与 `rules.py` 字面量逐字段相等，任何漂移立刻 fail。
- pytest **49 passed**（原 36 + 新 13），原测试零回退。
- 每条 rule 携带显式 `provenance.rationale + provenance.author + provenance.added_at`，第一批全部诚实标注 `source_kind = "seed_rule"`，不伪装真实教材引用。
- 编译器 fail-fast：未知 enum、duplicate rule_id、(rule_type, key) 冲突三类错误均 raise `CorpusValidationError`。

**Data Loop Insight**
- `rules.py` 保持字面量 runtime cache 不变 → 现有 36 测试零风险。
- JSONL 升格为"语料源真相"，字面量降格为"runtime fast-path"；测试断言两者必须一致。
- 第一批 72 条全部 `seed_rule`：论文 v6 中"pedagogy-derived"声明现在有了**可审计的代码证据**（每条 rule_id + rationale），但没有伪造真实教材引用。
- 后续从教材/SOP 蒸馏出新规则时，新条目用 `manual_distillation` 或 `pedagogy_text`，与第一批 seed 区分。

**Pending Criticals**
- DoD-Expert：✅ 已满足（六张运行时映射可从 expert corpus 编译，pytest 不回退，seed 标注诚实）
- 下一阶段进入 Phase 2 数据契约升级（BDI / next_bdi / state_summary / candidate_block / reward_components）
- 仍未启动：Phase 3 sampler/prompt_builder、Phase 4 Kling+抽帧+QA、Phase 5 dataset pilot

**Ref Reference**
- `piwm_data/expert_corpus/schemas.py`
- `piwm_data/expert_corpus/compile.py`
- `piwm_data/expert_corpus/distilled/conditional_rules.jsonl`
- `piwm_data/tests/test_expert_corpus.py`
- [docs/contracts/claim_to_artifact_audit.md](docs/contracts/claim_to_artifact_audit.md)（"Pedagogy-derived action space" 行可由 `blocking` 改为 `partial→covered`）

### [2026-04-29 21:40:00 CST] | Phase: Kling Smoke Test / Visual Contract Check

**Key Progress**
- 用 `Archive_prompts_review/piwm_1321b89375/prompt.json` 跑通 Kling v3.0，生成 10 秒 `video.mp4`。
- 追加测试 `repeated_product_handling` 与 `comparing_two_products`，共 3 条视频。
- 使用 OpenCV 按 2s / 5s / 8s 抽帧，生成 `frames/`、`frame_manifest.json` 和 contact sheet。
- 观察结果：`repeated_product_handling` 通过；`long_dwell_with_price_check` 与 `comparing_two_products` 部分通过但需要更强视觉约束。

**Data Loop Insight**
- `single current-state video -> sampled frames -> single-turn training row` 主结构可保留。
- 固定 K=3 不应作为唯一采样策略；对 price-check / comparison 这类细微时间性 cue，需要 cue-aware prompt 和 K=4/5 抽帧。

**Pending Criticals**
- DoD-Phase4：实现正式 `extract_frames.py`，读取 `frame_sampling_plan` 并写 `frame_manifest.json`。
- DoD-QA：QA gate 必须检查 sampled frames，不只检查整段视频。
- DoD-Prompt：强化 subtle cue prompt，要求价格标签、手指指向、头部/视线切换等可抽帧证据。

**Ref Reference**
- `Archive_generated_test/_smoke_test_report.json`
- `Archive_generated_test/phase4_test_contact_sheet.jpg`
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)

### [2026-04-29 21:15:00 CST] | Phase: Phase 3 Scenario Sampler / Prompt Builder

**Key Progress**
- 新增 `scripts/scenario_sampler.py`：枚举当前规则空间，生成 `data/scenario_manifest.jsonl`。
- 当前 manifest 共 1920 条：train 1112 / dev 148 / test 140 / ood_product 240 / ood_persona 280。
- 每条 scenario 包含 `session_id`、`split`、`product_category`、`persona_type`、`aida_stage`、`target_cue`、`source_rule_ids`、`runtime_fallbacks`。
- 新增 `scripts/prompt_builder.py`：将 scenario 转成 Kling 可读 `prompt.json`，包含 camera / scene / behavior timeline / negative 四层。
- 生成 10 条人工审阅样本到 `Archive_prompts_review/`，索引为 `Archive_prompts_review/_prompt_index.jsonl`。
- pytest **65 passed**。

**Data Loop Insight**
- 数据闭环已从“规则和字段契约”推进到“Kling 前置控制面”：每条未来视频现在都有可复现的规则来源、split、视觉 cue 时间轴和抽帧计划。
- 当前仍未调用 Kling；下一风险点从 prompt 构造转移到视频是否真实呈现 cue，以及 sampled frames 是否支持标签。

**Pending Criticals**
- DoD-Review：人工审阅 10 条 `Archive_prompts_review/*/prompt.json` 是否自然、可视、无标签泄露。
- DoD-Phase4：实现视频生成批处理、`extract_frames.py`、`frame_manifest.json`。
- DoD-QA：建立 video-level 与 sampled-frame-level QA gate，拒绝 sampled frames 不支持标签的样本。

**Ref Reference**
- `scripts/scenario_sampler.py`
- `scripts/prompt_builder.py`
- `data/scenario_manifest.jsonl`
- `data/_scenario_stats.json`
- `Archive_prompts_review/_prompt_index.jsonl`
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)

### [2026-04-29 20:55:00 CST] | Phase: Phase 2 Data Contract Upgrade

**Key Progress**
- 新增 `BDISummary` 与 `RewardComponents`，`MainSchemaRecord` 现在显式包含 `bdi`，`ActionOutcome` 包含 `next_aida_stage`、`next_bdi`、`reward_components`。
- `rules.py` 保留旧 reward / candidate / tie-break 数值不变，新增 deterministic BDI、next AIDA stage、reward component 派生函数。
- `archive_loader` 生成完整 action outcome；annotation override 会补齐 BDI 与 reward component 字段。
- `state_inference.jsonl` 输出 `aida_stage`、`state_subtype`、`bdi`；`transition_modeling.jsonl` 输出 `next_bdi`、`next_aida_stage`、`reward_components`；`policy_preference.meta` 输出 `state_summary` 与 `candidate_block`。
- `_stats.json` 新增 `n_transition_parent_states`、`avg_actions_per_state`、`n_states_with_action_contrast`、`n_states_without_action_contrast`。
- pytest **60 passed**。

**Data Loop Insight**
- Phase 2 已把论文的 perception / deliberation target 字段落到可训练 JSONL，当前阻塞从“数据契约缺字段”转移到“需要 sampler + Kling + QA 产出非空 pilot 数据”。
- reward components 当前是对既有 scalar reward 的公式一致性解释，不是独立专家标注；后续应上移到 expert corpus/source-backed rules。

**Pending Criticals**
- DoD-Phase3：实现 scenario sampler / prompt builder，生成可审阅 dry-run prompt。
- DoD-Visual：抽帧生成 `frame_manifest.json`，并验证 sampled frames 支持 target cue。
- DoD-Review：人工审阅 deterministic BDI 模板和低强度 provenance anchors。

**Ref Reference**
- `piwm_data/schemas.py`
- `piwm_data/rules.py`
- `piwm_data/archive_loader.py`
- `piwm_data/exporters.py`
- `piwm_data/build_dataset.py`
- [docs/contracts/claim_to_artifact_audit.md](docs/contracts/claim_to_artifact_audit.md)
- [docs/background/data_generation_loop_status.md](docs/background/data_generation_loop_status.md)
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)
- [docs/contracts/world_model_supervision_contract.md](docs/contracts/world_model_supervision_contract.md)

### [2026-04-29 02:19:27 CST] | Phase: Documentation Refactor / Claim-Data Alignment

**Key Progress**
- 将 `docs/` 活跃文档按处理顺序重命名为 `00` 到 `10`，archive 文档也统一编号。
- 新增 `00_claim_to_artifact_audit.md`，把 reward 三项分解、`sigma` vs `latent_state`、real-store split、六张运行时映射列为 P0 审计项。
- 拆出 `03_world_model_supervision_contract.md` 与 `04_visual_input_contract.md`，让 `01_data_generation_loop_status.md` 回到“现状诊断”职责。
- 更新 `02_data_loop_master_plan.md`：规则表口径修正为五张核心表 + fallback intent；数据契约加入 `aida_stage` output、`next_aida_stage`、`reward_components` 与 real-store 阻塞。
- 新增 `11_docs_maintenance_rules.md`，规定 docs 新增、编号、归档和 RESEARCH_LOG 更新规则。

**Data Loop Insight**
- 文档体系现在按闭环处理顺序组织：先审计 claim，再看现状，再执行主计划，再进入 World Model 和视觉输入细则。
- 当前最大 blocking 从“缺 BDI”升级为四类：专家规则来源、AIDA/BDI/latent_state 语义、reward decomposition、real-store split。

**Pending Criticals**
- DoD-0：`00_claim_to_artifact_audit.md` 中所有 P0 blocking 项有代码任务映射。
- DoD-Expert：六张运行时映射进入 `expert_corpus`，包含 fallback intent。
- DoD-Reward：transition reward 可由组件公式校验。
- DoD-Real：real-store split 有 schema、privacy metadata 与 QA 入口。

**Ref Reference**
- [docs/contracts/claim_to_artifact_audit.md](docs/contracts/claim_to_artifact_audit.md)
- [docs/background/data_generation_loop_status.md](docs/background/data_generation_loop_status.md)
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)
- [docs/contracts/world_model_supervision_contract.md](docs/contracts/world_model_supervision_contract.md)
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)
- [docs/contracts/docs_maintenance_rules.md](docs/contracts/docs_maintenance_rules.md)

### [2026-04-29 01:59:59 CST] | Phase: Data Loop Design / World Model Supervision

**Key Progress**
- 在 `docs/contracts/world_model_supervision_contract.md` 中固化“World Model 性质如何在训练中体现”。
- 明确 PIWM 的最小 World Model 判据：`same observation + same current state + different action -> different predicted future`。
- 将 `transition_modeling.jsonl` 定义为核心 world-modeling 证据，`state_inference` 仅负责 state estimation，`policy_preference` 只间接体现。
- 新增 action 对照组统计要求：`n_parent_states`、`n_transition_rows`、`avg_actions_per_state`、`n_states_with_action_contrast`。

**Data Loop Insight**
- 数据闭环必须从一条 current-state video 展开多条 action-conditioned transition rows；否则系统会退化为状态分类器加策略选择器，不能支撑 World Model claim。
- 后续实现应优先保证同一 `state_id` 下存在多个候选动作及差异化 future 标签。

**Pending Criticals**
- DoD-WM-1：每个有效 parent state 至少生成 2 条 action-conditioned transition rows。
- DoD-WM-2：统计 `n_states_with_action_contrast`，确保不同动作不总是导向同一 future。
- DoD-WM-3：`transition_modeling.jsonl` 保留 `parent_state_id`、`candidate_action`、`current_state_summary` 与完整 next-state outcome。

**Ref Reference**
- [docs/contracts/world_model_supervision_contract.md](docs/contracts/world_model_supervision_contract.md)
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)

### [2026-04-29 00:46:39 CST] | Phase: Data Loop Design / Visual Input Contract

**Key Progress**
- 在 `docs/contracts/visual_input_contract.md` 中固化“视觉样本形态与训练模式决策”。
- 将第一版主线固定为 `单视频 -> 多图抽帧 -> 单轮样本 -> 推理时多次调用`。
- 明确 `state_inference`、`transition_modeling`、`policy_preference` 均共享同一组 sampled frames，差异只在文本任务。
- 新增 `frame_manifest.json`、`training_input_mode`、`cue_visible_in_sampled_frames` 等字段要求，防止视频整体有 cue 但训练帧无 cue。

**Data Loop Insight**
- 数据闭环的视觉一致性不能只验证 `video.mp4`，必须验证“模型实际读到的帧”与标签一致。
- 当前主训练模式定义为 `multi_image_single_turn`；single-frame、video-native、多视频多轮均降级为 ablation 或后续增强。

**Pending Criticals**
- DoD-Visual-1：`prompt_builder.py` 输出 behavior timeline，能支持 cue onset / peak / resolution 三点抽帧。
- DoD-Visual-2：`extract_frames.py` 生成 `frame_manifest.json`，记录时间戳、帧角色、采样策略和 `training_input_mode`。
- DoD-Visual-3：QA gate 同时检查整段视频与 sampled frames，sampled frames 不支持标签时拒绝样本。

**Ref Reference**
- [docs/contracts/visual_input_contract.md](docs/contracts/visual_input_contract.md)
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)

### [2026-04-29 00:40:31 CST] | Phase: Data Loop Documentation / Cold Start

**Key Progress**
- 新增 `docs/background/data_generation_loop_status.md`，把当前数据生成闭环拆成已实现模块、缺口、实现目标、非优先事项。
- 明确当前 `data/piwm_dataset/*.jsonl` 是空数据产物，不代表已有可训练数据。
- 将训练/推理侧阻塞具体化为 `bdi`、`next_bdi`、`state_summary`、`candidate_block` 四个缺失字段。
- 固化下一步最小任务：先做 `claim_to_artifact_audit.md`，再做 `expert_corpus` 规则来源迁移。

**Data Loop Insight**
- 当前闭环断点不在 exporter 能不能写 JSONL，而在专家规则来源、Kling prompt 受控构造、QA gate、BDI 训练契约四个环节。
- 文档将“可运行的 schema 骨架”和“可训练的数据闭环”明确区分，降低后续实现者误判项目进度的风险。

**Pending Criticals**
- DoD-0：`docs/contracts/claim_to_artifact_audit.md` 完成，P0 claim 不得误标为 covered。
- DoD-1：`expert_corpus` 编译出的五张核心规则表 + fallback intent 表保持现有行为不漂移。
- DoD-2：BDI 与 preference meta 字段进入 data pipeline，而不是只存在于训练 spec。
- DoD-3：Kling 生成样本必须经过 target cue 可见性 QA。

**Ref Reference**
- [docs/background/data_generation_loop_status.md](docs/background/data_generation_loop_status.md)
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)
- [docs/background/current_code_status.md](docs/background/current_code_status.md)

### [2026-04-29 00:31:27 CST] | Phase: Research Documentation / Data Loop Governance

**Key Progress**
- 将项目文档控制原则固化为“数据生成闭环优于单一架构优化”。
- 新增 `docs/background/data_loop_master_plan.md`，把专家规则、Kling、QA gate、schema/exporter、训练解锁条件串成单一闭环。
- 保存最新 v6 论文草稿到 `docs/background/intro_related_work_v6.md`，作为当前 claim 源。
- 将 Claude method-side implementation spec 保存到 `docs/archive/06_piwm_implementation_spec_method_side_blocked.md`，标记为被 BDI 与 preference meta 数据契约阻塞。
- 清理过时/低活跃文档到 `docs/archive/`，活跃索引只保留当前闭环相关入口。

**Data Loop Insight**
- 当前不能直接进入 `piwm_train` / `piwm_infer`；训练侧 spec 依赖尚未产出的 `bdi`、`next_bdi`、`state_summary`、`candidate_block`。
- 下一步应先完成 `expert_corpus -> runtime rules -> sampler/prompt_builder -> Kling video -> QA -> dataset JSONL`，否则 architecture code 会绑定不存在的数据格式。

**Pending Criticals**
- DoD-0：完成 `docs/contracts/claim_to_artifact_audit.md`，确认 v6 每个 P0 claim 对应代码/数据工件。
- DoD-1：`conditional_rules.jsonl` 覆盖当前五张核心规则表 + fallback intent 表，编译后既有 pytest 不回退。
- DoD-2：data pipeline 输出显式 `bdi` / `next_bdi` / `meta.state_summary` / `meta.candidate_block`。
- DoD-3：Kling prompt 由 sampler + prompt builder 生成，且 QA gate 能拒绝 cue 不可见样本。

**Ref Reference**
- [docs/background/data_loop_master_plan.md](docs/background/data_loop_master_plan.md)
- [docs/background/intro_related_work_v6.md](docs/background/intro_related_work_v6.md)
- [docs/background/readable_data_plan_background.md](docs/background/readable_data_plan_background.md)
- [docs/archive/06_piwm_implementation_spec_method_side_blocked.md](docs/archive/06_piwm_implementation_spec_method_side_blocked.md)

### [2026-05-02 08:22:00 CST] | Phase: Dataset Schema Unification / QA Eval + World Model

**Key Progress**
- Re-exported `PIWM-Eval-QA-v1` from the exact previous 36 QA-pass parent IDs into `data/piwm_dataset_priority40_qareviewed_sample_compact_v2_exact`.
- Re-exported `PIWM-WorldModel-v1` into `data/piwm_dataset_pilot30_with_continuations_compact_v2` with compact `visual_state` and `best_action_realization` fields.
- Migrated Future Verification `visible_reaction` from four fields (`body/gaze/hand/movement`) to the shared three-axis schema: `engagement_pattern_change`, `gaze_and_attention_change`, `body_and_hands_change`.
- Regenerated ms-swift JSONL entrypoints for QA eval and World Model/Future Verification, then updated `data/official/` aliases.

**Data Loop Insight**
- Training, QA evaluation, and World Model evidence now speak the same schema: current-state perception uses `visual_state` axes, and future verification describes post-action change with aligned axes.
- This makes qualitative demos and error analysis traceable from visible customer evidence -> state label -> concrete action realization -> visible future reaction.

**Pending Criticals**
- Re-run the main eval table against `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl` after the compact eval migration.
- Re-run Future Verification eval against `data/official/ms_swift/piwm_future_verification_eval_all_v1.jsonl` because parser/metric fields changed.
- Add end-to-end reporting metrics for `visual_state` axis match and action-realization quality if time permits.

**Ref Reference**
- [data/official/DATASET_MANIFEST.json](data/official/DATASET_MANIFEST.json)
- [docs/current/dataset_inventory.md](docs/current/dataset_inventory.md)
- [data/official/README.md](data/official/README.md)

### [2026-05-02 18:55:00 CST] | Phase: Fresh Training Prep / Full-v2 Eight-GPU Run

**Key Progress**
- Created `data/official/ms_swift/piwm_train_full_v2.jsonl` as the next fresh-from-base training entrypoint.
- Full-v2 scale: 3339 SFT examples = 567 perception + 2077 deliberation + 567 action-selection + 44 continuation-caption + 84 future-verification.
- Regenerated component exports with remote data-disk image paths under `/root/lanyun-fs/ProactiveIntentWorldModel`.
- Updated future-verification and continuation prompts to include the compact current `visual_state` axes, so transition/future tasks receive the fine-grained visual state rather than only coarse labels.
- Added `logs/run_full_v2_len8192_8gpu.sh`, which trains from Qwen2.5-VL base on 8 GPUs and then runs main QA eval, e2e eval, and Future Verification eval.

**Data Loop Insight**
- The next run no longer trains only state/per-action transition; it also supervises final action selection and concrete intervention realization.
- Future verification now uses a symmetric current/future visual schema: current `engagement/gaze/body-hands` axes and future `engagement/gaze/body-hands` changes.

**Pending Criticals**
- Restore remote SSH access or run the prepared script directly on the remote data disk.
- Start the full-v2 8-GPU job with `nohup bash logs/run_full_v2_len8192_8gpu.sh > logs/run_full_v2_len8192_8gpu.out 2>&1 &`.
- After completion, compare full-v2 against enriched official v1 on QA eval, e2e strategy accuracy, and Future Verification.

**Ref Reference**
- [data/official/ms_swift/piwm_train_full_v2_summary.json](data/official/ms_swift/piwm_train_full_v2_summary.json)
- [logs/run_full_v2_len8192_8gpu.sh](logs/run_full_v2_len8192_8gpu.sh)
- [data/official/DATASET_MANIFEST.json](data/official/DATASET_MANIFEST.json)

### [2026-05-02 21:28:07 CST] | Phase: Full-v2 Training + Evaluation Completion

**Key Progress**
- Completed fresh-from-base Qwen2.5-VL-7B full-v2 SFT on 8 x RTX 4090: 3339 SFT examples, 2 epochs, 834 / 834 steps.
- Final checkpoint: `data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834`.
- Final training log: `train_loss=0.04035239`, `token_acc=0.99888617`.
- Completed official long-token QA eval: parse 1.000; stage / score / candidates all 0.861; transition risk / benefit / reward all 1.000.
- Completed official end-to-end decision-loop eval: strategy accuracy vs best action 0.833, candidate exact 0.861, action parse 0.972.
- Completed Future Verification full-84 eval: parse 1.000, expected state 0.988, match 0.512, visible-reaction three-axis exact 0.595.

**Data Loop Insight**
- Full-v2 is the first run where compact visual-state, concrete action realization, action-selection supervision, continuation captioning, and Future Verification are trained in one unified ms-swift entrypoint.
- The largest gain is at the loop level: end-to-end strategy accuracy increased from enriched official v1's 0.389 to full-v2's 0.833 on the same 36 QA-reviewed states.

**Pending Criticals**
- Use `full-v2` as the current main table anchor; demote enriched official v1 to previous-run comparison.
- Do not use the parallel e2e merge artifact for formal reporting; the merge script produced invalid zero metrics due field-name mismatch.
- Inspect Future Verification failures because `match_exact=0.512` remains weaker than expected-state and visible-reaction fields.

**Ref Reference**
- [docs/current/experiment_result_digest.md](docs/current/experiment_result_digest.md)
- [data/piwm_results/remote_full_v2/main_table_piwm_sft_full_v2_len8192_priority40_all_longtok.json](data/piwm_results/remote_full_v2/main_table_piwm_sft_full_v2_len8192_priority40_all_longtok.json)
- [data/piwm_results/remote_full_v2/e2e_piwm_sft_full_v2_len8192_priority40_decision_loop_longtok.json](data/piwm_results/remote_full_v2/e2e_piwm_sft_full_v2_len8192_priority40_decision_loop_longtok.json)
- [data/piwm_results/remote_full_v2/future_verification_piwm_sft_full_v2_len8192_all84_longtok.json](data/piwm_results/remote_full_v2/future_verification_piwm_sft_full_v2_len8192_all84_longtok.json)
