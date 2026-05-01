# PIWM Experiment Status: Main Table v2

更新时间：2026-05-01 04:50 CST

## 1. 一句话状态

实验主链路和主表 v2 已完成。当前结果显示 PIWM-SFT 在 rule-conditional fields 上已经稳定接近满分，但 perception fields 仍是主要短板；下一步先判断该短板是否来自低像素评测口径，再决定是否启动 SFT v2。

## 2. 冻结产物

主表结果：

- 本地 Markdown：`data/piwm_results/main_table_v2_full_midpix_results.md`
- 本地 JSON：`data/piwm_results/main_table_v2_full_midpix_results.json`
- 远端 Markdown：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/main_table_v2_full_midpix_results.md`
- 远端 JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/main_table_v2_full_midpix_results.json`

训练 checkpoint：

- `/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660`

训练框架与模型：

- SFT framework：ms-swift
- Base model：`Qwen2.5-VL-7B-Instruct`
- Tuning method：LoRA SFT
- 已完成步数：660 / 660
- 训练结束指标：`train_loss=0.0404377`，`token_acc=0.9972322169941876`

## 3. 评测口径

主表 v2 使用 3-frame mid-pixel 推理口径：

- `image_limit=3`
- `max_pixels=200704`
- `max_new_tokens=128`
- `torch_dtype=float16`
- checkpoint eval 脚本：`scripts/eval_ms_swift_checkpoint.py`

重要修正：

- `all` 评测必须显式全量；此前 smoke 曾被 `limit=24` 截断。
- 当前 v2 已用全量参数重跑，确认 `pilot30_all_with_continuations=134` 行，`priority40_qareviewed_all=162` 行。

## 4. Main Table v2

| Eval set | Rows | Model | Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward | Caption |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot30_all_with_continuations | 134 | Qwen2.5-VL zero-shot | 0.552 | -- | -- | -- | 0.333 | 0.500 | 0.600 | 0.033 | 0.000 |
| pilot30_all_with_continuations | 134 | PIWM-SFT | 1.000 | 0.417 | 0.792 | 0.333 | 0.985 | 1.000 | 1.000 | 0.970 | 1.000 |
| priority40_qareviewed_all | 162 | Qwen2.5-VL zero-shot | 0.235 | -- | -- | -- | 0.211 | 0.553 | 0.289 | 0.000 | -- |
| priority40_qareviewed_all | 162 | PIWM-SFT | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | -- |

## 5. 直接结论

已经站住的结果：

- PIWM-SFT 让 structured parse 从 `0.235/0.552` 提升到 `1.000`。
- Rule-conditional transition fields 已经很强：`next_stage/risk/benefit/reward` 在 SFT 后达到 `0.970-1.000`。
- Continuation caption head 在 pilot30 continuation set 上从 zero-shot `0.000` 提升到 SFT `1.000`。

仍未解决的问题：

- Perception 是当前短板，尤其是 `pilot30_all_with_continuations` 上的 `stage=0.417`、`candidates=0.333`。
- `priority40_qareviewed_all` 上 perception 明显更好：`stage=0.889`、`candidates=0.750`。这说明短板可能与数据分布、continuation set 构造、或低像素口径有关，而不是模型完全学不会。

## 6. 下一步判定树

下一步先做低成本诊断，不立刻启动 SFT v2：

1. High-pixel 3-frame perception smoke  
   目标：判断 perception 短板是否由 `max_pixels=200704` 过低造成。  
   如果 high-pixel 后 `stage/candidates` 明显反弹，则优先调整 inference config，而不是重训。

2. Inference-time ablation  
   目标：补出论文主表所需的第三行对照。  
   优先考虑不训练的新 ablation，例如 mask / no-head / task-only prompt ablation。

3. Case-level perception error analysis  
   目标：定位 `stage` 和 `candidate_actions` 错误来自标签、视觉证据、prompt、parser 还是像素设置。

4. SFT v2  
只有在 high-pixel 与 ablation 不能解释 perception 短板时启动。重点增强 perception，而不是重复强化已经接近满分的 rule-conditional fields。

## 7. High-Pixel Perception Smoke

已完成一轮 perception-only high-pixel smoke：

- 结果 Markdown：`data/piwm_results/perception_highpix_smoke_results.md`
- 结果 JSON：`data/piwm_results/perception_highpix_smoke_results.json`
- high-pixel 设置：`max_pixels=401408`
- v2 mid-pixel 设置：`max_pixels=200704`

