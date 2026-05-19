# PIWM Official Dataset Aliases

更新时间：2026-05-17

Kling API 已耗尽，本轮不会再新增视频。因此当前已落盘视频规模固定；v2.2 只做 schema、policy 和导出层迁移，不重生成 Kling 视频。

这里的目录是**正式名字入口**，不是重新复制视频数据。v1 目录保留为冻结兼容入口；v2.2 使用独立目录，避免训练脚本和结果文件被无提示替换。

对外说明、论文、汇报、示例数据展示和新脚本默认只引用 `data/official/` 下的 canonical path。`data/piwm_dataset_*` 这类目录只是 backing/source path，只能在 manifest lineage、复现实验路径或维护脚本中出现。

当前 official 数据已有 DialogueAct v2.1 human-salesperson schema，同时保留旧 `A1-A8 / T-state` alias。`PIWM-Train-Synth-v1` 明确保留真人导购逻辑；`best_action_realization` 是主监督，`realization / terminal_realization` 是后续 target terminal 数据集的草案字段。顶层 `co_acts` 已从 official 主表输出中移出；旧输入仍可读，兼容输出使用 `legacy_co_acts`，新字段使用 `act_params.supporting_acts`。2026-05-15 已新增独立 v2.2 导出：`PIWM-Train-Synth-v2` 和 `PIWM-PolicySlice-v2`。2026-05-16 已导入轻量 `piwm` target 域数据为 `PIWM-Target-Frontcam-v1`，并新增 `PIWM-Target-PromptReady-v1` 作为 318 条 target 上游生成索引。2026-05-17 已把项目负责人复核后的 30 条 target test QA 写回 target 主表和 target ms-swift 导出。

## Canonical Names

| 正式名 | 本目录入口 | Backing/source path（维护用） | 用途 | 口径 |
|---|---|---|---|---|
| `PIWM-Train-Synth-v1` | `piwm_train_synth_v1` | `../piwm_dataset_priority1000_unreviewed_compact_v2` | frozen 主 SFT 训练 | synthetic train, pending visual QA, human-salesperson logic with 6-act policy labels |
| `PIWM-Train-Synth-v2` | `piwm_train_synth_v2` | `piwm_train_synth_v1` | schema v2.2 主训练导出 | 543 parent / 2011 transition / 543 policy rows；含 `next_state_by_action_v2`，不覆盖 v1 |
| `PIWM-PolicySlice-v2` | `piwm_policy_slice_v2` | `scripts.scenario_sampler --candidate-rule-only` | explicit candidate-rule policy manifest | 864 rule-supported policy scenarios；不是视频数据，不是 QA-reviewed |
| `PIWM-Target-Frontcam-v1` | `piwm_target_v1` | `/Users/mutsumi/Desktop/WorkSpace/piwm` | target 域智能售货柜前置摄像头数据 | 118 records / 354 frames / 708 ms-swift examples；30 test records project-lead QA pass，88 train records synthetic_unreviewed |
| `PIWM-Target-PromptReady-v1` | `piwm_target_promptready_v1` | `/Users/mutsumi/Desktop/WorkSpace/piwm/data/{seed,manifest,labeled,prompts}` | target 域上游生成索引 | 318 prompt-ready records；118 video-backed，200 video-pending；不是 ms-swift SFT 文件 |
| `PIWM-Eval-QA-v1` | `piwm_eval_qa_v1` | `../piwm_dataset_priority40_qareviewed_sample_compact_v2_exact` | 主表与 e2e 评估 | QA-reviewed eval subset, compact visual-state/action-realization schema |
| `PIWM-WorldModel-v1` | `piwm_world_model_v1` | `../piwm_dataset_pilot30_with_continuations_compact_v2` | continuation / Future Verification | QA-reviewed pilot evidence, shared three-axis current/future visual schema |
| `PIWM-FutureVerification-v1` | `piwm_world_model_v1/future_verification.jsonl` | same | action-conditioned future verification | derived from QA-reviewed continuations |
| `PIWM-RealShoot-v1` | `piwm_realshoot_v1` | `docs/current/piwm_real_shooting_scripts_S01_S12.md` | real-shooting manifest template | template/sample only, not filmed, not QA-reviewed |

## Schema v2.1 Re-export

2026-05-13 已运行：

```bash
python3 -m scripts.refresh_official_v2_exports --summary-out data/official/V2_REEXPORT_SUMMARY.json
python3 -m scripts.build_realshoot_manifest --output-dir data/official/piwm_realshoot_v1
```

重导结果：

