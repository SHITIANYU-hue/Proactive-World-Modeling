# PIWM 给 Claude 的项目决策简报

更新时间：2026-05-18 CST  
用途：让 Claude 快速理解 PIWM 当前项目状态，并作为论文叙事、数据口径、实验设计的决策审阅者参与。

## 1. 一句话理解本项目

PIWM（Proactive Intent World Model）研究的是：**多模态模型能否从顾客的短视觉观察中判断顾客状态，比较多个主动导购动作的后果，并选择一个合适的主动响应**。

当前论文叙事已经收敛为：

```text
general retail guidance corpus
  -> low-resource target-frontcam smart-vending specialization
```

也就是说，项目不再把重点放在“target 域视频数量很大”，而是放在：模型先从 general 零售导购语料学通用主动导购能力，再用少量 target 前置摄像头数据适配到智能售货终端场景。

## 2. 当前最重要的决策口径

### 2.1 强主会故事，不等 200 条新视频

当前决定是：**坚持强主会故事，但不生成 200 条新的 prompt-pending 视频**。

强故事不是：

```text
我们有 300+ target 视频。
```

而是：

```text
我们构造了一个 general -> target 的低资源跨域适配问题：
general 数据学通用主动导购，
88 条 target train 做专项适配，
30 条 target QA-reviewed test 做 in-domain evaluation。
```

因此，200 条 `PIWM-Target-PromptReady-v1` video-pending 样本只能作为未来扩展队列，不能进入当前论文主数据规模，也不能写成 filmed multimodal training data。

### 2.2 论文要证明的核心问题

Claude 参与决策时应围绕这个问题判断：

> 少量 target-frontcam 数据是否足以把 general proactive retail guidance 迁移到智能终端前置摄像头场景？

对应实验应至少包含：

1. `general_on_target`：只用 general 训练，在 target QA test 上 zero-shot。
2. `target_on_target`：general 后继续用 88 条 target train 适配，再测 target QA test。
3. `joint_on_target`：general + target 混合训练，作为 joint baseline。
4. `target_on_general`：target-specialized 模型回测 general QA eval，检查是否遗忘 general 能力。

目前这些训练和评测结果还没有落地，这是当前论文主风险。

## 3. 当前数据资产

| 数据名 | 角色 | 当前规模 | QA 口径 |
|---|---|---:|---|
| `PIWM-Train-Synth-v2` | general retail guidance 训练集 | 543 parent / 2554 training examples | synthetic train，未人工视觉 QA |
| `PIWM-Target-Frontcam-v1` train | target-frontcam 适配训练 | 88 records / 528 examples / 264 frames | synthetic train |
| `PIWM-Target-Frontcam-v1` test | target-frontcam in-domain test | 30 records / 180 examples / 90 frames | 项目负责人 QA pass |
| `PIWM-Eval-QA-v1` | general QA eval / forgetting check | 36 parent / 162 eval rows | QA-reviewed subset |
| `PIWM-Target-PromptReady-v1` | target 未来生成队列 | 318 prompt-ready records，其中 200 video-pending | 不是 filmed data |

需要强调：

- `PIWM-Target-Frontcam-v1` 全量 118 条不是 full human QA-reviewed corpus。
- 只有其中 30 条 test records 是项目负责人 QA-reviewed。
- 88 条 target train records 可用于训练，但不能写成 benchmark。
- 200 条 prompt-ready / video-pending 不进入当前多模态训练规模。

## 4. 数据如何生成：专家知识到结构化输出

PIWM 的数据不是普通人工随手标注，也不是让模型凭空写答案。它来自一个可审计的专家知识链路。

### 4.1 知识来源

当前专家知识来自销售学和消费者行为研究，包括：

- AIDA：Attention / Interest / Desire / Action，用作购买阶段骨架。
- OpenStax marketing：消费者决策过程、购买影响因素、personal selling 过程。
- SPIN Selling：低压力提问、需求澄清、need-payoff 等 consultative selling 原则。
- Psychological Reactance Theory：解释高压推荐、强推、打断顾客自主感时为什么会反弹。
- Babin / Arnold / Reynolds 等 shopping motivation 研究：支撑 hedonic / utilitarian / recreational / gift shopping 的 intent prior。

版权边界：

- 开放教材可做 compact paraphrase。
- 受版权保护的书籍和论文只做 citation-level anchor，不把长篇原文放入训练数据。