| Eval set | Model | Pixel | Rows | Parse | Stage | Score | Candidates |
|---|---|---|---:|---:|---:|---:|---:|
| pilot30_perception | PIWM-SFT | midpix | 24 | 1.000 | 0.417 | 0.792 | 0.333 |
| pilot30_perception | PIWM-SFT | highpix | 24 | 1.000 | 0.500 | 0.750 | 0.375 |
| priority40_perception | PIWM-SFT | midpix | 36 | 1.000 | 0.889 | 0.750 | 0.750 |
| priority40_perception | PIWM-SFT | highpix | 36 | 1.000 | 0.833 | 0.722 | 0.722 |

结论：

- pilot30 perception 有小幅反弹，但幅度不足以解释整体短板。
- priority40 perception 在 high-pixel 下略降。
- 因此 perception 短板不是简单的 low-pixel artifact；需要继续做 case-level error analysis，重点看标签分布、prompt 信息、candidate set 生成逻辑和视觉证据是否一致。

## 8. Text-Only Inference Ablation

已完成同一 PIWM-SFT checkpoint 的 text-only ablation：

- 结果 Markdown：`data/piwm_results/ablation_text_only_results.md`
- 结果 JSON：`data/piwm_results/ablation_text_only_results.json`
- 设置：`image_limit=0`，即推理时移除全部视觉帧。

| Eval set | Rows | Condition | Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward | Caption |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot30_all_with_continuations | 134 | visual_3frame_midpix | 1.000 | 0.417 | 0.792 | 0.333 | 0.985 | 1.000 | 1.000 | 0.970 | 1.000 |
| pilot30_all_with_continuations | 134 | no_visual_frames | 1.000 | 0.333 | 0.042 | 0.042 | 0.955 | 1.000 | 1.000 | 0.970 | 1.000 |
| priority40_qareviewed_all | 162 | visual_3frame_midpix | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | -- |
| priority40_qareviewed_all | 162 | no_visual_frames | 1.000 | 0.111 | 0.111 | 0.111 | 1.000 | 1.000 | 1.000 | 1.000 | -- |

结论：

- 去掉视觉帧后，perception 明显崩塌，尤其 `score/candidates` 从 `0.750` 掉到 `0.111`，或从 `0.792/0.333` 掉到 `0.042/0.042`。
- 同时，deliberation/reward 仍保持高分，因为这些任务的输入中已经包含结构化 state/action 条件。
- 这可以作为低成本 ablation row：视觉帧对 perception 是必要的，而 rule-conditioned transition 主要测试 action-conditioned world-model 规则对齐。

## 9. Case-Level Perception Error Analysis

已生成初版错误分析：

- Markdown：`data/piwm_results/perception_error_analysis_v0.md`
- JSON：`data/piwm_results/perception_error_analysis_v0.json`

核心观察：

- pilot30 的 perception 错误明显多于 priority40，说明 continuation pilot set 的分布和标注更难。
- candidate 错误高度集中：模型常把 gold 的低干预候选集预测成更主动的干预集合。
- 常见模式包括：
  - `A1_silent_observe, A6_acknowledge_and_wait` 被预测为含 `A3_strong_recommend` 的主动集合。
  - gold 中的 `A5_provide_demonstration` 常被替换为 `A2_offer_value_comparison`。
  - `attention/action` 的边界比 `interest` 更不稳定。

因此 SFT v2 如果启动，重点不应继续增强 reward/transition，而应增强：

- AIDA stage boundary examples；
- low-intervention candidate set；
- candidate-actions exact order；
- hard negative perception examples；
- visual evidence 与 stage label 的一致性。

## 10. 当前禁止混淆的口径

- v2 是 full available evaluation rows，不是最终全规模 benchmark。
- priority40 是 QA-reviewed sample，priority280/unreviewed synthetic 只能用于赶训练，不应写成 QA-pass 数据。
- pilot30 continuation 是可用的 world-model continuation 证据，但规模仍是 pilot-level。
- 当前 continuation 不是“只有文字”：训练目标是 reaction caption，但每条 caption 都保留 continuation frames 作为可审计视觉证据。证据 manifest 见 `data/piwm_results/continuation_visual_evidence_manifest.jsonl` 和 `data/piwm_results/continuation_visual_evidence_summary.md`。
- 当前论文 framing 应保持 pilot-scale method paper，不要夸成完整 benchmark paper。

