# Current Sprint Status and Reporting Policy

更新时间：2026-05-01 09:45 CST

本文件固定当前 PIWM NeurIPS sprint 的事实状态与对外报告口径。核心原则：

```text
可以用 high-throughput synthetic split 赶训练；
不能把未人工审阅数据写成 QA-pass 数据；
不能把 mock / rule-oracle / OOM eval 写成模型指标。
```

## 1. 三层数据口径

| Tier | 名称 | 当前资产 | 可用于 | 不可用于 |
|---|---|---|---|---|
| A | QA-reviewed synthetic subset | `data/piwm_dataset_pilot30_with_continuations/`：24 parent，44 continuation；`data/piwm_dataset_fix3_continuation_validation/`：2 parent，2 continuation | 论文中展示数据闭环、World Model continuation 机制、人工审阅样例、定性分析 | 声称 full-scale benchmark |
| B | High-throughput synthetic train split, pending visual QA | `data/piwm_dataset_priority280_unreviewed/`：260 parent，927 transition，260 policy；`data/piwm_results/ms_swift_priority280_unreviewed/ms_swift_sft.jsonl`：1187 SFT examples | sprint-scale SFT 训练、工程压力测试、训练脚本验证 | 写成 QA-pass / manually verified / evaluation set |
| C | Diagnostic-only artifacts | MockVLM eval、rule-oracle baseline、OOM checkpoint eval | 验证解析器、决策循环、脚本可运行性 | 写成真实 VLM 或训练后模型性能 |

推荐英文口径：

> We train on a high-throughput synthetic generated split with file-level QA and pending visual QA, and we reserve the manually QA-reviewed pilot subset for qualitative inspection and data-contract validation.

推荐中文口径：

> 当前大批量数据是“高通量合成训练集”：已完成视频生成、抽帧、文件级 QA 与 schema 入库，但视觉 cue / viewpoint / 物理一致性尚未人工审阅。因此它可用于赶 SFT 训练，不能写成 QA-pass 评测数据。

## 2. 远端 live snapshot

远端数据盘路径：

```text
/root/lanyun-fs/ProactiveIntentWorldModel
```

数据盘状态：`/root/lanyun-fs` 约 200G，总使用约 48G，剩余约 153G。

### 2.1 Kling 生成资产

| Archive | video.mp4 | qa_report.json | qa_manual_review.json | 口径 |
|---|---:|---:|---:|---|
| `Archive_generated_priority24` | 24 | 24 | 0 | high-throughput synthetic, pending visual QA |
| `Archive_generated_priority256` | 236 | 236 | 0 | high-throughput synthetic, pending visual QA |
| `Archive_generated_pilot30` | 30 | 30 | 30 | QA-reviewed pilot |
| `Archive_generated_fix3` | 3 | 3 | 3 | targeted QA validation |

早期 snapshot 中 Kling API 额度从约 86% 降到约 46%，换来 260 条唯一 priority parent videos。2026-05-01 09:45 更新：Kling API 已耗尽，后续不得继续自动生成；当前训练使用的是已落盘的 partial priority500/priority1000 synthetic 资产。

### 2.2 数据集资产

| Dataset | loaded | skipped | state | transition | policy | continuation | 口径 |
|---|---:|---:|---:|---:|---:|---:|---|
| `data/piwm_dataset_priority280_unreviewed` | 260 | 0 | 260 | 927 | 260 | 0 | high-throughput synthetic train split |
| `data/piwm_dataset_pilot30_with_continuations` | 24 | 6 | 24 | 66 | 24 | 44 | QA-reviewed pilot continuation split |
| `data/piwm_dataset_fix3_continuation_validation` | 2 | 1 | 2 | 4 | 2 | 2 | targeted continuation validation |
| `data/piwm_dataset_combined_existing` | 33 | 13 | 33 | 94 | 33 | 4 | mixed historical QA-pass utility split |
| `data/piwm_dataset_priority40_qareviewed_sample` | 36 | 4 | 36 | 126 | 36 | 0 | QA-reviewed sample from priority split |

