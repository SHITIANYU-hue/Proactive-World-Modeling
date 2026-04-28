# PIWM Phase 2 Expert Corpus Plan

更新时间：2026-04-28

## 1. 目标

本阶段只解决一个问题：

> 让当前 PIWM 数据管线中的规则表，不再表现为 `rules.py` 里的凭空硬编码，而是来自一个可审计、可替换、可冲突检查的专家知识工件。

具体做法采用方案 A：

- `conditional_rules.jsonl` 不只放 2-3 条 demo；
- 它会覆盖当前 spec 已有的核心规则表；
- `rules.py` 在模块加载时从 `expert_corpus/distilled/conditional_rules.jsonl` 编译出规则表；
- 对外函数签名和现有行为保持不变；
- 现有 36 个 pytest 必须继续通过。

本阶段不进入 BDI schema 改造，不改 exporter 输出格式，不改 Kling 调用，不处理旧 Archive 数据。

## 2. 当前基线

当前仓库已有一套按 `/Users/mutsumi/Downloads/data_pipeline_spec.md` 实现的数据管线：

| 文件 | 当前职责 |
|---|---|
| `piwm_data/schemas.py` | Pydantic v2 主数据 schema |
| `piwm_data/rules.py` | spec 枚举、规则表、tie-break 逻辑 |
| `piwm_data/archive_loader.py` | 读取新格式 Archive session |
| `piwm_data/exporters.py` | 导出 state / transition / preference 三套 JSONL |
| `piwm_data/validate.py` | 校验 main schema 与图片路径 |
| `piwm_data/build_dataset.py` | CLI 入口 |

当前测试状态：

```text
36 passed
```

当前 `rules.py` 中需要迁移到专家语料编译链路的五张表规模如下：

| 表 | 当前条数 | Phase 2 处理方式 |
|---|---:|---|
| `CUE_TO_STATE_PRIOR` | 10 | 从 `conditional_rules.jsonl` 编译 |
| `PERSONA_STATE_TO_INTENT` | 14 | 从 `conditional_rules.jsonl` 编译 |
| `STATE_TO_PROACTIVE_SCORE` | 9 | 从 `conditional_rules.jsonl` 编译 |
| `STATE_AIDA_TO_CANDIDATES` | 9 | 从 `conditional_rules.jsonl` 编译 |
| `TRANSITION_TABLE` | 21 | 从 `conditional_rules.jsonl` 编译 |

合计 63 个核心映射条目。

说明：

- `STATE_FALLBACK_INTENT` 当前有 9 条，但不在 Claude 给出的五张编译目标表内。本批次先保持它在 `rules.py` 中不变，避免扩大 scope。若你审核后认为 fallback 也必须专家化，可以作为 Phase 2.1 加第六张编译表。
- `derive_latent_state()` 的多 cue 优先级逻辑也会保持原行为：`ready_to_decide` 优先，其次 `active_evaluation`，再到 `high_hesitation` / `disengaged` / `early_browsing`。本批次不改变这个 tie-break 规则。

## 3. 新增目录结构

计划新增：

```text
piwm_data/expert_corpus/
├── __init__.py
├── schemas.py
├── compile.py
├── README.md
└── distilled/
    ├── stage_definitions.jsonl
    ├── cue_taxonomy.jsonl
    ├── conditional_rules.jsonl
    └── _conflict_log.jsonl
```

每个文件职责：

| 文件 | 职责 |
|---|---|
| `schemas.py` | 定义专家语料层的 Pydantic 模型 |
| `compile.py` | 把 JSONL 条件规则编译成运行时规则表 |
| `README.md` | 说明专家语料层的用途、版权边界、维护方式 |
| `stage_definitions.jsonl` | AIDA 阶段定义的结构化说明 |
| `cue_taxonomy.jsonl` | 视觉 cue taxonomy 的结构化说明 |
| `conditional_rules.jsonl` | 核心专家规则表，覆盖当前 63 个映射 |
| `_conflict_log.jsonl` | 编译时发现冲突时写入，不手工维护 |

## 4. Schema 设计

### 4.1 `SourceRef`

用于记录规则出处。不会伪造不存在的教材页码。

字段计划：

```python
class SourceRef(BaseModel):
    manual: str
    section: str
    page: int | None = None
    url: str | None = None
    verbatim: str
```

