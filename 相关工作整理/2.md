# 立足点审视：专家知识蒸馏是否首发 + 补强切入点

_版本：2026-04-21 · 对 "从导购行业经典培训教材蒸馏线索-策略-话术模型" 这一立足点的系统调研与辩证深化_

---

## 0. 一句话诊断

**精确而言，你不是首发——但你在"精确组合"的位置上是首发**。

- 从**专家教材**做 LLM 蒸馏：已有先例（Samsung 手册 → RAG、Knowledge-Instruct、GER）。
- 从**销售/说服**对话做 LLM 训练：已有先例（AI-Salesman、SalesBot 1.0/2.0、CSI、Persuasion For Good、AffectMind）。
- 从**视觉观察线索 → 销售策略 → 话术**这个三级因果链：**没人做过**。
- 把**零售导购行业 pedagogy 本身**作为 supervision anchor（而不是历史对话行为或 teacher LLM）：**没人做过**。
- **把这两件事组合成一个针对线下物理零售场景、视觉 proactive agent 的 benchmark**：**没人做过**。

问题不在"你是否首发"，而在**你需要把区分度讲得多精确**，才能让审稿人不会简单地说"AI-Salesman 已经做过了"。

---

## 1. 近邻工作全景图（按相似距离分 4 圈）

### 圈 A：销售/说服对话 + LLM（最近邻，必须正面区分）

| 工作 | 年 | 数据源 | 创新点 | 与你的核心区分 |
| --- | --- | --- | --- | --- |
| **AI-Salesman / TeleSalesCorpus / DOGA** (Zhang et al., arXiv 2511.12133) | 2025-11 | **电销历史高转化率对话** → GPT-4 分类 annotate → 提取脚本 → 向量聚类成 template library | 双阶段（Bayesian RL 训练 + DOGA 检索）；第一个 real-world-grounded telemarketing dataset；LLM-as-Judge 评估 | (a) 他们的 knowledge 来自**成功行为反推**，你的来自**专家 pedagogy 正向蒸馏**；(b) 他们是**纯语音/文本电销**，你是**视觉 grounding 的线下零售**；(c) 他们的 script library 没有 cue-strategy-utterance 三级链 |
| **SalesBot 1.0 → 2.0 → SALESAGENT** (Chiu 2022, Chang & Chen 2024) | 2022-2024 | BlenderBot self-play (1.0) → LLM prompting (2.0) → CoT-annotated SALESAGENT | chit-chat → task-oriented 平滑过渡；CoT reasoning 注入 sales strategy | 纯 e-commerce 购物对话；intent-guided 而非 BDI-factored；没有视觉 grounding；无专家教材 anchor |
| **CSI / CSUser / CSales** (ACL Findings EMNLP 2025) | 2025 | Amazon Reviews → GPT-4 推断 fine-grained user profile → LLM-based simulator | 统一 preference elicitation + recommendation + persuasion；contextual user profiling 作为 action planning 的基础 | 纯文本 e-commerce；用户 profile 是 long-term preferences + current needs，没有"**心理状态机**"结构；无专家 pedagogy anchor |
| **SalesRLAgent** (arXiv 2503.23303) | 2025-03 | 1.2M GPT-4o 合成对话，覆盖 15 个 industry | 实时转化预测 + RL 优化 | 纯合成数据；没有专家 anchor；没有视觉；评估是 "conversion binary" 而非 "chain consistency" |
| **AffectMind** (arXiv 2511.21728) | 2025-11 | 两个新数据集 MM-ConvMarket / AffectPromo | PKGN + EIAM (Emotion-Intent Alignment) + RDL；**多模态（text / vision / prosody）marketing dialogue** | 上一轮已详细讨论——方法论 vs benchmark 的差异；他们有 emotion，但没有**视觉线索 → SOP 策略**的显式映射 |
| **Persuasion For Good** (Wang et al., ACL 2019) | 2019 | 众包完成的 1,017 场捐款说服对话 + 300 场 10 种 persuasion strategy 标注 | 说服对话的经典 strategy 分类法 | (a) 场景是单纯说服（捐款），不是销售+视觉感知；(b) 10 种 strategy 是扁平 flat，没有 cue→strategy→utterance 三级；(c) 纯文本 |
| **Hiraoka et al.** | 2016 | 职业销售员-顾客对话 transcripts | 最早分析 professional salesperson 的 dialogue behavior；发现约 30% 是 argument-framed 信息交换 | 只是分析，没做 agent；时代早于 LLM |
| **ProAssist** (Zhang et al., EMNLP 2025) | 2025 | EpicKitchen egocentric 视频 + 合成对话 | 流式 egocentric video → 主动 assistant 对话 | 任务是 procedural task（做饭），不是销售；与 GOALIE 类似 |

