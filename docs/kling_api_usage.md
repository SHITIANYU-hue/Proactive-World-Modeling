# Kling API 调用说明

旧项目只作为 Kling API 调用参考，不参与 schema、规则层或旧数据迁移。

本仓库新增的 Kling 入口：

```text
kling/generate_session.js
```

它读取一个符合 `data_pipeline_spec.md` 的 `prompt.json`，调用 Kling 生成 `video.mp4`，并把 `prompt.json` 一起放到输出 session 目录中。

## 安装

```bash
cd kling
npm install
```

环境变量沿用旧项目：

```bash
KLINGAI_ACCESS_KEY=...
KLINGAI_SECRET_KEY=...
```

可以放在 `kling/.env`，也可以从 shell 环境导入。

## Dry Run

不触网、不需要安装依赖：

```bash
node kling/generate_session.js \
  --prompt piwm_data/tests/fixtures/tiny_session/session_test_001/prompt.json \
  --out-root Archive_generated \
  --dry-run
```

## 真实生成

```bash
node kling/generate_session.js \
  --prompt path/to/prompt.json \
  --out-root Archive_generated \
  --model kling-v3.0-t2v \
  --duration 10 \
  --mode pro
```

输出：

```text
Archive_generated/<session_id>/
├── prompt.json
├── video.mp4
└── kling_generation.json
```

注意：主数据管线仍要求 `frames/` 存在。视频生成后需要单独抽帧到：

```text
Archive_generated/<session_id>/frames/
```

抽帧工具不放进本期主范围，避免给 Python 数据管线引入 ffmpeg / OpenCV 等依赖。

