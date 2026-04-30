# Priority Generation Policy

更新时间：2026-04-30

## 1. 为什么需要这个策略

Kling API 和远端存储都不是无限资源。PIWM 后续不能按 1920 个 scenario 平铺生成，而应先生成最能支撑 World Model claim 的样本。

优先级原则：

```text
先生成 action 对照最强、负干预最清楚、视觉 QA 风险可控、覆盖仍然足够的样本。
```

这不是替代全量数据集，而是 API 受限时的第一批生产策略。

## 2. 选择器

代码入口：

```bash
python3 -m scripts.priority_scenario_selector \
  --limit 64 \
  --out data/scenario_manifest_priority64.jsonl \
  --all-out data/scenario_manifest_priority_all.jsonl \
  --stats-out data/_scenario_stats_priority64.json \
  --seed 20260430
```

该命令只生成 manifest，不调用 Kling，不生成视频。

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

## 5. 当前 dry check 结果

仅在 `/tmp` 做过轻量 dry check，没有生产数据。

64 条 priority manifest 的检查结果：

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

## 6. 下一步生产顺序

等用户确认后再执行，不自动生产。

推荐顺序：

1. 在远端数据盘运行 priority selector，产出 `data/scenario_manifest_priority64.jsonl`。
2. 用 `scripts.prompt_builder` 生成 `Archive_prompts_priority64/`。
3. 先跑 parent videos，不立刻跑 continuation。
4. 对 parent 做 contact sheet QA。
5. 只对 QA-pass parent 生成 best/worst continuation。
6. 如果 Kling API 更紧张，则按 `priority.score` 从高到低进一步截断，例如先跑 top 24 或 top 32。

## 7. 当前不做

- 不调用 Kling；
- 不生成 `Archive_generated_priority64/`；
- 不在本机保存新视频；
- 不跑全量测试；
- 不直接扩到 1920 parent。