约束：

- `manual` 非空；
- `section` 非空；
- `verbatim` 非空；
- `page` 可空，因为公开网页或项目 seed rule 可能没有页码。

### 4.2 `FormalizedCondition`

表示规则触发条件。

```python
class FormalizedCondition(BaseModel):
    aida_stage: AIDAStage | None = None
    cue: str | None = None
    persona_type: str | None = None
    latent_state: str | None = None
```

用于覆盖不同规则类型：

- cue → state：需要 `cue`
- persona + state → intent：需要 `persona_type` + `latent_state`
- state → proactive_score：需要 `latent_state`
- state + AIDA → candidates：需要 `latent_state` + `aida_stage`
- state + action → transition：需要 `latent_state`

### 4.3 `FormalizedEffect`

表示规则产物。

```python
class FormalizedEffect(BaseModel):
    latent_state: str | None = None
    intent: str | None = None
    proactive_score: int | None = None
    candidate_actions: list[str] | None = None
    action: str | None = None
    next_state: str | None = None
    reward: float | None = None
    risk: Literal["low", "medium", "high"] | None = None
    benefit: Literal["low", "medium", "high"] | None = None
    preferred_action: str | None = None
    avoid_action: str | None = None
```

### 4.4 `ConditionalRule`

核心规则模型。

```python
class ConditionalRule(BaseModel):
    rule_id: str
    rule_kind: Literal[
        "cue_state_prior",
        "persona_state_intent",
        "state_proactive_score",
        "state_aida_candidates",
        "state_action_transition",
    ]
    source: SourceRef
    formalized: FormalizedRule
    rationale: str
    distillation_method: str
    distilled_by: str
    distilled_at: date
    confidence: float
```

约束：

- `rule_id` 非空且建议唯一；
- `confidence` 范围 `[0, 1]`；
- `rationale` 非空；
- `source.verbatim` 非空；
- enum 字段必须使用当前 `rules.py` 已有枚举值；
- 不允许引入新的 state / action / persona / cue 字符串。

### 4.5 `StageDefinition`

用于 `stage_definitions.jsonl`。

```python
class StageDefinition(BaseModel):
    stage: AIDAStage
    definition: str
    observable_signals: list[str]
    source: SourceRef
    distillation_method: str
    distilled_by: str
    distilled_at: date
    confidence: float
```

### 4.6 `CueTaxonomy`

用于 `cue_taxonomy.jsonl`。

```python
class CueTaxonomy(BaseModel):
    cue: str
    definition: str
    typical_examples: list[str]
    likely_states: list[str]
    source: SourceRef
    distillation_method: str
    distilled_by: str
    distilled_at: date
    confidence: float
```

## 5. `conditional_rules.jsonl` 内容策略

方案 A 要求它足够覆盖当前 63 个核心映射条目。

计划采用“一条 JSONL 对应一个运行时映射条目”的方式，牺牲一点文件长度，换取最大可审计性：

| rule_kind | 目标表 | 预计条数 |
|---|---|---:|
| `cue_state_prior` | `CUE_TO_STATE_PRIOR` | 10 |
| `persona_state_intent` | `PERSONA_STATE_TO_INTENT` | 14 |
| `state_proactive_score` | `STATE_TO_PROACTIVE_SCORE` | 9 |
| `state_aida_candidates` | `STATE_AIDA_TO_CANDIDATES` | 9 |
| `state_action_transition` | `TRANSITION_TABLE` | 21 |

合计 63 条左右。

重要边界：

- 我不会伪造真实销售培训手册的页码或原文。
- 如果当前仓库没有可引用的真实培训手册，初版规则会明确标记为 `manual: "PIWM_spec_v1_seed_rules"` 或类似 seed 来源。
- `stage_definitions.jsonl` 和少数通用规则可以使用公开领域 AIDA 相关材料的短摘录或改写摘要；但不会把 AIDA 原典硬说成每条零售动作规则的直接出处。
- 后续你团队拿到真实销售培训手册后，可以逐条把 `source.manual`、`source.section`、`source.page`、`source.verbatim` 替换成真实出处；编译器和测试不用改。

## 6. 编译器设计

新增函数：

```python
def compile_rules_from_distillation(jsonl_path: Path) -> CompiledRules:
    ...
```