### 圈 B：Knowledge Distillation / Library-based 对话指导（方法论近邻）

| 工作 | 年 | 核心方法 | 与你的核心区分 |
| --- | --- | --- | --- |
| **Beyond Mimicry to Contextual Guidance / GER** (Wang, Sudhir, Hong, arXiv 2408.07238) | 2024-08 | Teacher LLM 和 student 交互产生 scenario-guidance pairs，构建 library，student 在 inference 时 retrieve | **最近邻的 KD 方法论工作**。区分点：他们的 teacher 是另一个 LLM（GPT-4），你的 teacher 是**人类专家教材**。你的 supervision 有 pedagogical organization，他们的是 teacher 的 emergent 行为 |
| **Samsung Smart TV QA** (Lewis et al., arXiv 2502.19545) | 2025-02 | 用 Samsung 用户手册做 RAG + synthetic QA + SFT student | 证明从 **product manual** 做 distillation 可行；但他们是**产品说明书**，不是**销售方法论教材** |
| **Knowledge-Instruct / R2S / CoD** (2024-2025) | 2024-25 | 从 raw documents 生成 multi-turn SFT dialogue data | 通用方法；不针对销售；没有视觉；没有 cue-strategy-utterance schema |
| **Pedagogy Self-Distillation for Tutoring** (Wang et al., 2023-02) | 2023 | Conversational tutoring 系统；strategy-response 分层；self-distillation | 教育领域，不是销售；是 self-distillation 而不是从教材；但**"predict strategy first, generate response accordingly"** 的框架和你的 strategy-utterance 分层思路同构 |
| **Rationale-Based KD (RBKD)** | 综述类 | 让 student 学 teacher 的 reasoning rationale，不仅学输出 | 你的 cue-strategy-utterance 链对应到 RBKD 的 rationale 结构，可以借用这套话术 |

### 圈 C：零售场景 / 视觉 + Agent（场景近邻）

| 工作 | 年 | 做什么 | 和你的差距 |
| --- | --- | --- | --- |
| **Sari Sandbox / SariBench** (arXiv 2508.00400) | 2025-08 | 3D 零售店仿真 + embodied VLM agent + VR 人机对比 | 任务是 manipulation（picking/inspecting/checkout），**不是导购沟通**；没有顾客意图建模 |
| **Context-Aware 3D Virtual Agent for Financial CX** (arXiv 2410.12051) | 2024-10 | 金融网点 MR 3D agent + VLM scene understanding + 主动个性化服务 | **Phase 2 service-desk 的最接近竞品**。但是金融场景，强调 scene understanding，不强调行为线索 → 销售话术 |
| **Retail CV 监控类工作** (MDPI 2024、MERL 行为识别等) | 2024 | YOLO + DeepSort 跟踪顾客轨迹，热力图分析 | 纯 analytics/dashboard，不是 conversational agent |
| **商业产品**：Firework AVA, Macy's Ask Macy's, Lucidworks Guided Selling, Threekit, Walmart Sparky 等 | 2024-26 | LLM + RAG 的虚拟购物助手 | **全部是 e-commerce**（text/voice chat），没有线下物理场景的视觉 proactive 版本 |

### 圈 D：经典营销学框架（被 NLP/ML 社区完全忽略的宝藏）

