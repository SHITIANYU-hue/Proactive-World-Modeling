# `intro_related_work_v5.md` 修改与完善建议

目标文件：`/Users/mutsumi/Downloads/intro_related_work_v5.md`

参考材料：

- 图片信息整理文档：`docs/图片信息无损整理.md`
- 当前 v5 文稿：`/Users/mutsumi/Downloads/intro_related_work_v5.md`

## 0. 总体判断

v5 的论文主线基本正确：

1. 把任务定位为 in-store proactive sales guidance；
2. 把 gap 拆成 Perception、Action、Prospection；
3. 以 PIWM（Proactive Intent World Model）作为论文核心；
4. 用 third-person customer intent 区分现有 egocentric proactive agent；
5. 用 pedagogy-constrained action space 区分普通 sales dialogue / persuasion dialogue；
6. 用 action-conditioned next-state prediction 区分普通状态识别或单轮 ToM reasoning。

但是，v5 目前仍然偏“高层概念稿”。图片里显示的实际工作更具体：

- 数据不是抽象的 Markov transition equation，而是先抽成结构化五元组；
- Kling 生成结果需要先统一成主 schema；
- 同一主 schema 再导出三套训练集；
- 训练不是一个单一任务，而是 state inference、transition modeling、policy preference 三阶段；
- 推理时不是一次 forward 完成，而是“同一模型，多次调用”，把模型当成内部模拟器；
- evaluation 不只是和外部 baseline 比，还必须做完整路线的 ablation。

因此，v5 不需要推翻，但需要把这些“真实工程与训练方案”显性写进 Introduction、Contributions、Evaluation preview 和 Related Work 的边界描述里。

## 1. 最重要的修改方向

### 1.1 从“世界模型方程”改成“结构化动作条件样本”

当前 v5 在 Introduction 中写：

```text
Model-based reinforcement learning has established that an agent equipped with a transition model P(s_{t+1} | s_t, a_t) can plan in imagination ...
```

这个表述适合放在 Related Work，用来连接 world model 传统。但如果 Introduction 只停留在方程层面，会和实际工作产生距离。

图片里的建议很明确：当前阶段不应该直接追求一个很数学化的马尔可夫方程，而应该先提取：

```text
(persona, state, action, next_state, rationale)
```

更进一步可以是：

```json
{
  "persona": "price_sensitive_cautious",
  "state": "high_hesitation",
  "action": "strong_recommendation",
  "next_state_distribution": [
    {"state": "defensive", "weight": "high"},
    {"state": "leave_tendency", "weight": "medium"}
  ],
  "rationale": "强推荐可能增加心理压力，尤其对价格敏感、犹豫中的用户更容易引发防御。"
}
```

### 建议改法

在 Introduction 的 Prospection 段后补一句，说明 PIWM 如何把世界模型具体落地：

```text
In PIWM, this transition object is not introduced as a hand-written Markov model. We instantiate it as action-conditioned supervision records that bind a customer persona, a current state, a candidate intervention, a predicted next state or next-state distribution, and a rationale explaining why the transition is expected.
```

### 改动目的

这样可以避免 reviewer 误解你在做一个传统 RL transition model，同时又保留 world model 的理论支撑。

## 2. 补上“主 schema -> 三套训练集”的数据管线

当前 v5 的数据段落主要写：

```text
The bulk of the data is synthesized by a video generation model (Kling) conditioned on tuples of (product category, persona type, AIDA stage, target cue) ...
```

这说明了数据来源，但没有说明数据如何被组织成训练任务。

图片里的实际方案是：

第一步，把 Kling 生成结果统一转成一个主 schema：

- `state_id`
- `images`
- `observable_cues`
- `latent_state`
- `intent`
- `proactive_score`
- `candidate_actions`
- `best_action`
- `next_state_by_action`
- `reward_by_action`

第二步，从同一主 schema 导出三套训练集：

- `state_inference.jsonl`
- `transition_modeling.jsonl`
- `policy_preference.jsonl`

### 建议新增段落

建议加在 Introduction 的数据 pipeline 段之后：

```text
Operationally, each generated trajectory is first canonicalized into a master schema containing the customer persona, observed cues, latent state, intent, proactive score, candidate actions, the preferred action, and action-conditioned next-state and reward annotations. The same schema is then rendered into three training formats: state-inference examples, transition-modeling examples, and policy-preference pairs. This lets PIWM learn perception, consequence prediction, and action selection from the same underlying interaction graph rather than from three disconnected datasets.
```

