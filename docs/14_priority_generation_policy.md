# Priority Generation Policy

更新时间：2026-04-30

## 0. 2026-04-30 晚间状态修订

本文件前半部分仍保留 priority selector 的设计逻辑。当前 live 状态已经从“只生成队列”推进到“已真实调用 Kling 生成 priority parent videos”：

| 资产 | 当前状态 | 口径 |
|---|---:|---|
| `Archive_generated_priority24` | 24 条 `video.mp4`，24 个 `qa_report.json`，0 个 `qa_manual_review.json` | high-throughput synthetic, pending visual QA |
| `Archive_generated_priority256` | 236 条 `video.mp4`，236 个 `qa_report.json`，0 个 `qa_manual_review.json` | high-throughput synthetic, pending visual QA |
| `data/piwm_dataset_priority280_unreviewed` | 260 loaded sessions，927 transition rows，260 policy rows | 可用于 sprint SFT 训练，不可写成 QA-pass |
| `data/piwm_results/ms_swift_priority280_unreviewed/ms_swift_sft.jsonl` | 1187 SFT examples | 可用于 high-throughput synthetic SFT |
| `data/piwm_dataset_priority40_qareviewed_sample` | 40 条分层人工 QA，36 pass / 4 fail | 第一批 priority QA pass-rate 估计 |

Kling API 额度从约 86% 降到约 46%，换来 260 条唯一 priority parent videos。后续策略改为：

1. 先消化现有 260 条：抽样人工 QA、训练、低显存 eval。
2. 不继续宽泛生成 parent videos。
3. 新 Kling 额度只用于补洞：失败 cue、缺失 continuation、或抽样 QA 后确定的高价值组合。

第一批 40 条 stratified contact-sheet QA 显示 pass rate 为 90%。失败集中在：

- `salesperson_observable` 下脸/视线被裁切；
- `approaching_counter` / `looking_around_for_help` 这类动态 cue 在 3 帧中证据不足。

统一口径：

```text
priority280 是 high-throughput generated training split：
已完成视频生成、抽帧、文件级 QA 和 schema 入库；
尚未完成人工 visual QA；
因此可用于赶训练，不能写成 QA-pass / manually verified 数据。
```

## 1. 为什么需要这个策略

Kling API 和远端存储都不是无限资源。PIWM 后续不能按 1920 个 scenario 平铺生成，而应先生成最能支撑 World Model claim 的样本。

优先级原则：

```text
先生成 action 对照最强、负干预最清楚、视觉 QA 风险可控、覆盖仍然足够的样本。
```

这不是替代全量数据集，而是 API 受限时的第一批生产策略。

## 2. 选择器与本地队列

代码入口只生成 manifest，不调用 Kling，不生成视频。当前推荐保留两档：

- `priority24`：Kling API 很紧时先跑的最小高价值批；
- `priority64`：第一批主生产队列。

```bash
python3 -m scripts.priority_scenario_selector \
  --limit 64 \
  --out data/priority_generation_queue/scenario_manifest_priority64.jsonl \
  --all-out data/priority_generation_queue/scenario_manifest_priority_all.jsonl \
  --stats-out data/priority_generation_queue/_scenario_stats_priority64.json \
  --seed 20260430
```

如果 API 额度更紧，先用 24 条：

```bash
python3 -m scripts.priority_scenario_selector \
  --limit 24 \
  --out data/priority_generation_queue/scenario_manifest_priority24.jsonl \
  --all-out data/priority_generation_queue/scenario_manifest_priority_all_from24run.jsonl \
  --stats-out data/priority_generation_queue/_scenario_stats_priority24.json \
  --seed 20260430
```

随后把 manifest 转成 Kling-ready prompt queue：

```bash
python3 -m scripts.prompt_builder \
  --manifest data/priority_generation_queue/scenario_manifest_priority64.jsonl \
  --out-root Archive_prompts_priority64 \
  --index-out data/priority_generation_queue/prompt_index_priority64.jsonl \
  --overwrite
```

24 条队列对应：

