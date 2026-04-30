# PIWM 数据管线使用说明（已归档）

> **归档说明**：本文档对应 `data_pipeline_spec.md` v1 阶段，未涵盖 QA gate、
> visual-only state inference、`state_inference_with_cue.jsonl`、viewpoint 等
> 后续契约。新人入口请使用：
>
> - `README.md`（5 分钟 quickstart）
> - `docs/04_visual_input_contract.md`（视觉输入与多视角契约）
> - `docs/05_current_code_status.md`（当前代码现状）
>
> 本文保留供历史溯源，不要再作为执行入口。

范围只包括训练数据产出，不包括模型训练、评测、推理服务，也不调用网络。

## 输入目录结构

每个 session 必须符合规范结构：

```text
Archive/session_0001/
├── frames/
│   ├── 000.jpg
│   ├── 001.jpg
│   └── ...
├── prompt.json
├── persona.json             # 可选
├── piwm_annotation.json     # 可选
└── anchor/
    └── piwm_annotation.json # 可选
```

`prompt.json` 必须包含：

- `session_id`
- `product_category`
- `persona.type`
- `aida_stage`
- `target_cue`

这些字段缺失会抛出 `MissingRequiredFieldError`；枚举值不合法会抛出 `InvalidEnumValueError`。

## 运行命令

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive \
  --output-dir data/piwm_dataset \
  --frame-sample 3
```

常用参数：

- `--frame-sample 0`：保留全部帧。
- `--limit N`：只处理前 N 个 session。
- `--strict`：遇到第一个错误立即终止。
- `--no-validate`：跳过主 schema 和图片路径校验。

默认非 strict 模式下，坏 session 会被跳过，并写入 `_stats.json` 的 `skipped_reasons`。

## 输出文件

```text
data/piwm_dataset/
├── main_schema.jsonl
├── state_inference.jsonl
├── transition_modeling.jsonl
├── policy_preference.jsonl
└── _stats.json
```

### `main_schema.jsonl`

每行是一个 `MainSchemaRecord`，字段由 `piwm_data/schemas.py` 的 pydantic v2 模型约束。

规则层派生字段包括：

- `latent_state`
- `intent`
- `proactive_score`
- `candidate_actions`
- `best_action`
- `next_state_by_action`
- `reward_by_action`

这些字段的规则值来自 `piwm_data/rules.py`，版本号为 `v1.0`。

### `state_inference.jsonl`

每个 main schema 产出 1 行，用于当前状态识别 SFT。

### `transition_modeling.jsonl`

每个 main schema 按 `candidate_actions` 展开，N 个候选动作产出 N 行，用于动作后果预测 SFT。

### `policy_preference.jsonl`

每个 main schema 最多产出 1 行，用于 DPO / preference learning。

构造规则：

- `chosen = best_action`
- `rejected = reward 严格低于 chosen 的候选中 reward 最低者`
- 若候选动作少于 2 个，或所有 reward 相同，则跳过。

正式 schema 仍要求 `candidate_actions >= 2`；exporter 的少于 2 个候选动作处理只是防御逻辑。

## 当前仓库 Archive 的状态

当前 `/Users/mutsumi/Desktop/WorkSpace/ProactiveIntentWorldModel/Archive` 仍是旧格式：

- 有 `metadata.json`
- 帧图位于 `anchor/frames/`
- 缺少规范要求的 `prompt.json`
- 缺少规范要求的根级 `frames/`

因此直接运行新管线会跳过这些旧 session，`_stats.json` 中显示：

```json
{
  "n_sessions_total": 5,
  "n_sessions_loaded": 0,
  "n_sessions_skipped": 5,
  "skipped_reasons": {
    "MissingRequiredFieldError": 5
  }
}
```

这说明旧 Archive 需要先迁移成规范输入结构，或后续另写一个显式迁移脚本；当前 loader 不会对旧格式做 fuzzy match 或静默兼容。

## 测试

```bash
python3 -m pytest piwm_data/tests
```

当前测试覆盖：

- schema 枚举与交叉字段校验；
- 规则表与 tie-break；
- archive loader 错误处理和 annotation override；
- 三套 exporter；
- CLI 端到端输出。