| 理论框架 | 历史 | 核心内容 | 是否被 LLM 工作触及 |
| --- | --- | --- | --- |
| **AIDA** (St. Elmo Lewis 1898) | 100+ 年 | Attention → Interest → Desire → Action 四阶段购买漏斗；每阶段有不同的沟通策略 | **几乎为零**。Marketing 教科书里的 default 框架，但 NLP 社区没有一篇把它**作为 agent state machine 的 pedagogical ground truth** |
| **DAGMAR** (Colley 1961) | 60+ 年 | Defining Advertising Goals for Measured Advertising Results；四阶段：Awareness → Comprehension → Conviction → Action | 完全没有 computational 实现 |
| **AIDCAS / AISDALSLove** 等变体 | 近代 | 增加 Conviction, Satisfaction, Search, Like 等阶段 | 同上 |
| **SPIN Selling** (Rackham 1988) | 40 年 | Situation / Problem / Implication / Need-Payoff 四类提问；企业销售经典 | 没有 LLM/对话系统工作把它做成 agent schema |
| **Consultative Selling 框架** | 50 年 | 从销售人员视角的 7-step 流程（prospecting → approach → need assessment → presentation → handling objections → closing → follow-up） | 没有 |
| **神经语言程序学 NLP (Neuro-Linguistic Programming)** | 50 年 | mirroring、pacing、anchoring、sensory-specific language | 在人力销售培训里很流行，但从未被 computational AI 实现 |

**这是你最硬的护城河** — 只要你明确把某一个经典营销学框架（如 AIDA）作为**状态机的 skeleton**，你就获得了"100+ 年的 pedagogical weight"+"NLP 社区首创"的双重加持。

---

## 2. 你的"首发程度"逐维度 truth table

| 维度 | 你有 | 前人有 | 你是首发吗？ |
| --- | --- | --- | --- |
| LLM 从文本文档蒸馏 | ✓ | ✓（Samsung, Knowledge-Instruct, R2S） | 否 |
| 从销售对话学 sales strategy | ✓（教材→行为） | ✓（AI-Salesman 从历史对话） | 否 |
| 从 teacher (library) 做 scenario-guidance 蒸馏 | ✓ | ✓（GER, 2024） | 否 |
| **从"行业专业培训 pedagogy"（非成功行为、非 teacher LLM）做蒸馏** | ✓ | ✗ | **是** |
| 把 cue-strategy-utterance 三级因果链作为一阶标注 schema | ✓ | ✗（前人多是 flat strategy 或 2-d emotion×intent） | **是** |
| **把视觉 behavioral cue（视觉观察）和 verbal strategy 显式链接** | ✓ | ✗（所有 sales 对话工作都是 text/voice only；有视觉的工作没销售链） | **是** |
| 用状态机/BDI 约束 agent 的 action modality（强一致性） | ✓ | △（SALESAGENT 有 CoT，但无状态机） | **基本是**（如果绑定 AIDA 则绝对是） |
| 零售线下门店场景 + proactive agent + 对话 | ✓ | ✗（商业产品都是 e-commerce；Sari Sandbox 是 manipulation） | **是** |
| 把 AIDA/DAGMAR/SPIN 等经典营销学模型作为 agent schema | ? | ✗ | **可以是**（取决于你是否这样定位） |
| 对"何时介入"做非对称代价评估 | ✓ | △（PRISM 2026-02 已做过 in ProactiveBench） | 上一轮已讨论，不是单独 hero |
| 多模态（视觉）+ 主动 + 销售 + cost-aware | ✓ | ✗ | **是**（精确组合） |

**汇总**：在**精确组合**这个层面，你有 6 个维度是首发或近乎首发。不必担心 novelty，但要把这些维度同时讲出来才有说服力。

---

## 3. 六个补强立足点的切入点（按杠杆率排序）

### 切入点 1 — **"从行业 pedagogy 蒸馏"作为 supervision paradigm 的哲学区分**

**论点**：前人的 supervision 来源有三类，你是第四类：
1. **Crowdsourced labels**（Persuasion For Good, MultiWOZ）：量大但缺行业深度。
2. **Teacher LLM distillation**（GER, Self-Instruct 系）：依赖 teacher 模型的 emergent 能力。
3. **Successful behavior mining**（AI-Salesman：从高转化率对话反推）：学到 "what worked"，但不知道 "why" 和 "when to generalize"。
4. **Expert pedagogy distillation**（你）：从**人类专家有意识、pedagogically 组织的教学资源**蒸馏。关键区别：pedagogy 已经包含了 **分类、条件、反例、泛化原则**——这是**meta-level knowledge**。

**为什么这是硬护城河**：
- 成功行为反推告诉你 _"一位顶尖销售员在场景 X 下用了话术 Y"_。
- 教材告诉你 _"在场景 X 下，应该用话术 Y，**因为**顾客心理处于 Z 阶段；如果顾客心理是 Z'，则改用 Y'"_。
- **第二种信息密度远高于第一种**，且 "why + when to transfer" 正好是 benchmark agent 泛化能力的关键。

