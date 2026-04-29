# PIWM 数据管线当前状态

更新时间：2026-04-29（Phase 2 数据契约升级后）

## 1. 当前目标

当前工程目标是按 `/Users/mutsumi/Downloads/data_pipeline_spec.md` 实现 PIWM 数据产出链路。

本阶段只负责训练数据产出，不包括：

- 模型训练；
- 评测；
- 推理服务；
- 自动 VLM 标注；
- 图片 resize / 转码；
- 多轮 history 填充。

## 2. 已完成内容

### 2.1 主数据管线

已实现以下模块：

| 文件 | 作用 |
|---|---|
| `piwm_data/schemas.py` | pydantic v2 主 schema，包含 BDI、reward components、next action outcome 与交叉字段校验 |
| `piwm_data/rules.py` | 规则层，严格保留 spec 数值和 tie-break；新增 deterministic BDI / next AIDA / reward component 派生 |
| `piwm_data/archive_loader.py` | 从规范 Archive session 读取 `prompt.json + frames/`，生成带 BDI/transition outcome 的 `MainSchemaRecord` |
| `piwm_data/exporters.py` | 从 main schema 导出三套 JSONL，包含 `state_summary`、`candidate_block`、`next_bdi` |
| `piwm_data/validate.py` | 主 schema 和图片路径校验 |
| `piwm_data/build_dataset.py` | CLI 入口，写四个输出文件和 `_stats.json` |
| `piwm_data/tests/` | pytest 测试 |
| `pyproject.toml` | 项目依赖和 pytest 配置 |

### 2.2 三套导出数据

主数据管线会输出：

```text
data/piwm_dataset/
├── main_schema.jsonl
├── state_inference.jsonl
├── transition_modeling.jsonl
├── policy_preference.jsonl
└── _stats.json
```

三套训练数据对应：

| 文件 | 用途 |
|---|---|
| `state_inference.jsonl` | 当前状态识别 SFT |
| `transition_modeling.jsonl` | 动作后果预测 SFT |
| `policy_preference.jsonl` | DPO / preference learning |

### 2.3 测试状态

当前测试全部通过：

```bash
python3 -m pytest
```

结果：

```text
60 passed
```

测试覆盖：

- schema 枚举字段拒绝非法值；
- `next_state_by_action` / `candidate_actions` / `reward_by_action` 交叉一致；
- 规则层 cue → state、intent fallback、best action tie-break；
- archive loader 必填字段、非法枚举、annotation override；
- 三套 exporter；
- BDI、next BDI、reward component 公式一致性；
- World Model contrast stats；
- CLI e2e。

## 3. 严格遵循的规范点

### 3.1 合法输入结构

新数据管线只接受以下结构：

```text
Archive/session_xxx/
├── frames/
│   ├── 000.jpg
│   ├── 001.jpg
│   └── ...
└── prompt.json
```

`prompt.json` 必须包含：

```json
{
  "session_id": "session_0001",
  "product_category": "luxury_watch",
  "persona": {
    "type": "price_sensitive_cautious",
    "description": "..."
  },
  "aida_stage": "interest",
  "target_cue": "long_dwell_with_price_check"
}
```

可选字段：

- `behavior_description`
- `kling_prompt`
- `duration_seconds`

### 3.2 不做 fuzzy match

如果必填字段缺失，loader 抛出：

```text
MissingRequiredFieldError
```

如果枚举不在 spec 定义内，loader 抛出：

```text
InvalidEnumValueError
```

不会自动猜测、模糊匹配或静默填默认值。

### 3.3 `candidate_actions` 的处理

合法 main schema 仍要求：

```text
candidate_actions >= 2
```

但 `policy_preference` exporter 做了防御：

- 如果异常输入里 `candidate_actions < 2`，产出 0 行；
- 如果所有候选 reward 相同，产出 0 行；
- 正常情况下每个 main schema 最多产出 1 个 preference pair；
- `chosen = best_action`；
- `rejected = reward 严格低于 chosen 的候选中 reward 最低者`。

## 4. 旧项目 / 旧数据的处理边界

### 4.1 旧 Archive 不再处理

