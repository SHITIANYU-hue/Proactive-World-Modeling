# PIWM 数据管线当前状态

更新时间：2026-04-30（Viewpoint V1-V5 后）

## 1. 当前目标

当前工程目标是实现 PIWM 数据产出链路。早期实现以一份外部 spec 为基准，但
现在 spec 已被以下活跃文档替代：

- 数据契约：`docs/03_world_model_supervision_contract.md`、`docs/04_visual_input_contract.md`
- 阶段顺序：`docs/02_data_loop_master_plan.md`
- 现状诊断：`docs/01_data_generation_loop_status.md`

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
| `piwm_data/schemas.py` | pydantic v2 主 schema，包含 product/split、viewpoint、BDI、reward components、next action outcome 与交叉字段校验 |
| `piwm_data/rules.py` | 规则层，严格保留 spec 数值和 tie-break；新增 deterministic BDI / next AIDA / reward component / rationale / viewpoint enum |
| `piwm_data/archive_loader.py` | 从规范 Archive session 读取 `prompt.json + frames/`，生成带 viewpoint、BDI/transition outcome 的 `MainSchemaRecord` |
| `piwm_data/exporters.py` | 从 main schema 导出三套 JSONL，包含 `state_summary`、`candidate_block`、`next_bdi`，并在 meta 追踪 viewpoint |
| `piwm_data/validate.py` | 主 schema 和图片路径校验 |
| `piwm_data/build_dataset.py` | CLI 入口，默认只读取 QA pass session，写 JSONL 和 `_stats.json` |
| `scripts/scenario_sampler.py` | 生成 Kling 前的规则空间场景 manifest；默认 viewpoint 比例 8:2 |
| `scripts/prompt_builder.py` | 将 scenario manifest 转成 Kling 可用的 `prompt.json`；按 viewpoint 生成 camera / negative；顶层写入 `sampler.version` |
| `scripts/extract_frames.py` | 从 Kling `video.mp4` 按 `frame_sampling_plan` 抽帧，生成 `frames/` 与带 viewpoint 的 `frame_manifest.json` |
| `scripts/qa_gate.py` | 生成带 viewpoint visibility checklist 的 `qa_report.json`，控制样本是否可入库 |
| `scripts/run_kling_batch.py` | 按 prompt index 批量调用 Kling、抽帧、生成 QA report；已完成 10 条 mixed-view 真实小批量生成 |
| `piwm_data/tests/` | pytest 测试 |
| `pyproject.toml` | 项目依赖和 pytest 配置 |

### 2.2 三套导出数据

主数据管线会输出：

```text
data/piwm_dataset/
├── main_schema.jsonl
├── state_inference.jsonl
├── state_inference_with_cue.jsonl
├── transition_modeling.jsonl
├── policy_preference.jsonl
└── _stats.json
```

三套训练数据对应：

| 文件 | 用途 |
|---|---|
| `state_inference.jsonl` | 当前状态识别 SFT，visual-only 主线，不把 `observable_cues` 作为 input |
| `state_inference_with_cue.jsonl` | 带 cue 的调试/上限版本，不作为主训练输入 |
| `transition_modeling.jsonl` | 动作后果预测 SFT |
| `policy_preference.jsonl` | DPO / preference learning |

### 2.3 测试状态

当前测试全部通过：

```bash
python3 -m pytest
```

结果：

```text
80 passed
```

测试覆盖：

- schema 枚举字段拒绝非法值；
- `product_category` / `split` 进入 main schema、JSONL meta 与 `_stats.json`；
- BDI belief 不直接写 cue 枚举名；
- rule-derived transition rationale 进入 preference chosen/rejected；
- viewpoint 字段流转：scenario / prompt / frame manifest / QA report / JSONL meta；
- `next_state_by_action` / `candidate_actions` / `reward_by_action` 交叉一致；
- 规则层 cue → state、intent fallback、best action tie-break；
- archive loader 必填字段、非法枚举、annotation override；
- 三套 exporter；
- BDI、next BDI、reward component 公式一致性；
- World Model contrast stats；
- scenario sampler 和 prompt builder；
- extract_frames 正式抽帧；
- QA gate 与 build_dataset QA pass 过滤；
- mixed-view Kling batch dry-run、manual review template；
- mixed-view 已有视频复用，不重新调用 Kling；
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
  "viewpoint": "salesperson_observable",
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

`viewpoint` 第一版合法枚举：

```text
salesperson_observable
surveillance_oblique
third_party_side
first_person_pov
```

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
- 视频生成后用 `scripts/extract_frames.py` 抽帧到 `frames/`；
- `build_dataset` 默认只读取 `qa_report.overall_pass=true` 的 session。

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

### 5.5 Mixed-view 批量 dry-run

不触网：

```bash
python3 -m scripts.run_kling_batch \
  --prompt-index Archive_prompts_viewpoint_review/_prompt_index.jsonl \
  --out-root Archive_generated_viewpoint_review \
  --summary-out Archive_generated_viewpoint_review/_batch_summary_dry_run.json \
  --dry-run
```

dry-run 结果：

```json
{
  "n_sessions": 10,
  "status_counts": {"dry_run": 10},
  "viewpoint_counts": {
    "salesperson_observable": {"n": 8},
    "surveillance_oblique": {"n": 2}
  }
}
```

真实运行需要先设置：

```bash
export KLINGAI_ACCESS_KEY=...
export KLINGAI_SECRET_KEY=...
```

然后去掉 `--dry-run`。

当前 mixed-view 真实生成结果：

