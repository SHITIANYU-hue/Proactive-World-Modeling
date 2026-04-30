# Pilot30 Action-Continuation Review Report

更新时间：2026-04-30

## 1. 结论

Phase 7 Action-Continuation Layer 的 pilot 级闭环已经跑通：

- 48 条 continuation video 全部生成成功，无 Kling API 生成错误；
- 视觉 QA 后 44 条通过、4 条拒绝；
- 远端数据集 `data/piwm_dataset_pilot30_with_continuations/` 已构建成功；
- `world_model_continuation.jsonl` 从 0 行变为 44 行，可以支持第一版 visual-grounded world model caption objective。

当前结论不是“可以直接扩大到 1920 parent 全规模”，而是：

> PIWM 已经具备视觉级 action-conditioned future 的最小可训练数据形态。下一步应先用这 44 条跑训练入口 smoke，再修正弱动作 continuation prompt。

## 2. 远端产物位置

所有大文件均放在远端数据盘：

```text
/root/lanyun-fs/ProactiveIntentWorldModel/
├── Archive_generated_pilot30/
│   ├── piwm_*/video.mp4
│   ├── piwm_*/frames/
│   ├── piwm_*/continuations/*/video.mp4
│   ├── _continuation_visual_qa_summary.json
│   └── _continuation_review_sheet_*.jpg
└── data/piwm_dataset_pilot30_with_continuations/
    ├── main_schema.jsonl
    ├── state_inference.jsonl
    ├── state_inference_with_cue.jsonl
    ├── transition_modeling.jsonl
    ├── policy_preference.jsonl
    ├── world_model_continuation.jsonl
    └── _stats.json
```

本机只保留了小体积 review sheets：

```text
_remote_review_sheets/_continuation_review_sheet_00.jpg
...
_remote_review_sheets/_continuation_review_sheet_07.jpg
```

## 3. 生成与 QA 结果

### 3.1 Kling continuation generation

| 项目 | 数值 |
|---|---:|
| continuation prompt 总数 | 48 |
| 本机 smoke 已生成并同步 | 5 |
| 远端新生成 | 43 |
| 生成成功 video | 48 |
| 生成错误 | 0 |
| 每条 continuation 时长 | 5 秒 |
| 抽帧 | 3 帧：reaction onset / peak / settle |

### 3.2 视觉 QA

| 项目 | 数值 |
|---|---:|
| continuation 总数 | 48 |
| QA pass | 44 |
| QA fail | 4 |
| manual_review_required | 0 |

被拒绝的 4 条：

| continuation_id | 拒绝原因 |
|---|---|
| `piwm_59b32db5b6#best_A7_disengage` | 预期顾客 disengaged，但画面中顾客仍停留在商品/电脑区域，离开反应不充分 |
| `piwm_5da8b90e4a#best_A1_silent_observe` | 监控视角下 body trajectory 不清楚，无法可靠证明 early browsing |
| `piwm_ab5eddbc60#worst_A1_silent_observe` | smoke 阶段已判 fail；静默观察被生成成主动互动/新主体混入 |
| `piwm_e888fbf565#best_A1_silent_observe` | 预期 silent observe，但 continuation 中出现导购/员工主体，动作连续性不干净 |

## 4. 最终数据集统计

远端构建命令：

```bash
cd /root/lanyun-fs/ProactiveIntentWorldModel
PATH=/root/lanyun-fs/venvs/piwm/bin:$PATH \
python -m piwm_data.build_dataset \
  --archive-root Archive_generated_pilot30 \
  --output-dir data/piwm_dataset_pilot30_with_continuations \
  --frame-sample 3 \
  --require-continuation
```

输出统计：

| JSONL | 行数 |
|---|---:|
| `main_schema.jsonl` | 24 |
| `state_inference.jsonl` | 24 |
| `state_inference_with_cue.jsonl` | 24 |
| `transition_modeling.jsonl` | 66 |
| `policy_preference.jsonl` | 24 |
| `world_model_continuation.jsonl` | 44 |

关键 `_stats.json` 指标：

| 指标 | 数值 |
|---|---:|
| `n_sessions_total` | 30 |
| `n_sessions_loaded` | 24 |
| `n_sessions_skipped` | 6 |
| `n_states_with_action_contrast` | 24 |
| `avg_actions_per_state` | 2.75 |
| `n_continuations_with_visual_qa_pass` | 44 |
| `n_negative_reward_continuations` | 12 |
| `best_worst_reward_gap_distribution.min` | 0.2 |
| `best_worst_reward_gap_distribution.median` | 0.25 |
| `best_worst_reward_gap_distribution.max` | 1.3 |

Viewpoint 覆盖：

| viewpoint | parent sessions |
|---|---:|
| `salesperson_observable` | 17 |
| `surveillance_oblique` | 7 |

Product 覆盖：

| product_category | parent sessions |
|---|---:|
| `apparel_premium` | 4 |
| `electronics_laptop` | 4 |
| `electronics_phone` | 4 |
| `footwear` | 6 |
| `home_appliance` | 2 |
| `jewelry` | 2 |
| `luxury_watch` | 2 |

## 5. 对 World Model claim 的意义

