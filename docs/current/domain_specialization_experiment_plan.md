# PIWM Domain Specialization Experiment Plan

更新时间：2026-05-17 CST

本文记录当前 “general retail guidance -> target frontcam smart vending” 的实验入口。它服务 EMNLP 方向的强主会叙事：当前不依赖新增 200 条视频，而是把 118 条已成片 target-frontcam 数据定位为低资源目标域专项适配与评测集。200 条 prompt-ready / video-pending 扩展样本只作为后续数据储备，不进入当前论文主结果口径。

## Dataset Roles

| Corpus | Official name | Path | Rows / examples | Role |
|---|---|---:|---:|---|
| General | `PIWM-Train-Synth-v2` | `data/official/ms_swift/piwm_train_synth_v2.jsonl` | 2554 examples | Stage-1 general retail guidance SFT |
| Target | `PIWM-Target-Frontcam-v1` | `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` | 708 examples | Stage-2 low-resource target-frontcam specialization |
| Target prompt-ready | `PIWM-Target-PromptReady-v1` | `data/official/piwm_target_promptready_v1/promptready_index.jsonl` | 318 records | Upstream target generation index; 200 video-pending |
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
| `checkpoint_general` | target test split | zero-shot target transfer | 30 target records passed project-lead QA after Codex visual QA |
| `checkpoint_target` | target test split | target specialization gain | blocked by training |
| `checkpoint_target` | `PIWM-Eval-QA-v1` | catastrophic forgetting check | blocked by training |
| `checkpoint_joint_general_target` | both eval sets | joint SFT ablation | blocked by training + QA |

Fixed eval entrypoints:

| Eval set | Path | Rows | Status |
|---|---|---:|---|
| target-frontcam test all | `data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_all.jsonl` | 180 | 30 target records project-lead QA pass; 2 warning flags retained |
| target-frontcam perception | `data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_perception.jsonl` | 30 | same as above |
| target-frontcam deliberation | `data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_deliberation.jsonl` | 120 | same as above |
| target-frontcam action selection | `data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_action_selection.jsonl` | 30 | same as above |
| general QA all | `data/official/domain_specialization_eval_v1/general_qa_all.jsonl` | 162 | QA-reviewed pass subset |

Build command:

```bash
python3 -m scripts.build_domain_specialization_eval_sets
```

Result aggregation after checkpoint evaluation:

```bash
python3 -m scripts.summarize_domain_specialization_results
```

## Target QA Review Queue

The current target-domain test candidates are staged for manual review here:

```text
data/official/piwm_target_v1/qa_review_target30/qa_review_index.md
```

Generation command:

```bash
python3 -m scripts.build_target_frontcam_qa_review
```

Current artifacts:

| Artifact | Count / path |
|---|---:|
| Review rows | 30 |
| Contact sheets | 3 |
| Frames per row | 3 |
| Missing frames | 0 |
| Machine status before project-lead review | `synthetic_unreviewed` |
| Current merged status | 30 test records `qa_reviewed_pass`; 88 train records remain `synthetic_unreviewed` |

QA result:

| Item | Count |
|---|---:|
| Reviewed test records | 30 |
| QA-reviewed pass records | 30 |
| QA fail records | 0 |
| Warning records | 2 |
| Reviewed ms-swift eval rows | 180 |

Review output:

```text
data/official/piwm_target_v1/qa_review_target30/qa_review_results.md
```

Warning flags are retained for `target_piwm_797` and `target_piwm_815`; both remain pass because the customer identity and target-frontcam temporal state are still interpretable.

The QA promotion has been merged into the target dataset with:

```bash
python3 scripts/apply_target_frontcam_qa_review.py \
  --merge-target-data \
  --reviewer "Project lead human QA" \
  --reviewed-at 2026-05-17 \
  --review-type project_lead_human_review_after_codex_visual_qa
```

This updates `data/official/piwm_target_v1/main_schema.jsonl`, `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl`, and the fixed target eval files. It does not mark the 88 train records as QA-reviewed.

## Target Prompt-Ready Expansion

The lightweight `piwm` repository now contains 318 target records in `seed / manifest / labeled / prompts`:

| Layer | Count |
|---|---:|
| seed | 318 |
| manifest | 318 |
| labeled | 318 |
| prompts | 318 |
| video | 118 |

The new 200 records cover all six DialogueActs evenly at the best-action level after combining with the original 118:

| DialogueAct | Count |
|---|---:|
| Elicit | 53 |
| Greet | 53 |
| Hold | 53 |
| Inform | 53 |
| Reassure | 53 |
| Recommend | 53 |

Index:

```text
data/official/piwm_target_promptready_v1/promptready_index.jsonl
```

This is an upstream generation index, not an ms-swift multimodal training file. The 200 new rows are `video_pending` until Kling videos and sampled frames are generated.

## Current Status

Done:

- Imported 118 target-frontcam records from `/Users/mutsumi/Desktop/WorkSpace/piwm`.
- Extracted 354 target frames.
- Exported 708 target ms-swift examples.
- Exported 3262 mixed general+target ms-swift examples.
- Added explicit `response_id -> (act, params) -> action_key` mapping.
- Registered `target_frontcam` and `target_terminal_logic` in schema/documentation.
- Generated a 30-row target test QA review queue with contact sheets.
- Built fixed domain-specialization eval JSONL entrypoints for general QA and target-frontcam test rows.
- Completed project-lead QA review for the 30 target test records after Codex visual QA: 30 pass, 0 fail, 2 warning records; QA status is merged into target main schema and target ms-swift test rows.
- Expanded the lightweight `piwm` target generation corpus to 318 prompt-ready records: 118 video-backed and 200 video-pending.

Still missing for the current strong EMNLP main-conference claim:

- actual stage-1/stage-2 training runs on the server;
- target zero-shot and post-specialization evaluation;
- forgetting check on `PIWM-Eval-QA-v1`;

The current paper framing should not claim 300+ target videos. It should claim low-resource target specialization: broad general retail guidance learned from `PIWM-Train-Synth-v2`, then adapted with 88 target-frontcam training records and evaluated on 30 project-lead-QA-reviewed target records.
