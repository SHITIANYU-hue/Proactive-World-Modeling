# Expert Provenance Upgrade Plan

更新时间：2026-04-29（第一轮自动教材蒸馏已落地）

## 1. 修正后的判断

当前 `conditional_rules.jsonl` 的 72 条规则是可审计 seed corpus，不是不可修改的专家真理表。

因此下一步不应是：

```text
给现有 72 条规则强行找来源
```

而应是：

```text
可信销售来源 -> 抽取原则 -> 重构/保留/删除/新增规则 -> 人工审阅
```

现有 72 条规则的角色是：

- 保持管线行为稳定；
- 提供 seed baseline；
- 暴露哪些字段和映射需要来源支撑；
- 允许后续被修改、合并、删除或替换。

当前最大风险不是“没有 provenance 字段”，而是：

> `provenance` 容器已经有了，但真实高可信来源还没进入规则体系。

## 2. BDI 的位置

BDI 不应放进 sales-rule provenance。

BDI 是 agent theory / cognitive modeling source，用来解释为什么模型输出 `belief / desire / intention`，但它不能支撑具体销售规则，例如：

- `long_dwell_with_price_check -> high_hesitation`
- `A3_strong_recommend -> defensive_withdrawal`
- `A2_offer_value_comparison -> engaged_dialogue`

所以来源体系拆成两条线：

```text
Sales Provenance
  AIDA / SPIN / consumer decision process / retail SOP
  -> 支撑 cue、customer state、strategy、transition、risk/benefit

Modeling Provenance
  BDI / world model / preference learning
  -> 支撑模型输出格式、推理结构、训练 objective
```

代码层对应：

```text
piwm_data/expert_corpus/sources/sales_source_registry.jsonl
piwm_data/expert_corpus/sources/modeling_source_registry.jsonl
```

`rule_source_links.jsonl` 只允许引用 sales sources；BDI 不能出现在销售规则 source links 中。

## 3. 目标

建立一条诚实升级链：

```text
seed_only
  -> theory_anchored
  -> manual_supported
  -> expert_reviewed
```

同时允许规则生命周期变化：

```text
retained_seed
modified
removed
new_source_backed
```

也就是说，后续评审时每条规则都应该能回答：

1. 它是保留 seed、修改 seed、删除 seed，还是新增 source-backed rule？
2. 它现在只有 seed rationale，还是已有理论/教材/专家支持？
3. 如果还需要人工审阅，缺口是什么？

## 4. 新增工件

### 4.1 Sales Source Registry

路径：

```text
piwm_data/expert_corpus/sources/sales_source_registry.jsonl
```

用途：登记可用于销售规则的来源。

允许来源：

- AIDA；
- SPIN Selling；
- consumer purchasing decision process；
- personal selling process；
- 合法可用的 retail SOP / training materials。

不允许来源：

- BDI；
- world model；
- DPO；
- 泛泛心理学概念但无法支撑销售规则的材料。

### 4.2 Modeling Source Registry

路径：

```text
piwm_data/expert_corpus/sources/modeling_source_registry.jsonl
```

用途：登记 PIWM 模型结构来源。

允许来源：

- BDI agent theory；
- theory-of-mind / mental-state reasoning；
- world model / action-conditioned prediction；
- preference learning。

这些来源可以进入论文 framework 论证，但不能直接给销售规则背书。

### 4.3 Rule Source Links

路径：

```text
piwm_data/expert_corpus/distilled/rule_source_links.jsonl
```

用途：记录 seed rule 与 sales source 的关系。

示例：

```json
{
  "rule_id": "TRANS_003",
  "rule_type": "transition",
  "lifecycle": "retained_seed",
  "support_status": "theory_anchored",
  "source_ids": ["SRC_SALES_SPIN_001", "SRC_SALES_PERSONAL_SELLING_001"],
  "formalization_note": "A strong recommendation during hesitation is treated as a high-pressure pitch before need discovery.",
  "support_strength": "medium",
  "needs_manual_support": true,
  "review_status": "pending"
}
```

