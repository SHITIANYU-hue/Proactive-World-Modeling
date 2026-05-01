# PIWM Docs Entry Point

更新时间：2026-05-01

本文是 `docs/` 的唯一阅读入口。当前阶段的原则是：

```text
先服务 NeurIPS sprint 的实验闭环，再保留长期研究背景。
```

如果只想知道“现在做到哪、下一步做什么”，只读第 1 节。

## 1. 当前必读

| 顺序 | 文档 | 用途 |
|---:|---|---|
| 1 | [current/experiment_result_digest.md](current/experiment_result_digest.md) | 当前已落盘实验结果速览：能写什么、还缺什么 |
| 2 | [current/experiment_status_main_table_v2.md](current/experiment_status_main_table_v2.md) | 主表 v2、visual ablation、frame budget、Future Verification 结果 |
| 3 | [current/company_openrouter_funding_brief.md](current/company_openrouter_funding_brief.md) | 精简预算说明（完整版见 `company_data_status_for_openrouter.md`） |
| 4 | [current/company_data_status_for_openrouter.md](current/company_data_status_for_openrouter.md) | 完整版：进度、数据、效果、OpenRouter 机型与额度、附录主表（口径与精简版一致） |
| 5 | [current/current_sprint_status_and_reporting_policy.md](current/current_sprint_status_and_reporting_policy.md) | 对外报告口径：QA-reviewed / synthetic train / diagnostic-only 边界 |
| 6 | [current/priority_generation_policy.md](current/priority_generation_policy.md) | 新增 Kling 额度如何扩到 500/1000 parent synthetic |
| 7 | [current/remote_sprint_runbook.md](current/remote_sprint_runbook.md) | 远端数据盘、ms-swift、Kling、状态检查命令 |

## 2. 当前执行线

| 任务 | 主文档 | 备注 |
|---|---|---|
| 扩训练数据 | [current/priority_generation_policy.md](current/priority_generation_policy.md) | 先跑 `priority500_new_after280`，再视额度追加 `priority1000_new_after280` |
| 主实验结果冻结 | [current/experiment_status_main_table_v2.md](current/experiment_status_main_table_v2.md) | 表格数字必须来自落盘 JSON/Markdown |
| 结果摘要与写作入口 | [current/experiment_result_digest.md](current/experiment_result_digest.md) | 适合给写作对话或导师快速阅读 |
| 公司预算沟通 | [current/company_openrouter_funding_brief.md](current/company_openrouter_funding_brief.md) | 一页摘要；细节与表格见完整版 |
| 组内技术汇报 | [current/company_data_status_for_openrouter.md](current/company_data_status_for_openrouter.md) | 完整叙述 + 预算档位 + 附录数字 |
| 远端运行 | [current/remote_sprint_runbook.md](current/remote_sprint_runbook.md) | 所有大数据和视频放 `/root/lanyun-fs`，不要放系统盘 |
| 文档维护 | [contracts/docs_maintenance_rules.md](contracts/docs_maintenance_rules.md) | 新增或归档文档前先看 |

## 3. 研究契约

这些文件定义 PIWM 的方法边界和数据契约。它们不是每天第一入口，但改代码/写方法章节时需要查。

| 文档 | 用途 |
|---|---|
| [contracts/claim_to_artifact_audit.md](contracts/claim_to_artifact_audit.md) | 论文 claim 与代码/数据工件对应关系 |
| [contracts/world_model_supervision_contract.md](contracts/world_model_supervision_contract.md) | World Model 监督契约，含 continuation / Future Verification 逻辑 |
| [contracts/visual_input_contract.md](contracts/visual_input_contract.md) | 多视角、K=3 抽帧、QA gate、frame manifest |
| [contracts/expert_provenance_upgrade_plan.md](contracts/expert_provenance_upgrade_plan.md) | 专家规则 provenance 补强计划 |
| [contracts/kling_api_usage.md](contracts/kling_api_usage.md) | Kling wrapper 使用说明 |

## 4. 背景与历史参考

这些文件保留历史价值，但不再作为当前决策入口。

| 文档 | 当前状态 |
|---|---|
| [background/data_generation_loop_status.md](background/data_generation_loop_status.md) | 早期数据闭环诊断，已被 `current/` 的 sprint 状态覆盖 |
| [background/data_loop_master_plan.md](background/data_loop_master_plan.md) | 早期主计划，当前执行以 `current/` 为准 |
| [background/current_code_status.md](background/current_code_status.md) | 代码状态冷启动说明，查老 pipeline 时有用 |
| [background/intro_related_work_v6.md](background/intro_related_work_v6.md) | 早期 intro + related work 草稿，不等于当前 paper 最新结果 |
| [background/related_work_expert_distillation.md](background/related_work_expert_distillation.md) | 专家蒸馏 related-work 背景 |
| [background/readable_data_plan_background.md](background/readable_data_plan_background.md) | 给非实现者看的可读版背景 |
| [background/pilot30_continuation_review_report.md](background/pilot30_continuation_review_report.md) | pilot30 continuation 历史审阅报告 |
| [background/neurips_sprint_master_plan.md](background/neurips_sprint_master_plan.md) | sprint 初始总计划，已被当前结果文档覆盖 |
| [background/neurips_sprint_codex_plan.md](background/neurips_sprint_codex_plan.md) | sprint 初始执行计划，已被当前结果文档覆盖 |
| [background/neurips_sprint_result_snapshot_20260430.md](background/neurips_sprint_result_snapshot_20260430.md) | 2026-04-30 快照，已被当前结果文档覆盖 |

## 5. 不要混用的口径

| 概念 | 正确用法 |
|---|---|
| `priority280_unreviewed` | training-only synthetic，不写成 QA-pass |
| `priority40_qareviewed_sample` | 当前最干净的 QA-reviewed parent eval subset |
| `pilot30_with_continuations` | World Model / Future Verification 小规模视觉监督，不是主训练规模来源 |
| `Future Verification full84` | action-conditioned future verification 证据，不是完整 benchmark |
| DPO | 当前 sprint 暂停，不作为主实验阻塞项 |

## 6. 文档维护规则

- 新增文档前先判断是否能放入现有 `current/` 或 `contracts/`。
- 如果只是实验结果摘要，优先更新 [current/experiment_result_digest.md](current/experiment_result_digest.md)。
- 如果是主表数字或消融，优先更新 [current/experiment_status_main_table_v2.md](current/experiment_status_main_table_v2.md)。
- 如果是数据生成规模、Kling 队列、QA 口径，优先更新 [current/priority_generation_policy.md](current/priority_generation_policy.md) 或 [current/current_sprint_status_and_reporting_policy.md](current/current_sprint_status_and_reporting_policy.md)。
- `background/` 只作为历史参考，不再扩写。
