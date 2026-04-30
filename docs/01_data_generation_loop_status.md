# PIWM 数据生成闭环：现状、问题与实现目标

更新时间：2026-04-30（Pilot30 prompt 包生成后）

## 1. 定位

本文是数据生成闭环的冷启动诊断文档。它回答三件事：

1. 当前项目已经有什么；
2. 当前数据闭环断在哪里；
3. 下一步实现目标是什么。

详细设计拆到独立文档：

- [00_claim_to_artifact_audit.md](00_claim_to_artifact_audit.md)：论文 claim 与代码/数据工件对齐审计；
- [03_world_model_supervision_contract.md](03_world_model_supervision_contract.md)：什么训练才体现 World Model；
- [04_visual_input_contract.md](04_visual_input_contract.md)：Kling 视频、抽帧、多图输入与 QA 契约。

核心判断保持不变：

> 数据生成闭环优于单一架构优化。  
> 在 `expert rules -> controlled video -> QA -> dataset JSONL` 没有闭合之前，不应优先实现训练/推理侧大型架构。

## 2. 目标闭环

目标闭环是：

```text
销售专家知识 / AIDA / SOP
  -> conditional_rules.jsonl
  -> rules.py runtime tables
  -> scenario_sampler.py
  -> prompt_builder.py
  -> Kling multi-view current-state video
  -> frame_manifest.json + frames/
  -> QA gate
  -> main_schema.jsonl
  -> state_inference / transition_modeling / policy_preference
  -> piwm_train / piwm_infer
```

这个闭环服务论文当前主张：

- pedagogy-derived action constraints；
- AIDA-BDI state representation；
- action-conditioned transition prediction；
- controllable video rendering；
- synthetic / real-store / OOD split evaluation。

## 3. 当前已有模块

| 模块 | 路径 | 当前状态 |
|---|---|---|
| 主 schema | `piwm_data/schemas.py` | 已实现 Phase 2 数据契约；包含 `product_category`、`split`、`BDISummary`、`RewardComponents`、`next_bdi`、`next_aida_stage`；`intent` 保留为兼容字段 |
| 规则层 | `piwm_data/rules.py` | 已实现但为硬编码；包含五张核心表 + 一张 fallback intent 表 |
| Loader | `piwm_data/archive_loader.py` | 读取新格式 `prompt.json + frames/` |
| Exporter | `piwm_data/exporters.py` | 已导出三套 JSONL；`state_inference` 主线为 visual-only，`observable_cues` 移入 meta；另导出 `state_inference_with_cue.jsonl` 作为调试/上限版 |
| Validator | `piwm_data/validate.py` | 校验 schema 和图片路径 |
| Dataset CLI | `piwm_data/build_dataset.py` | 默认只读取 `qa_report.overall_pass=true` 的 session；写 `main_schema.jsonl`、四套训练/调试 JSONL 与 `_stats.json` |
| Scenario sampler | `scripts/scenario_sampler.py` | 已生成完整规则空间 manifest：1920 条场景；新增 `viewpoint`，默认 80% `salesperson_observable`、20% `surveillance_oblique` |
| Prompt builder | `scripts/prompt_builder.py` | 已生成 10 条 mixed-view 审阅包与 30 条 pilot prompt；prompt 按 viewpoint 生成 camera / negative，顶层写入 `sampler.version` |
| Frame extractor | `scripts/extract_frames.py` | 已实现正式抽帧脚本；读取 `frame_sampling_plan`，写 `frames/*.jpg` 与带 `viewpoint` 的 `frame_manifest.json` |
| QA gate | `scripts/qa_gate.py` | 第一版已实现；自动检查文件/帧/标签泄露，人工审阅 cue 可见性、物理一致性与 viewpoint visibility 后生成 `qa_report.json` |
| Kling batch runner | `scripts/run_kling_batch.py` | 已完成 mixed-view 真实小批量：10 条视频生成、6 条 QA pass、4 条 QA reject |
| Kling wrapper | `kling/generate_session.js` | 已验证存在；只做 API 调用，不构造受控 prompt |
| Pilot / formal dataset | `data/piwm_dataset_pilot/`、`data/piwm_dataset/`、`data/piwm_dataset_viewpoint_review/` | pilot 首次非空：2 条 QA pass；mixed-view 小批量：6 条 QA pass 入库；已补 product/split 统计、BDI 去 cue token、preference rationale |
| 测试 | `piwm_data/tests/` | 最近一次验证为 `python3 -m pytest`：80 passed |

仓库早期的 `data/piwm_dataset/*.jsonl` 曾是旧 Archive 失败后的空数据产物；Phase 4 已用 `Archive_generated_pilot/` 重建为非空正式产物，同时保留一份 `data/piwm_dataset_pilot/` 便于审阅。旧空产物不代表当前闭环失败，原因是仓库里的旧 `Archive/` 是旧格式，当前 loader 只接受：