当前仓库里的旧 `Archive` 是老格式：

```text
Archive/session_xxx/
├── metadata.json
└── anchor/
    ├── anchor_log.json
    ├── prompt.txt
    └── frames/
```

这不是新规范输入格式。按当前决定：

> 不再管旧数据，不做旧 Archive 迁移。

因此，直接对当前旧 `Archive` 跑新管线会全部跳过。

已经验证过：

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive \
  --output-dir data/piwm_dataset \
  --frame-sample 3
```

结果：

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

这是预期结果，不是管线失败。

### 4.2 旧项目只复用 Kling API 调用

旧项目 `/Users/mutsumi/Desktop/WorkSpace/proactive_vlm_neurips` 现在只作为 Kling API 调用参考。

已新增可选 Kling 工具：

| 文件 | 作用 |
|---|---|
| `kling/generate_session.js` | 读取规范 `prompt.json`，调用 Kling 生成视频 |
| `kling/package.json` | Node 依赖声明 |
| `docs/07_kling_api_usage.md` | Kling 调用说明 |

Kling 工具输出：

```text
Archive_generated/<session_id>/
├── prompt.json
├── video.mp4
└── kling_generation.json
```

注意：

- Kling 工具只负责视频生成；
- 主数据管线仍要求 `frames/`；
- 视频生成后还需要额外抽帧到 `frames/`；
- 抽帧工具还未纳入主数据管线。

## 5. 当前可运行命令

### 5.1 跑测试

```bash
python3 -m pytest
```

### 5.2 对规范 Archive 生成训练数据

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive_v1 \
  --output-dir data/piwm_dataset \
  --frame-sample 3
```

其中 `Archive_v1` 必须是新规范格式。

### 5.3 Kling dry-run

不触网：

```bash
node kling/generate_session.js \
  --prompt piwm_data/tests/fixtures/tiny_session/session_test_001/prompt.json \
  --out-root Archive_generated \
  --dry-run
```

### 5.4 Kling 真实生成

先安装 Node 依赖：

```bash
cd kling
npm install
```

设置环境变量：

```bash
export KLINGAI_ACCESS_KEY=...
export KLINGAI_SECRET_KEY=...
```

运行：

```bash
node kling/generate_session.js \
  --prompt path/to/prompt.json \
  --out-root Archive_generated \
  --model kling-v3.0-t2v \
  --duration 10 \
  --mode pro
```

## 6. 还缺什么

### 6.1 新数据生成器

目前已有：

- 规范数据 loader；
- 规则层；
- 三套 JSONL exporter；
- Kling 单条视频生成脚本。

还缺：

- 批量生成规范 `prompt.json` 的场景采样器；
- 批量调用 Kling 的 orchestration；
- 从 `video.mp4` 抽帧到 `frames/` 的工具；
- 批量生成后自动调用 `build_dataset.py` 的端到端脚本。

### 6.2 抽帧工具

主数据管线不引入 OpenCV / ffmpeg 依赖。

但实际 Kling 生成后，必须把：

```text
video.mp4
```

转成：

```text
frames/000.jpg
frames/001.jpg
...
```

这个工具可以单独实现，不影响 schema / exporter。

### 6.3 真实规范 Archive

当前仓库没有真实的新规范 Archive session。只有测试 fixture：

```text
piwm_data/tests/fixtures/tiny_session/session_test_001/
```

它用于测试，不是正式数据。

## 7. 建议下一步

建议下一步不要回头处理旧 Archive，而是直接做新数据生产入口：

1. 实现 `prompt_builder.py` 或 `scenario_sampler.py`，批量生成符合规范的 `prompt.json`；
2. 每个 prompt 里必须包含：
   - `session_id`
   - `product_category`
   - `persona.type`
   - `aida_stage`
   - `target_cue`
   - `kling_prompt`
3. 调用 `kling/generate_session.js` 生成 `video.mp4`；
4. 抽帧到 `frames/`；
5. 跑：

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive_generated \
  --output-dir data/piwm_dataset \
  --frame-sample 3
```

这样可以形成真正的新数据闭环。