- `PIWM-Train-Synth-v1`: 543 parent, 2011 transition rows, 543 policy rows.
- `PIWM-Eval-QA-v1`: 36 parent, 126 transition rows, 36 policy rows.
- `PIWM-WorldModel-v1`: 24 parent, 66 transition rows, 24 policy rows, 44 continuation rows.
- `PIWM-RealShoot-v1`: 24 manifest sample rows, covering S01-S12 A/B.

主数据 JSONL 现在包含 `schema_version=dialogue_act_human_salesperson_v2.1`、`actor_profile=human_salesperson_logic`、`dialogue_act / act_params.supporting_acts / best_action_realization / realization`。旧 `co_acts` 仍可被 schema 读入，但 official 主表输出不再使用顶层 `co_acts`；需要回溯兼容时使用 `legacy_co_acts`。Transition rows 包含 `candidate_dialogue_act / candidate_terminal_realization`。

## Schema v2.2 Export Status

v2.2 已完成 schema/runtime 增量、写回预演和独立导出。当前审计入口：

- `docs/v2_validation/compatibility_report.md`
- `docs/v2_validation/action_distribution.md`
- `docs/v2_validation/v2_2_reexport_dry_run.md`
- `docs/v2_validation/v2_2_reexport_diff_preview.md`
- `docs/v2_validation/v2_2_test_coverage.md`

关键结论：

- basic schema compatibility：`green=462`、`yellow=0`、`red=81`。这里的 `yellow=0` 不是 policy 无漂移，只是基础检测器没有非阻断 mismatch。
- extended v2 re-derivation audit：`green=109`、`yellow=353`、`red=81`。
- official 543 在 v2.2 规则下重新推导的 best action 分布：`Elicit=252`、`Recommend=119`、`Inform=105`、`Reassure=42`、`Hold=25`。
- red 样本集中在 `browser_low_intent`：81 / 94 条，属于 legacy Kling prompt 未显式区分低意图视觉表现的历史包袱。
- `next_state_by_action` 仍保留 legacy A-label key；v2.2 已新增 `next_state_by_action_v2` 作为 v2 action-keyed alias。
- `PIWM-Train-Synth-v2` 已写出到 `data/official/piwm_train_synth_v2/`，`PIWM-PolicySlice-v2` 已写出到 `data/official/piwm_policy_slice_v2/`。
- `PIWM-Target-Frontcam-v1` 已写出到 `data/official/piwm_target_v1/`。它来自 `guochenmeinian/piwm` 的 118 条设备前置摄像头样本，使用 `target_frontcam` 和 `actor_profile=target_terminal_logic`。30 条 test split 已完成项目负责人 QA 复核并写回 target 主数据：30 pass / 0 fail / 2 warning records；88 条 train records 仍是 `synthetic_unreviewed`。
- `PIWM-Target-PromptReady-v1` 已写出到 `data/official/piwm_target_promptready_v1/`。它索引轻量 `piwm` 的 318 条 `seed / manifest / labeled / prompts`，其中新增 200 条是 `video_pending`，不能当作已成片多模态训练样本。

v2.2 不覆盖 `PIWM-Train-Synth-v1`。v1 是冻结兼容入口；v2.2 新实验应显式使用 v2 路径。

## ms-swift Entrypoints

| 用途 | JSONL |
|---|---|
| frozen 主 SFT 训练 | `ms_swift/piwm_train_synth_v1.jsonl` |
| schema v2.2 主 SFT 训练 | `ms_swift/piwm_train_synth_v2.jsonl` |
| target 域低资源专项 SFT | `ms_swift/piwm_train_target_specialization_v1.jsonl` |
| target 域 prompt-ready 上游索引 | `piwm_target_promptready_v1/promptready_index.jsonl` |
| mixed-view joint SFT 对照 | `ms_swift/piwm_train_general_plus_target_v1.jsonl` |
| 新版 full-v2 SFT 训练 | `ms_swift/piwm_train_full_v2.jsonl` |
| 主 QA eval | `ms_swift/piwm_eval_qa_all_v1.jsonl` |
| World Model / FV SFT | `ms_swift/piwm_world_model_sft_v1.jsonl` |
| Future Verification eval | `ms_swift/piwm_future_verification_eval_all_v1.jsonl` |

`piwm_train_full_v2.jsonl` 是下一次从 base 重新八卡训练的推荐入口。它在
`PIWM-Train-Synth-v1` 的 perception / deliberation 基础上加入
action-selection rows，并合并 `PIWM-WorldModel-v1` 的 continuation caption
与 Future Verification rows：

