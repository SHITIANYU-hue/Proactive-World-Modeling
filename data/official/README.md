# PIWM Official Dataset Aliases

更新时间：2026-05-01

Kling API 已耗尽，本轮不会再新增视频。因此当前已落盘数据固定为 PIWM v1 正式数据集。

这里的目录是**正式名字入口**，不是重新复制数据。旧目录保留，`data/official/` 用软链接指向旧目录，避免训练脚本和结果文件失效。

## Canonical Names

| 正式名 | 本目录入口 | 来源目录 | 用途 | 口径 |
|---|---|---|---|---|
| `PIWM-Train-Synth-v1` | `piwm_train_synth_v1` | `../piwm_dataset_priority1000_unreviewed` | 主 SFT 训练 | synthetic train, pending visual QA |
| `PIWM-Eval-QA-v1` | `piwm_eval_qa_v1` | `../piwm_dataset_priority40_qareviewed_sample` | 主表与 e2e 评估 | QA-reviewed eval subset |
| `PIWM-WorldModel-v1` | `piwm_world_model_v1` | `../piwm_dataset_pilot30_with_continuations` | continuation / Future Verification | QA-reviewed pilot evidence |
| `PIWM-FutureVerification-v1` | `piwm_world_model_v1/future_verification.jsonl` | same | action-conditioned future verification | derived from QA-reviewed continuations |

## ms-swift Entrypoints

| 用途 | JSONL |
|---|---|
| 主 SFT 训练 | `ms_swift/piwm_train_synth_v1.jsonl` |
| 主 QA eval | `ms_swift/piwm_eval_qa_all_v1.jsonl` |
| World Model / FV SFT | `ms_swift/piwm_world_model_sft_v1.jsonl` |
| Future Verification eval | `ms_swift/piwm_future_verification_eval_all_v1.jsonl` |

## Reporting Rule

论文和汇报中优先使用正式名：

- 写 `PIWM-Train-Synth-v1`，不要写 `priority1000_unreviewed`。
- 写 `PIWM-Eval-QA-v1`，不要写 `priority40_qareviewed_sample`。
- 写 `PIWM-WorldModel-v1` / `PIWM-FutureVerification-v1`，不要写 `pilot30_with_continuations`。

旧名只在复现实验路径、脚本路径或附录 manifest 中出现。

## Red Lines

- `PIWM-Train-Synth-v1` 不是 QA-pass 数据。
- 不能写“1000 条视频已完成”；当前正式训练集是 543 loaded parent / 2554 SFT examples。
- `smoke`、`early pilot`、`DPO adapter`、`missing retry queue` 不属于正式数据集。
