# PIWM Target Frontcam Import Report

更新时间：2026-05-17 CST

本文记录轻量仓库 `guochenmeinian/piwm` 导入主项目 v2.2 的结果。该数据在论文口径中作为 target 域智能导购语料，区别于主项目 `PIWM-Train-Synth-v2` 的 general retail guidance 语料。

## Source

| Item | Value |
|---|---|
| Source repo | `/Users/mutsumi/Desktop/WorkSpace/piwm` |
| Imported dataset | `data/labeled/piwm_700.json` 到 `data/labeled/piwm_817.json` |
| Source count | 118 |
| Source view | 设备前置摄像头单视角 |
| Target official name | `PIWM-Target-Frontcam-v1` |
| Target official path | `data/official/piwm_target_v1` |
| Target ms-swift entrypoint | `data/official/ms_swift/piwm_train_target_specialization_v1.jsonl` |
| Mixed general+target entrypoint | `data/official/ms_swift/piwm_train_general_plus_target_v1.jsonl` |

## Action Mapping

`piwm` 的 `response_id` 不再作为自由字符串进入主项目，而是显式映射到 v2.2 canonical `(act, params)`，再生成稳定 action key。

| piwm response_id | v2.2 action spec | action key |
|---|---|---|
| `greet_open` | `Greet(phase=open)` | `Greet_4f8123f9f15e` |
| `greet_close` | `Greet(phase=close)` | `Greet_889a5021015d` |
| `elicit_need_focus_open` | `Elicit(openness=open, slot=need_focus)` | `Elicit_b1166d372e5e` |
| `inform_comparison_brief` | `Inform(content_type=comparison, depth=brief)` | `Inform_5ac252a82695` |
| `inform_demo_brief` | `Inform(content_type=demo, depth=brief)` | `Inform_5ff00ba15ca5` |
| `inform_attributes_brief` | `Inform(content_type=attributes, depth=brief)` | `Inform_24926eed1e21` |
| `inform_price_brief` | `Inform(content_type=price, depth=brief)` | `Inform_053014d173cc` |
| `recommend_soft` | `Recommend(target=item, pressure=soft)` | `Recommend_8d7f8993e333` |
| `recommend_firm` | `Recommend(target=item, pressure=firm)` | `Recommend_9ff23b139b07` |
| `reassure_time_wait` | `Reassure(focus=time, supporting_acts=[Hold(mode=ambient)])` | `Reassure_14e8d6fdd642` |
| `reassure_decision` | `Reassure(focus=decision)` | `Reassure_de423697f587` |
| `hold_silent` | `Hold(mode=silent)` | `Hold_eda24b4bb712` |
| `hold_ambient` | `Hold(mode=ambient)` | `Hold_e2721a9457de` |

Mapping source: `piwm_data/migration/piwm_response_mapping.py`.

## Export Results

| Artifact | Count |
|---|---:|
| main schema records | 118 |
| sampled frames | 354 |
| state inference rows | 118 |
| transition modeling rows | 472 |
| policy preference rows | 118 |
| ms-swift examples | 708 |
| mixed general+target examples | 3262 |

ms-swift task split:

| Task | Count |
|---|---:|
| perception | 118 |
| deliberation | 472 |
| action_selection | 118 |

Dataset split:

| Split | Count |
|---|---:|
| train | 88 |
| test | 30 |

The 30 test rows have now passed project-lead human QA after Codex visual QA. All 30 pass, with 2 warning flags retained for auditability. The reviewed rows have been merged back into the target main schema and target ms-swift export.

## Target QA Review Artifacts

The current manual-review queue has been generated from the 30 test rows:

