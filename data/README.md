# PIWM Data Directory

更新时间：2026-05-01

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
| 正式数据集入口 | `data/official/` | PIWM v1 canonical aliases |
| 正式数据集 manifest | `data/official/DATASET_MANIFEST.json` | 统一名称、来源路径、口径红线 |
| 主训练 JSONL | `data/official/ms_swift/piwm_train_synth_v1.jsonl` | 543 parent / 2554 examples，synthetic train，未人工视觉审阅 |
| 当前主 checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638` | 8 x 4090 ms-swift LoRA SFT |
| 主评估 dataset | `data/official/piwm_eval_qa_v1/` | 36 QA-pass parent，126 transition |
| 主评估 ms-swift input | `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl` | 162 eval rows |
| World Model pilot | `data/official/piwm_world_model_v1/` | 24 QA-pass parent，44 continuation，84 future verification |

## 口径红线

- `priority*_unreviewed` 只能写成 synthetic train split / pending visual QA。
- `priority40_qareviewed_sample` 才是当前主 QA-reviewed eval subset。
- `pilot30_with_continuations` 是 World Model / Future Verification 小规模证据。
- `*smoke*`、`dpo_adapter_smoke*`、早期 `pilot*` 只作诊断或历史复现。
- Kling API 已耗尽，missing-video queue 不应自动运行。

## 不要直接清理

不要手动删除以下目录，除非先生成清理清单并确认：

- `data/piwm_dataset_*`
- `data/piwm_results/ms_swift_*`
- `data/priority_generation_queue/`

这些目录之间有训练、评估和文档引用关系。
