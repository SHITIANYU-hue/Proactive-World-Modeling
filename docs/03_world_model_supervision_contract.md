# PIWM World Model Supervision Contract

更新时间：2026-04-30（Phase 7 Action-Continuation Layer 骨架后）

## 1. 核心判据

PIWM 要体现 World Model，训练不能只停留在：

```text
frames -> current_state
frames -> best_action
frames -> response text
```

这些任务最多证明模型能做状态识别或策略分类。

World Model 的文本级最小训练判据是：

```text
same observation + same current state + different action -> different predicted future
```

Phase 7 后增加视觉级判据：

```text
same observation + same current state + different action
  -> different textual future
  -> different visual continuation evidence
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
0-M 条 world_model_continuation 样本
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
| `transition_modeling.jsonl` | action-conditioned next-state prediction | 是，文本级核心证据 |
| `policy_preference.jsonl` | action ranking / DPO | 间接证据，依赖 transition |
| `world_model_continuation.jsonl` | action-conditioned future reaction caption | 是，视觉级核心证据 |

`world_model_continuation.jsonl` 不要求模型生成像素。第一版训练目标是 caption objective：

```text
input  = current_frames + candidate_action
target = reaction_caption + continuation_frames reference
```

其中 continuation frames 来自额外的 5 秒 action-continuation video，并通过 continuation QA gate 验证：

```text
reaction_visible
reaction_matches_expected_state
pre_action_continuity_pass
no_scene_change
no_new_subjects
```

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
| WM-6 | `world_model_continuation.jsonl` 可输出 action-conditioned continuation caption rows |
| WM-7 | continuation QA gate 能拒绝 reaction 不可见或不匹配 expected_state 的样本 |

当前实现状态：

- `transition_modeling.jsonl` 已输出 `next_aida_stage`、`next_bdi`、`next_state_subtype`、`reward_components`；
- `_stats.json` 已输出 `n_transition_parent_states`、`avg_actions_per_state`、`n_states_with_action_contrast`、`n_states_without_action_contrast`；
- Path A 已把 `A3_strong_recommend` / `A1_silent_observe` 等负干预纳入候选集，pilot30 重建后出现 13 条 negative reward transition；
- Phase 7.1/7.2 已完成 `ActionContinuation` schema、`reaction_templates.py`、`continuation_prompt_builder.py`、continuation QA gate 与 `world_model_continuation.jsonl` exporter；
- Phase 7.3 smoke 已完成：5 条 continuation 中 4 条视觉 QA pass，失败样本为 `A1_silent_observe -> disengaged` 被 Kling 生成成主动互动；
- Phase 7.4 pilot continuation 已在远端数据盘完成：48 条 continuation video 全部生成，4 条因 reaction/continuity 不可靠被 QA 拒绝，44 条进入 `world_model_continuation.jsonl`；
- 当前远端正式产物为 `/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_dataset_pilot30_with_continuations/`：
  - `main_schema.jsonl`: 24
  - `transition_modeling.jsonl`: 66
  - `policy_preference.jsonl`: 24
  - `world_model_continuation.jsonl`: 44
  - `n_continuations_with_visual_qa_pass`: 44
  - `n_negative_reward_continuations`: 12
- 下一步不是继续扩大生成，而是先审阅这 44 条 continuation 的失败/通过模式，决定是否修正 `A1_silent_observe`、`A7_disengage` 等 continuation prompt。
