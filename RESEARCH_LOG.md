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
| [docs/07_kling_api_usage.md](docs/07_kling_api_usage.md) | Kling API wrapper 使用说明 |
| [docs/08_intro_related_work_v6.md](docs/08_intro_related_work_v6.md) | 最新 intro + related work 草稿，定义当前论文 claim |
| [docs/09_related_work_expert_distillation.md](docs/09_related_work_expert_distillation.md) | 高价值 related-work 审阅：专家知识蒸馏与销售/视觉 agent 差异 |
| [docs/10_readable_data_plan_background.md](docs/10_readable_data_plan_background.md) | 可读版背景说明，非执行入口 |
| [docs/11_docs_maintenance_rules.md](docs/11_docs_maintenance_rules.md) | docs 维护守则：新增、编号、归档、日志更新规范 |
| [docs/12_expert_provenance_upgrade_plan.md](docs/12_expert_provenance_upgrade_plan.md) | expert corpus 从 seed_rule 升级到理论/教材/专家来源的补救计划 |
| [docs/13_pilot30_continuation_review_report.md](docs/13_pilot30_continuation_review_report.md) | Phase 7 continuation pilot 生成、QA、fix3 验证与下一步问题 |
| [docs/14_priority_generation_policy.md](docs/14_priority_generation_policy.md) | Kling API 受限时的重要样本优先生成策略 |
| [docs/90_neurips_sprint_master_plan.md](docs/90_neurips_sprint_master_plan.md) | NeurIPS sprint 用户视角总计划，含 projection 边界与诚信红线 |
| [docs/91_neurips_sprint_codex_plan.md](docs/91_neurips_sprint_codex_plan.md) | Codex sprint 执行计划，禁止 mock/projected-as-real |
| [docs/92_neurips_sprint_result_snapshot.md](docs/92_neurips_sprint_result_snapshot.md) | 当前 sprint 结果快照：数据、训练、评估口径 |
| [docs/93_remote_sprint_runbook.md](docs/93_remote_sprint_runbook.md) | 远端数据盘、Kling、ms-swift 运行入口 |
| [docs/94_current_sprint_status_and_reporting_policy.md](docs/94_current_sprint_status_and_reporting_policy.md) | 当前状态与对外报告口径：QA-reviewed / synthetic train / diagnostic-only 三层 |

## High-Density Updates

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
- [docs/94_current_sprint_status_and_reporting_policy.md](docs/94_current_sprint_status_and_reporting_policy.md)

### [2026-04-30 20:50:00 CST] | Phase: Sprint Status Audit / Reporting Policy

**Key Progress**
- 远端 live audit 确认：Kling 额度约从 86% 降到 46%，换来 260 条唯一 priority parent videos。
- `Archive_generated_priority24` 与 `Archive_generated_priority256` 共 260 条 parent videos，均有 `qa_report.json`，但 0 条人工 `qa_manual_review.json`。
- 构建 `data/piwm_dataset_priority280_unreviewed/`：260 parent、927 transition、260 policy；口径固定为 high-throughput synthetic train split, pending visual QA。
- `data/piwm_dataset_pilot30_with_continuations/` 保持 QA-reviewed pilot：24 parent、44 continuation。
- ms-swift 4 x 4090 SFT 完成：Qwen2.5-VL-7B-Instruct + LoRA，1321 examples，660/660 steps，train loss 0.0404377，checkpoint-660 落盘。
- checkpoint eval 已尝试 24 条 balanced input，但全部 CUDA OOM；当前没有有效模型推理指标，不能报告 accuracy=0。
- 新增 [docs/94_current_sprint_status_and_reporting_policy.md](docs/94_current_sprint_status_and_reporting_policy.md)，并更新 docs/14/90/91/92/93 的数据与口径。

**Data Loop Insight**
- 大批量数据已经从 prompt queue 转为可训练 synthetic split；当前瓶颈不再是 Kling parent generation，而是 visual QA 抽样、低显存 checkpoint eval 与论文口径控制。
- priority split 可以支撑赶 SFT，但不能替代 QA-reviewed evaluation set。

**Pending Criticals**
- DoD-EvalLowMem：生成 1-frame 或 low-image-token eval input，重跑 checkpoint eval，产出有效 JSON metric 或明确记录显存限制。
- DoD-VisualQASample：对 priority280 做 30-50 条分层人工 QA，估计 visual pass rate。
- DoD-PaperSafeTables：所有论文表格区分 QA-reviewed subset、synthetic train split、diagnostic-only artifacts。

**Ref Reference**
- [docs/94_current_sprint_status_and_reporting_policy.md](docs/94_current_sprint_status_and_reporting_policy.md)
- [docs/92_neurips_sprint_result_snapshot.md](docs/92_neurips_sprint_result_snapshot.md)
- `/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/sft_train_summary.json`

### [2026-04-30 15:05:31 CST] | Phase: NeurIPS Sprint 91 / Training Skeleton + Mock Eval

**Key Progress**
- 阅读 `docs/91_neurips_sprint_codex_plan.md` 后确认无阻塞歧义；执行假设：不自动 commit，不写 projected 数字，先做纯 Python Day1/Day2 任务。
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
- [docs/91_neurips_sprint_codex_plan.md](docs/91_neurips_sprint_codex_plan.md)
- [data/piwm_results/pilot24_mock_pipeline_eval.json](data/piwm_results/pilot24_mock_pipeline_eval.json)
- [data/piwm_results/sft_adapter_smoke/sft_smoke_summary.json](data/piwm_results/sft_adapter_smoke/sft_smoke_summary.json)

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
- [docs/13_pilot30_continuation_review_report.md](docs/13_pilot30_continuation_review_report.md)

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
- [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md)
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)
- [docs/05_current_code_status.md](docs/05_current_code_status.md)

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
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)
- [docs/05_current_code_status.md](docs/05_current_code_status.md)

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
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)
- [docs/05_current_code_status.md](docs/05_current_code_status.md)

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
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)
- [docs/05_current_code_status.md](docs/05_current_code_status.md)

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
- [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md)
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)

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
- [docs/01_data_generation_loop_status.md](docs/01_data_generation_loop_status.md)
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)

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
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)

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
- [docs/02_data_loop_master_plan.md](docs/02_data_loop_master_plan.md)
- [docs/04_visual_input_contract.md](docs/04_visual_input_contract.md)

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
