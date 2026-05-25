# PIWM Target Frontcam 5-Act Split Rebalance

- qa_status: `new_5act_test_requires_independent_review_before_promotion`
- main_schema: `data/official/piwm_target_v1/main_schema.jsonl`
- ms_swift_rows: 708
- archived_legacy_reviewed_eval_dir: `data/official/domain_specialization_eval_v1/_legacy_wrong_5act`

## Test Best-Act Counts

| Act | Count |
|---|---:|
| `Elicit` | 6 |
| `Greet` | 6 |
| `Hold` | 6 |
| `Inform` | 6 |
| `Recommend` | 6 |

## Train Best-Act Counts

| Act | Count |
|---|---:|
| `Elicit` | 14 |
| `Greet` | 11 |
| `Inform` | 41 |
| `Reassure` | 17 |
| `Recommend` | 5 |

## QA Boundary

The new 5-act test split must be reviewed independently from the old split. Do not use the old reviewed eval files as current QA-reviewed target eval.