## 11. End-to-End Decision Loop Eval

已完成一个更接近部署形态的 end-to-end decision loop eval：

- 脚本：`scripts/eval_e2e_decision_loop_checkpoint.py`
- pilot30 输出：`data/piwm_results/e2e_piwm_sft_pilot30_decision_loop.json`
- priority40 输出：`data/piwm_results/e2e_piwm_sft_priority40_decision_loop.json`

流程：

```text
current frames
→ model-predicted perception
→ model-predicted candidate_actions
→ per-action deliberation using model-predicted state
→ model action selection
→ compare with gold best_action
```

结果：

| Eval set | N | Perception parse | Stage | Score | Candidate exact | Delib parse | Action parse | Chosen in gold candidates | Strategy acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot30_with_continuations | 24 | 1.000 | 0.417 | 0.792 | 0.333 | 1.000 | 0.875 | 0.417 | 0.208 |
| priority40_qareviewed | 36 | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 0.806 | 0.778 | 0.500 |

解读：

- end-to-end 下 deliberation parse 仍为 `1.000`，说明动作后果预测链路可以稳定运行。
- 最终 strategy accuracy 主要受 perception/candidate quality 限制：pilot30 的 candidate exact 只有 `0.333`，对应 final action 只有 `0.208`。
- priority40 的 candidate exact 为 `0.750`，final action 升到 `0.500`，说明修 perception/candidate 预期能直接提高端到端导购动作。

## 12. Action-Conditioned Future Verification

已完成路线 C 的闭环：把 continuation frames 从“可审计附件”升级为训练输入，构造 `future_verification.jsonl`：

```text
current_frames + candidate_action + continuation_frames
→ match / mismatch + expected_next_state + visible_reaction
```

关键修正：

- 正样本：`action A + continuation A -> match=yes`。
- 负样本：同一 parent 下交换 continuation，且只在 expected next state 不同时构造。
- `expected_state` 表示候选 action 的专家规则后果。
- `visible_reaction` 表示 continuation frames 实际显示的未来反应；这点修复了早期版本中 negative pair 仍可从 action 规则直接复述的泄漏问题。

数据与训练产物：