### 改动目的

这段能回答三个 reviewer 可能会问的问题：

1. 你的视频生成数据怎么变成训练数据？
2. 你的 transition supervision 从哪里来？
3. 你说的 Perception / Deliberation / Action 是不是只是一种叙事，还是实际对应训练任务？

## 3. 强化“同一模型，多次调用”的推理机制

当前 v5 中 Perception–Deliberation–Action 的三层结构写得清楚，但 Deliberation 还比较抽象：

```text
Given the current state and a candidate intervention, PIWM predicts the customer's next Belief, Desire, and Intention (BDI), forming a short rollout from which the agent chooses among candidate strategies.
```

这句话方向正确，但没有体现图片中最关键的实际使用方案：

> 同一个模型，多次调用。

实际推理流程应该是：

1. 输入当前 3 帧图，可选输入上一轮结构化状态摘要；
2. 模型输出：
   - `current_state`
   - `intent`
   - `proactive_score`
   - `candidate_actions`
3. 对每个候选动作分别调用模型做后果预测；
4. 每个动作输出：
   - 下一状态
   - 风险
   - 收益
5. 最后再选动作：
   - 最优动作
   - 最终话术 / 是否沉默

示例内部表：

| 动作 | 预测下一状态 | 风险 | 收益 | worth_doing |
|---|---|---|---|---|
| `A1_silent` | 继续犹豫 | 低 | 中 | yes |
| `A2_empathize` | 可能防御后退 | 中高 | 低 | no |
| `A3_recommend` | 可能觉得被推销 | 高 | 低 | no |
| `A7_disengage` | 保持舒适距离，减少打扰 | 低 | 中 | yes |

### 建议新增段落

建议加在 PIWM hierarchy 三个 bullet 之后：

```text
At inference time, PIWM is used as an internal simulator rather than as a one-shot response generator. The agent first infers the current customer state from a short visual window and an optional structured history summary. It then evaluates each candidate intervention by predicting the next state, risk, and expected benefit under that action. The final policy chooses an intervention only after comparing these hypothetical outcomes, and may decide that silence is the best action.
```

### 改动目的

这段能把 “prospection” 具体化，让 reviewer 看见 PIWM 和普通 VLM response generation 的区别。

## 4. 调整 Contributions

当前 Contributions 中第 2 条写：

```text
PIWM couples an AIDA–BDI dual-schema state representation with a pedagogy-derived state machine for actions, and it trains a transition module that predicts the customer's next mental state under a candidate intervention.
```

这里有两个问题：

1. “transition module” 可能让 reviewer 以为你有一个独立神经模块；
2. 如果实际实现是同一个 VLM 分阶段训练、多次调用，那么 “module” 这个词可能过强。

### 建议替换

```text
We propose PIWM, a multimodal proactive intent world model organized along a Perception–Deliberation–Action hierarchy. PIWM couples an AIDA–BDI state representation with a pedagogy-derived action space, and trains the underlying VLM with action-conditioned transition objectives so that it can simulate the consequences of candidate interventions before selecting one.
```

### 改动目的

这能更准确地描述实际工作：

- 核心仍然是 PIWM；
- 仍然强调 AIDA–BDI；
- 仍然强调 pedagogy-derived action；
- 但不虚构一个过于确定的独立 transition module。

## 5. 调整数据贡献

当前第 3 条 contribution 写：

```text
We introduce a data pipeline that distills expert knowledge from retail training manuals into a cue–strategy–utterance specification and materializes it into multimodal transition-annotated samples through controllable video synthesis.
```

这句话不错，但可以更贴近实际 schema 和三阶段训练。

### 建议替换

```text
We introduce a pedagogy-anchored data pipeline that converts retail training knowledge into a unified interaction schema and renders each record into three supervision formats: state inference, action-conditioned transition modeling, and policy preference learning. Controllable video synthesis supplies the multimodal observations, while the schema preserves the expert-derived links among observable cues, latent customer state, candidate strategies, and expected outcomes.
```

### 改动目的

这样能避免 reviewer 以为贡献只是“用 Kling 造视频”，而是明确说明你的贡献是：

1. 主 schema；
2. 三种 supervision format；
3. cue / state / action / outcome 的专家结构。