### 4.2 当前专家库规模

当前专家知识库包含：

- 27 条 `distilled principles`
- 78 条 `source-linked conditional rules`

规则类型包括：

- 视觉线索 -> 顾客状态
- persona / state -> intent
- persona -> intent tier
- state + AIDA -> candidate actions
- action-conditioned transition / reward / risk / benefit / failure mode

### 4.3 生成链路

一条数据的结构化输出按下面链路生成：

```text
scene cues
  -> customer state
  -> intent tier
  -> candidate actions
  -> action outcomes
  -> training targets
```

其中：

- `customer state` 包含 AIDA 阶段和 BDI。
- BDI 是 belief / desire / intention，即顾客相信什么、想要什么、打算做什么。
- `candidate actions` 来自 6 个 DialogueAct 的候选规则。
- `action outcomes` 包含 next state、reward、risk、benefit、failure mode。
- `training targets` 被导出为 perception、deliberation、action selection 等训练任务。

这条链路的学术价值是可审计性：如果某个 label 有问题，可以追到规则和 source link，而不是只能说“模型或标注员这么写了”。

## 5. 动作空间

当前统一使用 6 个 DialogueAct：

| DialogueAct | 含义 |
|---|---|
| `Greet` | 问候、开启或结束互动 |
| `Elicit` | 询问需求，澄清顾客意图 |
| `Inform` | 提供事实信息，如比较、演示、属性、价格 |
| `Recommend` | 推荐商品，区分 soft / firm pressure |
| `Reassure` | 降低压力，安抚犹豫 |
| `Hold` | 等待、静默、低干预 |

动作不是单个扁平标签，而是 `act + params`。

例如：

```json
{"act": "Recommend", "params": {"target": "item", "pressure": "soft"}}
```

或：

```json
{"act": "Inform", "params": {"content_type": "comparison", "depth": "brief"}}
```

旧 `A1-A8` 只作为历史兼容 alias，不应作为论文主表达。

## 6. General 与 Target 的主体差异

这是 Claude 必须注意的一个核心边界。

### General corpus

`PIWM-Train-Synth-v2` 保留的是 human-salesperson guidance logic：

- 视角：第三人称 / 导购可观察视角。
- 行为主体：真人导购逻辑。
- 输出：导购应该如何介入、说什么、何时等待。

### Target corpus

`PIWM-Target-Frontcam-v1` 是 target terminal / smart-vending logic：

- 视角：设备前置摄像头。
- 行为主体：智能终端或数字人售货柜。
- 输出：屏幕、语音、灯效、等待状态等 terminal behavior。

不要把 general 的真人导购动作写成 target 终端硬件行为；也不要把 target 终端行为反写成真人导购肢体动作。

## 7. QA 口径

QA 是 Quality Assurance，即质量复核。这里主要检查：

- 顾客是否可见。
- 头部方向或视线是否可解释。
- 身体姿态是否可见。
- 终端 / 柜体上下文是否存在。
- 三张抽帧图是否时间连续。
- 标签是否能被视觉证据支撑。

当前 target test QA 结果：

```text
30 pass / 0 fail / 2 warning
```

两个 warning：

- `target_piwm_797`：玻璃反光可见，但顾客主体清楚。
- `target_piwm_815`：attention 阶段第一张图带有部分进入前上下文，但后续帧清楚。

重要边界：

- QA 证明的是“当前观察 + 标签”可用。
- QA 不证明动作造成了后续反应。
- 例如 `Greet(close)` 样本第三张图里顾客笑了，这只能当作当前状态视觉证据，不能写成 “Greeting 导致顾客笑”。

## 8. 当前论文数据部分状态

已经有两份数据部分审阅稿：

- 英文 LaTeX：`paper/data_section_emnlp.tex`
- 中文审阅稿：`paper/data_section_emnlp_zh.md`

这两份稿件已经包含：

- 低资源 target specialization 叙事。
- general / target / eval 数据表。
- perception / deliberation / action selection 任务表。
- 6-act 动作空间与 target action 分布表。
- QA 说明。
- 专家知识到结构化输出链路。

Claude 可以直接审这两份稿件的逻辑、措辞和是否过度主张。

## 9. 当前最大缺口

当前不是数据格式缺口，而是实验证据缺口。

仍缺：

