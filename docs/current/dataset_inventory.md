# PIWM Dataset Inventory

更新时间：2026-05-01 21:15 CST

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
| 正式数据集入口 | `data/official/` | PIWM v1 canonical aliases |
| 主 SFT 训练 | `data/official/ms_swift/piwm_train_synth_v1.jsonl` | `PIWM-Train-Synth-v1`，high-throughput synthetic train split，未人工视觉审阅 |
| 当前主 checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638` | ms-swift LoRA SFT，8 x 4090 |
| 主表 QA eval | `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl` | `PIWM-Eval-QA-v1`，QA-reviewed priority sample |
| 端到端 eval | `data/official/piwm_eval_qa_v1/state_inference.jsonl` | `PIWM-Eval-QA-v1`，QA-reviewed priority sample |
| World Model / continuation | `data/official/piwm_world_model_v1/` | `PIWM-WorldModel-v1`，QA-reviewed pilot continuation split |
| Future Verification | `data/official/piwm_world_model_v1/future_verification.jsonl` | `PIWM-FutureVerification-v1`，continuation-derived verification pairs |

禁止混用：

- `PIWM-Train-Synth-v1` 可以训练，但不能写成 QA-pass。旧名为 `priority1000_unreviewed`。
- `PIWM-Eval-QA-v1` 可以评估，但规模是 36 loaded parent，不是 full benchmark。旧名为 `priority40_qareviewed_sample`。
- `PIWM-WorldModel-v1` 是 World Model 视觉证据，不是主 SFT 规模来源。旧名为 `pilot30_with_continuations`。
- Kling API 已耗尽，所有 missing-video 队列只保留为待补，不自动生成。

## 1.1 Formal Dataset Names

| 正式名 | Canonical path | Source path | 角色 |
|---|---|---|---|
| `PIWM-Train-Synth-v1` | `data/official/piwm_train_synth_v1` | `data/piwm_dataset_priority1000_unreviewed` | 主 SFT 训练 |
| `PIWM-Eval-QA-v1` | `data/official/piwm_eval_qa_v1` | `data/piwm_dataset_priority40_qareviewed_sample` | 主表 / e2e QA 评估 |
| `PIWM-WorldModel-v1` | `data/official/piwm_world_model_v1` | `data/piwm_dataset_pilot30_with_continuations` | continuation / World Model 视觉证据 |
| `PIWM-FutureVerification-v1` | `data/official/piwm_world_model_v1/future_verification.jsonl` | `data/piwm_dataset_pilot30_with_continuations/future_verification.jsonl` | action-conditioned future verification |

正式名用于论文、汇报和新脚本；旧名仅作为 source path 或复现实验路径保留。

## 2. QA-Reviewed Evaluation / Evidence Sets

这些数据可以写成人工 QA-reviewed 或 QA-pass subset。

| Dataset | Loaded parent | Skipped | State | Transition | Policy | Continuation | Future Verification | 用途 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `data/piwm_dataset_priority40_qareviewed_sample` | 36 | 4 | 36 | 126 | 36 | 0 | 0 | 当前最干净的主评估集 |
| `data/piwm_dataset_pilot30_with_continuations` | 24 | 6 | 24 | 66 | 24 | 44 | 84 | World Model / Future Verification / qualitative evidence |
| `data/piwm_dataset_fix3_continuation_validation` | 2 | 1 | 2 | 4 | 2 | 2 | 0 | continuation prompt 修复验证，不作主表 |
| `data/piwm_dataset_combined_existing` | 33 | 13 | 33 | 94 | 33 | 4 | 0 | 历史 QA-pass utility split，不作为当前主表首选 |

### 2.1 `priority40_qareviewed_sample`

当前主表和端到端评估首选：

```text
data/piwm_dataset_priority40_qareviewed_sample/
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
data/piwm_dataset_pilot30_with_continuations/
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

## 3. Synthetic Train Splits Pending Visual QA

这些数据可以用于赶训练、工程验证、扩 SFT，但不能写成 manually verified / QA-pass。

| Dataset | Loaded parent | Skipped | State | Transition | Policy | SFT export | 用途 |
|---|---:|---:|---:|---:|---:|---|---|
| `data/piwm_dataset_priority280_unreviewed` | 260 | 0 | 260 | 927 | 260 | `ms_swift_priority280_unreviewed` 1187 examples | 旧主训练 split |
| `data/piwm_dataset_priority500_partial_unreviewed` | 376 | 8 | 376 | 1391 | 376 | `ms_swift_priority500_partial_unreviewed` 1767 examples | warmup 训练 |
| `data/piwm_dataset_priority500_unreviewed` | 427 | 81 | 427 | 1547 | 427 | `ms_swift_priority500_unreviewed` 1974 examples | priority500 v2 训练 |
| `data/piwm_dataset_priority1000_unreviewed` | 543 | 465 | 543 | 2011 | 543 | `ms_swift_priority1000_unreviewed` 2554 examples | 当前最大主训练 split |

### 3.1 Current Main Train Split

当前最有价值的训练输入：

```text
data/piwm_results/ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl
```

规模：

- 2554 SFT examples
- 543 loaded parent
- 2011 transition rows
- 543 policy rows
- 543 state rows

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
| `data/piwm_results/ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl` | 2554 | 当前主训练输入 |
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
| `data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638` | `ms_swift_priority1000_unreviewed` 2554 examples | 当前主结果候选 |
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
- 不删除历史目录，除非先生成删除清单并单独确认。
- 新训练前优先使用当前主训练输入 `ms_swift_priority1000_unreviewed`；不要回退到 smoke 数据。
- 新评估默认使用 `priority40_qareviewed_sample`，除非明确在做 World Model/Future Verification。

## 9. 当前下一步

1. 不再自动跑 Kling；API 已耗尽。
2. 若继续提升主表，先修 action-selection prompt/parser/fallback，而不是扩视频。
3. 若需要更强评估可信度，优先人工 QA `priority500` 抽样到 80-120 条，而不是把 unreviewed split 写成 QA-pass。
4. 论文表格必须标出数据口径：QA-reviewed eval vs synthetic train vs diagnostic smoke。
