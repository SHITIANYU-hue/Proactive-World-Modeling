# PIWM NeurIPS Sprint 实验结果速览

更新时间：2026-05-01 CST

本文只整理当前已经落盘的 sprint 实验事实，方便快速判断“已经能写什么、还缺什么”。核心来源包括 `docs/current/experiment_status_main_table_v2.md`、`RESEARCH_LOG.md`、`data/piwm_results/*.md`、`data/piwm_results/*.json` 以及 ms-swift summary JSON。

## 1. 当前一句话结论

主链路已经跑通：Qwen2.5-VL-7B-Instruct 经 ms-swift LoRA SFT 后，结构化输出、action-conditioned transition/reward 和 continuation caption 明显站住；真正限制端到端决策的是 current-state perception，尤其是 AIDA stage 与 candidate action set。

当前论文口径应保持为 **pilot-scale method evidence**，不能写成 full-scale benchmark。

## 2. Main Table v2 已完成什么

主表 v2 是当前最重要的冻结结果：

- 结果文件：`data/piwm_results/main_table_v2_full_midpix_results.md`
- JSON：`data/piwm_results/main_table_v2_full_midpix_results.json`
- 推理口径：3-frame mid-pixel，`image_limit=3`，`max_pixels=200704`，`max_new_tokens=128`
- 模型：zero-shot `Qwen2.5-VL-7B-Instruct` vs PIWM-SFT checkpoint `checkpoint-660`
- 评测行数：`pilot30_all_with_continuations=134`，`priority40_qareviewed_all=162`

| Eval set | Rows | Model | Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward | Caption |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot30_all_with_continuations | 134 | Qwen2.5-VL zero-shot | 0.552 | -- | -- | -- | 0.333 | 0.500 | 0.600 | 0.033 | 0.000 |
| pilot30_all_with_continuations | 134 | PIWM-SFT | 1.000 | 0.417 | 0.792 | 0.333 | 0.985 | 1.000 | 1.000 | 0.970 | 1.000 |
| priority40_qareviewed_all | 162 | Qwen2.5-VL zero-shot | 0.235 | -- | -- | -- | 0.211 | 0.553 | 0.289 | 0.000 | -- |
| priority40_qareviewed_all | 162 | PIWM-SFT | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | -- |

可以写成论文结果的点：

- **Structured parse**：PIWM-SFT 在两个 eval set 上都达到 `1.000` parse rate；zero-shot 只有 `0.552` / `0.235`。
- **Perception**：priority40 QA-reviewed 上较强，`stage=0.889`、`candidates=0.750`；pilot30 continuation set 上仍弱，`stage=0.417`、`candidates=0.333`。
- **Transition / reward**：SFT 后 rule-conditional `next_stage/risk/benefit/reward` 基本接近满分，pilot30 为 `0.985/1.000/1.000/0.970`，priority40 为全 `1.000`。
- **Caption**：pilot30 continuation caption 从 zero-shot `0.000` 到 PIWM-SFT `1.000`。注意它是语义 reaction caption，并保留 continuation frames 作为可审计证据，不是视频生成指标。

## 3. Ablation 已完成什么

### 3.1 Text-only inference ablation

文件：`data/piwm_results/ablation_text_only_results.md` / `.json`

同一 PIWM-SFT checkpoint 在推理时移除全部视觉帧，即 `image_limit=0`。

| Eval set | Rows | Condition | Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward | Caption |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot30_all_with_continuations | 134 | visual_3frame_midpix | 1.000 | 0.417 | 0.792 | 0.333 | 0.985 | 1.000 | 1.000 | 0.970 | 1.000 |
| pilot30_all_with_continuations | 134 | no_visual_frames | 1.000 | 0.333 | 0.042 | 0.042 | 0.955 | 1.000 | 1.000 | 0.970 | 1.000 |
| priority40_qareviewed_all | 162 | visual_3frame_midpix | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | -- |
| priority40_qareviewed_all | 162 | no_visual_frames | 1.000 | 0.111 | 0.111 | 0.111 | 1.000 | 1.000 | 1.000 | 1.000 | -- |

