# PIWM Repo Cleanup and GitHub Management Plan

更新时间：2026-05-02 CST

## 1. 当前状态

### 本地

- 路径：`/Users/mutsumi/Desktop/WorkSpace/ProactiveIntentWorldModel`
- 已经是 Git repo。
- Git remote：

```text
origin = https://github.com/gamefreshman/ProactiveIntentWorldModel.git
```

- 当前主要问题：
  - repo 根目录堆了大量 `Archive_*` 生成产物。
  - Git 历史/索引里已经追踪了部分早期视频、帧和 prompt archive。
  - `kling/.env` 存在，必须保持本地/服务器私有，不能进 GitHub。

### 服务器

- 路径：`/root/lanyun-fs/ProactiveIntentWorldModel`
- 当前不是 Git repo。
- 当前大小约 `14G`。
- 主要空间来源：

| 路径 | 大小 | 说明 |
|---|---:|---|
| `data/` | 7.6G | 数据集、训练输入、评估结果、checkpoint/导出 |
| `Archive_generated_priority256/` | 2.2G | 生成视频与抽帧 |
| `Archive_generated_priority500_new_after280/` | 1.7G | 生成视频与抽帧 |
| `Archive_generated_priority1000_remaining_after500/` | 1.2G | 生成视频与抽帧 |
| `Archive_generated_pilot30/` | 609M | pilot30 与 continuation |

- 服务器敏感文件：

```text
.secrets/kling.env
kling/.env
```

这些只能留在服务器/本地，不进 GitHub。

## 2. 目标结构

GitHub 只管理代码、论文、文档和小型 manifest：

```text
ProactiveIntentWorldModel/
├── piwm_data/
├── piwm_train/
├── piwm_infer/
├── scripts/
├── kling/                    # wrapper only, exclude .env/node_modules
├── docs/
├── paper/
├── data/
│   ├── README.md
│   └── official/
│       ├── README.md
│       └── DATASET_MANIFEST.json
├── README.md
├── RESEARCH_LOG.md
├── pyproject.toml
└── .gitignore
```

数据盘保留大文件和生成产物：

```text
Archive_generated_*/
Archive_prompts_*/
Archive_continuation_prompts_*/
data/piwm_dataset*/
data/piwm_results/
data/priority_generation_queue/
.secrets/
kling/.env
```

## 3. 已完成的低风险改动

- 强化 `.gitignore`，默认排除：
  - 所有 `Archive_generated_*`
  - 所有 `Archive_prompts_*`
  - 所有 `Archive_continuation_prompts_*`
  - `data/piwm_dataset*`
  - `data/piwm_results/`
  - `data/priority_generation_queue/`
  - `.secrets/`
  - `kling/.env`
  - cache / scratch / logs

## 4. 需要确认后执行的高风险动作

下面动作不会删除本地文件，但会从 Git 索引里移除已追踪的大文件。执行后 GitHub 只保留代码/文档，不再跟踪早期视频与帧。

```bash
git rm -r --cached Archive
git rm -r --cached Archive_generated_priority24
git rm -r --cached Archive_generated_priority256
git rm -r --cached Archive_generated_fix3
git rm -r --cached Archive_prompts_priority24
git rm -r --cached Archive_prompts_priority64
git rm -r --cached Archive_prompts_priority256
git rm -r --cached data/piwm_dataset_priority40_qareviewed_sample
git rm -r --cached data/piwm_results
git rm --cached .DS_Store
```

当前检测到约 `2080` 个已追踪的 generated/media 文件需要从 Git 索引移除。

## 5. 服务器接入 GitHub 的建议

推荐直接在服务器当前目录初始化 Git，但大文件保持 ignored：

```bash
cd /root/lanyun-fs/ProactiveIntentWorldModel
git init
git remote add origin https://github.com/gamefreshman/ProactiveIntentWorldModel.git
git fetch origin
git checkout -B main origin/main
```

注意：执行前必须确认当前服务器代码与本地代码差异，避免 checkout 覆盖服务器独有脚本。

更稳的方案是：

```text
/root/lanyun-fs/ProactiveIntentWorldModel      # 保留现有运行目录和数据
/root/lanyun-fs/ProactiveIntentWorldModel_git  # 新建干净 Git checkout
```

然后把数据目录通过软链接或环境变量接给新 checkout。这个方案最安全，但需要更新部分运行路径。

## 6. 推荐执行顺序

1. 本地提交 `.gitignore`、docs、scripts、训练/评估代码。
2. 本地执行 `git rm --cached`，把已追踪的大文件从 Git 管理里拿掉。
3. Push 到 GitHub。
4. 服务器先备份当前目录结构清单：

```bash
find /root/lanyun-fs/ProactiveIntentWorldModel -maxdepth 2 -type d | sort > /root/lanyun-fs/piwm_dirs_before_git.txt
```

5. 服务器新建干净 Git checkout，确认代码能跑。
6. 再决定是否把旧运行目录替换为 Git checkout。

## 7. 不做的事

- 不删除任何视频、frames、训练结果。
- 不把 Kling API key、`.env`、`.secrets` 提交到 GitHub。
- 不把 14G 数据推到 GitHub。
- 不在系统盘存放新增数据。
