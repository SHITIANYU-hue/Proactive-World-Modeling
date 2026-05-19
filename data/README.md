# PIWM Data Directory

更新时间：2026-05-17

完整数据集总账见：

```text
docs/current/dataset_inventory.md
```

本文只给 `data/` 目录的快速入口。当前权威大数据源在远端数据盘：

```text
/root/lanyun-fs/ProactiveIntentWorldModel/data
```

本地 `data/` 是部分镜像，不保证包含全部 priority500 / priority1000 产物。

## 当前主入口

| 用途 | Path | 口径 |
|---|---|---|
| 正式数据集入口 | `data/official/` | PIWM canonical aliases；对外展示和新脚本默认只引用这里 |
| 正式数据集 manifest | `data/official/DATASET_MANIFEST.json` | 统一名称、来源路径、口径红线 |
| frozen 主训练主表 | `data/official/piwm_train_synth_v1/main_schema.jsonl` | 543 parent，保留真人导购逻辑，v1/v2.1 兼容入口 |
| schema v2.2 主训练主表 | `data/official/piwm_train_synth_v2/main_schema.jsonl` | 543 parent，含 `candidate_action_specs / best_action_spec / next_state_by_action_v2 / compatibility_tier` |
| frozen 主训练 JSONL | `data/official/ms_swift/piwm_train_synth_v1.jsonl` | 543 parent / 2554 examples，synthetic train，未人工视觉审阅 |
| schema v2.2 主训练 JSONL | `data/official/ms_swift/piwm_train_synth_v2.jsonl` | 543 parent / 2554 examples，schema v2.2 独立导出，不新增视频 |
| v2 policy manifest | `data/official/piwm_policy_slice_v2/policy_manifest.jsonl` | 864 explicit candidate-rule scenarios；不是视频数据 |
| target-frontcam 训练 JSONL | `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` | 118 records / 708 examples；30-record test split 已项目负责人 QA 复核，88 train records 仍未人工 QA |
| target-frontcam QA eval | `data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_all.jsonl` | 30 QA-reviewed target records / 180 eval rows |
| target prompt-ready 队列 | `data/official/piwm_target_promptready_v1/promptready_index.jsonl` | 318 prompt-ready records；200 条仍是 video-pending，不是已成片多模态数据 |
| 推荐 full-v2 训练 JSONL | `data/official/ms_swift/piwm_train_full_v2.jsonl` | 3339 examples，包含 action-selection、continuation、Future Verification |
| 当前主 checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834` | 8 x 4090 ms-swift LoRA SFT，训练入口为 `PIWM-Train-Full-v2` |
| 主评估 dataset | `data/official/piwm_eval_qa_v1/` | 36 QA-pass parent，126 transition |
| 主评估 ms-swift input | `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl` | 162 eval rows |
| World Model pilot | `data/official/piwm_world_model_v1/` | 24 QA-pass parent，44 continuation，84 future verification |

## 口径红线

- `priority*_unreviewed` 只能作为 backing/source path 或历史复现实验路径；公开口径写 `PIWM-Train-Synth-v1`。
- v2.2 数据格式公开口径写 `PIWM-Train-Synth-v2`，不要说成新增视频规模。
- policy 规则空间公开口径写 `PIWM-PolicySlice-v2`，不要说成 filmed dataset 或 QA-reviewed dataset。
- `PIWM-Train-Synth-v1` 不是 target terminal 数据集，不能把 `best_action_realization` 写成终端硬件采集动作。
- `PIWM-Target-Frontcam-v1` 只有 30-record test split 是项目负责人 QA-reviewed；不要把 118 全量写成 full human QA-reviewed corpus。
- `PIWM-Target-PromptReady-v1` 的 200 条 video-pending 不能计入 video-backed multimodal training scale。
- `priority40_qareviewed_sample` 只能作为 backing/source path；公开口径写 `PIWM-Eval-QA-v1`。
- `pilot30_with_continuations` 只能作为 backing/source path；公开口径写 `PIWM-WorldModel-v1` / `PIWM-FutureVerification-v1`。
- `*smoke*`、`dpo_adapter_smoke*`、早期 `pilot*` 只作诊断或历史复现。
- Kling API 已耗尽，missing-video queue 不应自动运行。

## 不要直接清理

不要手动删除以下目录，除非先生成清理清单并确认：

- `data/piwm_dataset_*`
- `data/piwm_results/ms_swift_*`
- `data/priority_generation_queue/`

这些目录之间有训练、评估和文档引用关系。