结论：视觉帧对 perception 是必要的；去掉视觉后 `score/candidates` 明显崩塌。但 transition/reward 仍高，因为这些任务输入中已有结构化 state/action 条件。

### 3.2 高像素 perception smoke

文件：`data/piwm_results/perception_highpix_smoke_results.md` / `.json`

高像素设置为 `max_pixels=401408`，主表 midpix 为 `200704`。

| Eval set | Model | Pixel | Rows | Parse | Stage | Score | Candidates |
|---|---|---|---:|---:|---:|---:|---:|
| pilot30_perception | PIWM-SFT | midpix | 24 | 1.000 | 0.417 | 0.792 | 0.333 |
| pilot30_perception | PIWM-SFT | highpix | 24 | 1.000 | 0.500 | 0.750 | 0.375 |
| priority40_perception | PIWM-SFT | midpix | 36 | 1.000 | 0.889 | 0.750 | 0.750 |
| priority40_perception | PIWM-SFT | highpix | 36 | 1.000 | 0.833 | 0.722 | 0.722 |

结论：高像素没有系统性解决 perception 短板。pilot30 有小幅反弹，但 priority40 略降，因此当前问题不只是 low-pixel artifact。

### 3.3 Frame-budget K=1/K=3/K=5

文件：`data/piwm_results/frame_budget_ablation_results.md`

评测对象是 `priority40_qareviewed_sample` perception rows，同一 PIWM-SFT checkpoint，同一 `max_pixels=200704`。

| K | Rows | Parse | Stage | Score | Candidates |
|---:|---:|---:|---:|---:|---:|
| 1 | 36 | 1.000 | 0.722 | 0.694 | 0.694 |
| 3 | 36 | 1.000 | 0.861 | 0.722 | 0.722 |
| 5 | 36 | 1.000 | 0.861 | 0.722 | 0.722 |

结论：K=3 明显优于 K=1，尤其是 AIDA stage；K=5 在当前样本和像素预算下没有继续提升。默认 K=3 可以解释为 onset / peak / resolution 的最小行为片段预算。

### 3.4 Future verification

文件：`data/piwm_results/future_verification_observed_results.md`

任务形式：

```text
current_frames + candidate_action + continuation_frames
-> match / mismatch + expected_next_state + visible_reaction
```

已构造 `future_verification.jsonl`：84 行，44 positive / 40 negative。negative pair 通过同一 parent 下交换 continuation 构造，且 `expected_state` 表示 action-conditioned expert expectation，`visible_reaction` 表示 continuation frames 实际显示的未来反应，修复了早期版本中 negative pair 可直接从 action 规则复述的泄漏问题。

| Condition | N | Parse | Match | Expected State | Body | Gaze | Hand | Movement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full6 | 4 | 1.000 | 0.750 | 1.000 | 0.500 | 0.500 | 0.500 | 0.500 |
| current3 | 4 | 1.000 | 0.500 | 1.000 | 0.500 | 0.500 | 0.500 | 0.500 |
| full6 | 8 | 1.000 | 0.625 | 1.000 | 0.375 | 0.375 | 0.375 | 0.375 |
| current3 | 8 | 1.000 | 0.500 | 1.000 | 0.250 | 0.250 | 0.250 | 0.250 |

结论：这是 smoke，不是最终 benchmark；但 balanced-8 上移除 continuation frames 后 `match_exact` 从 `0.625` 降到 `0.500`，visible reaction fields 从 `0.375` 降到 `0.250`，说明 future frames 已经影响 verification 任务。

Full-84 结果已经补齐：

- 文件：`data/piwm_results/future_verification_observed_all84_results.md`
- JSON：`data/piwm_results/future_verification_observed_full6_all84_eval.json`
- JSON：`data/piwm_results/future_verification_observed_current3_all84_eval.json`

| Condition | Rows | Parse | Match | Expected State | Body | Gaze | Hand | Movement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current 3 + continuation 3 | 84 | 1.000 | 0.595 | 0.988 | 0.667 | 0.667 | 0.667 | 0.667 |
| current 3 only | 84 | 1.000 | 0.488 | 0.988 | 0.583 | 0.583 | 0.583 | 0.583 |

