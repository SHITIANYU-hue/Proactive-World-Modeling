# PIWM Documentation Map

更新时间：2026-05-17 CST

本文是主仓库 `docs/` 的唯一人工阅读入口。当前项目口径已经从单纯的 sprint 结果整理，收敛为：

```text
general retail guidance corpus -> target-frontcam smart-vending specialization
```

读文档时先按目标选择路线，不要从文件名挨个打开。

## 0. 当前一句话状态

| 层级 | 当前状态 | 入口 |
|---|---|---|
| General training | `PIWM-Train-Synth-v2`，543 parent / 2554 ms-swift examples，schema v2.2 独立导出 | [current/dataset_inventory.md](current/dataset_inventory.md) |
| Target video-backed | `PIWM-Target-Frontcam-v1`，118 records / 354 frames / 708 examples，30 test records 已完成项目负责人 QA 复核并写回 target 数据 | [current/domain_specialization_experiment_plan.md](current/domain_specialization_experiment_plan.md) |
| Target prompt-ready | `PIWM-Target-PromptReady-v1`，318 records，其中 200 条仍是 video-pending | [../data/official/piwm_target_promptready_v1/README.md](../data/official/piwm_target_promptready_v1/README.md) |
| Domain eval | general QA + target-frontcam test eval entrypoints 已生成；训练和跑分仍待完成 | [../data/official/domain_specialization_eval_v1/eval_sets_summary.md](../data/official/domain_specialization_eval_v1/eval_sets_summary.md) |
| Real shooting | `PIWM-RealShoot-v1` 仍是 S01-S12 A/B manifest 和拍摄协议，不是已采集真实数据 | [current/piwm_real_shooting_scripts_S01_S12.md](current/piwm_real_shooting_scripts_S01_S12.md) |

## 1. 只想知道数据现在能不能用

按这个顺序读：

| 顺序 | 文档 | 回答的问题 |
|---:|---|---|
| 1 | [current/dataset_inventory.md](current/dataset_inventory.md) | 当前 official 数据总账：训练、评估、World Model、target、real-shooting 分别是什么 |
| 2 | [current/project_progress_report_2026-05-17.md](current/project_progress_report_2026-05-17.md) | 给项目负责人和外部协作者看的单文档进度报告 |
| 3 | [../data/official/README.md](../data/official/README.md) | `data/official/` 下每个 canonical 数据名对应什么，哪些名字不能混用 |
| 4 | [../data/official/DATASET_MANIFEST.json](../data/official/DATASET_MANIFEST.json) | 机器可读 manifest：行数、角色、QA 状态、入口路径 |
| 5 | [current/current_sprint_status_and_reporting_policy.md](current/current_sprint_status_and_reporting_policy.md) | 对外汇报时哪些能写成 QA-reviewed，哪些只能写成 synthetic / pending |

核心红线：

- `PIWM-Train-Synth-v2` 是同一批 543 parent 的 v2.2 schema 独立导出，不代表新增视频。
- `PIWM-Target-PromptReady-v1` 里的 200 条 video-pending 不是多模态训练数据，必须等 Kling 视频、抽帧和 QA 完成。
- `PIWM-Target-Frontcam-v1` 的 30 条 test records 已完成项目负责人 QA 复核；88 条 train records 仍是 `synthetic_unreviewed`，不要写成 full human-reviewed corpus。
- `PIWM-RealShoot-v1` 目前只能写成 planned real-shooting protocol / manifest template。

## 2. 要写 EMNLP / domain-specialization 实验

按这个顺序读：

