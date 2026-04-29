# PIWM Research Log

核心逻辑基点：**数据生成闭环优于单一架构优化**。

本文件是 PIWM 项目的动态索引与计划跟踪中心。活跃文档只保留能直接服务当前闭环的入口；历史材料统一放入 `docs/archive/`。

## Active Document Index

| Active Doc | Role |
|---|---|
| [docs/00_claim_to_artifact_audit.md](docs/00_claim_to_artifact_audit.md) | 最高优先级审计：论文 claim 与代码/数据工件差距 |
| [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md) | 数据生成闭环现状、问题、目标 |
| [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md) | 当前执行计划：阶段顺序与 DoD |
| [docs/03_world_model_supervision_contract.md](docs/03_world_model_supervision_contract.md) | World Model 监督契约：action-conditioned transition |
| [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md) | 视觉输入契约：Kling、抽帧、frame manifest、QA |
| [docs/05_current_code_status.md](docs/05_current_code_status.md) | 当前代码状态：schema/rules/exporter/Kling wrapper |
| [docs/06_data_pipeline_usage.md](docs/06_data_pipeline_usage.md) | 现有数据管线使用说明 |
| [docs/07_kling_api_usage.md](docs/07_kling_api_usage.md) | Kling API wrapper 使用说明 |
| [docs/08_intro_related_work_v6.md](docs/08_intro_related_work_v6.md) | 最新 intro + related work 草稿，定义当前论文 claim |
| [docs/09_related_work_expert_distillation.md](docs/09_related_work_expert_distillation.md) | 高价值 related-work 审阅：专家知识蒸馏与销售/视觉 agent 差异 |
| [docs/10_readable_data_plan_background.md](docs/10_readable_data_plan_background.md) | 可读版背景说明，非执行入口 |
| [docs/11_docs_maintenance_rules.md](docs/11_docs_maintenance_rules.md) | docs 维护守则：新增、编号、归档、日志更新规范 |
| [docs/12_expert_provenance_upgrade_plan.md](docs/12_expert_provenance_upgrade_plan.md) | expert corpus 从 seed_rule 升级到理论/教材/专家来源的补救计划 |

## High-Density Updates

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
- [docs/00_claim_to_artifact_audit.md](docs/00_claim_to_artifact_audit.md)
- [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md)
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)
- [docs/03_world_model_supervision_contract.md](docs/03_world_model_supervision_contract.md)

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
- [docs/12_expert_provenance_upgrade_plan.md](docs/12_expert_provenance_upgrade_plan.md)

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
- [docs/12_expert_provenance_upgrade_plan.md](docs/12_expert_provenance_upgrade_plan.md)

### [2026-04-29 23:40:00 CST] | Phase: Expert Provenance Implementation

**Key Progress**
- 更新 `docs/12_expert_provenance_upgrade_plan.md`：现有 72 条规则不再作为必须映射对象，而是 seed baseline，可保留、修改、删除或被 source-backed rules 替换。
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
- [docs/12_expert_provenance_upgrade_plan.md](docs/12_expert_provenance_upgrade_plan.md)
- `piwm_data/expert_corpus/provenance.py`
- `piwm_data/expert_corpus/sources/sales_source_registry.jsonl`
- `piwm_data/expert_corpus/sources/modeling_source_registry.jsonl`
- `piwm_data/expert_corpus/distilled/rule_source_links.jsonl`
- `piwm_data/expert_corpus/distilled/_provenance_coverage.json`
- `piwm_data/tests/test_provenance.py`

### [2026-04-29 23:10:00 CST] | Phase: Expert Provenance Risk Control

**Key Progress**
- 确认现有 docs 只记录了 `seed_rule` 风险和方向性建议，没有一份可执行的 provenance 补救计划。
- 新增 `docs/12_expert_provenance_upgrade_plan.md`，把当前状态定义为 `expert corpus container: done`、`expert provenance content: incomplete`。
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
- [docs/12_expert_provenance_upgrade_plan.md](docs/12_expert_provenance_upgrade_plan.md)
- [docs/00_claim_to_artifact_audit.md](docs/00_claim_to_artifact_audit.md)
- [docs/09_related_work_expert_distillation.md](docs/09_related_work_expert_distillation.md)

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
- [docs/00_claim_to_artifact_audit.md](docs/00_claim_to_artifact_audit.md)（"Pedagogy-derived action space" 行可由 `blocking` 改为 `partial→covered`）

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
- [docs/00_claim_to_artifact_audit.md](docs/00_claim_to_artifact_audit.md)
- [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md)
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)
- [docs/03_world_model_supervision_contract.md](docs/03_world_model_supervision_contract.md)
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)
- [docs/11_docs_maintenance_rules.md](docs/11_docs_maintenance_rules.md)