```text
Archive_generated_viewpoint_review/
videos = 10
qa_pass = 6
qa_rejected = 4
```

正式入库命令：

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive_generated_viewpoint_review \
  --output-dir data/piwm_dataset_viewpoint_review \
  --frame-sample 3
```

当前入库统计：

```json
{
  "n_sessions_total": 10,
  "n_sessions_loaded": 6,
  "n_sessions_skipped": 4,
  "n_state_inference_rows": 6,
  "n_state_inference_with_cue_rows": 6,
  "n_transition_modeling_rows": 16,
  "n_policy_preference_rows": 6,
  "n_sessions_by_viewpoint": {
    "salesperson_observable": 5,
    "surveillance_oblique": 1
  },
  "n_sessions_by_product_category": {
    "apparel_premium": 1,
    "cosmetics_skincare": 1,
    "electronics_phone": 3,
    "home_appliance": 1
  },
  "n_sessions_by_split": {
    "ood_persona": 1,
    "test": 1,
    "train": 4
  }
}
```

### 5.6 Pilot30 prompt 审阅包

当前已生成 30 条 Kling 前置 prompt，不触网：

```bash
python3 -m scripts.scenario_sampler \
  --out data/scenario_manifest_pilot30.jsonl \
  --stats-out data/_scenario_stats_pilot30.json \
  --limit 30 \
  --balanced-cues \
  --viewpoints salesperson_observable surveillance_oblique \
  --viewpoint-ratio 0.7 0.3

python3 -m scripts.prompt_builder \
  --manifest data/scenario_manifest_pilot30.jsonl \
  --out-root Archive_prompts_pilot30 \
  --overwrite
```

审阅入口：

```text
Archive_prompts_pilot30/_prompt_index.jsonl
```

统计：

```text
n_prompts = 30
salesperson_observable = 21
surveillance_oblique = 9
每个 cue = 3 条
forbidden_label_hits = 0
```

如果 `video.mp4` 已经存在，只需要重跑抽帧、QA 和 summary，不重新调用 Kling：

```bash
python3 -m scripts.run_kling_batch \
  --prompt-index Archive_prompts_viewpoint_review/_prompt_index.jsonl \
  --out-root Archive_generated_viewpoint_review \
  --summary-out Archive_generated_viewpoint_review/_batch_summary.json \
  --reuse-existing \
  --overwrite
```

## 6. 还缺什么

### 6.1 新数据生成器

目前已有：

- 规范数据 loader；
- 规则层；
- 三套 JSONL exporter；
- Kling 单条视频生成脚本。
- scenario sampler；
- prompt builder；
- viewpoint-aware prompt camera / negative；
- 抽帧工具；
- QA gate；
- 非空 pilot 数据集。
- mixed-view Kling 批量生成与 QA 过滤；
- QA pass 的 mixed-view 正式 JSONL 数据集。
- pilot30 prompt 审阅包。

还缺：

- 批量生成后自动调用 `build_dataset.py` 的端到端脚本。
- 更大规模的 QA pass 数据；
- 对 viewpoint / cue / persona 覆盖率的批量质量统计。
- prompt 审阅通过后的 pilot30 Kling 真实生成与 QA。

### 6.2 抽帧工具

Kling 生成后，用：

```text
scripts/extract_frames.py
```

把：

```text
video.mp4
```

转成：

```text
frames/000.jpg
frames/001.jpg
...
```

该工具读取 `prompt.json.frame_sampling_plan`，写 `frame_manifest.json`，并作为独立脚本保持在主管线外部，不污染 schema / exporter。

### 6.3 真实规范 Archive

当前已有最小 pilot：

```text
Archive_generated_pilot/
data/piwm_dataset_pilot/
data/piwm_dataset/
Archive_generated_viewpoint_review/
data/piwm_dataset_viewpoint_review/
```

`data/piwm_dataset/_stats.json` 与 `data/piwm_dataset_pilot/_stats.json` 当前显示同一批 QA pass 结果：

```json
{
  "n_sessions_total": 3,
  "n_sessions_loaded": 2,
  "n_sessions_skipped": 1,
  "n_state_inference_rows": 2,
  "n_transition_modeling_rows": 5,
  "n_policy_preference_rows": 2,
  "require_qa_pass": true
}
```

这说明数据闭环已最小跑通，但规模和 cue 覆盖仍不足以训练。

当前新增 mixed-view 小批量数据集：

```json
{
  "n_sessions_total": 10,
  "n_sessions_loaded": 6,
  "n_sessions_skipped": 4,
  "n_transition_modeling_rows": 16,
  "n_states_with_action_contrast": 6,
  "n_sessions_by_viewpoint": {
    "salesperson_observable": 5,
    "surveillance_oblique": 1
  }
}
```

这说明“prompt -> Kling video -> extract frames -> QA gate -> JSONL”的闭环已经真实跑通。当前瓶颈从“能否生成”转为“如何提高 QA pass rate 与覆盖率”。

## 7. 建议下一步

建议下一步不要回头处理旧 Archive，而是把 pilot 扩到 30 条 QA pass：

1. 批量调用 `kling/generate_session.js` 生成 `video.mp4`；
2. 用 `scripts.extract_frames` 抽帧到 `frames/`；
3. 跑 `scripts.qa_gate` 生成 `qa_report.json`；
4. 只让 `overall_pass=true` 的 session 入库；
5. 跑：

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive_generated \
  --output-dir data/piwm_dataset \
  --frame-sample 3
```

当前已经形成最小新数据闭环；下一步是规模化与质量统计。