- Future verification JSONL：`data/piwm_dataset_pilot30_with_continuations/future_verification.jsonl`
- 样本数：84 行，44 positive / 40 negative
- ms-swift 训练 JSONL：`data/piwm_results/ms_swift_pilot30_future_verification_observed/ms_swift_sft.jsonl`
- 训练框架：ms-swift + Qwen2.5-VL-7B-Instruct + LoRA
- 远端 checkpoint：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_future_verification_observed_4gpu/v0-20260501-043301/checkpoint-162`
- 训练结束：3 epochs，162 steps，`train_loss=0.18426619`，`token_acc=0.99136691`

Smoke 结果：

| Condition | N | Parse | Match | Expected State | Body | Gaze | Hand | Movement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full6: current 3 + continuation 3 | 4 | 1.000 | 0.750 | 1.000 | 0.500 | 0.500 | 0.500 | 0.500 |
| current3 only | 4 | 1.000 | 0.500 | 1.000 | 0.500 | 0.500 | 0.500 | 0.500 |
| full6: current 3 + continuation 3 | 8 | 1.000 | 0.625 | 1.000 | 0.375 | 0.375 | 0.375 | 0.375 |
| current3 only | 8 | 1.000 | 0.500 | 1.000 | 0.250 | 0.250 | 0.250 | 0.250 |

解读：

- 这是 sprint smoke，不是最终 benchmark；样本数仍小。
- 但方向正确：移除 continuation frames 后，balanced-8 的 `match_exact` 从 `0.625` 降到 `0.500`，visible reaction fields 从 `0.375` 降到 `0.250`。
- 这比旧 continuation caption 更符合 World Model 叙事：模型不是生成未来视频，而是在验证“给定当前观察和 action，这段候选未来视觉反应是否符合动作条件后果”。

Full-84 结果：

- 结果 Markdown：`data/piwm_results/future_verification_observed_all84_results.md`
- Full-84 JSON：`data/piwm_results/future_verification_observed_full6_all84_eval.json`
- Current-only JSON：`data/piwm_results/future_verification_observed_current3_all84_eval.json`

| Condition | Rows | Parse | Match | Expected State | Body | Gaze | Hand | Movement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current 3 + continuation 3 | 84 | 1.000 | 0.595 | 0.988 | 0.667 | 0.667 | 0.667 | 0.667 |
| current 3 only | 84 | 1.000 | 0.488 | 0.988 | 0.583 | 0.583 | 0.583 | 0.583 |

解读：

- continuation frames 进入输入后，全 84 条上 `match_exact` 从 `0.488` 提升到 `0.595`。
- visible reaction fields 从 `0.583` 提升到 `0.667`。
- `expected_state` 基本不变，是因为它主要由 action-conditioned expert rule 决定；视觉增益主要体现在 match 与 visible reaction。
- 这可以支撑路线 C 的核心表述：continuation frames 不是只做审计附件，而是作为 action-conditioned future verification 的视觉证据参与监督。

## 13. Frame Budget Ablation

已完成 perception head 的 frame-budget ablation，用于回答“为什么默认 K=3，而不是 K=1/K=5”。

- 结果 Markdown：`data/piwm_results/frame_budget_ablation_results.md`
- Eval set：`priority40_qareviewed_sample` perception rows
- Model：PIWM-SFT Qwen2.5-VL-7B LoRA `checkpoint-660`
- Pixel budget：每张图 `max_pixels=200704`
- K=1：只取 5s cue peak
- K=3：2s / 5s / 8s，对应 onset / peak / resolution
- K=5：1s / 3s / 5s / 7s / 9s

| K | Rows | Parse | Stage | Score | Candidates |
|---:|---:|---:|---:|---:|---:|
| 1 | 36 | 1.000 | 0.722 | 0.694 | 0.694 |
| 3 | 36 | 1.000 | 0.861 | 0.722 | 0.722 |
| 5 | 36 | 1.000 | 0.861 | 0.722 | 0.722 |

结论：

- K=1 可用但明显弱于 K=3，尤其是 AIDA stage。
- K=3 相比 K=1 提供主要收益。
- K=5 在当前样本和像素预算下没有继续提升。
- 因此默认 K=3 可以解释为最小行为片段预算：保留 onset--peak--settle，同时控制推理成本和 QA 成本。

## 14. Priority1000-Current Checkpoint Update

更新时间：2026-05-01 09:45 CST

Kling API 已耗尽，本轮不再继续生成视频。已用当前可用的 partial priority1000 synthetic 数据完成一次更大规模 ms-swift SFT，并在 QA-reviewed `priority40` 上完成主表与端到端评估。

训练数据与 checkpoint：

- 训练 JSONL：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl`
- 训练样本：2554 条 SFT examples
- Parent rows：543
- 数据口径：high-throughput synthetic train split，未人工视觉审阅；不能写成 QA-pass
- 训练框架：ms-swift + Qwen2.5-VL-7B-Instruct + LoRA
- GPU：8 x 4090
- Checkpoint：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638`
- 训练结束：2 epochs，638 steps，`train_loss=0.02578463`，`token_acc=0.99722675`

主表评估：

- 结果 JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/main_table_piwm_sft_priority1000_current_len8192_priority40_all.json`
- Eval set：`priority40_qareviewed_all`
- Rows：162
- Parse：1.000

| Eval set | Rows | Model | Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| priority40_qareviewed_all | 162 | PIWM-SFT priority1000-current | 1.000 | 0.917 | 0.833 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |

端到端决策评估：

- 结果 JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/e2e_piwm_sft_priority1000_current_len8192_priority40_decision_loop.json`
- Eval set：`priority40_qareviewed`
- Rows：36

| Eval set | N | Perception parse | Stage | Score | Candidate exact | Delib parse | Action parse | Chosen in gold candidates | Strategy acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| priority40_qareviewed | 36 | 1.000 | 0.917 | 0.833 | 0.833 | 1.000 | 0.667 | 0.833 | 0.500 |

解读：

- 更大 synthetic SFT 规模让 priority40 的 perception 从 v2 的 `stage=0.889 / score=0.750 / candidates=0.750` 提升到 `0.917 / 0.833 / 0.833`。
- Transition/reward 继续保持满分，说明更大训练没有破坏 rule-conditioned world-model head。
- 端到端 strategy accuracy 仍为 `0.500`，主要原因不再是 perception parse，而是 action-selection parse 只有 `0.667`，fallback rate 为 `0.333`。
- 下一步如果继续优化主表，不应再消耗 Kling；应优先修 action-selection 输出约束或做 inference-time robust parser/fallback ablation。