**如何用**：在 Introduction 和 Method 里各插入一段，用上面这四类 supervision paradigm 的对比做 framing。可以叫它 **"Pedagogy-Distilled Supervision"** 或 **"Curriculum-Anchored Knowledge"**。

---

### 切入点 2 — **把经典营销学框架（AIDA 或 SPIN）作为 agent state machine 的 pedagogical backbone**

**论点**：你在计划里提到"使用状态机约束 Agent 对行为模态"，这个状态机本来可以是任意设计的。但如果**状态机的节点直接对应 AIDA 的 Attention/Interest/Desire/Action（或 SPIN 的 S/P/I/N）**，你就获得了：
1. **百年 pedagogical weight**：这些模型是营销学学科共识，不是你凭空造的 ontology。
2. **可 ground truth 的 mapping**：每个阶段的 cue 和 strategy 在教材里是明确定义的。
3. **State transition 的 ground truth**：教材也明确给了 "Interest → Desire" 应该用什么沟通策略。

**为什么没人做过**：
- NLP/ML 社区读的是 SIGDIAL、ACL、NeurIPS；AIDA 等在营销学教科书里。
- Marketing 社区会用 AIDA，但不写 agent。
- **你正好卡在这个交叉点上**。

**如何用**：把 PIWM 的 BDI 改成 **"AIDA + BDI 复合 schema"**——BDI 描述 agent 对顾客的心理建模（Belief/Desire/Intention），AIDA 描述顾客当前所处的购买阶段。这让你同时有 agent 侧（BDI）和 customer 侧（AIDA）的结构化 schema。

**升级后的主张**：_"We present the first agent benchmark where the customer-side state machine is directly lifted from a century-old marketing pedagogy (AIDA), and the agent-side decision structure from decades-old BDI agent theory. Both are ground-truth-bearing, not researcher-invented."_

### 切入点 3 — **"视觉 cue → 销售策略"的显式因果链作为新标注 schema**

**论点**：现有销售对话的标注粒度：
- Persuasion For Good：flat 10 种 strategy（文本级）。
- SalesBot：flat intent list（文本级）。
- AffectMind：emotion × intent 二维（多模态但二维）。
- AI-Salesman：dialogue intent + 检索的 script template（文本级）。

你的 **cue (视觉观察) → strategy (心理推断) → utterance (话术)** 是三级因果链，且 cue 是**视觉级**。这在 schema 层面是全新的。

**为什么重要**：
- 它提供了 "why this strategy" 的 intermediate anchor，可以做 process reward（BCC 的雏形）。
- 它让 agent 的决策可审计：如果 agent 用错了 strategy，你能知道是 cue 识别错了还是 strategy 选错了。
- 它让数据集可以跨粒度评估：cue-only、strategy-only、end-to-end 三种 accuracy 都能单独报告。

**如何用**：把 "cue → strategy → utterance" 提升为 Introduction 里明确命名的**数据格式贡献**，和 "BDI chain audit" 一起作为 benchmark schema 的双支柱。

---

### 切入点 4 — **"pedagogical ground truth" vs "behavioral ground truth" 的有效性论证**

**论点**：前人（AI-Salesman 尤其）会被审稿人看作 "已经解决了 sales distillation"。你需要一个**实验**来反驳：

> _假设_：仅从成功行为反推（AI-Salesman 风格）训练的 agent，在 OOD 场景下的 strategy 选择会差于从专家教材蒸馏训练的 agent。

**可执行的小实验**：
- 两组 SFT data：
  - **Group A**：AI-Salesman 风格——只给成功对话，让 student 学 "input → output"。
  - **Group B**：你的风格——给专家教材的 "cue → why → strategy → utterance" 链。
- 评估：in-distribution 应该差不多；**OOD 场景**（新产品类型、新顾客 persona）下 Group B 应该明显更好。
- 这个实验即使只有小规模，也能在论文里作为 **"Why pedagogy matters"** 的 empirical 论证。

**为什么值得做**：没有这个实验，你的 "教材 vs 行为" 区分就只是 framing 层面的区分。有这个实验，就成了 empirical contribution。

---

### 切入点 5 — **视觉 proactive sales 作为完全空白的任务空间**