之前的数据监督只到：

```text
current frames + action -> next_state / reward text
```

现在新增了：

```text
current frames + action -> continuation reaction caption + continuation frames reference
```

这使 PIWM 的 world model claim 至少具备 pilot 级数据证据：

- 同一个 parent observation 下有多个 candidate action；
- 不同 action 对应不同文本 future；
- 通过 QA 的 continuation video 给出可见的 future reaction；
- 训练侧已有独立 `world_model_continuation.jsonl` 入口。

需要注意：第一版仍是 caption objective，不是像素生成 objective。论文表述应称为 visual-grounded action-conditioned future modeling，而不是强行声称模型能生成视频。

## 6. 暴露的问题

### 6.1 `A1_silent_observe` 是弱动作

`A1_silent_observe` 的 prompt 容易被 Kling 生成成“有人介入”或“顾客离开不清楚”。这是因为无动作本身难以可视化，模型会自发加入导购或额外人物来制造动态。

改进方向：

- negative constraints 明确加入 `no salesperson appears, no staff enters, no one approaches the shopper`；
- reaction timeline 强调顾客自主行为，而不是由外部互动触发；
- 对 `A1 -> disengaged` 使用更明确的可见动作：customer checks once, loses interest, walks away alone。

### 6.2 `A7_disengage` 的目标容易被误解

`A7_disengage` 描述的是导购退场，但 next_state 关注的是顾客是否 disengaged。当前有样本只生成了导购退场，顾客仍停留在商品前。

改进方向：

- continuation prompt 中把导购退场和顾客反应分开写；
- expected next state 为 `disengaged` 时必须出现 `customer turns away or leaves product area`；
- QA checklist 继续保留 `no_further_product_interaction`。

### 6.3 Surveillance 的可见性仍需保守

7 条 surveillance parent 进入最终数据，说明视角可用；但对 early browsing、continued hesitation 等微弱状态，3 帧有时不足以证明身体轨迹。

改进方向：

- surveillance continuation 可提高到 K=4 或 K=5；
- 对 movement-based next_state 使用更早/更晚的时间戳；
- 后续统计 strict visual future pass rate，不只统计 `overall_pass`。

## 7. 下一步

建议顺序：

1. 用 `data/piwm_dataset_pilot30_with_continuations/world_model_continuation.jsonl` 跑 caption objective smoke，验证第 4 头训练入口能读。
2. 修正 `A1_silent_observe` 和 `A7_disengage` continuation prompt。
3. 重新生成 5-10 条弱动作 continuation，确认失败模式下降。
4. 再决定是否扩大到 100 条 parent，而不是直接上 1920 parent。

## 8. Fix3 Targeted Validation

更新时间：2026-04-30

根据 pilot30 中暴露的弱动作失败模式，已做一次 3 条针对性 Kling 验证。目标不是扩大数据量，而是验证修正后的 `A1_silent_observe` / `A7_disengage` prompt 是否改善。

远端位置：

```text
/root/lanyun-fs/ProactiveIntentWorldModel/
├── Archive_generated_fix3/
│   ├── _fix3_contact_sheet.jpg
│   └── _fix3_qa_summary.json
└── data/piwm_dataset_fix3_continuation_validation/
    ├── main_schema.jsonl
    ├── transition_modeling.jsonl
    ├── policy_preference.jsonl
    ├── world_model_continuation.jsonl
    └── _stats.json
```

本机 review sheet：

```text
_remote_review_sheets_fix3/_fix3_contact_sheet.jpg
```

### 8.1 三条验证结果

| continuation_id | 目标 | QA | 结论 |
|---|---|---|---|
| `piwm_0b17a72423#worst_A1_silent_observe` | `A1_silent_observe -> disengaged` | pass | 修复有效：无导购介入，顾客离开商品区域 |
| `piwm_59b32db5b6#best_A7_disengage` | `A7_disengage -> disengaged` | pass | 修复有效：顾客停止与商品互动并离开/转离 |
| `piwm_5da8b90e4a#best_A1_silent_observe` | `A1_silent_observe -> early_browsing` | fail | 无导购介入已修正，但画面仍像近距离 active evaluation，且 surveillance body trajectory 不足 |

### 8.2 验证集统计

`data/piwm_dataset_fix3_continuation_validation/_stats.json`：

| 指标 | 数值 |
|---|---:|
| generated continuations | 3 |
| QA pass continuations | 2 |
| skipped parents | 1 |
| `world_model_continuation.jsonl` rows | 2 |
| negative reward continuations | 1 |

### 8.3 结论

本轮修复不是完全成功，但已经把最严重的问题从“无动作 prompt 被 Kling 自动生成导购介入”推进为：

```text
A1 -> disengaged: 可用
A7 -> disengaged: 可用
A1 -> early_browsing: 仍需继续修
```

下一轮应针对 `A1_silent_observe -> early_browsing` 单独改 prompt：

- 使用更宽的 surveillance shot；
- 明确 `keeps walking slowly / does not lean in / does not touch product`；
- 对 expected `early_browsing` 避免玻璃柜近距离手部操作；
- 必要时将该组合从主生产优先级降权。