### 4.4 Provenance Coverage Report

路径：

```text
piwm_data/expert_corpus/distilled/_provenance_coverage.json
```

用途：客观报告当前规则来源覆盖率。

第一版不要求 72 条全覆盖；重点先看：

- 21 条 transition；
- 9 条 state+AIDA candidate rules；
- 是否还有 seed-only；
- 哪些规则需要 manual support；
- 哪些规则建议删除或重写。

## 5. 执行顺序

### Phase P0：更新边界

目标：防止 claim 过度。

要求：

- 不把第一批 72 条 seed rule 批量改成 `pedagogy_text`；
- 不再要求 72 条必须全部映射；
- 明确 BDI 只进入 modeling provenance；
- 论文当前只能写 `auditable seed rules` 或 `pedagogy-structured seed rules`。

验收：

- docs 明确 seed baseline 可以删改；
- rule source links 不引用 BDI；
- 测试继续断言 first batch 是 `seed_rule`。

### Phase P1：建立两个 source registry

目标：把销售来源和建模来源分开。

第一批建议：

Sales：

- AIDA；
- OpenStax consumer purchasing decision process；
- OpenStax personal selling process；
- SPIN Selling official citation。

Modeling：

- Rao & Georgeff BDI agents；
- PIWM 后续采用的 world-model / preference-learning 来源。

验收：

- 每个 source 有 `source_id`、`domain`、`citation`、`copyright_mode`、`usable_for`；
- `SRC_MODELING_*` 不得出现在 `rule_source_links.jsonl`；
- SPIN 等版权书只作为 `citation_only`，不爬取全文。

### Phase P2：先覆盖 candidate 与 transition

目标：优先支撑论文最核心的 action selection / world model claim。

范围：

- 9 条 `state_aida_to_candidates`；
- 21 条 `transition`。

验收：

- 这 30 条规则至少达到 `theory_anchored`；
- 每条都有 `formalization_note`；
- `needs_manual_support=true` 时必须在 coverage report 中可统计；
- 允许后续把其中不稳的 seed 标成 `modified` 或 `removed`。

### Phase P3：再处理 cue 与 intent

目标：处理视觉状态识别和 persona intent。

原则：

- 如果某个 cue 找不到可信来源，不强行保留；
- 可以合并 cue；
- 可以把过主观的 state 改成更可观察的 state；
- 可以新增更符合公开资料的规则。

验收：

- 每条被保留 cue rule 至少有 theory/manual support 或明确标成 seed-only；
- 不稳定规则有 `candidate_for_removal` 或 `modified` 标记；
- 人工只做审阅，不做逐条标注。

### Phase P4：人工审阅

目标：把 agent 自动调研结果变成可信数据工件。

人工只审：

- source 是否可信；
- mapping 是否牵强；
- 哪些 rule 应删除/修改；
- 论文措辞能否升级。

不要求人工逐条从零标注。

## 6. Subagent / 自动调研工作流

可行，但必须有边界。

### Agent 1：Source Scout

任务：

- 找高可信来源；
- 区分 sales source 与 modeling source；
- 标记 copyright mode；
- 不抓取版权教材全文。

输出：

```text
sales_source_registry candidates
modeling_source_registry candidates
```

### Agent 2：Principle Extractor

任务：

- 从开放来源抽取原则；
- 对版权书只抽 framework-level summary；
- 不保存长原文。

输出：

```text
extracted_principles.jsonl
```

### Agent 3：Rule Rebuilder

任务：

- 不强制保留 72 条；
- 对每条 seed rule 给出 retain/modify/remove；
- 必要时新增 source-backed rules；
- 生成 `rule_source_links.jsonl`。

### Agent 4：Audit Agent

任务：

- 统计 coverage；
- 找 unsupported rules；
- 找 BDI 被误用为 sales evidence 的地方；
- 生成人工审阅清单。

## 7. 论文措辞边界

### 当前可以写