**论点**：按当前文献，可以这样分区：
- 文本/语音 proactive sales：Persuasion For Good、SalesBot、AI-Salesman、AffectMind 已经占了。
- 视觉 proactive non-sales：YETI（AR 任务指导）、ProAssist（做饭）、GOALIE（AR 教程）。
- **视觉 proactive sales**：完全空白。

你可以直接在 abstract 里写一句：
> _"Despite extensive prior work on text-based proactive sales agents (Wang 2019; Chiu 2022; Zhang 2025) and visual proactive task-assistance agents (Zhou 2025 / ProAssist; Bohus 2025 / YETI), the intersection—visual proactive sales—remains unaddressed."_

这一句话可以挡住"首发性不够"的攻击。

---

### 切入点 6 — **把"导购"精确定义成一个独立的 subfield**

**论点**：英文学术圈里，"salesperson"、"telemarketer"、"customer service agent"、"shopping assistant" 都有各自的文献，但**"in-store guided sales (导购)"** 这个精确的中文商业概念——即**线下实体门店、顾客处于 browsing 状态、销售人员主动介入**——**没有一个对应的英文学术术语**。

你可以在论文里 officially introduce 一个术语，例如：
- **"In-store Proactive Guidance"** 或
- **"Physical-Space Retail Guidance"** 或
- **"Embodied Sales Interaction"**

然后把这个 subfield 的独立性和之前的文献对比：
| 已有 subfield | 场景 | 关键限制 |
| --- | --- | --- |
| Telemarketing (AI-Salesman) | 电话外呼 | 无视觉 |
| Customer service (GER) | 事后支持 | 不主动销售 |
| Shopping assistant (Firework AVA 等) | 线上浏览 | 无物理场景 |
| Conversational recommender (CSI) | 结构化偏好 elicit | 不在物理空间 |
| **In-store proactive guidance (你)** | **物理门店 + 视觉 + 主动销售** | — |

**Novelty 一行论证**：_"We introduce the first benchmark for In-store Proactive Guidance, a subfield at the intersection of four previously disjoint research lines."_

---

## 4. 三个战略性风险必须提前处理

### 风险 1 — **教材版权**

"导购行业经典培训教材"很可能包含版权保护的内容。必须决定：
- **选 A：paraphrase distillation**——不发布原文，只发布"cue-strategy-utterance" 抽取的结构化数据（加 provenance note）。在论文里只给出教材的**类别**（如 "retail training manuals from the Chinese retail industry"），不给 full citation。
- **选 B：选用公开资源**——Lewis, Rackham 等公开出版作品的**核心框架**（AIDA、SPIN），加上博客/开放课程讲义、政府出版物（如中国商务部的销售培训指南）。
- **选 C：找行业合作伙伴**，获得明确的 data license。

**我的建议**：**A + B 组合**。A 保证 distillation 过程的 faithfulness，B 保证可复现性和学术引用链。论文里必须有 "Data Licensing" 小节明确说清楚。

### 风险 2 — **AI-Salesman 的冲击评估**

AI-Salesman (2025-11) 是目前最强的竞争者，但它是方法论文章（新模型架构），你是 benchmark + 数据 paper。这个差异必须在 related work 里**显式**讲出来，不要让审稿人自己去推断。

具体建议：
- 在 §Related Work 开一段子节专门叫 _"Distinction from AI-Salesman (Zhang et al., 2025)"_（或者更 diplomatic 的名字）。
- 用 3 个 bullet 直接对比：**Telemarketing vs in-store**、**Successful behavior reverse engineering vs pedagogical distillation**、**Method paper vs benchmark paper**。

### 风险 3 — **"教材蒸馏"的单一 novelty 不够硬**

纯粹讲 "我们是第一个从导购教材蒸馏"，审稿人会说：
- 这和 Samsung 手册蒸馏 (2025-02) 有什么本质区别？
- 这和 GER 的 library-based distillation (2024-08) 有什么本质区别？

**解决办法**：**不要只靠"教材蒸馏"单点卖 novelty**。把它和下面这些绑定：
1. AIDA 状态机 backbone（切入点 2）
2. 视觉 cue → strategy schema（切入点 3）
3. 视觉 proactive sales 的空白（切入点 5）
4. 教材 vs 成功行为的实验对比（切入点 4）

也就是说——**让"教材蒸馏"成为整套数据方法的一根支柱，而不是唯一的支柱**。

---

## 5. 三个核心 claim 候选（供你选择）

基于上面所有分析，重新打磨你的核心立论：