返回：

```python
class CompiledRules(BaseModel):
    cue_to_state: dict[str, str]
    persona_state_to_intent: dict[tuple[str, str], str]
    state_to_proactive_score: dict[str, int]
    state_aida_to_candidates: dict[tuple[str, str], list[str]]
    transition_table: dict[tuple[str, str], dict[str, Any]]
```

### 6.1 编译规则

不同 `rule_kind` 对应不同写入：

| rule_kind | key | value |
|---|---|---|
| `cue_state_prior` | `cue` | `latent_state` |
| `persona_state_intent` | `(persona_type, latent_state)` | `intent` |
| `state_proactive_score` | `latent_state` | `proactive_score` |
| `state_aida_candidates` | `(latent_state, aida_stage)` | `candidate_actions` |
| `state_action_transition` | `(latent_state, action)` | `{next_state, reward, risk, benefit}` |

### 6.2 冲突策略

如果同一个 key 出现多个不同 value：

- 不抛错；
- 采用 first-wins，保持第一次出现的值；
- 把冲突写入 `distilled/_conflict_log.jsonl`；
- 冲突记录包含：
  - `key`
  - `rule_kind`
  - `kept_rule_id`
  - `conflicting_rule_id`
  - `kept_value`
  - `conflicting_value`

选择 first-wins 的原因：

- 让 JSONL 行顺序具备明确含义；
- 避免后续追加一条低置信规则时静默覆盖已有行为；
- 测试和复现实验更稳定。

### 6.3 非冲突错误

以下情况会直接失败，而不是写 conflict log：

- JSONL 不是合法 JSON；
- 必填字段缺失；
- enum 值不在当前 spec 中；
- `confidence` 越界；
- `rule_kind` 与字段组合不匹配，例如 `state_action_transition` 没有 `action` 或 `next_state`。

原因：这些不是专家意见冲突，而是语料文件损坏。

## 7. `rules.py` 改造计划

改造目标：

- 保留所有 public constants 和 derive 函数签名；
- 保留当前枚举值；
- 保留当前默认候选动作、默认 transition、fallback intent、tie-break 顺序；
- 只改变五张核心表的来源。

计划结构：

```python
from pathlib import Path
from .expert_corpus import compile_rules_from_distillation

_DISTILLED_RULES = compile_rules_from_distillation(
    Path(__file__).parent / "expert_corpus" / "distilled" / "conditional_rules.jsonl"
)

CUE_TO_STATE_PRIOR = _DISTILLED_RULES.cue_to_state
PERSONA_STATE_TO_INTENT = _DISTILLED_RULES.persona_state_to_intent
STATE_TO_PROACTIVE_SCORE = _DISTILLED_RULES.state_to_proactive_score
STATE_AIDA_TO_CANDIDATES = _DISTILLED_RULES.state_aida_to_candidates
TRANSITION_TABLE = _DISTILLED_RULES.transition_table
```

保留不动：

- `PRODUCT_CATEGORIES`
- `PERSONA_TYPES`
- `CUES`
- `LATENT_STATES`
- `INTENTS`
- `ACTIONS`
- `STATE_FALLBACK_INTENT`
- `DEFAULT_CANDIDATES`
- `DEFAULT_TRANSITION`
- `_RISK_RANK`
- `_BENEFIT_RANK`
- `_ACTION_ORDER`
- `derive_latent_state`
- `derive_intent`
- `derive_proactive_score`
- `derive_candidate_actions`
- `derive_transition`
- `pick_best_action`

## 8. 测试计划

新增：

```text
piwm_data/tests/test_expert_corpus.py
```

覆盖：

| 测试 | 验证点 |
|---|---|
| schema 校验 | `ConditionalRule` / `StageDefinition` / `CueTaxonomy` 可解析合法样例 |
| verbatim 非空 | 空 `source.verbatim` 会失败 |
| enum 校验 | 非法 cue / state / action 会失败 |
| compile 输出格式 | 五张表均为预期 dict 结构 |
| compile 覆盖数 | 编译出的五张表条数等于当前基线：10 / 14 / 9 / 9 / 21 |
| conflict 检测 | 同 key 不同 value 写 `_conflict_log.jsonl` 且不抛错 |
| first-wins | 冲突时保留第一条值 |

