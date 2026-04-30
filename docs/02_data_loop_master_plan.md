# PIWM 数据生成闭环主计划

更新时间：2026-04-29（Viewpoint V1-V4 后）

## 0. 核心判断

本项目当前的首要目标不是先优化训练/推理架构，而是先打通可信的数据生成闭环：

```text
专家规则 -> 场景采样 -> 多视角 Kling 当前状态视频 -> 抽帧与 QA -> 主 schema -> 三套训练数据 -> 训练/推理代码
```

训练代码只有在数据格式稳定之后才有意义。当前 Claude 生成的 method-side implementation spec 已保存到 [archive/06_piwm_implementation_spec_method_side_blocked.md](archive/06_piwm_implementation_spec_method_side_blocked.md)。其中曾经阻塞训练代码的两个数据契约已经在 Phase 2 第一版补齐：

- `state_inference.jsonl` / `transition_modeling.jsonl` 已有显式 `bdi` / `next_bdi`；
- `policy_preference.jsonl.meta` 已有 `state_summary` 与结构化 `candidate_block`。

因此，当前执行顺序必须以数据闭环优先。

## 1. 当前闭环结构

```mermaid
flowchart LR
    A["Retail pedagogy / AIDA / SOP"] --> B["expert_corpus/conditional_rules.jsonl"]
    B --> C["rules.py runtime tables"]
    C --> D["scenario_sampler.py"]
    D --> E["prompt_builder.py"]
    E --> F["Kling multi-view current-state video"]
    F --> G["extract_frames.py"]
    G --> H["QA gate: cue visible / no leakage"]
    H --> I["main_schema.jsonl"]
    I --> J["state_inference.jsonl"]
    I --> K["transition_modeling.jsonl"]
    I --> L["policy_preference.jsonl"]
    J --> M["piwm_train / piwm_infer"]
    K --> M
    L --> M
```

## 2. 活跃阶段

### Phase 0：Claim-to-Artifact 审计

目标：确认论文 v6 的每个关键 claim 都有明确代码或数据工件承接。

必须覆盖：

- pedagogy-derived action space；
- AIDA-BDI state representation；
- Kling renders visual side, not labels；
- unified interaction schema；
- state / transition / preference 三套 supervision；
- OOD split；
- internal simulator inference。

产出：

- [00_claim_to_artifact_audit.md](00_claim_to_artifact_audit.md)

进入下一阶段条件：

- 所有 P0 claim 标为 `covered` 或 `blocking`；
- 不允许把未实现的 claim 写成已完成。

### Phase 1：专家规则语料层

目标：让当前规则不再只表现为 `rules.py` 硬编码。

产出：

- `piwm_data/expert_corpus/schemas.py`
- `piwm_data/expert_corpus/compile.py`
- `piwm_data/expert_corpus/distilled/conditional_rules.jsonl`
- `piwm_data/expert_corpus/distilled/_conflict_log.jsonl`
- `tests/test_expert_corpus.py`

验收：

- 五张核心规则表 + 一张 fallback intent 表从 `conditional_rules.jsonl` 编译；
- 编译结果条数匹配当前基线：10 / 14 / 9 / 9 / 9 / 21；
- `python3 -m pytest` 全部通过；
- seed rule 明确标注，不伪装真实教材来源。

进入下一阶段条件：

- 既有测试不回退（基线见 RESEARCH_LOG 最新条目）；
- 新增 expert corpus 测试通过；
- conflict log 可生成且无未解释冲突。

### Phase 2：数据契约升级

状态：**已完成第一版（2026-04-29）**。当前实现保留旧字段兼容，同时补齐 method-side 需要的 AIDA/BDI/reward/contrast 字段。

目标：解除 method-side implementation spec 的 P0 阻塞。

产出：

- `MainSchemaRecord.bdi`
- `state_inference.output.aida_stage`
- `state_inference.output.bdi`
- `transition_modeling.output.next_aida_stage`
- `transition_modeling.output.next_bdi`
- `policy_preference.meta.state_summary`
- `policy_preference.meta.candidate_block`
- `reward_components`

验收：

- `aida_stage` 对应论文中的 `sigma_t`；
- `belief / desire / intention` 三字段非空；
- `latent_state` 定位为 `state_subtype`，不再冒充 AIDA stage；
- reward 标量能由 `alpha * delta_stage + beta * delta_mental - gamma * action_cost` 解释；
- `candidate_block` 使用结构化 list/dict，不直接输出拼好的 prompt 字符串；
- `state_summary` 明确包含 `aida_stage`、`bdi`、`state_subtype`；
- exporter 对旧 `intent` 的兼容策略写入测试。

进入下一阶段条件：

- method-side target 构造所需字段全部存在；
- schema/exporter/validator 测试全部通过（当前 baseline 见 RESEARCH_LOG 最新条目）。

### Phase 3：场景采样与 Prompt 构造

状态：**已完成 Viewpoint V1-V2（2026-04-29）**。已能生成完整规则空间 manifest 和 10 条 mixed-view 人工审阅用 Kling prompt。

目标：让 Kling 输入由规则和 coverage 计划自动产生。

产出：

- `scripts/scenario_sampler.py`
- `scripts/prompt_builder.py`
- `data/scenario_manifest.jsonl`
- `data/_scenario_stats.json`
- `Archive_prompts_viewpoint_review/<session_id>/prompt.json`（10 条 mixed-view 审阅样本）

验收：

