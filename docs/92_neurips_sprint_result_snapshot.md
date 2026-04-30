# NeurIPS Sprint Result Snapshot

- Generated / refreshed: `2026-04-30 20:50 CST`
- Source of truth: remote data disk `/root/lanyun-fs/ProactiveIntentWorldModel`
- Scope: generated data assets, ms-swift SFT status, and evaluation guardrails.
- Guardrail: this snapshot separates training data, QA-reviewed data, diagnostic artifacts, and real model metrics.

## Paper-Safe Summary

| Row | Status | Nature | N / Size | Metric | Notes |
|---|---|---:|---:|---|---|
| QA-reviewed pilot continuation subset | present | manually QA-reviewed synthetic pilot | 24 parent / 44 continuation | no model metric | Safe for qualitative examples and data-contract validation. |
| High-throughput synthetic train split | present | generated synthetic, file-level QA, pending visual QA | 260 parent / 1187 SFT examples | no model metric | Safe for sprint-scale SFT training; not safe to call QA-pass. |
| ms-swift SFT | complete | Qwen2.5-VL-7B-Instruct + LoRA | 1321 examples / 660 steps | train loss 0.0404377 | Real training run completed; no valid inference metric yet. |
| Priority QA sample | present | manually reviewed sample from priority split | 40 reviewed / 36 pass | pass rate 90% | Contact-sheet QA sample, not full priority280 QA. |
| MockVLM pipeline eval | present | diagnostic-only mock | 24 records | strategy accuracy 0.125 | Tests plumbing only; not a trained model result. |
| Rule-oracle diagnostic | present in older local artifact | metadata-assisted diagnostic | 24 records | not a real baseline | Do not label as zero-shot VLM performance. |
| Checkpoint smoke eval | complete | trained checkpoint inference, 3-frame low-pixel | 24 records | parse rate 1.0 | Valid multi-frame low-res tag-format smoke; not full-image benchmark. |

## Dataset Assets

| Dataset | Loaded | Skipped | State Rows | Transition Rows | Policy Rows | Continuation Rows | Reporting Tier |
|---|---:|---:|---:|---:|---:|---:|---|
| `data/piwm_dataset_priority280_unreviewed` | 260 | 0 | 260 | 927 | 260 | 0 | high-throughput synthetic train split, pending visual QA |
| `data/piwm_dataset_pilot30_with_continuations` | 24 | 6 | 24 | 66 | 24 | 44 | QA-reviewed pilot subset |
| `data/piwm_dataset_fix3_continuation_validation` | 2 | 1 | 2 | 4 | 2 | 2 | targeted QA validation |
| `data/piwm_dataset_combined_existing` | 33 | 13 | 33 | 94 | 33 | 4 | mixed historical QA-pass utility split |
| `data/piwm_dataset_priority40_qareviewed_sample` | 36 | 4 | 36 | 126 | 36 | 0 | QA-reviewed sample from priority split |

Priority split coverage:

- viewpoint: `salesperson_observable=192`, `surveillance_oblique=68`
- split: `train=199`, `dev=8`, `test=6`, `ood_product=26`, `ood_persona=21`
- product category: 8/8 categories covered

## ms-swift Training

| Field | Value |
|---|---|
| Framework | `ms-swift` |
| Model | `Qwen2.5-VL-7B-Instruct + LoRA` |
| Data | `data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl` |
| Examples | 1321 |
| GPUs | 4 x 4090 |
| Steps | 660 / 660 |
| Epoch | 2.0 |
| Runtime | 1653.8411 seconds |
| Train loss | 0.0404377 |
| Last-step loss | 0.0061066948 |
| Token accuracy | 0.9972322 |
| Last checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660` |

This is a real completed training run. It is not yet an evaluated model result.

## Evaluation Guardrails

- `pilot24_mock_pipeline_eval.json` is diagnostic-only. It validates parser / decision-loop plumbing.
- `sft_checkpoint_eval_balanced24.json` was the full-frame OOM attempt. Do not report it as 0% model performance.
- `sft_checkpoint_eval_balanced24_3frame_lowpix.json` has `parse_success=24/24`, `parse_rate=1.0`, and should be described as multi-frame low-res tag-format smoke only.
- External GPT/Gemini/Claude/Qwen zero-shot baselines are not available as real completed metrics in the current sprint snapshot.
- Missing metrics stay `unknown` / `pending`, not projected.

## Reporting Policy

- Use `QA-reviewed pilot subset` only for the 24 parent / 44 continuation manually reviewed data.
- Use `high-throughput synthetic train split, pending visual QA` for the 260 priority parent data.
- Use `sprint-scale ms-swift SFT completed` for the 660-step Qwen2.5-VL LoRA run.
- Do not write `full QA-pass dataset`, `manually verified 260 samples`, `real-store results`, or full-image `checkpoint accuracy` until those artifacts exist.
