# PIWM：实验进度、数据资产与 OpenRouter 预算说明（完整版）

更新时间：2026-05-01 CST

---

## 这篇文档写给谁

写给需要同时回答三件事的人：**项目有没有做实、现有结果能不能对外讲、下一笔钱该不该花在多模型对比上**。读者可以是技术负责人、业务负责人或外部顾问；不要求预先熟悉论文里的 World Model、SFT 等术语。

**阅读建议：** 先读 **[一页结论](#一页结论)**；需要报价与机型清单时跳到 **[OpenRouter：对比什么、选哪些模型、建议额度](#openrouter对比什么选哪些模型建议额度)**；需要和论文或工程数字对齐时再看 **[附录](#附录数据名称对照与主表)**。

如需更短的对外摘要，可用同目录下的 [`company_openrouter_funding_brief.md`](company_openrouter_funding_brief.md)（内容由本文精简而成，口径一致）。

---

## 一页结论

- **工程阶段**：已完成「合成店内导购视频 → 抽帧 → QA → 结构化训练数据 → Qwen2.5-VL LoRA SFT → 评估」的第一轮闭环；不是停留在 prompt 或纸面方案。
- **最值得对外说的结果**：在**人工 QA 通过的评测子集**上，微调后模型相比原始通用 VLM，能**稳定按业务约定格式输出**（下游可解析），在「购买阶段、动作后的风险/收益/回报」等**结构化后果推理**上提升很大。
- **仍要说清楚的边界**：**状态识别与候选导购动作**仍是短板；整体定位在 **受控 Demo / POC**，不宜承诺无人值守上线。
- **数据**：已有约 **260** 条 parent 级合成视频训练资产、**1321** 条 SFT 样本（口径见附录）；**500 / 1000** parent 扩展队列已就绪，扩规模主要是预算与 API，不是重做管线。
- **下一笔 OpenRouter 的目的**：在**同一套数据与评测协议**下做多模型横评，选出效果—成本最适合产品化与论文的基座；**不是**再证明「PIWM 能不能做」——这一条已由当前 Qwen SFT 基线回答。

一句话概括预算诉求：

```text
不是验证 PIWM 能不能做，而是找出 PIWM 应该基于哪个 VLM 做得最好、最便宜、最适合产品化。
```

---

## 项目是干什么的（一句话）

线下零售场景下的**主动导购**：系统先理解顾客状态，再预测「若导购采取某个动作，后果如何」，最后决定是否开口、说什么。视觉来自**多视角店内画面**，不是纯聊天推理。

---

## 术语对照（读表前看一眼即可）

| 文中说法 | 白话 |
|---|---|
| 大规模合成训练集 | 机器批量生成、**未**全员人工逐条验收；适合扩训练，**不能**说成「全是黄金标注」。 |
| 行为 QA 评测集 | 人工抽检通过的样本，用来可信评估「看懂行为 + 推演动作后果」。 |
| 未来反应相关数据 | 含动作之后的顾客反应（视频或结构化标签），支撑 World Model / 未来反应叙事。 |
| Future Verification | 给定当前画面、某个动作、一段候选「未来反应」，判断是否与专家预期一致；检验模型是否真用未来视觉，而非只背文本。 |

---

## 当前进度（闭环长什么样）

```text
合成店内导购视频
-> 抽取关键帧
-> 人工/规则 QA
-> 结构化训练数据
-> Qwen2.5-VL LoRA SFT
-> 模型评估
```

---

## 已有数据资产（规模）

| 类型 | 当前规模 | 用途 |
|---|---:|---|
| 合成导购视频训练集 | 260 条 parent videos | 主训练数据来源 |
| SFT 训练样本 | 1321 条 examples（多帧图像引用） | 当前主 checkpoint 训练口径 |
| 人工 QA 行为评估集 | 40 条审阅 / 36 条通过 | 可信「行为 + 后果」评估 |
| 未来反应相关（continuation 等） | 44 条通过 QA（pilot 口径） | 未来反应监督与叙事 |
| Future Verification | 84 对（机制验证、pilot 规模） | 动作与未来反应是否匹配 |
| FV 专项 SFT 样本（独立实验口径） | 218 条 | 与主表 1321 条口径不同，详见附录 |

扩展到 **500 / 1000** 条 parent 的 prompt 队列与静态检查已就绪，**无需重做数据管线**。

---

## 第一轮模型结果（Qwen2.5-VL-7B LoRA）

我们用当前数据训练了一个主基座版本，结论是：**训练有效**，且现象与「能做结构化导购决策原型」一致。

### 对照表（便于汇报）

下列为零样本与 PIWM-SFT 在同一评测协议下的对比摘要（细节与附录主表一致）。

| 能力 | 原始 Qwen2.5-VL | PIWM-SFT 后 | 说明 |
|---|---:|---:|---|
| 输出能否被系统稳定解析 | 约 23.5%–55.2%（依评测集） | 100% | 从「经常无法接系统」到「稳定可解析」 |
| 识别顾客购买阶段 | 不稳定 | 88.9%（Behavior QA 口径） | 能初步判断阶段，仍有提升空间 |
| 候选导购动作 | 不稳定 | 75.0% | 已能列出可用候选，仍是短板之一 |
| 推演动作后果（风险/收益等） | 约 26%–37% | 约 99%–100% | 结构化后果推理大幅提升 |
| 未来反应相关 | zero-shot 难按协议输出 | 明显提升 | continuation 已进入监督，不仅是展示素材 |

### 用人话补充几句

- **结构化输出**是基础能力：不能稳定解析，就无法接业务 API；这一项必须先站住。
- **后果推理**在协议化评测上涨幅大，支撑 World Model 叙事；但这是**可自动比对指标**，不等于「听起来像真人导购」的主观评价。
- **感知与候选动作**分数仍明显低于后果推理项，对外材料要写清楚，避免过度承诺。
- **视觉**：同一 checkpoint 上去掉画面后，与「当前状态、候选动作」相关指标显著变差，说明模型在吃视觉；部分转移/回报任务在给出结构化 state/action 后更接近规则推演，附录中有分项数字。

### 工程取舍：为什么默认 K=3 帧

对比 1/3/5 帧：**3 帧相对单帧提升明显**，加到 5 帧边际收益不大，当前以 3 帧作为成本与信息量折中。

---

## 现在还不能直接上线的原因

可以做 **受控 Demo / POC**，不建议直接 **无人值守** 上线，主要原因如下：

- QA-reviewed 评估集仍需扩大到更有说服力的规模（例如 parent 级 80–120 的规划已在路线图中）。
- **状态识别与候选动作**仍是薄弱项，需要更多数据与更强基座对照。
- 目前主结果集中在 **Qwen2.5-VL** 一条线，尚未系统回答「商用或国产别的 VLM 是否更强、更省」。
- 产品化需要 **效果—调用成本** 曲线，必须先有多模型可比数据。

---

## OpenRouter：对比什么、选哪些模型、建议额度

### 为什么要这笔钱

下一阶段的重点是 **同一套数据与评测协议下的多模型对比**，而不是重做 pipeline。OpenRouter 便于快速拉齐多款视觉模型，产出可放进公司汇报与论文 baseline 的**统一表格**。

| 对比内容 | 想回答的问题 |
|---|---|
| 各模型 zero-shot | 是否天生更适配店内导购场景 |
| 结构化输出 | 是否容易接入业务系统 |
| 视觉理解 | 是否真在看顾客行为，而非猜文本 |
| 动作后果推理 | 是否适合 proactive sales assistant 路线 |
| 效果 / 成本 | 产品化与论文最值得押注的基座是谁 |

### 候选模型（本轮不优先测 Claude）

| 类别 | 候选 | 备注 |
|---|---|---|
| GPT | GPT-4.1 Mini / GPT-4o Mini | 商用强基线，成本可控 |
| Gemini | Gemini 2.5 Flash / Flash Lite | 视觉与成本平衡 |
| Qwen VL | Qwen3-VL-235B / 32B、Qwen2.5-VL-72B | 国产视觉主力候选 |
| GLM V | GLM-5V Turbo、GLM-4.6V、GLM-4.5V | 国产替代路线 |
| 其他扩展 | Kimi K2.6、ByteDance Seed、MiniMax-01 等 | 低成本扩充对比 |

DeepSeek 在 OpenRouter 上偏**文本**能力，适合做 text-only reasoning / policy sanity check，**不宜**作为多图视觉主评测的主力型号。

### 调用量与建议额度（务实口径）

当前结构化视觉评测样本量级约为 **380 条**。横评 **6–8** 个模型时，粗算约 **2280–3040** 次视觉调用；本轮以 GPT/Gemini mini、flash 与国产低成本 VLM 为主，预算可比「全上大模型」方案收敛。

| 档位 | 预计调用量 | 覆盖范围 | 建议额度 |
|---|---:|---|---:|
| 最小 smoke | 约 400 次 | 例如 5 模型 × 80 条样本，快速筛掉明显不合适 | **$30–$50** |
| 标准横评（推荐） | 约 3000 次 | 6–8 模型 × 当前完整评测集，形成汇报与论文表 | **$100–$150** |
| 扩展横评 | 5000+ 次 | Top 模型复测、扩 QA、不同 prompt、成本曲线 | **$200–$300** |

**建议：** 本轮可先按 **$150–$200** 申请；审批偏保守时至少 **$50** 做 smoke；若希望覆盖更多国产型号并预留 top-2 复测，可按 **$300** 准备。

### 预算批复后能直接拿到的产出

| 产出 | 用途 |
|---|---|
| 4–8 个 VLM 的统一评测表 | 选型依据 |
| 能力对比摘要 / 图 | 对内汇报、对外融资或合作展示 |
| 更强论文 baseline | 提升实验可信度 |
| 成本—效果曲线 | 部署路线决策 |
| 后续 SFT 目标模型清单 | 避免在不合适基座上浪费训练算力 |

### 与数据扩容的配合节奏（可与预算并行规划）

| 阶段 | 目的 | 产出 |
|---|---|---|
| A | 多模型 zero-shot 横评 | 同一张对比表 |
| B | 扩大 QA 评测规模 | 更稳的排序 |
| C | 合成 parent 扩到 500 | 更强训练基线 |
| D | Top 模型上做 PIWM-SFT 对比 | 公司侧选型结论 |
| E | 扩大 Future Verification | 差异化叙事（保持 pilot 口径诚实） |

---

## 风险边界（对外口径）

| 风险 | 建议说法 |
|---|---|
| 大规模合成数据未全员 QA | 称 **synthetic 训练集**，不写「全人工 gold」 |
| QA 子集仍小 | **QA-reviewed sample**，正在扩容 |
| perception / candidate 弱 | 如实写，并指向数据与横评计划 |
| DPO 等暂停 | 当前 sprint **不以 DPO 阻塞主线** |
| Future Verification | **pilot-scale**，强调机制验证而非全行业 benchmark |

---

## 附录：数据名称对照与主表

以下供工程追溯与论文引用；投资决策读完前文即可。

### A. 展示名称与内部目录

| 展示名称 | 含义 | 内部路径 |
|---|---|---|
| High-throughput synthetic train set | 大批量合成训练，非全员 QA | `data/piwm_dataset_priority280_unreviewed` |
| Behavior QA set | 行为侧 QA 评测 | `data/piwm_dataset_priority40_qareviewed_sample` |
| Future-reaction QA set | 未来反应 pilot | `data/piwm_dataset_pilot30_with_continuations` |
| Future Verification set | 动作与未来反应是否匹配 | 数据目录内 `future_verification.jsonl` |

### B. 数据规模摘录

| 数据资产 | 规模（摘录） | 用途 |
|---|---:|---|
| 大规模合成训练集 | 260 parent；927 transition 等 | 主 SFT |
| QA 行为评测 | 40 审 / 36 pass | 可信行为评估 |
| QA 未来反应 pilot | 30 审 / 24 pass parent 等 | World Model / FV |
| Future Verification | 84 pairs（44 pos / 40 neg） | pilot 验证 |
| 当前合并 SFT | 1321 examples | 主 checkpoint |

### C. 主表：Zero-shot vs PIWM-SFT

下列为**严格协议匹配**，非主观打分；zero-shot 未按项目标签格式输出则记未命中。

| Eval set | Rows | Model | Parse | Stage | Score | Candidates | Next Stage | Risk | Benefit | Reward | Reaction Caption |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Future-reaction QA set | 134 | Qwen2.5-VL zero-shot | 0.552 | -- | -- | -- | 0.333 | 0.500 | 0.600 | 0.033 | 未按协议输出 |
| Future-reaction QA set | 134 | PIWM-SFT | 1.000 | 0.417 | 0.792 | 0.333 | 0.985 | 1.000 | 1.000 | 0.970 | 1.000 |
| Behavior QA set | 162 | Qwen2.5-VL zero-shot | 0.235 | -- | -- | -- | 0.211 | 0.553 | 0.289 | 0.000 | -- |
| Behavior QA set | 162 | PIWM-SFT | 1.000 | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | -- |

### D. 视觉消融（摘要）

| Eval set | Condition | Stage | Score | Candidates | Next Stage | Reward |
|---|---|---:|---:|---:|---:|---:|
| Future-reaction QA set | visual 3-frame | 0.417 | 0.792 | 0.333 | 0.985 | 0.970 |
| Future-reaction QA set | no visual frames | 0.333 | 0.042 | 0.042 | 0.955 | 0.970 |
| Behavior QA set | visual 3-frame | 0.889 | 0.750 | 0.750 | 1.000 | 1.000 |
| Behavior QA set | no visual frames | 0.111 | 0.111 | 0.111 | 1.000 | 1.000 |

### E. Future Verification（摘要）

| Input condition | Rows | Parse | Match | Expected State | Body | Gaze | Hand | Movement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Current + future frames | 84 | 1.000 | 0.595 | 0.988 | 0.667 | 0.667 | 0.667 | 0.667 |
| Current only | 84 | 1.000 | 0.488 | 0.988 | 0.583 | 0.583 | 0.583 | 0.583 |

### F. 扩展队列（摘要）

| 目标规模 | 新增 parent | 静态 QA |
|---:|---:|---|
| 500 | 248 | prompt 全存在，label leakage = 0 |
| 1000 | 748 | 同上 |

### G. 对外英文段落（可选）

```text
PIWM has completed an end-to-end synthetic data and evaluation loop for proactive in-store assistance. The current Qwen2.5-VL SFT baseline already shows large gains in structured parsing and action-conditioned transition reasoning. Additional OpenRouter budget will be used for controlled multi-model comparison under the same QA-reviewed evaluation protocol, helping identify the best foundation model for PIWM before larger-scale data expansion.
```

**中文对照：** PIWM 已完成「合成数据 + 评测」闭环；当前 Qwen2.5-VL 微调基线在结构化解析与动作条件下转移推理上相对 zero-shot 提升明显。追加 OpenRouter 预算用于在统一 QA 评测协议下做多模型对比，以便在更大规模扩数据之前选定最适合的基座模型。
