# PIWM World Model Supervision Contract

更新时间：2026-04-29（Phase 2 数据契约升级后）

## 1. 核心判据

PIWM 要体现 World Model，训练不能只停留在：

```text
frames -> current_state
frames -> best_action
frames -> response text
```

这些任务最多证明模型能做状态识别或策略分类。

World Model 的最小训练判据是：

```text
same observation + same current state + different action -> different predicted future
```

在 PIWM 中，state 是顾客购买意图状态：

```text
s_t = (aida_stage, belief, desire, intention)
```

`latent_state` 只应作为行为子状态或中间标签，不应替代 AIDA stage。

## 2. 最小训练展开

一条 current-state video 不能只产生一条 `frames -> best_action`。它必须展开成：

```text
1 条 state_inference 样本
N 条 transition_modeling 样本
0-1 条 policy_preference pair
```

其中 transition 是核心：

```text
for action in candidate_actions:
    input  = sampled_frames + current_state + bdi + action
    target = next_aida_stage + next_bdi + next_state_subtype + risk + benefit + reward
```

## 3. 示例

同一组 sampled frames：

```text
target_cue = long_dwell_with_price_check
persona = price_sensitive_cautious
aida_stage = interest
state_subtype = high_hesitation
```

应展开为：

| action | next_state_subtype | reward | risk | benefit |
|---|---|---:|---|---|
| `A1_silent_observe` | `continued_hesitation` | 0.3 | low | medium |
| `A2_offer_value_comparison` | `engaged_dialogue` | 0.8 | low | high |
| `A3_strong_recommend` | `defensive_withdrawal` | -0.5 | high | low |
| `A4_open_with_question` | `engaged_dialogue` | 0.6 | low | high |

这组样本的证据价值在于：同一个状态下，动作改变未来。

## 4. 数据字段要求

`transition_modeling.jsonl` 至少保留：

```text
state_id
input.frames
input.current_state_summary.aida_stage
input.current_state_summary.bdi
input.current_state_summary.state_subtype
input.candidate_action
output.next_aida_stage
output.next_bdi
output.next_state_subtype
output.risk
output.benefit
output.reward
meta.parent_state_id
meta.rule_version
```

## 5. 统计指标

`_stats.json` 或额外统计文件应记录：

```text
n_transition_parent_states
n_transition_rows
avg_actions_per_state
n_states_with_action_contrast
n_states_without_action_contrast
```

`n_states_with_action_contrast` 的定义：

> 同一 parent state 下至少两个 action 的 future 标签不同。

如果这个数很低，数据形式上像 transition modeling，实质上仍可能是反应式策略标注。

## 6. 与三套 JSONL 的关系

| JSONL | 训练能力 | World Model 证据 |
|---|---|---|
| `state_inference.jsonl` | state estimation | 否 |
| `transition_modeling.jsonl` | action-conditioned next-state prediction | 是，核心证据 |
| `policy_preference.jsonl` | action ranking / DPO | 间接证据，依赖 transition |

## 7. 失败模式

以下情况不能支撑 World Model claim：

- 只有 `frames -> best_action`；
- 每个 parent state 只有一条 transition；
- 不同 action 的 next state 全部相同；
- reward 没有来源，只是 magic number；
- candidate action 没有进入输入，只在输出里出现。

## 8. Definition of Done

| DoD | 验收 |
|---|---|
| WM-1 | 每个有效 parent state 至少 2 条 action-conditioned transition rows |
| WM-2 | `n_states_with_action_contrast` 被统计并进入 `_stats.json` |
| WM-3 | transition 输入显式包含 `candidate_action` |
| WM-4 | transition 输出包含 next AIDA / next BDI / risk / benefit / reward |
| WM-5 | policy preference pair 来自 highest-reward vs lowest-reward 候选动作 |

当前实现状态：

- `transition_modeling.jsonl` 已输出 `next_aida_stage`、`next_bdi`、`next_state_subtype`、`reward_components`；
- `_stats.json` 已输出 `n_transition_parent_states`、`avg_actions_per_state`、`n_states_with_action_contrast`、`n_states_without_action_contrast`；
- 这只是字段与统计契约完成，仍需要 Phase 3-5 产出非空 pilot 数据来验证视觉样本确实支撑这些标签。