## 6. 修改 Evaluation Preview

当前 v5 的 evaluation paragraph 是：

```text
We evaluate PIWM against three families of baselines: reactive VLMs, a transferred AI-Salesman baseline, and text-only dialogue world models.
```

这个方向可以保留，但还缺少图片中更重要的内部比较。

图片建议的 baseline 是三类：

1. 通用 VLM；
2. 只做第一层 SFT 的“感知版模型”；
3. 完整路线模型：感知 + 转移 + 策略。

并且要做 ablation：

- 单帧 vs 多帧；
- 无 reasoning text vs 有 reasoning text；
- 只有 current-state label vs 加上 next-state label；
- 只有 SFT vs SFT + DPO；
- 无 history vs 带短历史。

### 建议替换 Evaluation Preview

```text
We evaluate PIWM against three groups of baselines: general-purpose VLMs under zero-shot and few-shot prompting, a perception-only variant trained only for current-state inference, and prior sales-dialogue or dialogue-world-model systems adapted to our setting. The key comparison is not only whether PIWM outperforms generic VLMs, but which part of the pipeline is responsible for the gain. We therefore ablate the number of visual frames, the presence of reasoning traces, current-state labels versus next-state labels, SFT-only training versus SFT plus preference alignment, and no history versus a short structured history summary.
```

### 改动目的

这段更贴近你现在最关心的问题：

> 到底是一张图够，还是多张图更好；到底只学当前状态够，还是必须学动作后果。

## 7. Related Work 的修改建议

Related Work 整体已经比较完整，不需要大改。建议做局部增强。

### 7.1 Reactive and Proactive Agents

当前已经写了 first-person vs third-person 的区别，这是对的。

可以补一个更直接的句子，强调现有 proactive video dialogue 主要学习“何时回答”，但不学习“如果我采取某个动作，对方状态会怎样变”。

建议补句：

```text
They optimize the timing and content of a response, but they do not require the agent to compare multiple candidate interventions by forecasting how each one would change a third party's latent state.
```

### 7.2 Sales and Persuasion Dialogue

当前对 AI-Salesman 的定性已经比 v4 精确：script extraction、template library、turn-by-turn retrieval。这里建议保持。

但可以加一句说明：AI-Salesman 的 action guidance 来自成功话术聚类，而 PIWM 的 action space 来自训练手册中的条件规则。

建议补句：

```text
This distinction matters because our supervision is organized around conditional pedagogical rules, not around clusters of historically successful utterances.
```

### 7.3 World Models for Dialogue and Interactive Agents

当前这段的问题是 “world model” 讲得偏传统 RL 和 dialogue policy。建议补一句，明确 PIWM 的世界模型是“多模态、第三方、动作条件”的。

建议补句：

```text
PIWM differs in the object being modeled: the transition is not between dialogue slots or simulator states, but between visually inferred customer intent states under sales interventions.
```

### 7.4 Theory of Mind for Embodied Agents

当前对 MindPower 的区分很好：

1. 第三人称 vs 第一人称；
2. pedagogy-constrained action vs embodied action；
3. world model vs single forward reasoning pass。

建议只做一个小修：如果你们实际训练不是独立 transition module，而是 action-conditioned VLM training，这里也别写得太像单独 world-model architecture。

建议把：

```text
PIWM is trained as a world model
```

改成：

```text
PIWM is trained with an action-conditioned world-modeling objective
```

## 8. 需要弱化或避免的表述

### 8.1 避免过强的 “transition module”

如果现在没有独立架构模块，建议避免：

- `transition module`
- `transition function` 作为你自己的实现对象
- `P(s_{t+1} | s_t, a_t)` 直接作为你的模型定义

可以改成：

- `action-conditioned transition objective`
- `internal simulator`
- `predictive deliberation step`
- `next-state prediction under candidate interventions`

### 8.2 避免把 Kling 数据说成天然完整 ground truth

更稳妥的说法是：

- sales pedagogy / scripts 提供强监督链条；
- Kling 提供可控视觉实现；
- 主 schema 保留 cue、state、action、outcome 的结构关系；
- 少量真实视频用于校准 realism。

不要让 reviewer 以为“视频生成模型自动产生真实心理状态标签”。

### 8.3 避免只强调 dataset novelty

这篇的中心应该是 PIWM，而不是 GuidanceSalesBench 或 synthetic data pipeline。

