# PIWM Domain Specialization Experiment Plan

更新时间：2026-05-16 CST

本文记录当前 “general retail guidance -> target frontcam smart vending” 的实验入口。它服务 EMNLP 方向的 domain-specialization 叙事，但当前 target 数据仍是 pilot 规模。

## Dataset Roles

| Corpus | Official name | Path | Rows / examples | Role |
|---|---|---:|---:|---|
| General | `PIWM-Train-Synth-v2` | `data/official/ms_swift/piwm_train_synth_v2.jsonl` | 2554 examples | Stage-1 general retail guidance SFT |
| Target | `PIWM-Target-Frontcam-v1` | `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` | 708 examples | Stage-2 target-frontcam specialization |
| Joint baseline | `PIWM-GeneralPlusTarget-v1` | `data/official/ms_swift/piwm_train_general_plus_target_v1.jsonl` | 3262 examples | Joint SFT ablation |

Config source:

```text
configs/domain_specialization_v1.json
```

## Training Design

```text
Stage 1:
Qwen/Qwen2.5-VL-7B-Instruct
  -> SFT on PIWM-Train-Synth-v2
  -> checkpoint_general

Stage 2:
checkpoint_general
  -> continued LoRA SFT on PIWM-Target-Frontcam-v1
  -> checkpoint_target

Baseline:
Qwen/Qwen2.5-VL-7B-Instruct
  -> joint LoRA SFT on general + target
  -> checkpoint_joint_general_target
```

LoRA default:

```text
r=16
alpha=32
target_modules=q_proj,k_proj,v_proj,o_proj
```

## Evaluation Matrix

| Checkpoint | Eval set | Purpose | Current status |
|---|---|---|---|
| `checkpoint_general` | `PIWM-Eval-QA-v1` | general performance after stage 1 | eval set exists |
| `checkpoint_general` | target test split | zero-shot target transfer | target split exists but unreviewed |
| `checkpoint_target` | target test split | target specialization gain | blocked by training + QA |
| `checkpoint_target` | `PIWM-Eval-QA-v1` | catastrophic forgetting check | blocked by training |
| `checkpoint_joint_general_target` | both eval sets | joint SFT ablation | blocked by training + QA |

## Current Status

Done:

- Imported 118 target-frontcam records from `/Users/mutsumi/Desktop/WorkSpace/piwm`.
- Extracted 354 target frames.
- Exported 708 target ms-swift examples.
- Exported 3262 mixed general+target ms-swift examples.
- Added explicit `response_id -> (act, params) -> action_key` mapping.
- Registered `target_frontcam` and `target_terminal_logic` in schema/documentation.

Still missing for a strong EMNLP main-conference claim:

- target corpus expansion from 118 to roughly 300+ records;
- manual QA of at least 30 target test rows;
- actual stage-1/stage-2 training runs on the server;
- target zero-shot and post-specialization evaluation;
- forgetting check on `PIWM-Eval-QA-v1`.

Because EMNLP 2026 ARR deadline is 2026-05-25 AoE, the current realistic paper framing is pilot domain specialization unless target expansion and QA can be completed immediately.