继续运行现有测试：

```bash
python3 -m pytest piwm_data/tests/test_rules.py
python3 -m pytest
```

验收标准：

```text
全部 pytest 通过
```

## 9. 实施顺序

严格按文件推进，每步跑对应测试。

### Step 1：新增专家语料 package 骨架

文件：

- `piwm_data/expert_corpus/__init__.py`
- `piwm_data/expert_corpus/README.md`

验证：

```bash
python3 -m pytest piwm_data/tests/test_schemas.py
```

### Step 2：新增专家语料 schema

文件：

- `piwm_data/expert_corpus/schemas.py`

验证：

先新增最小 schema 测试，再跑：

```bash
python3 -m pytest piwm_data/tests/test_expert_corpus.py
```

### Step 3：新增 distilled JSONL

文件：

- `piwm_data/expert_corpus/distilled/stage_definitions.jsonl`
- `piwm_data/expert_corpus/distilled/cue_taxonomy.jsonl`
- `piwm_data/expert_corpus/distilled/conditional_rules.jsonl`

验证：

```bash
python3 -m pytest piwm_data/tests/test_expert_corpus.py
```

### Step 4：新增编译器

文件：

- `piwm_data/expert_corpus/compile.py`

验证：

```bash
python3 -m pytest piwm_data/tests/test_expert_corpus.py
```

### Step 5：改造 `rules.py`

文件：

- `piwm_data/rules.py`

验证：

```bash
python3 -m pytest piwm_data/tests/test_rules.py
```

### Step 6：全量回归

验证：

```bash
python3 -m pytest
```

预期：

```text
36+ passed
```

新增测试后总数会大于 36。

### Step 7：停下给你审阅

完成后只汇报以下内容，不进入批次 2：

- `conditional_rules.jsonl` 的前若干条；
- `_conflict_log.jsonl` 内容；
- pytest 结果；
- 哪些 source 仍是 seed draft，等待人工替换真实教材出处。

## 10. 不做事项

本批次明确不做：

- 不新增 `BDISummary`；
- 不移除现有 `intent` 字段；
- 不改 `MainSchemaRecord`；
- 不改三套 exporter 的输出字段；
- 不改 Kling 生成逻辑；
- 不处理旧 Archive；
- 不做 VLM 自动标注；
- 不做真实销售手册批量蒸馏；
- 不伪造真实教材引用；
- 不改变任何现有数值、枚举、tie-break 顺序。

## 11. 风险与处理

### 风险 1：专家语料只是 seed draft，不是真实教材

处理：

- 文件中明确标记 `manual: "PIWM_spec_v1_seed_rules"`；
- `README.md` 说明 seed 规则只用于保持当前 spec 行为和打通代码链路；
- 后续人工替换真实教材来源时不需要改编译器。

### 风险 2：规则表来源迁移后行为漂移

处理：

- 编译覆盖数测试；
- `test_rules.py` 保持原样；
- 全量 pytest 回归；
- 不改 derive 函数签名。

### 风险 3：冲突日志污染仓库

处理：

- 每次编译先重写 `_conflict_log.jsonl`；
- 无冲突时写空文件或保持空 JSONL；
- 测试使用临时目录构造冲突，不污染正式 distilled 文件。

### 风险 4：循环导入

处理：

- `expert_corpus/schemas.py` 可以引用 `piwm_data.rules` 的枚举常量时要谨慎；
- 优先把 enum 校验放在 validator 中延迟执行；
- `rules.py` 导入 `compile_rules_from_distillation` 时，避免 `compile.py` 在模块顶层反向导入 `rules.py` 造成循环。

具体实现中可采用：

- `compile.py` 内部函数按需导入 `piwm_data.rules`；
- 或把枚举校验列表作为参数传入 schema validator。

## 12. 审阅时需要你确认的点

请重点看这几个决策：

1. `STATE_FALLBACK_INTENT` 是否可以暂时留在 `rules.py`，还是你希望这次也一并专家化？
2. 冲突策略是否接受 first-wins？
3. 当前没有真实销售培训手册时，是否接受 `PIWM_spec_v1_seed_rules` 作为初版 source？
4. `conditional_rules.jsonl` 是否接受 63 条左右的完整规则，而不是 2-3 条 demo？

只要这四点通过，我再开始实现代码。
