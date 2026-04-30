# PIWM Claim-to-Artifact Audit

更新时间：2026-04-29（Viewpoint V1-V4 后更新）

## 1. 目的

本文把论文 `paper/main.tex` 中的核心 claim 映射到当前代码和数据工件，标出缺口与修正优先级。

状态定义：

- `covered`：当前已有代码/数据工件基本支撑；
- `partial`：已有骨架，但语义或字段不完整；
- `blocking`：论文 claim 当前缺少必要工件，继续实现前必须补；
- `future`：论文或实验后续增强，当前不阻塞小规模 pilot。

## 2. P0 审计表

| Claim | 论文位置 / 内容 | 当前工件 | 状态 | 缺口 | 必须修正 |
|---|---|---|---|---|---|
| Pedagogy-derived action space | action set compiled from retail training manuals | `conditional_rules.jsonl` 72 条 seed；`rule_source_links.jsonl` 全量分类；32 manual-supported / 40 theory-anchored / 0 seed-only / 0 candidate-for-removal | partial | 所有 seed rule 已有 source link；但还没有 expert-reviewed，且 reward 数值仍不是教材推导 | 人工审阅低强度 anchors；补 reward components；不要声称 all rules are expert-reviewed |
| AIDA-BDI state | `s_t=(sigma_t,b_t,d_t,i_t)` | `MainSchemaRecord.bdi` + `aida_stage` + `latent_state/state_subtype` | partial | 字段契约已落地；BDI 当前仍是 deterministic rule-derived summary，未人工审阅 | 人工审阅 BDI 模板；后续可接入 source-backed BDI principles |
| Perception target | `<sigma,b,d,i,rho,C>` | `state_inference.output` | covered | `output.aida_stage`、`output.bdi`、`output.state_subtype` 已进入监督目标 | pilot 后检查训练脚本是否读取这些字段 |
| Deliberation target | `<sigma_next,b_next,d_next,i_next,risk,benefit,reward>` | `transition_modeling.output` | covered | 已输出 `next_aida_stage`、`next_bdi`、`next_state_subtype/risk/benefit/reward` | pilot 后检查同一 parent state 下 action-conditioned future 是否足够多样 |
| Reward decomposition | `r=alpha*Delta_sigma+beta*Delta_m-gamma*c(a)` | `ActionOutcome.reward_components` | partial | 组件公式已校验，但 `delta_mental` 是为保持现有 scalar reward 反解得到，不是教材独立标注 | 后续把 reward components 上移到 expert corpus/source-backed rules |
| World Model supervision | same state + different action -> different future | `transition_modeling.jsonl` + `_stats.json` | partial | 已有 action 展开和 contrast stats；2 条 pilot 数据已经能展开 5 行 transition；规模仍小 | 扩到 30 条 QA pass session 后再校核 |
| Two-phase training | Phase 1 SFT, Phase 2 DPO | 三套 JSONL | partial | 文档未明确三套数据如何分配到训练阶段 | Phase 1: state + transition；Phase 2: preference |
| Real-store split | reserved real-store scenes for calibration/test | 无 | blocking | 无 real data schema、split、privacy metadata | 定义 `real_test` / `real_calibration` 契约 |
| OOD split | held-out products/personas | `data/scenario_manifest.jsonl` 已写入 `ood_product` 240 / `ood_persona` 280 | partial | sampler 已支持，但尚未跑出 OOD QA pass 样本 | pilot 扩到 OOD 子集 |
| Visual rendering | Kling renders visual side, not labels | `kling/generate_session.js` + `scripts/{scenario_sampler,prompt_builder,extract_frames,qa_gate}.py` | partial | API wrapper、prompt builder、QA gate 已具备；2 条 QA pass pilot 入库 | 扩 pilot 规模并接 VLM reviewer |
| Multi-view evaluation | salesperson_observable / surveillance_oblique / first_person_pov | `viewpoint` 字段贯穿 schema / sampler / prompt_builder / qa_gate / exporter；当前 manifest 1536 sales / 384 surveillance | partial | view-aware vs view-agnostic vs view-shift 三种实验设置尚未跑过；first_person_pov 暂缓 | 实现 view-shift evaluation；当前 viewpoint 仅进 meta，不进 input |
| Internal simulator | same VLM queried three times | method-side spec in archive | future | 数据契约未稳定，训练代码暂缓 | 数据 pilot 后解锁 `piwm_train` / `piwm_infer` |