```text
We implement an auditable seed rule corpus with rule-level rationales and explicit provenance tags.
```

```text
We separate sales-rule provenance from modeling-theory provenance to avoid treating BDI as sales pedagogy.
```

### 当前不能写

```text
All sales rules are distilled from retail training manuals.
```

```text
BDI supports the cue-to-state or sales-transition rules.
```

```text
Every existing seed rule is source-backed.
```

### Phase P2 后可以写

```text
The core action-candidate and transition rules are anchored to classical sales and marketing frameworks, while unsupported seed rules remain explicitly marked for revision or removal.
```

### Phase P3/P4 后可以写

```text
The released rule corpus separates retained seed rules, source-backed revisions, removed unsupported rules, and expert-reviewed rules, with coverage statistics for each rule type.
```

## 8. 最小实施目标

本轮最小实施：

1. 更新本文档，承认 72 条规则可删改；
2. 新建 `sales_source_registry.jsonl`；
3. 新建 `modeling_source_registry.jsonl`；
4. 新建 `rule_source_links.jsonl`，先覆盖 9 条 candidate + 21 条 transition；
5. 新增 provenance coverage 代码与测试；
6. 确保 `pytest` 通过。

## 9. 第一轮落地结果

第一轮自动教材蒸馏已经完成到“可审阅版本”。

本轮没有把 72 条 seed rule 全部强行改成教材来源，而是做了四类判定：

```text
manual_supported      = 有开放教材或销售理论可支持
theory_anchored       = 有理论框架支撑，但仍需销售手册或专家审阅
seed_only             = 仅保留为 seed calibration
candidate_for_removal = 当前来源不足，建议后续删除、合并或重写
```

当前覆盖率：

```text
n_existing_rules_total      = 72
n_rule_source_links_total   = 72
n_existing_rules_linked     = 72
n_existing_rules_unlinked   = 0

manual_supported            = 32
theory_anchored             = 40
seed_only                   = 0
candidate_for_removal       = 0
expert_reviewed             = 0
```

按规则类型：

| Rule type | Total | Linked | Manual supported | Theory anchored or better | Candidate for removal |
|---|---:|---:|---:|---:|---:|
| `cue_to_state_prior` | 10 | 10 | 6 | 10 | 0 |
| `persona_state_to_intent` | 14 | 14 | 6 | 14 | 0 |
| `state_fallback_intent` | 9 | 9 | 4 | 9 | 0 |
| `state_to_proactive_score` | 9 | 9 | 0 | 9 | 0 |
| `state_aida_to_candidates` | 9 | 9 | 7 | 9 | 0 |
| `transition` | 21 | 21 | 9 | 21 | 0 |

新增工件：

```text
piwm_data/expert_corpus/sources/sales_source_registry.jsonl
piwm_data/expert_corpus/sources/modeling_source_registry.jsonl
piwm_data/expert_corpus/distilled/extracted_principles.jsonl
piwm_data/expert_corpus/distilled/rule_source_links.jsonl
piwm_data/expert_corpus/distilled/_provenance_coverage.json
piwm_data/expert_corpus/provenance.py
piwm_data/tests/test_provenance.py
```

来源原则：

- 销售规则只引用 `SRC_SALES_*`；
- BDI 只在 `SRC_MODELING_*` 中出现，不允许作为销售规则证据；
- OpenStax 等开放教材只保存 paraphrase principle，不保存长原文；
- SPIN Selling 只作为 citation-level framework，不抓取或存储版权书正文。

## 10. 还不能声称什么

虽然 72 条规则都已有审阅状态，但当前仍不能写：

```text
All rules are expert-reviewed.
All rules are directly distilled from retail training manuals.
All reward values are textbook-derived.
```

现在可以写：

```text
We release a source-audited rule corpus in which all seed rules are classified as manual-supported, theory-anchored, seed-only, or candidates for removal.
```

也可以写：

```text
All seed rules are source-linked and classified; 32 are manual-supported and 40 are theory-anchored, while low-strength anchors remain flagged for review.
```