数据管线要服务于方法：

- 为什么能训练 PIWM；
- 为什么能训练 transition；
- 为什么能做 policy preference；
- 为什么比普通 synthetic QA 更有结构。

## 9. 建议加入的术语映射

为了让整篇更清楚，建议固定以下术语：

| 实际工作术语 | 论文中建议术语 |
|---|---|
| 当前状态识别 | state inference / perception |
| 动作后果预测 | action-conditioned transition modeling |
| 策略选择 | policy preference / action selection |
| 同一个模型，多次调用 | VLM-as-internal-simulator / multi-call deliberation |
| 五元组 | action-conditioned transition record |
| 主 schema | unified interaction schema |
| `next_state_by_action` | action-conditioned next-state annotation |
| `reward_by_action` | action-conditioned reward / risk-benefit annotation |
| 短历史摘要 | structured history summary |

## 10. 建议后的 Introduction 结构

建议 v6 的 Introduction 按这个顺序组织：

1. 服务领域需要 proactive agent，不是 reactive command follower。
2. Retail sales 是典型场景：要判断什么时候说、说什么、是否不说。
3. 现有 proactive VLM 主要是 first-person user intent，不是 third-person customer intent。
4. 现有 sales dialogue 主要是 text / voice after conversation，不是视觉行为 cue。
5. 现有 dialogue world model 是 text slot state，不是 multimodal customer mental state。
6. PIWM 的核心：Perception–Deliberation–Action。
7. 关键落地：
   - 统一主 schema；
   - 三套训练集；
   - 同一 VLM 分阶段训练；
   - 推理时多次调用做内部模拟。
8. 数据来源：
   - training manuals / scripts 提供条件规则；
   - Kling 生成多模态 observations；
   - real-store videos 校准 realism。
9. Evaluation：
   - 通用 VLM；
   - perception-only model；
   - 完整模型；
   - AI-Salesman / dialogue world model adapted baseline；
   - ablation。
10. Contributions。

## 11. 建议后的 Contributions

建议将 contributions 改为四条：

### Contribution 1：任务定义

```text
We formalize in-store proactive sales guidance as a third-person multimodal decision problem that requires customer-state perception, action-conditioned consequence prediction, and pedagogy-constrained intervention.
```

### Contribution 2：PIWM 方法

```text
We propose PIWM, a Proactive Intent World Model organized around a Perception–Deliberation–Action hierarchy. PIWM uses a pedagogy-derived action space and trains a VLM to simulate how candidate interventions may change a customer's latent state before selecting an action.
```

### Contribution 3：数据与训练格式

```text
We introduce a unified interaction schema that converts sales-pedagogy knowledge and controllable video synthesis into three supervision formats: state inference, transition modeling, and policy preference learning.
```

### Contribution 4：实验与 ablation

```text
We evaluate PIWM against general VLMs, perception-only variants, sales-dialogue baselines, and dialogue world models, and isolate the effects of visual context length, reasoning traces, next-state supervision, preference alignment, and structured history.
```

## 12. 修改优先级

### P0：必须改

- 在 Introduction 中补上主 schema 和三套训练集；
- 把 evaluation preview 改成包含 perception-only / full-route / ablation；
- 弱化 “transition module”，改为 action-conditioned transition objective；
- 补上推理时“同一模型，多次调用”的 internal simulator 描述。

### P1：建议改

- 在 Prospection 段补五元组 / action-conditioned transition record；
- 在 Related Work 中补 “forecast multiple candidate interventions” 的区别；
- Contributions 改成更贴近真实工作。

### P2：润色项

- 正式 paper source 移除前面的中文版本说明和去 AI 味风格表；
- 检查所有模型名和引用是否在 `references.bib` 中存在；
- 把占位 `[X]%`、`[Y]%`、`[Z]%` 保留到实验结果确定后再替换；
- 统一 AIDA、BDI、persona、state、intent、action、reward 的术语。

## 13. 一句话总结

v5 的方向不用推翻，但要把“实际正在做的东西”写进去：PIWM 不是泛泛的 proactive VLM，也不是抽象地套一个 world-model 方程，而是一个以销售教学规则为监督骨架、以主 schema 组织数据、以三阶段训练学习感知/转移/策略、并在推理时通过多次调用模拟候选动作后果的 proactive intent world model。