- 每条样本有 `session_id`、`split`、`viewpoint`、`product_category`、`persona_type`、`aida_stage`、`target_cue`、`source_rule_ids`；
- prompt 不泄露 state/action 标签；
- prompt 有 camera / scene / behavior timeline / negative 四层，camera / negative 按 viewpoint 生成；
- train / dev / test / ood_product / ood_persona split 可复现。
- 当前验证：`data/scenario_manifest.jsonl` 1920 条；split = train 1112 / dev 148 / test 140 / ood_product 240 / ood_persona 280；
- 当前验证：viewpoint = `salesperson_observable` 1536 / `surveillance_oblique` 384；
- 当前验证：`Archive_prompts_viewpoint_review/` 10 条 prompt = 8 条 `salesperson_observable` + 2 条 `surveillance_oblique`。

进入下一阶段条件：

- 10 条 dry-run prompt 人工审阅通过（当前已生成，待人工审阅）；
- target cue 都能转写成可见行为描述。

### Phase 4：Kling 生成、抽帧与 QA Gate

状态：**已完成 Viewpoint V3（2026-04-29）**。已用正式 `extract_frames.py` 抽帧，并用 QA gate 拒绝失败样本、放行 2 条 pilot 样本；QA report 已支持 viewpoint visibility checklist。

目标：只允许视觉 cue 真实可见的样本进入训练数据。

产出：

- `Archive_generated/<session_id>/video.mp4`
- `Archive_generated/<session_id>/frames/*.jpg`
- `Archive_generated/<session_id>/frame_manifest.json`
- `Archive_generated/<session_id>/qa_report.json`
- `scripts/extract_frames.py`（已完成）
- `scripts/qa_gate.py`（第一版已完成）

验收：

- 视频存在且时长/帧数达标；
- 抽帧成功；
- `training_input_mode = multi_image_single_turn`；
- 无字幕、品牌、额外主角、明显标签泄露；
- target cue 在 sampled frames 中可见；
- QA fail 样本写入 `qa_report.json`，不进入 dataset build；
- `build_dataset` 默认要求 `qa_report.overall_pass=true`。
- `qa_report.json` 包含 `viewpoint`、`viewpoint_pass`、`required_visibility`。
- 当前验证：`Archive_generated_pilot/` 共 3 条 session，2 条 `overall_pass=true`，1 条被拒绝。

进入下一阶段条件：

- 小批量样本 QA pass rate 可接受；
- 至少 30 条 QA pass session 可被 loader 读取。

### Phase 5：小规模 Dataset Pilot

状态：**已完成最小闭环（2026-04-29）**。已有非空正式数据集与 pilot 镜像，但规模仍不足以训练。

目标：用真实生成的 QA pass session 跑完训练数据导出。

产出：

- `data/piwm_dataset/main_schema.jsonl`
- `data/piwm_dataset/state_inference.jsonl`
- `data/piwm_dataset/state_inference_with_cue.jsonl`
- `data/piwm_dataset/transition_modeling.jsonl`
- `data/piwm_dataset/policy_preference.jsonl`
- `data/piwm_dataset/_stats.json`
- `data/piwm_dataset_pilot/`（同源 pilot 镜像，便于保留本轮实验结果）

验收：

- loader 只吃 QA pass 样本；
- 三套 JSONL 非空；
- `policy_preference` 不产生 malformed pair；
- `transition_modeling` 统计 `n_states_with_action_contrast`；
- `_stats.json` 记录 loaded / skipped / rejected 计数；
- `python3 -m pytest` 全部通过。
- 当前验证：2 条 QA pass session 入库，产出 2 行 state inference、5 行 transition modeling、2 行 policy preference。
- 当前验证：1 条 QA fail session 被 `QAGateNotPassedError` 跳过。

进入下一阶段条件：

- method-side spec 中步骤 1-7 可以用 pilot 数据 fixture 做非 GPU 测试；
- DPO 所需 preference meta 字段齐全。
- `viewpoint` 只进入三套 JSONL 的 `meta`，不进入主 `input`。

### Phase 6：训练/推理代码解锁

目标：在数据契约稳定后，回到 `piwm_train` / `piwm_infer`。

产出：

- `piwm_train/config.py`
- `piwm_train/targets.py`
- `piwm_train/prompts.py`
- `piwm_infer/parsers.py`
- `piwm_infer/decision_loop.py`

验收：

- 无 GPU 步骤只依赖 mock fixture；
- parser 出错即 raise，不做 fuzzy match；
- `stage` 与 `latent_state` 字段语义不混用；
- `pyproject.toml` 纳入新增测试路径。

进入下一阶段条件：

- pilot 数据可被 target builder 读取；
- `piwm_train` / `piwm_infer` 单测通过；
- GPU 训练入口另开阶段。

## 3. 当前阻塞

1. 当前环境缺少 `KLINGAI_ACCESS_KEY` / `KLINGAI_SECRET_KEY`，mixed-view 10 条真实 Kling 生成尚未执行；`scripts/run_kling_batch.py --dry-run` 已通过。
2. 当前只有 2 条 QA pass pilot 样本，且都来自 `checking_phone_likely_research` cue，不能代表规则空间。
3. QA gate 仍依赖人工 `qa_manual_review.json`，尚未接 VLM reviewer。
4. 失败样本原因尚未系统回流到 prompt_builder；需要统计 cue-by-cue pass/fail。
5. reward components 已有公式一致性，但还不是 source-backed 独立标注。
6. real-store split 仍没有 schema 和隐私/授权 metadata，不能支撑论文 real-store test claim。

## 4. 当前不做

- 不直接实现 `piwm_train.sft` / `piwm_train.dpo`；
- 不让 Kling 生成 action-continuation video；
- 不把旧 Archive 迁移作为主线；
- 不伪造真实销售手册引用；
- 不把 seed rules 写成真实教材蒸馏结果。
