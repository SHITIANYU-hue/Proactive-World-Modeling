# PIWM Target Frontcam Import Report

更新时间：2026-05-16 CST

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

The 30 test rows are only unreviewed in-domain eval candidates. They must pass manual QA before paper claims can call them QA-reviewed.

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

The importer extracts three frames per source video with OpenCV and writes them under:

```text
data/official/piwm_target_v1/frames/<session_id>/
```

## Current Red Lines

- Do not call `PIWM-Target-Frontcam-v1` QA-reviewed.
- Do not merge it silently into `PIWM-Train-Synth-v2`; keep it as a named target-domain corpus.
- Do not use the 30 test rows as final in-domain benchmark until manual QA is complete.
- Do not describe this as real-shooting data; it is imported synthetic target-frontcam data from the lightweight repo.
