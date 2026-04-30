# PIWM — Proactive Intent World Model

PIWM 是一个面向**线下零售第三人称导购**场景的多模态主动 agent 研究项目。
它把同一个 VLM 当作 internal simulator：先识别顾客状态，再为每个候选话术
动作预测后果，最后决定**是否开口、何时开口、说什么**。

> 本仓库当前阶段只做**数据生成闭环**：从专家规则到可训练 JSONL。
> 训练 / 推理代码暂缓，等数据契约稳定后再解锁。

## 三层结构

```
Perception   →  从视觉 cue 推断  AIDA 阶段 + BDI（belief / desire / intention）
Deliberation →  对每个候选动作预测  next AIDA + next BDI + risk + benefit + reward
Action       →  比较 rollouts，选最优动作（包括沉默）
```

视觉输入是**多视角店内观察**（multi-view in-store visual observations）。
主设置是导购可观察视角（`salesperson_observable`）；监控/第三方视角与第一
人称视角保留作 view-shift 评估。详见 `docs/04_visual_input_contract.md`。

## 目录速览

```
piwm_data/                数据管线（pydantic v2 schema、规则层、loader、exporter）
piwm_data/expert_corpus/  专家规则语料层与 source provenance
scripts/                  scenario_sampler / prompt_builder / qa_gate
kling/                    Kling API 调用脚本（Node.js）
docs/                     活跃文档（00–12）+ archive
paper/                    NeurIPS 2026 草稿
data/scenario_manifest.jsonl  规则空间场景 manifest（重抽即可复现）
RESEARCH_LOG.md           动态索引与 phase 进度
```

## 5 分钟 quickstart

```bash
# 1. 跑测试
python3 -m pytest

# 2. 生成场景 manifest（含 viewpoint）
python3 -m scripts.scenario_sampler \
  --out data/scenario_manifest.jsonl \
  --stats-out data/_scenario_stats.json

# 3. 生成 10 条 mixed-view 人工审阅用 Kling prompt（dry-run，不调用 Kling）
python3 -m scripts.scenario_sampler \
  --out data/scenario_manifest_review10.jsonl \
  --stats-out data/_scenario_stats_review10.json \
  --limit 10 --balanced-cues
python3 -m scripts.prompt_builder \
  --manifest data/scenario_manifest_review10.jsonl \
  --out-root Archive_prompts_viewpoint_review \
  --overwrite

# 4. （可选）用 fixture 走通端到端 dry-run
node kling/generate_session.js \
  --prompt piwm_data/tests/fixtures/tiny_session/session_test_001/prompt.json \
  --out-root Archive_generated \
  --dry-run
```

## 文档导航

活跃文档索引以 `RESEARCH_LOG.md` 顶部 Active Document Index 为准。常用入口：

| 入口 | 何时看 |
|---|---|
| `RESEARCH_LOG.md` | 想知道项目最新进度、下一步在做什么 |
| `docs/00_claim_to_artifact_audit.md` | 想知道论文每个 claim 的代码 / 数据落地状态 |
| `docs/02_data_loop_master_plan.md` | 想知道 phase 顺序、DoD、进入条件 |
| `docs/03_world_model_supervision_contract.md` | 想知道哪些字段才算 World Model 监督 |
| `docs/04_visual_input_contract.md` | 想知道视频 / 多视角 / 抽帧 / QA 契约 |
| `docs/05_current_code_status.md` | 想知道当前代码每个文件做什么 |
| `docs/11_docs_maintenance_rules.md` | 想新增、归档、修改 docs |
| `docs/12_expert_provenance_upgrade_plan.md` | 想知道规则的来源链路 |

## 当前状态（高频更新）

实时数字看 `RESEARCH_LOG.md` 顶部条目；不要在本 README 里复述测试通过数。

## License

待补。本仓库当前为研究内部草稿。
