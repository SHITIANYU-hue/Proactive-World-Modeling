# PIWM Dataset Inventory

更新时间：2026-05-16 CST

本文是当前数据集总账。Kling API 已耗尽，本轮不会再新增视频，因此当前已落盘数据固定为 PIWM v1 正式数据集。它的目标不是记录所有历史文件，而是回答三个问题：

1. 现在训练应该用哪个数据？
2. 现在论文评估能写哪个数据？
3. 哪些目录只是中间产物、历史 smoke 或待补队列，不能混进主口径？

当前权威数据源在远端数据盘：

```text
/root/lanyun-fs/ProactiveIntentWorldModel
```

本地 `/Users/mutsumi/Desktop/WorkSpace/ProactiveIntentWorldModel` 只视为代码与文档源，以及部分数据镜像。大规模数据、checkpoint、视频相关产物以远端数据盘为准。

## 1. 当前推荐用法

| 用途 | 使用对象 | 口径 |
|---|---|---|
| 正式数据集入口 | `data/official/` | PIWM v2-compatible canonical aliases |
| frozen 主 SFT 训练（轻量） | `data/official/ms_swift/piwm_train_synth_v1.jsonl` | `PIWM-Train-Synth-v1`，high-throughput synthetic train split，未人工视觉审阅；保留真人导购逻辑，动作语义约束为 6-act |
| schema v2.2 主 SFT 训练 | `data/official/ms_swift/piwm_train_synth_v2.jsonl` | `PIWM-Train-Synth-v2`，2554 examples；独立 v2.2 导出，不覆盖 v1 |
| v2 policy 生成入口 | `data/official/piwm_policy_slice_v2/policy_manifest.jsonl` | `PIWM-PolicySlice-v2`，864 条 explicit candidate-rule scenarios；不是视频数据 |
| target 域专项训练 | `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` | `PIWM-Target-Frontcam-v1`，118 target-frontcam records / 708 examples；synthetic_unreviewed，不能写成 QA-reviewed |
| mixed-view 联合训练 | `data/official/ms_swift/piwm_train_general_plus_target_v1.jsonl` | general v2 + target frontcam；3262 examples；用于 joint SFT 对照，不替代 two-stage 入口 |
| 下一次从 base 重训 | `data/official/ms_swift/piwm_train_full_v2.jsonl` | `PIWM-Train-Full-v2`，3339 examples；在主训练基础上加入 action-selection、continuation caption、Future Verification |
| 当前最新 checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834` | ms-swift LoRA SFT，8 GPU，`PIWM-Train-Full-v2` |
| 主表 QA eval | `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl` | `PIWM-Eval-QA-v1`，QA-reviewed priority sample |
| 端到端 eval | `data/official/piwm_eval_qa_v1/state_inference.jsonl` | `PIWM-Eval-QA-v1`，QA-reviewed priority sample |
| World Model / continuation | `data/official/piwm_world_model_v1/` | `PIWM-WorldModel-v1`，QA-reviewed pilot continuation split |
| Future Verification | `data/official/piwm_world_model_v1/future_verification.jsonl` | `PIWM-FutureVerification-v1`，continuation-derived verification pairs |
| 真实拍摄 manifest | `data/official/piwm_realshoot_v1/realshoot_manifest_sample.jsonl` | `PIWM-RealShoot-v1`，S01-S12 A/B manifest template；未拍摄、未 QA，不能写成已采集真实数据 |

禁止混用：

- `PIWM-Train-Synth-v1` 可以训练，但不能写成 QA-pass。`priority1000_unreviewed*` 只能作为 backing/source path 或历史复现实验路径出现，不能当公开数据名。
- `PIWM-Train-Synth-v2` 是同一批 543 parent 的 schema v2.2 独立导出，不代表新增视频。
- `PIWM-PolicySlice-v2` 只能写成规则支撑的 policy manifest / 生成入口，不能写成 filmed dataset 或 QA-reviewed dataset。
- `PIWM-Target-Frontcam-v1` 是从 `guochenmeinian/piwm` 导入的 target 域设备前置摄像头数据；它有视频抽帧和 v2.2 action specs，但当前仍是 synthetic_unreviewed。
- `PIWM-Eval-QA-v1` 可以评估，但规模是 36 loaded parent，不是 full benchmark。旧名为 `priority40_qareviewed_sample`。
- `PIWM-WorldModel-v1` 是 World Model 视觉证据，不是主 SFT 规模来源。旧名为 `pilot30_with_continuations`。
- Kling API 已耗尽，所有 missing-video 队列只保留为待补，不自动生成。

## 1.1 Formal Dataset Names

| 正式名 | Canonical path | Backing/source path（维护用） | 角色 |
|---|---|---|---|
| `PIWM-Train-Synth-v1` | `data/official/piwm_train_synth_v1` | `data/piwm_dataset_priority1000_unreviewed_compact_v2` | frozen 主 SFT 训练，compact visual-state/action-realization schema；字段文本已加入产品类别、视觉线索和具体导购动作细化 |
| `PIWM-Train-Synth-v2` | `data/official/piwm_train_synth_v2` | `data/official/piwm_train_synth_v1` | schema v2.2 独立导出：`candidate_action_specs / best_action_spec / next_state_by_action_v2 / compatibility_tier` |
| `PIWM-PolicySlice-v2` | `data/official/piwm_policy_slice_v2` | `scripts.scenario_sampler --candidate-rule-only` | 864 条 explicit candidate-rule policy manifest；用于后续生成/均衡动作分析，不作为 filmed data |
| `PIWM-Target-Frontcam-v1` | `data/official/piwm_target_v1` | `/Users/mutsumi/Desktop/WorkSpace/piwm` | target 域智能售货柜前置摄像头数据；118 records，354 sampled frames，708 ms-swift examples；synthetic_unreviewed |
| `PIWM-Eval-QA-v1` | `data/official/piwm_eval_qa_v1` | `data/piwm_dataset_priority40_qareviewed_sample_compact_v2_exact` | 主表 / e2e QA 评估，compact visual-state/action-realization schema；与主训练字段语义对齐 |
| `PIWM-WorldModel-v1` | `data/official/piwm_world_model_v1` | `data/piwm_dataset_pilot30_with_continuations_compact_v2` | continuation / World Model 视觉证据，共享三轴 current/future visual schema |
| `PIWM-FutureVerification-v1` | `data/official/piwm_world_model_v1/future_verification.jsonl` | `data/piwm_dataset_pilot30_with_continuations_compact_v2/future_verification.jsonl` | action-conditioned future verification |

正式名用于论文、汇报、新脚本和示例数据展示；旧名仅作为 source path、manifest lineage 或复现实验路径保留。

## 1.2 Schema Version Policy

当前项目采用兼容迁移：

| 层级 | 当前字段 | 兼容字段 | 维护入口 |
|---|---|---|---|
| Policy label | `candidate_action_specs`, `best_action_spec`, `dialogue_act`, `act_params.supporting_acts` | `best_action`, `candidate_actions`, `co_acts` | `docs/contracts/action_space_realization_contract.md` |
| Human salesperson behavior | `best_action_realization` | `realization` terminal draft | `docs/contracts/data_schema_v2_contract.md` |
| Target terminal behavior | `realization`, `actor_profile=target_terminal_logic`, `viewpoint=target_frontcam` | piwm `response_id` | `scripts/import_piwm_target_dataset.py` |
| Real shooting clip | `ShootingClipRecord` | S05 PDF / 旧 A/T 标签 | `docs/current/piwm_real_shooting_scripts_S01_S12.md` |
| Paper data story | 5 层数据脊柱 | 历史 dataset nickname | `docs/current/paper_data_section_blueprint.md` |

`PIWM-Train-Synth-v1`、`PIWM-Eval-QA-v1`、`PIWM-WorldModel-v1` 仍可按旧 action 字段运行。2026-05-13 v2.1 重导后，official 主表输出 `schema_version=dialogue_act_human_salesperson_v2.1` 和 `actor_profile=human_salesperson_logic`；顶层 `co_acts` 只作 legacy input alias，不再作为 official 输出主字段。2026-05-15 runtime/schema 已进入 v2.2，并已写出独立 `PIWM-Train-Synth-v2`：新导出包含 `candidate_action_specs`、`best_action_spec`、`next_state_by_action_v2`、`compatibility_tier`、`legacy_mismatch_flags`。v1 仍保持冻结兼容入口。

`PIWM-RealShoot-v1` 已有 `ShootingClipRecord` manifest 模板与 24 行 S01-S12 A/B 样例。在素材通过 QA 并补齐 assets 前，论文只能写成 planned real-shooting validation protocol，不能写成已完成数据规模。

`PIWM-Target-Frontcam-v1` 已于 2026-05-16 从轻量 `piwm` 仓库导入主项目。该数据把 13 个 `response_id` 映射到 v2.2 canonical `(act, params)`，使用 `target_frontcam` 视角，抽取每条视频 3 帧。它可用于 target-domain specialization pilot，但 30 条 test split 当前只是 unreviewed eval candidate，必须经过人工 QA 后才能写成 in-domain evaluation set。

## 1.3 V2.1 Re-export Status and V2.2 Independent Export

2026-05-13 已运行官方数据重导：

```bash
python3 -m scripts.refresh_official_v2_exports --summary-out data/official/V2_REEXPORT_SUMMARY.json
python3 -m scripts.build_realshoot_manifest --output-dir data/official/piwm_realshoot_v1
```

重导摘要：

| Dataset | Parent / manifest rows | Transition | Policy | Continuation | V2 状态 |
|---|---:|---:|---:|---:|---|
| `PIWM-Train-Synth-v1` | 543 | 2011 | 543 | 0 | `schema_version / actor_profile / dialogue_act / act_params.supporting_acts / best_action_realization` 已写入；`realization` 是终端草案 |
| `PIWM-Eval-QA-v1` | 36 | 126 | 36 | 0 | `schema_version / actor_profile / dialogue_act / act_params.supporting_acts / realization` 已写入 |
| `PIWM-WorldModel-v1` | 24 | 66 | 24 | 44 | transition 已含 `candidate_dialogue_act / candidate_terminal_realization` |
| `PIWM-RealShoot-v1` | 24 manifest rows | - | - | - | `ShootingClipRecord + terminal_realization` 样例已生成 |

v2.2 已完成 schema/runtime 增量和独立导出。当前已生成：

- `docs/v2_validation/compatibility_report.md`
- basic schema compatibility：`green=462`、`yellow=0`、`red=81`。这里的 `yellow=0` 只表示基础检查没有非阻断 schema mismatch，不表示 policy 没有漂移。
- extended v2 re-derivation audit：`green=109`、`yellow=353`、`red=81`。
- official 543 在 v2.2 规则下重新推导的 best action 分布：`Elicit=252`、`Recommend=119`、`Inform=105`、`Reassure=42`、`Hold=25`。
- `red` 全部来自 `intent_tier_visual_mismatch`，且集中在 `browser_low_intent`：81 / 94 条。
- `docs/v2_validation/v2_2_reexport_diff_preview.md` 已预演写回 diff；未修改 official JSONL。
- `next_state_by_action` 当前仍保留 legacy A-label key；`next_state_by_action_v2` 已新增为 v2 action-keyed alias。
- `data/official/piwm_train_synth_v2/` 已写出：543 main records、543 state rows、2011 transition rows、543 policy rows。
- `data/official/ms_swift/piwm_train_synth_v2.jsonl` 已写出：2554 examples，perception=543，deliberation=2011。
- `data/official/piwm_policy_slice_v2/policy_manifest.jsonl` 已写出：864 explicit policy scenarios，policy best 为 `Recommend=360 / Elicit=272 / Inform=136 / Hold=56 / Reassure=40`。
- `data/official/piwm_target_v1/` 已写出：118 target-frontcam main records、354 sampled frames、118 state rows、472 transition rows、118 policy rows。
- `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` 已写出：708 examples，perception=118，deliberation=472，action_selection=118。
- `data/official/ms_swift/piwm_train_general_plus_target_v1.jsonl` 已写出：3262 examples，general=2554，target=708。该文件用于 mixed-view joint SFT 对照；two-stage specialization 仍应显式使用 general stage-1 和 target stage-2 两个入口。

如果要重新生成或覆盖 v2.2 独立目录，必须先运行：

```bash
python3 scripts/refresh_official_v2_exports.py --dry-run --output-diff docs/v2_validation/v2_2_reexport_diff_preview.md
```

人工确认 dry-run 摘要和 diff preview 后，才能重写独立 v2 目录。不要覆盖 `PIWM-Train-Synth-v1`。

## 2. QA-Reviewed Evaluation / Evidence Sets

这些数据可以写成人工 QA-reviewed 或 QA-pass subset。

| Dataset | Loaded parent | Skipped | State | Transition | Policy | Continuation | Future Verification | 用途 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `data/piwm_dataset_priority40_qareviewed_sample_compact_v2_exact` | 36 | 4 | 36 | 126 | 36 | 0 | 0 | 当前最干净的主评估集，已与训练 schema 对齐 |
| `data/piwm_dataset_pilot30_with_continuations_compact_v2` | 24 | 6 | 24 | 66 | 24 | 44 | 84 | World Model / Future Verification / qualitative evidence，未来反应三轴化 |
| `data/piwm_dataset_fix3_continuation_validation` | 2 | 1 | 2 | 4 | 2 | 2 | 0 | continuation prompt 修复验证，不作主表 |
| `data/piwm_dataset_combined_existing` | 33 | 13 | 33 | 94 | 33 | 4 | 0 | 历史 QA-pass utility split，不作为当前主表首选 |

### 2.1 `priority40_qareviewed_sample`

当前主表和端到端评估首选：

```text
data/piwm_dataset_priority40_qareviewed_sample_compact_v2_exact/
├── main_schema.jsonl              36
├── state_inference.jsonl          36
├── transition_modeling.jsonl      126
├── policy_preference.jsonl        36
└── _stats.json
```

覆盖：

- viewpoint：`salesperson_observable=18`，`surveillance_oblique=18`
- split：`train=9`，`dev=1`，`test=1`，`ood_product=20`，`ood_persona=5`
- 40 条人工审阅，36 pass，4 fail

### 2.2 `pilot30_with_continuations`

World Model 视觉证据首选：

```text
data/piwm_dataset_pilot30_with_continuations_compact_v2/
├── main_schema.jsonl                  24
├── state_inference.jsonl              24
├── transition_modeling.jsonl          66
├── policy_preference.jsonl            24
├── world_model_continuation.jsonl     44
├── future_verification.jsonl          84
├── _stats.json
└── _future_verification_stats.json
```

关键口径：

- `require_qa_pass=true`
- `require_continuation=true`
- continuation QA pass：44
- continuation roles：best 21 / worst 23
- future verification：44 positive / 40 negative
- `visible_reaction` 与 `visual_state` 共享三轴：`engagement_pattern_change`、`gaze_and_attention_change`、`body_and_hands_change`

## 3. Synthetic Train Splits Pending Visual QA

这些数据可以用于赶训练、工程验证、扩 SFT，但不能写成 manually verified / QA-pass。

| Dataset | Loaded parent | Skipped | State | Transition | Policy | SFT export | 用途 |
|---|---:|---:|---:|---:|---:|---|---|
| `data/piwm_dataset_priority280_unreviewed` | 260 | 0 | 260 | 927 | 260 | `ms_swift_priority280_unreviewed` 1187 examples | 旧主训练 split |
| `data/piwm_dataset_priority500_partial_unreviewed` | 376 | 8 | 376 | 1391 | 376 | `ms_swift_priority500_partial_unreviewed` 1767 examples | warmup 训练 |
| `data/piwm_dataset_priority500_unreviewed` | 427 | 81 | 427 | 1547 | 427 | `ms_swift_priority500_unreviewed` 1974 examples | priority500 v2 训练 |
| `data/piwm_dataset_priority1000_unreviewed` | 543 | 465 | 543 | 2011 | 543 | `ms_swift_priority1000_unreviewed` 2554 examples | 旧字段版主训练 split，保留回滚 |
| `data/piwm_dataset_priority1000_unreviewed_compact_v2` | 543 | 465 | 543 | 2011 | 543 | `ms_swift_priority1000_compact_v2` 2554 examples | `PIWM-Train-Synth-v1` backing source；不要作为公开数据名 |
| `data/official/piwm_train_synth_v2` | 543 | 465 | 543 | 2011 | 543 | `data/official/ms_swift/piwm_train_synth_v2.jsonl` 2554 examples | `PIWM-Train-Synth-v2`；schema v2.2 独立导出，不新增视频 |
| `data/official/piwm_policy_slice_v2` | 864 scenarios | - | - | - | - | `policy_manifest.jsonl` | explicit candidate-rule policy manifest；用于动作均衡和生成，不是视频数据 |

### 3.1 Current Official Train Entrypoint

当前最有价值的训练输入：

```text
data/official/ms_swift/piwm_train_synth_v2.jsonl
```

当前主表样本入口：

```text
data/official/piwm_train_synth_v1/main_schema.jsonl
data/official/piwm_train_synth_v2/main_schema.jsonl
```

规模：

- 2554 SFT examples
- 543 loaded parent
- 2011 transition rows
- 543 policy rows retained in dataset; current ms-swift SFT export uses perception + deliberation rows
- 543 state rows
- schema：`visual_state.summary / engagement_pattern / gaze_and_attention / body_and_hands` + `dialogue_act / act_params.supporting_acts / candidate_action_specs / best_action_spec / next_state_by_action_v2`，并保留 `best_action / candidate_actions / next_state_by_action / best_action_realization` 兼容字段
- 字段语义：`visual_state` 使用 product-specific scene/focus，`bdi.belief` 使用 cue-aware belief，`best_action_realization` 使用 product-specific utterance / physical action / timing / rationale
- 主体口径：该数据集保留真人导购逻辑；target terminal 数据集后续单独建设。

当前 best DialogueAct 分布偏斜，作为训练口径必须说明：

| DialogueAct | Count |
|---|---:|
| `Inform` | 407 |
| `Elicit` | 69 |
| `Hold` | 59 |
| `Reassure` | 8 |
| `Recommend` | 0 |
| `Greet` | 0 |

因此，`PIWM-Train-Synth-v1` 适合训练当前 synthetic 行为策略，不适合作为“六动作均衡 policy benchmark”。后续需要 balanced policy slice 或 target terminal dataset 来补 `Recommend(pressure=soft)`、`Greet`、更多 `Reassure` 正样本。

v2.2 re-derived policy best 分布另算，不覆盖 legacy `best_action`：

| DialogueAct | Count |
|---|---:|
| `Elicit` | 252 |
| `Recommend` | 119 |
| `Inform` | 105 |
| `Reassure` | 42 |
| `Hold` | 25 |
| `Greet` | 0 |

来源：

| Source archive | Loaded parent |
|---|---:|
| `Archive_generated_priority24` | 24 |
| `Archive_generated_priority256` | 235 |
| `Archive_generated_priority500_new_after280` | 168 |
| `Archive_generated_priority1000_remaining_after500` | 116 |

失败/缺失：

- `FrameNotFoundError=464`
- `JSONDecodeError=1`
- 主要原因是 Kling API 耗尽后剩余 prompt 未生成视频或未抽帧。

## 4. ms-swift Export Registry

| Export | Rows | 推荐状态 |
|---|---:|---|
| `data/official/ms_swift/piwm_train_full_v2.jsonl` | 3339 | 下一次 fresh 8-GPU 重训入口：perception + deliberation + action-selection + continuation/FV |
| `data/official/ms_swift/piwm_train_synth_v1.jsonl` | 2554 | 轻量主训练输入：perception + deliberation |
| `data/piwm_results/ms_swift_priority1000_compact_v2_action/ms_swift_sft.jsonl` | 3097 | 主训练 + action-selection |
| `data/piwm_results/ms_swift_world_model_compact_v2_action/ms_swift_sft.jsonl` | 242 | WorldModel/FV + action-selection |
| `data/piwm_results/ms_swift_priority1000_compact_v2/ms_swift_sft.jsonl` | 2554 | 当前正式主训练源导出 |
| `data/piwm_results/ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl` | 2554 | 旧字段版回滚输入 |
| `data/piwm_results/ms_swift_priority500_unreviewed/ms_swift_sft.jsonl` | 1974 | 可复现实验 / fallback |
| `data/piwm_results/ms_swift_priority500_partial_unreviewed/ms_swift_sft.jsonl` | 1767 | warmup 历史输入 |
| `data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl` | 1321 | v2 主表 checkpoint 输入 |
| `data/piwm_results/ms_swift_priority280_unreviewed/ms_swift_sft.jsonl` | 1187 | 旧训练输入 |
| `data/piwm_results/ms_swift_pilot30_full/ms_swift_sft.jsonl` | 134 | pilot continuation SFT |
| `data/piwm_results/ms_swift_pilot30_future_verification_observed/ms_swift_sft.jsonl` | 218 | Future Verification 训练输入 |
| `data/piwm_results/ms_swift_pilot30_with_future_verification/ms_swift_sft.jsonl` | 218 | Future Verification 历史导出 |
| `data/piwm_results/ms_swift_pilot30/ms_swift_sft.jsonl` | 8 | smoke，不作论文结果 |

## 5. Current Checkpoint Mapping

| Checkpoint | Training data | 当前用途 |
|---|---|---|
| `data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834` | `data/official/ms_swift/piwm_train_full_v2.jsonl`，3339 examples | 当前最新有效 checkpoint；优先用于后续 full_v2 eval / demo |
| `data/piwm_results/ms_swift_sft_qwen25vl7b_enriched_official_v1_len8192_8gpu/v0-20260502-090632/checkpoint-638` | `data/official/ms_swift/piwm_train_synth_v1.jsonl`，2554 examples | enriched official v1 checkpoint；保留作为轻量主训练对照 |
| `data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638` | `ms_swift_priority1000_unreviewed` 2554 examples | 历史主结果候选；已被 full_v2 取代 |
| `data/piwm_results/ms_swift_sft_qwen25vl7b_priority500_v2_8gpu/v0-20260501-075304/checkpoint-492` | `ms_swift_priority500_unreviewed` 1974 examples | 中间 checkpoint，主 eval 曾因无进度被中止 |
| `data/piwm_results/ms_swift_sft_qwen25vl7b_priority500_partial_warmup_8gpu/v0-20260501-072942/checkpoint-220` | `ms_swift_priority500_partial_unreviewed` 1767 examples | warmup checkpoint |
| `data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660` | `ms_swift_sprint_combined` 1321 examples | v2 主表 checkpoint |
| `data/piwm_results/ms_swift_sft_qwen25vl7b_future_verification_observed_4gpu/v0-20260501-043301/checkpoint-162` | `ms_swift_pilot30_future_verification_observed` 218 examples | Future Verification checkpoint |

## 6. Queue / Generation Artifacts

这些不是训练数据本身，而是生成队列、QA 抽样或失败重试入口。

| Path | 状态 |
|---|---|
| `data/priority_generation_queue/prompt_index_priority500_missing_retry.jsonl` | priority500 缺失视频待补队列；Kling API 耗尽前未跑 |
| `data/priority_generation_queue/priority500_missing_video_ids.txt` | priority500 缺失视频 ID 列表 |
| `data/priority_generation_queue/prompt_index_priority1000_remaining_after500.jsonl` | priority1000 后半队列；只生成出 116 loaded parent |
| `data/priority_generation_queue/qa_review_priority280_stratified40/` | priority280 的 40 条人工 QA contact sheet |
| `data/priority_generation_queue/qa_review_priority500_stratified120/` | priority500 QA 抽样目录；如未完成人工审阅，不得写成 QA-pass |

## 7. Historical / Diagnostic-Only Data

以下目录保留复现价值，但不作为当前主结果入口。

| Path | 说明 |
|---|---|
| `data/piwm_dataset_pilot` | 早期 pilot，已被 `pilot30_with_continuations` 覆盖 |
| `data/piwm_dataset_pilot30` | 早期 pilot30，无完整 continuation |
| `data/piwm_dataset_pilot30_pathA` | Path A 过渡数据 |
| `data/piwm_dataset_pilot30_smoke*` | smoke / retry 数据 |
| `data/piwm_dataset_viewpoint_review` | viewpoint prompt 验证集 |
| `data/piwm_results/*smoke*` | 训练/解析器 smoke，不写成最终模型指标 |
| `data/piwm_results/dpo_adapter_smoke*` | DPO adapter smoke；DPO 当前暂停 |

## 8. File Placement Rules

- 大数据、视频、checkpoint 只放远端 `/root/lanyun-fs/ProactiveIntentWorldModel`。
- 本地仓库只保留代码、文档、小型 JSON/Markdown 结果和必要样例。
- 目录职责和 official symlink 关系见 [project_directory_map.md](project_directory_map.md)。
- 不删除历史目录，除非先生成删除清单并单独确认。
- 新训练前优先使用 `data/official/ms_swift/piwm_train_full_v2.jsonl`；如果显存或时间不够，再回退到轻量 `piwm_train_synth_v1.jsonl`。
- 新评估默认使用 `priority40_qareviewed_sample`，除非明确在做 World Model/Future Verification。

## 9. 当前下一步

1. 不再自动跑 Kling；API 已耗尽。
2. 若继续提升主表，先修 action-selection prompt/parser/fallback，而不是扩视频。
3. 若需要更强评估可信度，优先人工 QA `priority500` 抽样到 80-120 条，而不是把 unreviewed split 写成 QA-pass。
4. 论文表格必须标出数据口径：QA-reviewed eval vs synthetic train vs diagnostic smoke。