- 3339 SFT examples
- perception 567
- deliberation 2077
- action_selection 567
- continuation_caption 44
- future_verification 84

这版用于训练模型输出更细的 `visual_state`、具体真人导购动作和话术，以及
action-conditioned future verification。旧 `piwm_train_synth_v1.jsonl`
仍保留为只含主训练 perception / deliberation 的轻量入口。

`piwm_train_synth_v2.jsonl` 来自 `PIWM-Train-Synth-v2`，同样是 2554 examples：perception 543 / deliberation 2011。它的价值是 schema v2.2 字段完整，而不是新增视频规模。

`piwm_train_target_specialization_v1.jsonl` 来自 `PIWM-Target-Frontcam-v1`，共 708 examples：perception 118 / deliberation 472 / action_selection 118。它适合作为 low-resource target-domain specialization 的 Stage-2 数据入口。当前 30 条 target test records 已完成项目负责人 QA 复核，并导出 180 行 reviewed eval rows 到 `data/official/domain_specialization_eval_v1/target_frontcam_test_qa_reviewed_all.jsonl`；这些 QA 状态也已写回 target ms-swift 文件的 test split 元数据。

`piwm_target_promptready_v1/promptready_index.jsonl` 来自轻量 `piwm` 扩展后的 318 条上游记录。它的 best DialogueAct 分布已均衡到每类 53 条，但其中 200 条没有视频，必须先生成 Kling 视频并抽帧，才能进入 `PIWM-Target-Frontcam-v1` 或 ms-swift 多模态训练。

`piwm_train_general_plus_target_v1.jsonl` 是 general v2 + target frontcam 的 mixed-view joint SFT 对照入口，共 3262 examples：general=2554，target=708。它用于对比 joint training；正式 two-stage specialization 仍应分开使用 `piwm_train_synth_v2.jsonl` 和 `piwm_train_target_specialization_v1.jsonl`。

## Reporting Rule

论文和汇报中优先使用正式名：

- 写 `PIWM-Train-Synth-v1`，默认引用 `data/official/piwm_train_synth_v1/` 或 `data/official/ms_swift/piwm_train_synth_v1.jsonl`，不要用 `priority1000_unreviewed*` 当公开数据名。
- 写 v2.2 数据格式时，引用 `PIWM-Train-Synth-v2` 和 `data/official/piwm_train_synth_v2/`。
- 写平衡动作空间或 policy 生成入口时，引用 `PIWM-PolicySlice-v2`；不要把它写成 filmed dataset。
- 写 target 域设备前置摄像头数据时，引用 `PIWM-Target-Frontcam-v1`；可以说明 30 条 test records 已通过项目负责人 QA 复核，但全体 118 仍不是 full human QA-reviewed corpus。
- 写 target 扩展生成队列时，引用 `PIWM-Target-PromptReady-v1`；不要把其中 200 条 video-pending 样本写成 filmed multimodal dataset。
- 写 `PIWM-Eval-QA-v1`，不要写 `priority40_qareviewed_sample`。
- 写 `PIWM-WorldModel-v1` / `PIWM-FutureVerification-v1`，不要写 `pilot30_with_continuations`。
- `PIWM-RealShoot-v1` 目前只能写成 planned real-shooting protocol and manifest schema，不能写成已采集真实数据。

旧名只在复现实验路径、脚本路径或附录 manifest 中出现。

旧 manifest 副本已移到 `data/official/archive/`。当前有效 manifest 只有 `DATASET_MANIFEST.json`。

## Red Lines

- `PIWM-Train-Synth-v1` 不是 QA-pass 数据。
- `PIWM-Train-Synth-v1` 不是 target terminal 数据集；不要把其中的真人导购动作写成终端硬件已采集行为。
- 不能写“1000 条视频已完成”；当前正式训练集是 543 loaded parent / 2554 SFT examples。
- `smoke`、`early pilot`、`DPO adapter`、`missing retry queue` 不属于正式数据集。
- `FutureVerification` 的 `visible_reaction` 使用 `engagement_pattern_change / gaze_and_attention_change / body_and_hands_change` 三轴，不再使用旧的四字段 reaction schema。
- `PIWM-RealShoot-v1` 在视频、音频、UI 录屏、转写和 QA 字段填齐前，不得进入 QA-reviewed eval。
- `PIWM-Target-Frontcam-v1` 的 30 条 test records 已完成项目负责人 QA 复核；不要把 88 条 train records 也写成 human QA-reviewed。
- `PIWM-Target-PromptReady-v1` 的 200 条扩展样本没有 Kling 视频和抽帧，不得进入多模态 SFT 统计。