## 3. 关键语义决策

### 3.1 `sigma` 与 `latent_state`

论文中的 `sigma_t` 是 AIDA 四阶段：

```text
attention / interest / desire / action
```

代码中的 `latent_state` 是行为/心理子状态：

```text
high_hesitation / active_evaluation / ready_to_decide / ...
```

修正原则：

- `aida_stage` 对应论文 `sigma_t`；
- `bdi` 对应论文 `(b_t,d_t,i_t)`；
- `latent_state` 不再冒充 `stage`，应定位为 `state_subtype` 或 `behavioral_state`；
- 训练 tag `<stage>` 只能输出 AIDA，不输出 `latent_state`。

### 3.2 Reward 标量与公式

当前 `reward=0.8` 等数值可以暂时保留，但必须能解释为：

```text
final_reward = alpha * delta_stage + beta * delta_mental - gamma * action_cost
```

建议规则 JSONL 增加：

```json
{
  "reward_components": {
    "delta_stage": 0.4,
    "delta_mental": 0.6,
    "action_cost": 0.1,
    "alpha": 0.4,
    "beta": 0.5,
    "gamma": 0.1,
    "final_reward": 0.75
  }
}
```

编译时：

- 校验 `final_reward` 在 `[-1, 1]`；
- 校验 `alpha + beta + gamma = 1`；
- 校验公式结果与 `final_reward` 在容差内一致；
- `TRANSITION_TABLE.reward` 使用 `final_reward`。

### 3.3 Real-store 数据契约

real-store 数据不经过 Kling，但必须进入同一主 schema。

建议字段：

```json
{
  "is_synthetic": false,
  "split": "real_test",
  "capture_source": "real_store",
  "privacy_review": {
    "consent_status": "approved",
    "face_blur": true,
    "brand_blur": true,
    "raw_video_restricted": true
  }
}
```

real-store 样本仍需：

- `prompt.json` 或等价 metadata；
- `frames/`；
- `qa_report.json`；
- 人工或专家确认的 cue/state/action labels。

## 4. DoD 映射

| DoD | 对应文档 | 验收条件 |
|---|---|---|
| DoD-0 | 本文 | P0 claims 均标注 `covered/partial/blocking`，不得把缺失 claim 写成已完成 |
| DoD-Expert | [01_data_generation_loop_status.md](01_data_generation_loop_status.md) | 六张运行时映射可从 expert corpus 编译 |
| DoD-Reward | 本文 | reward components 可解释并校验 final reward |
| DoD-Visual | [04_visual_input_contract.md](04_visual_input_contract.md) | sampled frames 支持 target cue |
| DoD-WM | [03_world_model_supervision_contract.md](03_world_model_supervision_contract.md) | 同一 parent state 有多条 action-conditioned future |
| DoD-View | [04_visual_input_contract.md](04_visual_input_contract.md) | viewpoint 字段贯穿 schema/sampler/prompt/qa/exporter；first_person_pov 暂缓；view-shift 实验记录 |
| DoD-Real | 本文 | real-store split 有 schema、privacy metadata 与 QA |

## 5. 当前最急修正

> 进度：第 1 项的规则容器已完成；provenance 已拆成 sales/modeling 两条线；72 条规则均已有 support_status。第 2-5 项的数据契约已完成第一版。具体见 RESEARCH_LOG 2026-04-29 20:55。

1. ~~将"规则表五张"修为"六张运行时映射"~~（**已完成 2026-04-29**：72 条 = 10/14/9/9/9/21）
2. ~~明确 `aida_stage=sigma`，`latent_state=state_subtype`~~（**已完成第一版 2026-04-29**）
3. ~~`state_inference.output` 增加 `aida_stage` 与 `bdi`~~（**已完成第一版 2026-04-29**）
4. ~~`transition_modeling.output` 增加 `next_bdi`，并明确 next stage 字段~~（**已完成第一版 2026-04-29**）
5. ~~`TRANSITION_TABLE` 增加 reward component 来源~~（**已完成第一版 2026-04-29**：当前为公式一致性组件，仍需 source-backed 升级）
6. ~~Multi-view 视觉契约~~（**已完成 V1-V4 2026-04-29**：viewpoint 字段贯穿管线；first_person_pov 暂缓；view-shift 评估未跑）
7. 新增 real-store split 契约。
