# PIWM v6: Intro + Related Work（readable）

> NeurIPS 2026 Main Track。LaTeX 版：`intro_related_work_v6.tex`
> 占位数字 `[X]%`、`[Y]%`、`[Z]%` 留待实验定稿替换。

---

## 我对同事修改建议的处理（写作角度）

### 采纳

| 同事建议 | 我的处理 |
|---|---|
| §1.1 弱化 P(s'|s,a) 方程 | Intro 完全移除该方程；只在 Related Work 锚定 Ha–Schmidhuber 谱系时出现一次 |
| §3 推理时多次调用 = internal simulator | 在 Deliberation bullet 与第 3 段尾各出现一次，作为 PIWM 的核心区分点 |
| §7.1 现有 proactive video 不学习"动作后果" | 在 Related Work §1 末尾合并入 first-person vs third-person 的同一句 |
| §7.2 AI-Salesman 的 supervision 来源是 outcome cluster | 已嵌入 Sales 段落第二个分论点 |
| §7.3 PIWM 的 transition object 是 multimodal customer intent | 已嵌入 World Models 段末句 |
| §7.4 改"trained as a world model"为"action-conditioned world-modeling objective" | 已修改 |
| §8.1 弱化 transition module | Intro 与 Related Work 全面替换为 "action-conditioned next-state prediction" / "action-conditioned world-modeling objective" |
| §8.2 不夸大 Kling 的标注能力 | 数据段重写为：pedagogy 提供 conditional structure，Kling 仅渲染视觉，real video 校准 realism |
| §11 Contribution 4 重写 | 第 4 条改为"问题定义 / 方法 / 数据 / 实验"四条，第 4 条强调 OOD gap 而非 ablation 列表 |

### 拒绝或弱化

| 同事建议 | 我拒绝的原因 |
|---|---|
| §2 把 schema 字段名（state_id、images、observable_cues 等）写进 Intro | Intro 不写工程细节。MindPower 与 ContextAgent 的 Intro 都没有字段列表。下沉到 §3 或 §4。Intro 只用一句话："canonicalized into a unified interaction schema and exported into supervision formats for the three hierarchy levels" |
| §6 Evaluation Preview 列 5 条 ablation | ContextAgent 的 Intro 实验段只有 3 行，给 headline 数字 + baseline 类别。Ablation 不进 Intro。我用一句"the gain comes from Deliberation, not from better perception alone" 作为定性 ablation 提示，详细列表留 §5 |
| §10 把 Intro 拆成 10 段 | MindPower / ContextAgent 都是 5–6 段。10 段会撑到 2 页，破坏 NeurIPS 节奏。我合并为 6 段 |
| §11 4 条 contribution 都写得极长 | 单条 contribution 不应超过 3 行。我修剪了第 2 条与第 3 条 |
| §9 反复使用 "VLM-as-internal-simulator" | 只用一次（Deliberation bullet 之后的段落）。多次重复会变 buzzword |
| §1 提"v5 偏高层概念稿"的批评 | 写作上不能"为了反驳概念化"就把工程细节全堆进 Intro。Intro 的功能是说服 reviewer "为什么要读下去"，不是描述系统组成。我让 Intro 仍然抽象，但用 internal-simulator 这一具体机制锚定，避免空洞 |

### 关键写作判断

**为什么 v6 比 v5 更接近 MindPower / ContextAgent**：

1. **Subheading 数量**：v5 在 Intro 用了 3 个 `\paragraph{}`（Perception / Action / Prospection），过密。MindPower Intro 用 0 个，ContextAgent 用 2 个。v6 减到 2 个：`What current systems miss` 和 `What pedagogy already encodes`，把 Prospection 内化成 PIWM 引入段的核心 framing
2. **方法引入位置**：MindPower 与 ContextAgent 都在 Intro 的中段（约 50% 处）说 "We introduce X"。v5 把 PIWM 的引入推到了第 6 段（约 65%）。v6 提到第 4 段，恢复正常节奏
3. **bullet hierarchy**：MindPower 的 hierarchy 用三个 bullet 描述三个 level，每个 bullet 含一个具体动作。v6 的三个 bullet 严格对照这个写法，不要 v5 那种长段叙述
4. **末段结构**：MindPower 末段是"实验结果 + qualitative finding + ablation 暗示"。v6 复用同一结构，把 "the gain comes from Deliberation, not from better perception alone" 放在末句作为 ablation 暗示

---

## 1. Introduction

Vision-language models now drive autonomous agents across digital and physical domains, from web navigation [Mind2Web; SeeClick; WebAgent] and software engineering [SWE-Agent; CodeAgent] to household assistance [SayCan] and health companionship [DrHouse; ConversationalHealth]. Most of these agents still respond only when asked: a user issues a command, the agent executes, and the loop closes. Such reactivity fits poorly with service domains where the value of a human expert lies in choosing the right moment to speak and the right thing to say, rather than in executing a stated instruction. Retail sales is the canonical example. A skilled floor salesperson reads a shopper's posture, gaze, dwell time, and product handling, judges whether the shopper is ready to be approached, and decides what to say --- often before a single word is exchanged. Replicating this behavior requires an agent that is not only multimodal but also *prospective*: it must anticipate how a candidate intervention would change the customer's mental state before committing to it.

**What current systems miss.** Two communities have moved part of the way toward such an agent. Proactive multimodal agents have learned to decide *when* to speak in streaming video [MMDuet; MMDuet2; StreamBridge; Dispider; ViSpeak; ProactiveVideoQA], wearable streams [ContextAgent; SocialMind], and egocentric procedural assistance [ProAssist]. These systems share one assumption: the observed subject is the *user* wearing the device, and the inferred intent is the wearer's own. A salesperson faces the opposite setup --- the observed subject is a third party, and the intent to be modeled is an external interlocutor's. Sales-dialogue systems have learned the other half: they generate persuasive language conditioned on dialogue history [PersuasionForGood; Hiraoka 2016; SalesBot; SalesBot 2; SalesAgent; CSales; AffectMind; SalesRLAgent], and the most recent entry, AI-Salesman, mines high-conversion telemarketing transcripts, clusters them into a script library, and retrieves stage-specific guidance turn by turn. These systems act only after the customer has engaged in conversation; they operate in a purely linguistic channel; and their action choices are induced from what *worked* in past transcripts, which captures success patterns but not the conditional rules behind them.

**What pedagogy already encodes.** Sales strategies, however, are not unstructured. Retail training programs and classical marketing frameworks --- AIDA [Lewis 1898; Strong & Hughes 1925], SPIN Selling [Rackham 1988] --- have for decades organized the sales conversation as a finite, stage-dependent action set, written in the form "if the customer is at stage X and shows cue Y, then strategy Z is appropriate." This conditional structure is exactly the supervision an agent needs to generalize across product categories and customer personas, and it is exactly what is missing from outcome-mined script libraries. Yet no current sales agent treats this pedagogical knowledge as a first-class supervision source. Combined with the perception gap above, this means today's agents lack both the visual ground for state inference and the conditional ground for action selection. They also lack the third capability that distinguishes a salesperson from a respondent: the ability to imagine how the customer will react to each candidate intervention before choosing one.

We address these gaps with **PIWM** (*Proactive Intent World Model*), a multimodal world model of customer intent that serves as the predictive core of an in-store guidance agent. PIWM is organized along a three-level hierarchy --- Perception, Deliberation, and Action --- that mirrors the salesperson's own decision loop:

- *Perception* parses multimodal cues (posture, gaze, dwell, product handling) into an AIDA-aligned estimate of the customer's purchasing stage and a structured Belief–Desire–Intention summary.
- *Deliberation* treats the underlying VLM as an internal simulator. For each candidate intervention, the model is queried again to predict the customer's next state, the likely reaction, and a coarse risk–benefit assessment, producing a short hypothetical rollout per action.
- *Action* selects the intervention --- including the choice to remain silent --- after comparing rollouts. The action set is finite and drawn from a state machine extracted from retail training manuals, rather than from clusters of historically successful utterances.

The key shift is at Deliberation: PIWM does not commit to a single forward generation. It uses the same VLM to walk through alternative interventions in imagination and chooses among them. This is what gives the agent its *prospective* character.

Training a model of this form needs paired supervision linking observation, current state, candidate action, and next state --- in a setting where real in-store video is hard to obtain at scale. Privacy and licensing barriers are high, rare but diagnostically important personas are under-sampled, and ground-truth mental states are not directly observable. We sidestep these constraints with a pedagogy-anchored data pipeline. The pedagogical source supplies the conditional structure: which cues correspond to which customer states, and which strategies are appropriate at which stages. A controllable video generation model (Kling) renders the visual side of each scenario, conditioned on tuples of (product category, persona type, AIDA stage, target cue) drawn from the same state machine that governs the action space. A small anchor set of real-store recordings calibrates realism. Each generated record is canonicalized into a unified interaction schema and exported into supervision formats for the three hierarchy levels, so that Perception, Deliberation, and Action are trained against the same underlying interaction graph rather than against three disconnected datasets.

We evaluate PIWM against three groups of baselines: general-purpose VLMs under zero-shot and few-shot prompting (GPT-4V, Gemini-2.5-Pro, Claude-3.7-Sonnet, Qwen2.5-VL); a perception-only variant of our model trained only for current-state inference; and a transferred AI-Salesman baseline together with a text-only dialogue world model. PIWM improves intervention-timing F1 by `[X]%` and strategy-selection accuracy by `[Y]%` over the strongest VLM baseline. The more revealing test is the out-of-distribution split, in which product categories and customer personas seen at training are held out: PIWM's gap from in-distribution shrinks by `[Z]%` relative to AI-Salesman, indicating that pedagogy-derived rules transfer where outcome-mined scripts do not. A qualitative analysis shows that the perception-only variant fails differently from the full model: it can identify the current customer state but commits to interventions that misjudge the next-state consequences --- evidence that the gain comes from Deliberation, not from better perception alone.

We summarize our contributions as follows.

1. We formalize *in-store proactive sales guidance* as a third-person multimodal decision problem, requiring customer-state perception, action-conditioned consequence prediction, and pedagogy-constrained intervention. We show that existing reactive VLMs, sales-dialogue systems, and generic proactive agents are each insufficient along at least one of these axes.

2. We propose **PIWM**, a Proactive Intent World Model organized along a Perception–Deliberation–Action hierarchy. PIWM couples an AIDA–BDI state representation with a pedagogy-derived action space, and trains the underlying VLM with action-conditioned next-state prediction so that, at inference, the model serves as an internal simulator that compares hypothetical interventions before committing to one.

3. We introduce a pedagogy-anchored data pipeline that converts retail training knowledge into a unified interaction schema and renders each record into supervision formats for state inference, action-conditioned transition prediction, and policy preference. Controllable video synthesis supplies the multimodal observations; the schema preserves the expert-derived links among cues, latent state, candidate strategies, and expected outcomes.

4. We evaluate PIWM against general VLMs, a perception-only variant, and sales-dialogue and dialogue-world-model adaptations. PIWM achieves up to `[X]%` higher intervention-timing F1 and `[Y]%` higher strategy-selection accuracy, with a `[Z]%` smaller out-of-distribution gap than the strongest baseline.

---

## 2. Related Work

### Reactive and Proactive Agents.

Mind2Web, SeeClick, and SWE-Agent established that large language and vision-language models can carry out multi-step digital tasks in response to explicit user instructions. A parallel line has asked whether such agents can initiate actions on their own. Early efforts [Proactive Agent; CodingGenie; Ask-Before-Plan; ProAgent] monitor closed digital environments --- desktop UIs, code editors, planning dialogues --- and trigger when a predefined condition is met. ContextAgent generalizes this to open-world wearable streams, predicting whether a proactive response is warranted given egocentric video, audio, and user personas. On the streaming-video side, MMDuet, MMDuet2, StreamBridge, Dispider, and ViSpeak push timing-aware response generation, with ProactiveVideoQA providing the PAUC metric for joint timing–quality evaluation. These works optimize the timing and content of a response, but they do not require the agent to compare multiple candidate interventions by forecasting how each one would change a third party's latent state. They also share a first-person setup: the agent and the subject are the same person. The salesperson setting reverses both --- the subject is a third party, and the decision is which counterfactual future to bring about, not whether to speak now.

### Sales and Persuasion Dialogue.

Hiraoka et al. and PersuasionForGood provided the community its first strategy-annotated sales and persuasion corpora, with flat per-utterance labels. SalesBot and SalesBot 2.0 introduced the chit-chat-to-task transition as a phenomenon to model, and SalesAgent scaled this to e-commerce. SalesRLAgent framed conversion prediction as a reinforcement-learning problem on 1.2M synthetic dialogues. CSI/CSales unified preference elicitation, recommendation, and persuasion into a single agent, and AffectMind added joint emotion–intent modeling. The closest entry is AI-Salesman: it releases TeleSalesCorpus, mines high-conversion telemarketing transcripts, extracts persuasive scripts with GPT-4, clusters them into a template library, and retrieves stage-specific guidance at inference. Two properties separate our setting from this line. First, the input modality: all of the above operate on text or voice, not on the visual behavioral cues an in-store salesperson actually uses. Second, the supervision source: AI-Salesman's script library is induced from dialogue outcomes, capturing what worked but not why; a pedagogy-derived action space, by contrast, encodes the conditional rules under which a strategy is appropriate, which matters when the agent must handle products or personas absent from the training transcripts. We adapt AI-Salesman as a transferred baseline in Section 5.

### World Models for Dialogue and Interactive Agents.

Ha and Schmidhuber introduced the modern notion of a learned world model --- a transition function $P(s_{t+1} \mid s_t, a_t)$ that supports planning in imagination --- and subsequent work has scaled this primitive to games [IRIS], interactive environments [Genie], and embodied control [DreamerV3]. In the dialogue domain, DDQ was the first to train a dialogue policy with a learned user-response model, and its successors [Switch-DDQ; Budget-DDQ; DR-D3Q] improved sample efficiency. Xu et al. recently proposed an autoregressive Transformer world model coupled with a causal-chain module for dialogue policy. These formulations are text-only and are evaluated on abstract task-completion domains such as movie booking and medical diagnosis: their state is a structured slot–value record and their action is a dialogue act. A separate strand develops LLM-based user simulators for sales and persuasion --- RetailSim, CSUser, UserLM-R1, HumanLM, GenTUS, Personality-Aware RL, and the Bayesian-persuasion formulation of Harris et al. These are simulation frameworks: they generate trajectories by prompting or fine-tuning a user-role LLM, but do not provide the action-conditioned next-state object that supports planning in the Ha–Schmidhuber sense. PIWM differs from both strands in what is being modeled: the transition is not between dialogue slots or simulator states, but between visually inferred customer-intent states under sales interventions, with the action space drawn from marketing pedagogy rather than from a dialogue-act ontology.

### Theory of Mind for Embodied Agents.

MindPower is the closest recent work in spirit. It introduces a Perception–Mental Reasoning–Decision–Action hierarchy over `<Belief>`, `<Desire>`, `<Intention>` tags and evaluates whether VLM-based embodied agents can reason about human mental states in first-person scenarios. MindForge applies belief tracking to cultural learning in Minecraft, and Jafari et al. probe whether ToM components extracted from LLM hidden states improve conversational alignment. We share MindPower's commitment to an explicit Perception–Deliberation–Action decomposition and to BDI-structured mental states. We diverge in three respects. First, the observed subject is a third-party customer rather than a first-person task actor, and the inferred state is the customer's purchasing disposition rather than the human's task-level goal. Second, the action space is constrained by a sales-pedagogy state machine, not by an open-ended embodied-agent action repertoire. Third, MindPower performs a single forward reasoning pass that classifies the current mental state and selects a response; PIWM is trained with an action-conditioned world-modeling objective, and at inference it queries the same VLM repeatedly to compare hypothetical futures before acting. The difference matters most in the decision whether to intervene at all, where the agent must compare counterfactuals rather than classify the current frame.

### Knowledge Distillation from Expert Sources.

Document-to-dialogue pipelines synthesize multi-turn supervised data from unstructured corpora [R2S; SamsungManual], and teacher-LLM distillation formalizes the extraction of interaction-ready guidance [GER]. Rationale-based distillation [RBKD] and conversational tutoring self-distillation [TutoringSelfDistill] go further, transferring reasoning traces rather than only outputs. The shared assumption is that a stronger LLM teacher is the source of knowledge, which means the distilled rules inherit the teacher's biases and offer no guarantee of matching domain expertise. Our source is different in kind: authored retail training manuals and the AIDA marketing framework, written by human sales instructors to teach conditional rules of the form "if the customer is at stage X with cue Y, then strategy Z." That conditional structure is the foundation of both our state machine and the action-conditioned transition supervision PIWM consumes.

### Retail and Shopper Behavior Modeling.

Retail computer vision has long analyzed shopper trajectories, gaze heatmaps, and product engagement, but its downstream target is inventory and layout optimization [RetailCVSurvey; SariSandbox] rather than conversational intervention. A mixed-reality agent for banking customer experience [FinancialCX3D] integrates scene understanding with proactive service, but in a counter-service setting with no sales strategy space. MIND distills 1.26M shopping intentions from product-image pairs, but its input is product imagery rather than customer behavior. None of these provides the combination --- visually-observed third-party customer, proactive intervention, pedagogy-constrained action --- that the PIWM setting requires.