| 顺序 | 文档 | 回答的问题 |
|---:|---|---|
| 1 | [current/domain_specialization_experiment_plan.md](current/domain_specialization_experiment_plan.md) | general -> target 的 two-stage SFT、joint baseline、eval matrix |
| 2 | [current/paper_data_section_blueprint.md](current/paper_data_section_blueprint.md) | 论文数据部分怎么讲：general corpus、target corpus、QA、真实拍摄协议 |
| 3 | [current/claude_project_brief_2026-05-18.md](current/claude_project_brief_2026-05-18.md) | 给 Claude 的项目决策简报：叙事、数据、风险和审阅问题 |
| 4 | [../paper/data_section_emnlp.tex](../paper/data_section_emnlp.tex) | 可直接进入论文的 EMNLP 风格数据章节草稿 |
| 5 | [current/dataset_inventory.md](current/dataset_inventory.md) | 论文表格里的数据名、规模、QA 口径 |
| 6 | [../data/official/domain_specialization_eval_v1/eval_sets_summary.md](../data/official/domain_specialization_eval_v1/eval_sets_summary.md) | 已生成的 target/general eval JSONL 入口 |
| 7 | [current/experiment_result_digest.md](current/experiment_result_digest.md) | 旧主实验结果速览；引用前确认是否仍服务当前 EMNLP 叙事 |
| 8 | [current/experiment_status_main_table_v2.md](current/experiment_status_main_table_v2.md) | 主表、ablation、frame budget、Future Verification 历史结果 |

当前 EMNLP 关键缺口：

- Stage-1 / Stage-2 SFT 还没有完整新跑分。
- target-only baseline、joint baseline、forgetting check 还没有完整评测日志。
- 论文口径已改为低资源 target specialization；118 条 target video-backed 数据不再被视为必须扩到 300+，但需要用 zero-shot / Stage-2 / joint baseline 的结果证明少量 target 数据确实带来迁移收益。

## 3. 要改 schema、动作空间或生成链路

先读契约，再改代码或数据：

| 文档 | 用途 |
|---|---|
| [contracts/data_schema_v2_contract.md](contracts/data_schema_v2_contract.md) | 当前成熟数据格式：MainSchemaRecord、ShootingClipRecord、导出字段和维护规则 |
| [contracts/action_space_realization_contract.md](contracts/action_space_realization_contract.md) | 6 个 DialogueAct、`act + params`、真人导购逻辑与 target terminal 的边界 |
| [contracts/data_generation_chain_v2_1_contract.md](contracts/data_generation_chain_v2_1_contract.md) | 专家知识、规则、scenario、label、policy slice、official 重导的唯一维护链路 |
| [contracts/visual_input_contract.md](contracts/visual_input_contract.md) | 视角、抽帧、frame manifest、QA gate |
| [contracts/world_model_supervision_contract.md](contracts/world_model_supervision_contract.md) | continuation / Future Verification 监督定义 |
| [contracts/claim_to_artifact_audit.md](contracts/claim_to_artifact_audit.md) | 论文 claim 与代码/数据工件对应关系 |
| [contracts/docs_maintenance_rules.md](contracts/docs_maintenance_rules.md) | 新增、归档、重命名文档前先看 |

动作和字段的当前原则：

- 新 policy 语义以 6 个 `DialogueAct + params` 为中心。
- `A1-A8 / T-state` 只保留为 legacy alias、迁移键或历史数据解释。
- 主项目 `PIWM-Train-Synth-*` 保留真人导购逻辑；target-frontcam 数据使用智能终端 / 设备前置摄像头视角。
- 旧 `co_acts` 不再作为新 official 顶层字段；辅助动作放到 `act_params.supporting_acts`。

## 4. 要审查这次 v2.2 迁移做了什么

这些是审计和验证报告，不是日常入口：