Priority split 覆盖：

- viewpoint：192 `salesperson_observable`，68 `surveillance_oblique`
- split：199 train，8 dev，6 test，26 ood_product，21 ood_persona
- product：8 类全覆盖

## 3. 训练状态

当前训练框架：**ms-swift**。

当前完成的真实训练：

| 项 | 值 |
|---|---|
| Base model | `Qwen2.5-VL-7B-Instruct` |
| Method | LoRA SFT via ms-swift |
| Data | `data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl` |
| Examples | 1321 |
| Images referenced | 3963 |
| GPUs | 4 x 4090 |
| Steps | 660 / 660 |
| Epoch | 2.0 |
| Train runtime | 1653.8411 sec |
| Train loss | 0.0404377 |
| Last-step loss | 0.0061066948 |
| Token acc | 0.9972322 |
| Checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660` |

这可以写成：

> We completed a sprint-scale ms-swift LoRA SFT run on 1321 synthetic training examples.

不能写成：

> The model achieves X% accuracy.

原因：当前 checkpoint inference eval 还没有有效模型指标。

## 4. 评估状态

| Artifact | 状态 | 口径 |
|---|---|---|
| `pilot24_mock_pipeline_eval.json` | 24/24 plumbing success，strategy accuracy 0.125 | MockVLM 管线诊断，不是训练结果 |
| `pilot24_zero_shot_baselines.json` | 本地/旧 artifact 中 rule-oracle 可见，其它 API baseline 缺失或不可用 | rule-oracle 是 metadata-assisted diagnostic，不是真实 zero-shot VLM |
| `sft_checkpoint_eval_balanced24.json` | 24 条 full-frame checkpoint eval 尝试全部 CUDA OOM，`parse_success=0` | 历史失败是显存配置问题，不是模型性能结论 |
| `sft_checkpoint_eval_balanced24_1frame_lowpix.json` | 1-frame / low-pixel smoke eval，24/24 parse success | 可报告 tag-format smoke，不是 full-image benchmark |
| `sft_checkpoint_eval_balanced24_3frame_lowpix.json` | 3-frame / low-pixel smoke eval，24/24 parse success | 当前最接近训练输入的可用 checkpoint smoke |

当前主 smoke eval 结果（3-frame / low-pixel）：

| Metric | Value |
|---|---:|
| `n_records` | 24 |
| `parse_success` | 24 |
| `parse_rate` | 1.0 |
| `stage_exact` | 0.125 |
| `score_exact` | 0.75 |
| `candidates_exact` | 0.125 |
| `next_stage_exact` | 1.0 |
| `risk_exact` / `benefit_exact` / `reward_exact` | 1.0 / 1.0 / 1.0 |
| `caption_exact` | 1.0 |

注意：这是 balanced 24-row smoke，且用 low-pixel inference 降低显存；可以说明 checkpoint 能按 PIWM tag 契约输出，不能替代 full-resolution benchmark。

## 4.1 Priority split 抽样 QA

已对 priority280 做第一批 40 条分层 contact-sheet QA：

| 项 | 数值 |
|---|---:|
| reviewed | 40 |
| pass | 36 |
| fail | 4 |
| pass rate | 90% |

失败集中在两类：

- `salesperson_observable` 但脸/视线被裁掉；
- 动态 cue（`approaching_counter`、`looking_around_for_help`）在 3 帧里证据不足。

落盘资产：

- `data/priority_generation_queue/qa_review_priority280_stratified40_manual_decisions.json`
- `data/piwm_dataset_priority40_qareviewed_sample/`

## 5. 对外写法红线

可以写：

- `synthetic generated training split`
- `file-level QA completed`
- `pending manual visual QA`
- `QA-reviewed pilot subset`
- `sprint-scale SFT run completed`
- `1-frame low-pixel checkpoint smoke eval completed`
- `3-frame low-pixel checkpoint smoke eval completed`

不要写：

- `QA-pass full dataset`
- `manually verified 260 samples`
- `real-store results`
- `zero-shot GPT/Gemini/Claude/Qwen baseline completed`
- `full-image checkpoint accuracy = X`（当前只有 low-memory smoke，不是 full-image benchmark）
- `fabricated / unsupported measured data`

## 6. 现在最该做的事

1. **停止宽泛 Kling 生成**：现有 260 parent 足够支撑下一轮训练与 QA 抽样。
2. **扩大 priority split 抽样 QA**：已完成 40 条，下一步可补到 80-100 条以稳定 pass-rate 估计。
3. **升级 checkpoint eval**：3-frame low-pixel 已通过；下一步逐步提高像素或样本量，观察显存边界。
4. **继续训练侧产物整理**：把 ms-swift run、checkpoint、训练日志、数据口径写入 paper-safe 表格。

## 7. 2026-05-01 Priority1000-Current 更新

Kling API 当前已经耗尽，本轮停止所有新增视频生成。已有 `priority500` / `priority1000` 部分生成资产已全部按“未人工审阅 synthetic train split”口径使用；未完成的视频队列只保留为待补，不再自动运行。

### 7.1 已用数据

| Dataset | Parent rows | SFT examples | 口径 |
|---|---:|---:|---|
| `priority280_unreviewed` + pilot continuation | 284 parent effective | 1321 | sprint-scale synthetic train split |
| `priority1000_unreviewed` 当前可用部分 | 543 parent | 2554 | larger synthetic train split, pending visual QA |

`priority1000_unreviewed` 来源包括：

- priority24：24 parent
- priority256：235 parent
- priority500 new：168 parent
- priority1000 remaining：116 parent

这些数据可以用于训练和工程验证；不能写成 QA-reviewed / manually verified。

### 7.2 新训练 checkpoint

| 项 | 值 |
|---|---|
| Framework | ms-swift |
| Base model | Qwen2.5-VL-7B-Instruct |
| Method | LoRA SFT |
| Data | `data/piwm_results/ms_swift_priority1000_unreviewed/ms_swift_sft.jsonl` |
| Examples | 2554 |
| GPUs | 8 x 4090 |
| Steps | 638 / 638 |
| Epoch | 2.0 |
| Train loss | 0.02578463 |
| Token acc | 0.99722675 |
| Checkpoint | `/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/ms_swift_sft_qwen25vl7b_priority1000_current_len8192_8gpu/v0-20260501-082114/checkpoint-638` |

### 7.3 新评估结果

主表：

- JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/main_table_piwm_sft_priority1000_current_len8192_priority40_all.json`
- Eval set：`priority40_qareviewed_all`
- Rows：162

| Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.000 | 0.917 | 0.833 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |

End-to-end decision loop：

- JSON：`/root/lanyun-fs/ProactiveIntentWorldModel/data/piwm_results/e2e_piwm_sft_priority1000_current_len8192_priority40_decision_loop.json`
- Eval set：`priority40_qareviewed`
- Rows：36

| Perception parse | Stage | Score | Candidate exact | Delib parse | Action parse | Chosen in gold candidates | Strategy acc |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.000 | 0.917 | 0.833 | 0.833 | 1.000 | 0.667 | 0.833 | 0.500 |

### 7.4 当前对外口径

可以写：

- “We train on 2554 high-throughput synthetic SFT examples, with evaluation on a separate QA-reviewed priority subset.”
- “The larger synthetic SFT run improves perception fields on QA-reviewed priority40 from `0.889/0.750/0.750` to `0.917/0.833/0.833`.”
- “End-to-end decision accuracy remains limited by action-selection formatting/fallback, not by transition parsing.”

不能写：

- “1000 videos completed”：实际当前可用 parent 为 543，Kling API 已耗尽。
- “priority1000 is QA-pass”：该数据是未人工视觉审阅 synthetic train split。
- “strategy accuracy improved”：当前仍为 `0.500`，改进在 perception/candidate，不在 final strategy。