### Candidate 1 — 保守版："Pedagogy-Anchored" 

> _"We present **GuidanceSalesBench-VS**, a benchmark for in-store proactive sales agents. Its distinctive supervision source is not crowd-sourced labels, successful dialogue mining, or teacher-LLM synthesis, but **retail training manuals authored by industry expert pedagogues**. This yields a three-level causal schema—visual cue → inferred customer mental state → SOP-anchored utterance—that no prior proactive-agent benchmark provides."_

### Candidate 2 — 进攻版：绑定 AIDA

> _"We present the first benchmark where a century-old marketing-science state machine (AIDA: Attention / Interest / Desire / Action) is operationalized as the customer-side ground-truth structure for a visual proactive sales agent. The agent's decision schema is BDI-factored, the customer's state is AIDA-factored, and their coupling is distilled from retail training manuals—three sources of pedagogical authority, not researcher-invented ontology."_

### Candidate 3 — 终极版："In-store Proactive Guidance as a subfield"

> _"In-store Proactive Guidance—a salesperson in a physical store deciding, from visual cues alone, **whether to approach** a browsing customer and **what to say**—sits at the intersection of four previously separate research lines: proactive multimodal agents, conversational sales, knowledge distillation from expert sources, and cost-asymmetric decision. We introduce the first benchmark targeting this subfield. **GuidanceSalesBench-VS** couples (a) a BDI-factored agent schema, (b) an AIDA-factored customer schema, and (c) a visual-cue–anchored supervision distilled from retail training manuals. Baselines across eight SOTA VLMs reveal that single-point F1 rankings reverse across cost regimes, and that even strong models show substantial BDI chain violations despite high outcome accuracy."_

**我的推荐**：**Candidate 3**。它有三个好处——
1. 定义了一个 subfield（审稿人会引用它），
2. 包含了你的 3 个最硬的差异点（pedagogy + dual-schema + visual-cue），
3. 自然接到 ED Track 新 scope（evaluation 作为核心贡献）。

---

## 6. 对"立足点"本身的最终辩证深化

你最初的立足点——"使用导购行业经典培训教材，从中对专家知识进行蒸馏，提取线索-策略-话术模型"——**不是一个错误的立足点，而是一个"未完全绑定"的立足点**。

它的问题是：**"教材蒸馏"这个动作本身可以泛化到任何领域**（Samsung 已经做过产品手册，医学、法律、教育都有类似工作）。所以仅凭 "我们是第一个在销售导购领域做教材蒸馏" 的 framing，novelty 太薄，审稿人会觉得是 "一个已知方法在新领域的应用"。

**补强的方向**不是替换它，而是给它绑三样东西：

1. **绑一个 pedagogical theory**（AIDA 或 SPIN）：让蒸馏有 framework anchor，不是随机 distillation。
2. **绑一个 data schema innovation**（cue → strategy → utterance 三级链）：让蒸馏产物有 formal structure。
3. **绑一个 task space definition**（In-store Proactive Guidance）：让这个 subfield 由你的论文定义。

绑了这三样之后，你原本的 "教材蒸馏" 从**方法 step** 升级为 **pedagogy-first methodology**，审稿人很难再说 "这是已知方法"——因为 "先建构 subfield、再用 pedagogy 作为 supervision anchor、再提炼 multi-level schema" 这套组合，没有先例。

---

## 7. 下一步建议

1. **先做一个决策**：在 Introduction 第一段是用 Candidate 1/2/3 里的哪一个？我推荐 3。
2. **教材清单梳理**：列出你手头实际能用的教材，分成 "公开可引用"、"仅能 paraphrase distill" 两类。这决定了 Data Licensing 小节怎么写。
3. **AIDA 绑定决策**：要不要把 AIDA 放进论文的 framework？如果要，PIWM 的 BDI 和 AIDA 的关系要画清楚（BDI 描述 agent，AIDA 描述 customer）。
4. **一个小对照实验**：教材 distillation SFT data 和 合成对话 SFT data 的 OOD 对比，即使只用一个小模型做也值。这是唯一能把 "pedagogy > behavior" 从 framing 升级为 empirical claim 的路径。
5. **"In-store Proactive Guidance" 这个命名**要不要采用？如果用，Introduction 第一句就可以引入。

时间窗口只剩 15 天。上述五个决策最好在 48 小时内全部落地，后续才是写作执行。