1. Stage-1 general SFT 正式新跑分。
2. Stage-2 target SFT 正式新跑分。
3. joint baseline。
4. general-on-target zero-shot eval。
5. target-specialized eval。
6. target-on-general forgetting check。

如果这些结果显示 target specialization 没有明显收益，强主会故事会变弱。因此，Claude 应重点审：当前数据设计是否足以支撑这些实验，以及实验结果应该如何呈现。

## 10. Claude 应参与判断的问题

请 Claude 重点回答以下问题：

1. **主故事是否成立？**  
   “general proactive retail guidance -> low-resource target-frontcam specialization” 是否足够强，还是仍显得像小规模 pilot？

2. **数据规模是否表述得当？**  
   118 条 target video-backed + 30 QA-reviewed target test 是否能作为低资源适配实验成立？论文中如何避免 reviewer 质疑规模太小？

3. **专家知识链路是否可信？**  
   27 principles + 78 source-linked rules 的叙事是否足够支撑“pedagogy-anchored supervision”？是否需要在论文中加入更多 provenance 表或例子？

4. **评估矩阵是否完整？**  
   zero-shot、Stage-2、joint baseline、forgetting check 是否够？是否还必须加 target-only baseline？

5. **是否存在过度主张？**  
   哪些句子容易被 reviewer 认为夸大？尤其注意：
   - 不能说 full target corpus QA-reviewed。
   - 不能说 200 pending 是视频数据。
   - 不能说 Greet 导致顾客笑。
   - 不能说 expert-reviewed rules，当前是 source-linked / project-reviewed / theory-anchored。

6. **数据章节是否足够 EMNLP 风格？**  
   当前数据章节是否更像 NeurIPS 方法论文，还是足够贴近 EMNLP 对 dataset / annotation / evaluation protocol 的期待？

## 11. Claude 不应误读的红线

- 不要把 `PIWM-Target-PromptReady-v1` 的 200 条 video-pending 写成已完成视频。
- 不要把 `PIWM-Target-Frontcam-v1` 全量 118 条写成 full human QA-reviewed。
- 不要把 `PIWM-Train-Synth-v2` 写成新增视频规模；它是同一批 543 parent 的 v2.2 schema 独立导出。
- 不要把旧 `A1-A8` 写成主动作空间；正文应写 6-act `DialogueAct + params`。
- 不要把 current observation frames 解释成 post-action causal reaction。
- 不要说已有 Stage-1 / Stage-2 target specialization 结果；目前只是入口和数据已准备。

## 12. Claude 可直接查看的文件

如果 Claude 只能看少量文件，优先顺序如下：

1. `paper/data_section_emnlp_zh.md`  
   中文数据章节审阅稿，最适合先判断叙事。

2. `paper/data_section_emnlp.tex`  
   英文 LaTeX 数据章节，可直接进入论文。

3. `docs/current/domain_specialization_experiment_plan.md`  
   训练与评估矩阵。

4. `docs/current/dataset_inventory.md`  
   数据总账和规模口径。

5. `data/official/DATASET_MANIFEST.json`  
   机器可读 official manifest。

6. `docs/v2_validation/distillation_summary.md`  
   专家知识蒸馏、principles、rules、source 链路状态。

7. `docs/v2_validation/piwm_target_frontcam_import.md`  
   target frontcam 数据如何从轻量 `piwm` 仓库进入主项目。

## 13. 建议给 Claude 的审阅提示词

可以直接把下面这段给 Claude：

```text
你现在作为 PIWM 项目的论文和数据决策审阅者。
请先读这份 brief，再重点审 paper/data_section_emnlp_zh.md 和 paper/data_section_emnlp.tex。

请判断：
1. 当前“general retail guidance -> low-resource target-frontcam specialization”的强主会故事是否成立。
2. 118 条 target video-backed 数据、88 train、30 QA-reviewed test 的数据口径是否足以支撑 EMNLP 论文。
3. 专家知识 -> distilled principles -> conditional rules -> structured outputs 的链路是否说得可信，是否需要补表或例子。
4. 当前 eval matrix 是否足够，是否必须增加 target-only baseline 或 human eval。
5. 哪些句子存在过度主张、概念混淆或 reviewer 会攻击的点。

请输出：
- 你认可的核心叙事
- 必须修改的高风险表述
- 建议补充的实验或表格
- 你认为当前最强和最弱的论文 claim
```