```text
session/
├── prompt.json
└── frames/
```

旧 Archive 不再作为主线迁移；旧项目只复用 Kling API 调用经验。

## 4. 核心问题与修正目标

| 问题 | 当前状态 | 修正目标 | 验收 |
|---|---|---|---|
| 专家规则来源不足 | `rules.py` 已有 seed corpus 镜像；真实来源仍不完整 | 保留 seed baseline，但允许删改/新增；sales/modeling provenance 分离 | **部分完成**：72 条均已 source-linked；32 manual-supported、40 theory-anchored；仍需人工审阅低强度 anchors |
| BDI 缺失 | **已完成第一版**：schema 有 `bdi`，transition 有 `next_bdi`；belief 不再直接写 cue 枚举名 | 人工审阅 BDI 模板，避免过度解释 | 三字段非空；训练 target 可读取；不含 `Observable cue(s): xxx` |
| `sigma` 与 `latent_state` 混淆 | **已完成第一版**：`aida_stage` 进入 output；`latent_state` 同步输出为 `state_subtype` | 后续论文和训练脚本统一使用 `aida_stage=sigma` | `state_inference.output.aida_stage` 已进入监督目标 |
| reward 公式未落地 | **已完成第一版**：`reward_components` 校验公式并保留旧 scalar reward | 后续把组件来源上移到 expert corpus | `final_reward` 与组件公式一致 |
| Kling 只接 API | 缺 sampler / prompt builder / split | 场景采样与 prompt timeline 自动生成 | manifest 可复现，prompt 不泄露标签 |
| QA gate 缺失 | **已完成第一版**：默认只允许 QA pass 入库 | 后续接 VLM reviewer，减少人工审阅负担 | fail 样本写 `qa_report.json`，build_dataset 默认跳过 |
| OOD split 缺失 | sampler 已生成 train/dev/test/ood_product/ood_persona；`main_schema` 与 JSONL meta 已写入 split | 后续训练脚本按 split 读取 | split 可复现且可从 `_stats.json` 审计 |
| 多视角输入缺失 | **已完成 V1-V4**：scenario / prompt / frame_manifest / qa_report / JSONL meta 均有 `viewpoint` | 第一阶段主线 `salesperson_observable`，辅助 `surveillance_oblique`，暂缓 `first_person_pov` | 10 条审阅 prompt 中 8/2 mixed-view |
| real-store split 缺失 | 论文承诺 real-store test，但代码未定义 | 定义 `real_test` / `real_calibration` 数据契约 | 不经 Kling，但进入同一 schema |
| 两阶段训练契约不完整 | 三套 JSONL 已有雏形，但与 SFT/DPO 未显式绑定 | Phase 1 用 state+transition SFT，Phase 2 用 preference DPO | 见 `02_data_loop_master_plan.md` |

## 5. 规则表口径

当前 `rules.py` 中需要进入专家规则语料层的映射不是单纯“五张表”，而是：

| 映射 | 当前条数 | 处理方式 |
|---|---:|---|
| `CUE_TO_STATE_PRIOR` | 10 | 编译自 expert corpus |
| `PERSONA_STATE_TO_INTENT` | 14 | 编译自 expert corpus |
| `STATE_FALLBACK_INTENT` | 9 | 编译自 expert corpus，避免隐藏硬编码 |
| `STATE_TO_PROACTIVE_SCORE` | 9 | 编译自 expert corpus |
| `STATE_AIDA_TO_CANDIDATES` | 9 | 编译自 expert corpus |
| `TRANSITION_TABLE` | 21 | 编译自 expert corpus，并补 reward components |

后续文档中如果简称“五张核心表”，必须额外说明 fallback intent 是第六张运行时映射。

## 6. 当前不应优先做

- 不直接实现 `piwm_train.sft` / `piwm_train.dpo`；
- 不直接实现完整 `piwm_infer`；
- 不把完整视频输入作为第一版主训练模式；
- 不做多视频多轮训练；
- 不迁移旧 Archive 作为主线；
- 不把 seed rules 说成真实教材蒸馏结果；
- 不在没有 QA gate 的情况下批量生成训练数据。

## 7. 下一步

1. 人工审阅 `Archive_prompts_pilot30/` 的 30 条 prompt，重点看 cue 是否可视、camera 是否满足 viewpoint；
2. 审阅通过后再跑 Kling，避免对明显不合格 prompt 消耗额度；
3. 跑完 Kling 后按 `extract_frames -> qa_gate -> build_dataset` 生成 `data/piwm_dataset_pilot30/`；
4. 统计不同 cue/viewpoint/persona/product 的 QA pass/fail 原因，反向修正 prompt_builder；
5. 用 30 条 pilot 数据回测 `n_states_with_action_contrast` 和 preference pair 质量。