```bash
python3 -m scripts.prompt_builder \
  --manifest data/priority_generation_queue/scenario_manifest_priority24.jsonl \
  --out-root Archive_prompts_priority24 \
  --index-out data/priority_generation_queue/prompt_index_priority24.jsonl \
  --overwrite
```

## 3. 评分逻辑

每个 scenario 会被补上：

```json
"priority": {
  "score": 17.9,
  "reasons": [
    "negative_reward_contrast",
    "reward_gap=1.30",
    "strict_next_state_contrast=3",
    "includes_A3_strong_recommend"
  ],
  "metrics": {
    "reward_gap": 1.3,
    "has_negative_reward": true,
    "n_unique_next_states": 3,
    "strict_next_state_contrast": true,
    "worst_action": "A3_strong_recommend"
  }
}
```

高优先级样本通常满足：

- 同一 current state 下有 `reward < 0` 的候选动作；
- best action 与 worst action 的 reward gap 大；
- 不同 action 会导向不同 `next_state`；
- 候选动作里包含 `A3_strong_recommend` 这类高风险负干预；
- 候选动作里包含 `A1_silent_observe` 这类静默/非干预对照；
- state 属于 `high_hesitation`、`active_evaluation`、`ready_to_decide`、`early_browsing` 这类主线状态。

## 4. 覆盖约束

为避免“所有 API 都烧在同一个 cue 上”，选择器同时施加覆盖约束：

- 默认 viewpoint 比例：`salesperson_observable : surveillance_oblique = 75 : 25`
- 64 条默认选择时，每个 cue 至少 3 条；
- 每个 product 至少 3 条；
- 每个 persona 至少 4 条；
- `dev/test/ood_product/ood_persona` 至少保留少量样本；
- 每个 cue 默认有上限，避免 `long_dwell_with_price_check` 等高分 cue 挤占全部名额。

## 5. 当前本地队列结果（历史队列设计）

已在本地仓库实际落盘 manifest 和 prompt queue。注意：本节描述的是 selector/prompt queue 的静态设计；截至 2026-04-30 晚，远端已经基于 priority 队列生成了 260 条 parent videos，见 §0。

64 条 priority manifest：

| 指标 | 数值 |
|---|---:|
| selected scenarios | 64 |
| salesperson / surveillance | 48 / 16 |
| negative reward contrast | 61 / 64 |
| strict next-state contrast | 64 / 64 |
| includes `A3_strong_recommend` | 61 / 64 |
| includes `A1_silent_observe` | 64 / 64 |
| reward gap median | 1.1 |
| reward gap max | 1.3 |

Cue 覆盖：

| cue | count |
|---|---:|
| `long_dwell_with_price_check` | 9 |
| `repeated_product_handling` | 9 |
| `comparing_two_products` | 9 |
| `asking_companion_opinion` | 9 |
| `trying_on_or_testing` | 9 |
| `checking_phone_likely_research` | 7 |
| `approaching_counter` | 3 |
| `brief_glance_walking_past` | 3 |
| `looking_around_for_help` | 3 |
| `no_eye_contact_avoidant` | 3 |

这个分布符合“重要优先但不完全牺牲覆盖”的目标。

24 条 priority manifest：

| 指标 | 数值 |
|---|---:|
| selected scenarios | 24 |
| salesperson / surveillance | 18 / 6 |
| negative reward contrast | 22 / 24 |
| strict next-state contrast | 24 / 24 |
| includes `A3_strong_recommend` | 22 / 24 |
| includes `A1_silent_observe` | 24 / 24 |
| reward gap median | 1.1 |
| reward gap max | 1.3 |

Prompt queue：

| 队列 | manifest | prompt index | prompt root |
|---|---|---|---|
| priority24 | `data/priority_generation_queue/scenario_manifest_priority24.jsonl` | `data/priority_generation_queue/prompt_index_priority24.jsonl` | `Archive_prompts_priority24/` |
| priority64 | `data/priority_generation_queue/scenario_manifest_priority64.jsonl` | `data/priority_generation_queue/prompt_index_priority64.jsonl` | `Archive_prompts_priority64/` |

本地 smoke：