### [2026-04-29 01:59:59 CST] | Phase: Data Loop Design / World Model Supervision

**Key Progress**
- 在 `docs/03_world_model_supervision_contract.md` 中固化“World Model 性质如何在训练中体现”。
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
- [docs/03_world_model_supervision_contract.md](docs/03_world_model_supervision_contract.md)
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)

### [2026-04-29 00:46:39 CST] | Phase: Data Loop Design / Visual Input Contract

**Key Progress**
- 在 `docs/04_visual_input_contract.md` 中固化“视觉样本形态与训练模式决策”。
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
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)

### [2026-04-29 00:40:31 CST] | Phase: Data Loop Documentation / Cold Start

**Key Progress**
- 新增 `docs/01_data_generation_loop_status.md`，把当前数据生成闭环拆成已实现模块、缺口、实现目标、非优先事项。
- 明确当前 `data/piwm_dataset/*.jsonl` 是空数据产物，不代表已有可训练数据。
- 将训练/推理侧阻塞具体化为 `bdi`、`next_bdi`、`state_summary`、`candidate_block` 四个缺失字段。
- 固化下一步最小任务：先做 `claim_to_artifact_audit.md`，再做 `expert_corpus` 规则来源迁移。

**Data Loop Insight**
- 当前闭环断点不在 exporter 能不能写 JSONL，而在专家规则来源、Kling prompt 受控构造、QA gate、BDI 训练契约四个环节。
- 文档将“可运行的 schema 骨架”和“可训练的数据闭环”明确区分，降低后续实现者误判项目进度的风险。

**Pending Criticals**
- DoD-0：`docs/00_claim_to_artifact_audit.md` 完成，P0 claim 不得误标为 covered。
- DoD-1：`expert_corpus` 编译出的五张核心规则表 + fallback intent 表保持现有行为不漂移。
- DoD-2：BDI 与 preference meta 字段进入 data pipeline，而不是只存在于训练 spec。
- DoD-3：Kling 生成样本必须经过 target cue 可见性 QA。

**Ref Reference**
- [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md)
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)
- [docs/05_current_code_status.md](docs/05_current_code_status.md)

### [2026-04-29 00:31:27 CST] | Phase: Research Documentation / Data Loop Governance

**Key Progress**
- 将项目文档控制原则固化为“数据生成闭环优于单一架构优化”。
- 新增 `docs/02_data_loop_master_plan.md`，把专家规则、Kling、QA gate、schema/exporter、训练解锁条件串成单一闭环。
- 保存最新 v6 论文草稿到 `docs/08_intro_related_work_v6.md`，作为当前 claim 源。
- 将 Claude method-side implementation spec 保存到 `docs/archive/06_piwm_implementation_spec_method_side_blocked.md`，标记为被 BDI 与 preference meta 数据契约阻塞。
- 清理过时/低活跃文档到 `docs/archive/`，活跃索引只保留当前闭环相关入口。

**Data Loop Insight**
- 当前不能直接进入 `piwm_train` / `piwm_infer`；训练侧 spec 依赖尚未产出的 `bdi`、`next_bdi`、`state_summary`、`candidate_block`。
- 下一步应先完成 `expert_corpus -> runtime rules -> sampler/prompt_builder -> Kling video -> QA -> dataset JSONL`，否则 architecture code 会绑定不存在的数据格式。

**Pending Criticals**
- DoD-0：完成 `docs/00_claim_to_artifact_audit.md`，确认 v6 每个 P0 claim 对应代码/数据工件。
- DoD-1：`conditional_rules.jsonl` 覆盖当前五张核心规则表 + fallback intent 表，编译后既有 pytest 不回退。
- DoD-2：data pipeline 输出显式 `bdi` / `next_bdi` / `meta.state_summary` / `meta.candidate_block`。
- DoD-3：Kling prompt 由 sampler + prompt builder 生成，且 QA gate 能拒绝 cue 不可见样本。

**Ref Reference**
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)
- [docs/08_intro_related_work_v6.md](docs/08_intro_related_work_v6.md)
- [docs/10_readable_data_plan_background.md](docs/10_readable_data_plan_background.md)
- [docs/archive/06_piwm_implementation_spec_method_side_blocked.md](docs/archive/06_piwm_implementation_spec_method_side_blocked.md)