结论：全 84 条上 continuation frames 使 `match_exact` 从 `0.488` 提升到 `0.595`，visible reaction fields 从 `0.583` 提升到 `0.667`。`expected_state` 基本不变，因为它主要由 action-conditioned expert rule 决定；视觉增益集中在“是否匹配”和“未来反应可见字段”。

## 4. End-to-end decision loop 结果

文件：

- `data/piwm_results/e2e_piwm_sft_pilot30_decision_loop.json`
- `data/piwm_results/e2e_piwm_sft_priority40_decision_loop.json`

流程：

```text
current frames
-> model-predicted perception
-> model-predicted candidate_actions
-> per-action deliberation using model-predicted state
-> model action selection
-> compare with gold best_action
```

| Eval set | N | Perception parse | Stage | Score | Candidate exact | Delib parse | Action parse | Chosen in gold candidates | Strategy acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot30_with_continuations | 24 | 1.000 | 0.417 | 0.792 | 0.333 | 1.000 | 0.875 | 0.417 | 0.208 |
| priority40_qareviewed | 36 | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 0.806 | 0.778 | 0.500 |

结论：decision loop 本身能跑，deliberation parse 都是 `1.000`；最终 strategy accuracy 主要被 perception/candidate 限制。priority40 因 candidate exact 更高，最终 action accuracy 也从 pilot30 的 `0.208` 提升到 `0.500`。

## 5. 当前训练数据规模与写作口径

### 5.1 QA-reviewed / 可写成 QA-reviewed 的部分

可写成 QA-reviewed：

- `data/piwm_dataset_pilot30_with_continuations/`
  - 24 loaded parent，6 skipped
  - 24 state rows，66 transition rows，24 policy rows
  - 44 continuation rows，其中 best 21 / worst 23
  - `require_qa_pass=true`，`require_continuation=true`
- `data/piwm_dataset_priority40_qareviewed_sample/`
  - 40 reviewed，36 pass，4 fail
  - 36 loaded parent，126 transition rows，36 policy rows
  - 可作为 priority split 的 QA-reviewed sample / evaluation set

注意：`priority40_qareviewed_sample` 可以写成 QA-reviewed sample，但不能把整个 priority280 写成 QA-reviewed。

### 5.2 只能写成 synthetic / unreviewed 的部分

只能写成 high-throughput synthetic train split / pending visual QA：

- `data/piwm_dataset_priority280_unreviewed/`
  - 260 parent
  - 260 state rows，927 transition rows，260 policy rows
  - `require_qa_pass=false`
  - 来源为 `Archive_generated_priority24` + `Archive_generated_priority256`
- `data/piwm_results/ms_swift_priority280_unreviewed/ms_swift_sft.jsonl`
  - 1187 SFT examples

这部分可以用于 sprint-scale SFT 训练和工程验证，但不能写成 manually verified / QA-pass / evaluation set。

### 5.3 当前主 SFT 训练规模

当前主 SFT run：

- 训练数据：`data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl`
- examples：1321
- images referenced：3963
- 输入组成：
  - `ms_swift_priority280_unreviewed/ms_swift_sft.jsonl`：1187 examples
  - `ms_swift_pilot30_full/ms_swift_sft.jsonl`：134 examples
- 训练：4 x 4090，660 / 660 steps，2 epochs
- 结束指标：`train_loss=0.0404377`，`token_acc=0.9972322`
- checkpoint：`data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660`

写作口径：可以写 “sprint-scale ms-swift LoRA SFT run on 1321 synthetic training examples”。其中包含 unreviewed synthetic，因此不要写成全量 QA-reviewed 训练集。

### 5.4 Pilot continuation / future verification 规模

Pilot continuation：

- QA-reviewed pilot continuation split：24 parent / 44 continuation
- continuation caption training examples 已包含在 `ms_swift_pilot30_full` 的 134 examples 中
- continuation frames 是可审计视觉证据，当前模型训练的是 semantic reaction caption

Future verification：

- `future_verification.jsonl`：84 行，44 positive / 40 negative
- ms-swift 导出：`data/piwm_results/ms_swift_pilot30_future_verification_observed/ms_swift_sft.jsonl`
- 导出总量：218 examples，其中 perception 24 / deliberation 66 / continuation_caption 44 / future_verification 84
- 该路线已有单独 4 卡训练：3 epochs / 162 steps，`train_loss=0.18426619`，`token_acc=0.99136691`

