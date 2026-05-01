# Local Artifacts Layout

更新时间：2026-05-02

本文记录本机根目录生成产物的整理结果。目标是让 repo 根目录只保留代码、文档和配置；视频、prompt、审阅图和缓存集中放在 `local_artifacts/`，并保持不进入 Git。

## 当前布局

| 目录 | 内容 | 说明 |
|---|---|---|
| `local_artifacts/generated_videos/` | `Archive_generated_*` | Kling 生成的视频 session、抽帧、QA report、continuation 结果 |
| `local_artifacts/prompts/` | `Archive_prompts_*`, `Archive_continuation_prompts_*` | Kling parent prompt 与 continuation prompt 包 |
| `local_artifacts/review_sheets/` | `_remote_review_sheets*` | 远端/本地 QA contact sheet 与审阅材料 |
| `local_artifacts/legacy_archive/` | `Archive/` | 早期旧 pipeline 归档，保留作历史参考 |
| `local_artifacts/cache/` | `.pytest_cache/` | 本地测试缓存，可随时重建 |

## 重要约束

- `local_artifacts/` 已加入 `.gitignore`，不会进入 GitHub。
- 本次整理只移动目录，不删除视频、帧、prompt 或 QA 文件。
- 当前正式数据集口径仍以 `docs/current/dataset_inventory.md` 为准。
- 服务器上大数据仍放在 `/root/lanyun-fs/ProactiveIntentWorldModel`；干净 Git checkout 是 `/root/lanyun-fs/ProactiveIntentWorldModel_git`。

## 常用定位

```bash
# 查看本地整理后的生成产物
du -sh local_artifacts
find local_artifacts -maxdepth 2 -type d | sort

# 找 pilot30 生成视频
ls local_artifacts/generated_videos/Archive_generated_pilot30

# 找 priority prompt 包
ls local_artifacts/prompts/Archive_prompts_priority256

# 找审阅图
ls local_artifacts/review_sheets
```

## 如果脚本仍使用旧根路径

旧路径：

```text
Archive_generated_pilot30
Archive_prompts_priority256
_remote_review_sheets
```

新路径：

```text
local_artifacts/generated_videos/Archive_generated_pilot30
local_artifacts/prompts/Archive_prompts_priority256
local_artifacts/review_sheets/_remote_review_sheets
```

如果某个旧脚本短期内必须按旧路径运行，优先在命令行参数里传入新路径；不要重新把这些目录散放回 repo 根目录。