| 文档 | 用途 |
|---|---|
| [v2_validation/v2_2_release_notes.md](v2_validation/v2_2_release_notes.md) | v2.2 上线说明：字段、产物、计数、边界 |
| [v2_validation/compatibility_report.md](v2_validation/compatibility_report.md) | official 543 在 v2.2 下的兼容分级和 policy re-derivation |
| [v2_validation/action_distribution.md](v2_validation/action_distribution.md) | v1 best 分布、official 543 v2 重推导、864 policy slice 分布 |
| [v2_validation/piwm_target_frontcam_import.md](v2_validation/piwm_target_frontcam_import.md) | 轻量 `piwm` target-frontcam 数据如何导入主仓库 |
| [v2_validation/distillation_summary.md](v2_validation/distillation_summary.md) | intent tier、failure mode、Recommend pressure 的专家蒸馏状态 |
| [v2_validation/failure_mode_coverage.md](v2_validation/failure_mode_coverage.md) | failure_mode taxonomy 覆盖范围和未建模边界 |
| [v2_validation/v2_2_test_coverage.md](v2_validation/v2_2_test_coverage.md) | v2.2 新增测试清单和未覆盖项 |
| [v2_validation/v2_2_reexport_dry_run.md](v2_validation/v2_2_reexport_dry_run.md) | official v2.2 dry-run 和独立导出记录 |
| [v2_validation/v2_2_reexport_diff_preview.md](v2_validation/v2_2_reexport_diff_preview.md) | `--output-diff` 写回预演 |

## 5. 真实拍摄和外部附件

| 文档 | 用途 |
|---|---|
| [current/piwm_real_shooting_scripts_S01_S12.md](current/piwm_real_shooting_scripts_S01_S12.md) | 拍摄团队唯一脚本：S01-S12 A/B 单文件 |
| [current/piwm_real_shooting_data_annotation_appendix_v2.md](current/piwm_real_shooting_data_annotation_appendix_v2.md) | 真实素材后期入库字段：ShootingClipRecord、QA、asset manifest |
| [current/piwm_real_shooting_execution_checklist_v2.md](current/piwm_real_shooting_execution_checklist_v2.md) | 执行 checklist；不要替代脚本 |
| [source_materials/2026-05-action-space/source_digest.md](source_materials/2026-05-action-space/source_digest.md) | 本次动作空间整合的原始附件副本和来源优先级 |

## 6. 目录和远端运行

| 文档 | 用途 |
|---|---|
| [current/project_directory_map.md](current/project_directory_map.md) | 本地、远端、official、checkpoint、视频、docs 的职责边界 |
| [current/remote_sprint_runbook.md](current/remote_sprint_runbook.md) | 远端数据盘、Kling、ms-swift、状态检查命令 |
| [current/repo_cleanup_github_plan.md](current/repo_cleanup_github_plan.md) | 本地/服务器如何用 Git 管代码文档，数据留数据盘 |
| [current/local_artifacts_layout.md](current/local_artifacts_layout.md) | 本机生成产物、review sheet、cache 的整理位置 |

## 7. 轻量 `piwm` 仓库怎么读

轻量仓库只负责 target 数据生成，不负责主论文总账：

```text
/Users/mutsumi/Desktop/WorkSpace/piwm
```

读：

- `/Users/mutsumi/Desktop/WorkSpace/piwm/docs/index.md`
- `/Users/mutsumi/Desktop/WorkSpace/piwm/docs/schema.md`
- `/Users/mutsumi/Desktop/WorkSpace/piwm/docs/pipeline.md`
- `/Users/mutsumi/Desktop/WorkSpace/piwm/docs/action_space.md`

它的核心链路是：

```text
seed -> manifest -> prompt -> video
seed -> manifest -> labeled
```

主仓库负责把这些 target 数据转换成 `PIWM-Target-Frontcam-v1`、`PIWM-Target-PromptReady-v1` 和 domain-specialization eval entrypoints。

## 8. 背景和历史材料

`docs/background/` 和 `docs/archive/` 只作历史参考，不作为当前执行入口。常见历史材料包括：

- 早期 NeurIPS sprint plan / result snapshot；
- 早期 data loop master plan；
- 旧 intro / related work 草稿；
- 被 v2.2 contract 和 current docs 替代的设计草稿。

如果当前文档和历史文档冲突，优先级为：

```text
data/official/DATASET_MANIFEST.json
> data/official/README.md
> docs/current/dataset_inventory.md
> docs/contracts/*
> docs/v2_validation/*
> docs/background/*
> docs/archive/*
```