| Artifact | Value |
|---|---|
| Review index | `data/official/piwm_target_v1/qa_review_target30/qa_review_index.md` |
| Machine-readable index | `data/official/piwm_target_v1/qa_review_target30/qa_review_index.json` |
| Review rows JSONL | `data/official/piwm_target_v1/qa_review_target30/qa_review_rows.jsonl` |
| Contact sheets | `target_frontcam_qa_sheet_00.jpg` to `target_frontcam_qa_sheet_02.jpg` |
| Rows staged | 30 |
| Rows with all sampled frames | 30 |
| Missing frames | 0 |
| Status | `project_lead_human_qa_completed_and_merged` |

Generation command:

```bash
python3 -m scripts.build_target_frontcam_qa_review
```

QA promotion and merge command:

```bash
python3 scripts/apply_target_frontcam_qa_review.py \
  --merge-target-data \
  --reviewer "Project lead human QA" \
  --reviewed-at 2026-05-17 \
  --review-type project_lead_human_review_after_codex_visual_qa
```

QA result:

| Item | Count |
|---|---:|
| reviewed test records | 30 |
| QA-reviewed pass records | 30 |
| QA fail records | 0 |
| warning records | 2 |
| reviewed ms-swift eval rows | 180 |

Reviewed eval entrypoint:

```text
data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_all.jsonl
```

The contact sheets are only review aids. The audited promotion step writes reviewed rows to QA artifacts and now also merges the 30 reviewed test records into `data/official/piwm_target_v1/main_schema.jsonl` and the target ms-swift export. The 88 train records remain `synthetic_unreviewed`.

## Best Act Distribution

| Act | Count |
|---|---:|
| Inform | 47 |
| Elicit | 20 |
| Greet | 17 |
| Reassure | 17 |
| Recommend | 11 |
| Hold | 6 |

This target set complements the general synthetic corpus, where `Greet` and `Recommend` are absent from legacy best-action labels. Because the target set has only 118 records, it improves action coverage but does not by itself balance the full merged corpus.

## Command

```bash
python3 -m scripts.import_piwm_target_dataset \
  --piwm-root /Users/mutsumi/Desktop/WorkSpace/piwm \
  --overwrite
```

Mixed-view joint SFT baseline:

```bash
python3 -m scripts.build_domain_specialization_dataset
```

Target test review queue:

```bash
python3 -m scripts.build_target_frontcam_qa_review
```

Domain-specialization eval entrypoints:

```bash
python3 -m scripts.build_domain_specialization_eval_sets
```

This creates:

| Eval file | Rows |
|---|---:|
| `data/official/domain_specialization_eval_v1/target_frontcam_test_all.jsonl` | 180 |
| `data/official/domain_specialization_eval_v1/target_frontcam_test_perception.jsonl` | 30 |
| `data/official/domain_specialization_eval_v1/target_frontcam_test_deliberation.jsonl` | 120 |
| `data/official/domain_specialization_eval_v1/target_frontcam_test_action_selection.jsonl` | 30 |
| `data/official/domain_specialization_eval_v1/general_qa_all.jsonl` | 162 |

Prompt-ready target expansion:

```bash
python3 -m scripts.generate_piwm_target_promptready_expansion
python3 -m scripts.build_piwm_target_promptready_index
```

Current prompt-ready status:

| Layer | Count |
|---|---:|
| seed | 318 |
| manifest | 318 |
| labeled | 318 |
| prompts | 318 |
| video | 118 |

The 200 new records are `video_pending`; they should not enter multimodal SFT until Kling videos and sampled frames are available.

The importer extracts three frames per source video with OpenCV and writes them under:

```text
data/official/piwm_target_v1/frames/<session_id>/
```

## Current Red Lines

- Do not call all of `PIWM-Target-Frontcam-v1` full-corpus QA-reviewed; only the 30-record test split is project-lead QA-reviewed.
- Do not merge it silently into `PIWM-Train-Synth-v2`; keep it as a named target-domain corpus.
- Do use the 30 test rows as the current QA-reviewed in-domain eval split; keep the warning flags visible and do not claim the 88 train records are QA-reviewed.
- Do not describe this as real-shooting data; it is imported synthetic target-frontcam data from the lightweight repo.