写作口径：future verification 当前可以写成 pilot continuation-derived action-conditioned verification smoke；还不能写成 full benchmark。

## 6. 当前还缺什么

1. **是否需要更多数据**  
   不建议盲目继续 Kling 生成。现有 priority280 已足够支撑训练侧，当前更需要扩大 QA 抽样、补强 visually distinct best/worst continuation pairs，并针对 perception/candidate 错误做定向数据增强。

2. **是否需要 DPO**  
   用户当前决定先不做 DPO。已有 SFT 结果显示 transition/reward 已接近满分，主要短板在 perception/candidate；短期优先级应放在 perception 数据质量、frame/eval 口径、future verification 全量评估，而不是立刻引入 DPO。

3. **端到端 action accuracy 的上限问题**  
   当前 e2e 结果已经说明：deliberation parse 不是瓶颈，candidate exact 才是最直接限制项。后续若要提升 final strategy accuracy，应优先减少 stage/candidate 误判。

4. **论文表格口径**  
   所有表格必须区分：
   - QA-reviewed pilot / QA-reviewed priority sample；
   - unreviewed synthetic train split；
   - smoke / diagnostic-only artifact；
   - full available evaluation rows。

## 7. Priority1000-Current 追加结果

更新时间：2026-05-01 09:45 CST

Kling API 已耗尽，本轮停止所有新增视频生成；当前可用的 partial priority1000 synthetic 数据已经用于一次更大规模 SFT。

训练产物：

- 训练数据：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl`
- SFT examples：2554
- Parent rows：543
- Checkpoint：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638`
- 训练：8 x 4090，2 epochs，638 steps，`train_loss=0.02578463`，`token_acc=0.99722675`
- 数据口径：未人工视觉审阅 synthetic train split，不能写成 QA-pass

主表结果：

- JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/main_table_piwm_sft_priority1000_current_len8192_priority40_all.json`
- Eval：`priority40_qareviewed_all`
- Rows：162，parse：1.000

| Model | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward |
|---|---:|---:|---:|---:|---:|---:|---:|
| PIWM-SFT v2, 1321 examples | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 |
| PIWM-SFT priority1000-current, 2554 examples | 0.917 | 0.833 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |

端到端 decision loop：

- JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/e2e_piwm_sft_priority1000_current_len8192_priority40_decision_loop.json`
- Eval：`priority40_qareviewed`
- Rows：36

| Model | Perception parse | Stage | Score | Candidate exact | Delib parse | Action parse | Chosen in gold candidates | Strategy acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PIWM-SFT v2, 1321 examples | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 0.806 | 0.778 | 0.500 |
| PIWM-SFT priority1000-current, 2554 examples | 1.000 | 0.917 | 0.833 | 0.833 | 1.000 | 0.667 | 0.833 | 0.500 |

解读：

- 扩大 synthetic SFT 对 perception 有正向效果，尤其 `score/candidates` 从 `0.750` 升到 `0.833`。
- 端到端 strategy accuracy 没升，原因转移到 action-selection parse：新 checkpoint action parse 为 `0.667`，fallback 为 `0.333`。
- 下一步最划算的是修 action-selection 输出约束和 robust parser/fallback，而不是继续消耗 Kling。

## 8. 最重要的三条实验结论

1. **PIWM-SFT 解决了结构化输出和 action-conditioned transition/reward 对齐**：parse 达到 `1.000`，transition/reward 多数达到 `0.970-1.000`，这是当前最稳的主结果。
2. **视觉输入确实必要，但 perception 仍是瓶颈**：text-only ablation 让 perception 明显崩塌；高像素 smoke 又说明瓶颈不是简单的低像素问题。
3. **端到端决策瓶颈已从 perception/candidate 部分转向 action selection 稳定性**：v2 时 priority40 的 candidate exact `0.750` 对应 strategy accuracy `0.500`；priority1000-current 把 candidate exact 提到 `0.833`，但 action parse 降到 `0.667`，strategy accuracy 仍停在 `0.500`。