```bash
python3 -m scripts.priority_scenario_selector \
  --limit 4 \
  --out /tmp/piwm_priority_smoke_manifest.jsonl \
  --all-out /tmp/piwm_priority_smoke_all.jsonl \
  --stats-out /tmp/piwm_priority_smoke_stats.json \
  --seed 20260430

python3 -m scripts.prompt_builder \
  --manifest /tmp/piwm_priority_smoke_manifest.jsonl \
  --out-root /tmp/piwm_priority_smoke_prompts \
  --index-out /tmp/piwm_priority_smoke_prompt_index.jsonl \
  --overwrite
```

另外检查了 24/64 两档：manifest 行数、prompt index 行数、prompt 文件存在性、`priority` 字段、viewpoint 合法性、prompt forbidden-label hits 均通过。

## 6. 下一步生产顺序

远端继续时从 prompt queue 开始，先不要扩全量。

推荐顺序：

1. 同步本地 `data/priority_generation_queue/` 与 `Archive_prompts_priority24/` 或 `Archive_prompts_priority64/` 到远端。
2. 如果 Kling API 很紧，先跑 `Archive_prompts_priority24/`；否则跑 `Archive_prompts_priority64/`。
3. 先跑 parent videos，不立刻跑 continuation。
4. 对 parent 做 contact sheet QA。
5. 只对 QA-pass parent 生成 best/worst continuation。
6. 如果中途限流，则按 `data/priority_generation_queue/scenario_manifest_priority64.jsonl` 中的 `priority.score` 顺序截断。

远端 parent 生产命令模板：

```bash
python3 -m scripts.run_kling_batch \
  --prompt-index data/priority_generation_queue/prompt_index_priority24.jsonl \
  --out-root Archive_generated_priority24 \
  --summary-out data/priority_generation_queue/kling_batch_priority24_summary.json
```

或：

```bash
python3 -m scripts.run_kling_batch \
  --prompt-index data/priority_generation_queue/prompt_index_priority64.jsonl \
  --out-root Archive_generated_priority64 \
  --summary-out data/priority_generation_queue/kling_batch_priority64_summary.json
```

这些命令需要在远端 Kling 环境变量配置好后再执行。

## 7. 当前不做（状态已被 §0 修订）

- 不继续宽泛调用 Kling；
- 不把 `Archive_generated_priority24/` 或 `Archive_generated_priority256/` 写成 QA-pass；
- 不在本机保存新视频；
- 不跑全量测试；
- 不直接扩到 1920 parent；
- 不在未抽样 QA 前继续烧 parent video 额度。

## 8. Parent QA contact sheet 后处理

生成完成后，先抽帧，再只用本地已生成的 archive 做 QA 审阅图和待填模板；这个步骤不调用 Kling、不生成新视频。

priority24：

```bash
python3 -m scripts.extract_frames \
  --archive-root Archive_generated_priority24 \
  --index-out data/priority_generation_queue/frame_extract_priority24.jsonl

python3 -m scripts.make_contact_sheets \
  --archive-root Archive_generated_priority24 \
  --output-dir data/priority_generation_queue/qa_review_priority24
```

priority64：

```bash
python3 -m scripts.extract_frames \
  --archive-root Archive_generated_priority64 \
  --index-out data/priority_generation_queue/frame_extract_priority64.jsonl

python3 -m scripts.make_contact_sheets \
  --archive-root Archive_generated_priority64 \
  --output-dir data/priority_generation_queue/qa_review_priority64
```

`scripts.make_contact_sheets` 会输出：

- `contact_sheet_*.jpg`：人工快速看 cue/viewpoint/frame 的审阅图；
- `contact_sheet_index.json`：机器可读索引；
- `contact_sheet_index.md`：人工审阅入口；
- `qa_manual_review_templates/*.qa_manual_review.json`：待填模板，填完后按 index 里的 `manual_review_target` 放回对应 session 的 `qa_manual_review.json`。

轻量 smoke：

```bash
python3 -m scripts.make_contact_sheets \
  --archive-root Archive_generated_priority24 \
  --output-dir /tmp/piwm_priority24_contact_sheet_smoke

python3 -m pytest piwm_data/tests/test_make_contact_sheets.py
```
