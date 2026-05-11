# Remote Sprint Runbook

更新时间：2026-05-11

本 runbook 只记录远端执行入口和状态检查命令。不要在仓库、命令行历史或文档里写入真实 API key；Kling / 模型服务凭据只从远端 shell 环境或私有 secret 文件加载。

## 0. 当前 live 状态

远端数据盘项目路径：

```text
/root/lanyun-fs/ProactiveIntentWorldModel
```

远端完整 Git checkout：

```text
/root/lanyun-fs/ProactiveIntentWorldModel_git
```

当前已完成：

- `data/official/`：PIWM v1 official aliases 已固定。
- Action Space / data schema v2 已推送到 GitHub 分支 `codex/piwm-action-space-v2-integration`，远端完整 Git checkout 按该分支最新提交通过 Git bundle 快进；精确提交以 `git rev-parse --short HEAD` 为准。
- 单文件拍摄脚本已固定：`docs/current/piwm_real_shooting_scripts_S01_S12.md`；旧分散脚本目录不再作为入口。
- `PIWM-RealShoot-v1` manifest 样例已生成：24 rows，覆盖 S01-S12 的 A/B 响应。
- 本地与远端完整测试均通过：`python3 -m pytest piwm_data/tests piwm_train/tests piwm_infer/tests` = `170 passed`。
- `data/official/ms_swift/piwm_train_synth_v1.jsonl`：543 parent / 2554 SFT examples，synthetic train，未全量人工视觉 QA。
- `data/official/ms_swift/piwm_train_full_v2.jsonl`：3339 SFT examples，包含 perception / deliberation / action-selection / continuation caption / Future Verification。
- `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl`：36 QA-pass parent / 162 eval rows。
- `data/official/ms_swift/piwm_world_model_sft_v1.jsonl`：24 parent / 44 continuation / 84 Future Verification rows。
- 最新有效训练 checkpoint：`data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834`。

当前未完成：

- Kling API 已耗尽，当前不会继续生成新视频。
- synthetic train 不能写成 QA-pass；若需要更强评估可信度，只能补人工 QA 或引入真实拍摄数据。
- 远端连接偶发不可用时，不要在本地系统盘重跑大任务；等待远端恢复或只做文档/小 JSON 更新。

口径：

```text
PIWM-Train-Synth-v1 = high-throughput synthetic train split, visual QA pending.
PIWM-Eval-QA-v1 = QA-reviewed eval subset.
PIWM-WorldModel-v1 = QA-reviewed pilot continuation / Future Verification subset.
```

## 1. 路径约定

| 用途 | 路径 |
|---|---|
| 远端数据盘工作目录 | `/root/lanyun-fs/ProactiveIntentWorldModel` |
| 远端完整 Git checkout | `/root/lanyun-fs/ProactiveIntentWorldModel_git` |
| 远端数据管线虚拟环境 | `/root/lanyun-fs/venvs/piwm` |
| 远端训练虚拟环境 | `/root/lanyun-fs/venvs/piwm-train-fast` |
| official 数据入口 | `data/official/` |
| full v2 SFT 输入 | `data/official/ms_swift/piwm_train_full_v2.jsonl` |
| synth v1 SFT 输入 | `data/official/ms_swift/piwm_train_synth_v1.jsonl` |
| QA eval 输入 | `data/official/ms_swift/piwm_eval_qa_all_v1.jsonl` |
| World Model/FV 输入 | `data/official/ms_swift/piwm_world_model_sft_v1.jsonl` |
| 最新 full v2 checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834` |
| priority24 prompt index | `data/priority_generation_queue/prompt_index_priority24.jsonl` |
| priority24 prompt 目录 | `Archive_prompts_priority24/` |
| priority24 Kling 输出目录 | `Archive_generated_priority24/` |
| priority24 Kling batch summary | `data/priority_generation_queue/kling_batch_priority24_summary.json` |
| pilot30 + continuation 数据集 | `data/piwm_dataset_pilot30_with_continuations/` |
| sprint 结果目录 | `data/piwm_results/` |
| priority280 unreviewed dataset | `data/piwm_dataset_priority280_unreviewed/` |
| ms-swift combined SFT jsonl | `data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl` |
| legacy sprint checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660` |

本地和远端尽量保持同一相对路径。需要同步时，只同步代码、`data/priority_generation_queue/`、`Archive_prompts_priority24/`、必要的 QA 后产物和结果 JSON；不要把模型 cache、checkpoint 大目录或凭据文件混进 git。

### 1.1 Action Space v2 同步包

2026-05-11 本地已生成只包含动作空间 v2、数据格式 v2、S01-S12 拍摄脚本和对应测试的轻量同步包：

```text
local_artifacts/remote_sync/piwm_action_space_v2_20260511.tgz
local_artifacts/remote_sync/piwm_action_space_v2_20260511.tgz.sha256
local_artifacts/remote_sync/piwm_action_space_v2_filelist_20260511.txt
```

当前状态：

- 已通过 `ssh -p 37150 root@qhdlink.lanyun.net` 连接远端。
- 已上传并解包到 `/root/lanyun-fs/ProactiveIntentWorldModel`。
- 已建立完整 Git checkout：`/root/lanyun-fs/ProactiveIntentWorldModel_git`。由于远端直接 GitHub clone/fetch 偶发挂起，当前采用本地 Git bundle 增量同步并在远端 `git merge --ff-only FETCH_HEAD`。
- 远端 checksum 已通过；最新哈希以 `/root/lanyun-fs/piwm_action_space_v2_20260511.tgz.sha256` 为准。
- 已清理第一次 macOS tar 产生的 `._*` AppleDouble 元数据文件。
- 已删除远端旧分散脚本目录 `docs/current/shooting_scripts/`，现在只保留单文件脚本 `docs/current/piwm_real_shooting_scripts_S01_S12.md`。
- 已同步 `PIWM-RealShoot-v1` manifest 样例：24 rows。
- 已把远端 official symlink 目标目录同步到 v2：`data/official/piwm_train_synth_v1`、`data/official/piwm_eval_qa_v1`、`data/official/piwm_world_model_v1` 的 `main_schema.jsonl` 均含 `dialogue_act / act_params / co_acts / realization`。
- 远端 v2 相关轻量测试通过：`57 passed`。
- 远端完整 Git checkout 已补齐测试夹具 symlink：`Archive_generated_pilot30`、`data/piwm_dataset_pilot30`、`data/piwm_dataset_pilot30_with_continuations_compact_v2`、`data/official/piwm_world_model_v1`。
- 远端完整测试通过：`/root/lanyun-fs/venvs/piwm/bin/python -m pytest piwm_data/tests piwm_train/tests piwm_infer/tests` = `170 passed in 9.14s`。

复同步命令：

```bash
scp local_artifacts/remote_sync/piwm_action_space_v2_20260511.tgz \
  local_artifacts/remote_sync/piwm_action_space_v2_20260511.tgz.sha256 \
  root@qhdlink.lanyun.net:/root/lanyun-fs/

ssh -p 37150 root@qhdlink.lanyun.net \
  'cd /root/lanyun-fs && sha256sum -c piwm_action_space_v2_20260511.tgz.sha256'

ssh -p 37150 root@qhdlink.lanyun.net \
  'cd /root/lanyun-fs/ProactiveIntentWorldModel && rm -rf docs/current/shooting_scripts && tar -xzf ../piwm_action_space_v2_20260511.tgz'
```

解包后先跑远端轻量校验：

```bash
cd /root/lanyun-fs/ProactiveIntentWorldModel
PATH=/root/lanyun-fs/venvs/piwm/bin:$PATH
python3 -m pytest piwm_data/tests/test_rules.py piwm_data/tests/test_schemas.py piwm_data/tests/test_exporters.py
```

完整仓库校验在 Git checkout 下运行：

```bash
cd /root/lanyun-fs/ProactiveIntentWorldModel_git
PATH=/root/lanyun-fs/venvs/piwm/bin:$PATH
python3 -m pytest piwm_data/tests piwm_train/tests piwm_infer/tests
```

若 GitHub fetch 不稳定，用本地 bundle 增量同步，不要在数据盘目录里手工覆盖 tracked 源码文件。

## 2. 数据盘规则

- 在 `/root/lanyun-fs/ProactiveIntentWorldModel` 下运行大文件任务；不要写系统盘临时目录。
- Kling 输出、抽帧、QA report、SFT checkpoint 和中间结果都放数据盘相对目录。
- 新一轮真实生成使用新的输出目录，例如 `Archive_generated_priority24/`；不要覆盖 `Archive_generated_pilot30/` 或已有审阅目录。
- `build_dataset` 默认只纳入 `qa_report.overall_pass=true` 的 session。priority280 是 sprint 的显式例外：它可以作为 `*_unreviewed` 训练 split 使用，但必须在路径和文档中保留 `unreviewed` / `pending visual QA` 口径。
- 所有论文数字必须来自落盘 JSON；缺失就保持 missing / unknown，不补估计值。

## 3. priority24 Kling 命令

先进入远端目录并启用环境：

```bash
cd /root/lanyun-fs/ProactiveIntentWorldModel
PATH=/root/lanyun-fs/venvs/piwm/bin:$PATH
```

真实调用 Kling 前确认远端 shell 已有私有凭据环境变量，但不要打印它们。

```bash
python3 -m scripts.run_kling_batch \
  --prompt-index data/priority_generation_queue/prompt_index_priority24.jsonl \
  --out-root Archive_generated_priority24 \
  --summary-out data/priority_generation_queue/kling_batch_priority24_summary.json \
  --model kling-v3.0-t2v \
  --duration 10 \
  --mode pro
```

只检查脚本和 prompt wiring、不调用 Kling：

```bash
python3 -m scripts.run_kling_batch \
  --prompt-index data/priority_generation_queue/prompt_index_priority24.jsonl \
  --out-root Archive_generated_priority24_dryrun \
  --summary-out data/priority_generation_queue/kling_batch_priority24_dryrun_summary.json \
  --dry-run
```

## 4. QA gate 命令

对 priority24 生成目录重新生成 QA report，并写出可审计索引：

```bash
python3 -m scripts.qa_gate \
  --archive-root Archive_generated_priority24 \
  --index-out data/priority_generation_queue/qa_index_priority24.jsonl
```

只读检查、不覆盖已有 QA report：

```bash
python3 -m scripts.qa_gate \
  --archive-root Archive_generated_priority24 \
  --index-out data/priority_generation_queue/qa_index_priority24_readonly.jsonl \
  --no-write
```

## 5. build_dataset 命令

priority24 生成完成并通过 QA 后，构建单独数据集：

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive_generated_priority24 \
  --output-dir data/piwm_dataset_priority24 \
  --frame-sample 3 \
  --require-continuation
```

当前 sprint 的已验证 pilot30 + continuation 数据集路径是：

```bash
data/piwm_dataset_pilot30_with_continuations/
```

如果只是复查现有产物，不要重建覆盖该目录；先用 `scripts/print_sprint_status.py` 看状态。

## 6. SFT / ms-swift 状态

当前正式 SFT 使用 `ms-swift`，不是 LLaMA-Factory。最新有效 run：

```text
model: Qwen2.5-VL-7B-Instruct + LoRA
data: data/official/ms_swift/piwm_train_full_v2.jsonl
examples: 3339
checkpoint: data/piwm_results/ms_swift_sft_qwen25vl7b_full_v2_len8192_8gpu/v0-20260502-193050/checkpoint-834
```

以下旧 `piwm_train.sft` 命令只保留为纯 Python adapter / dry-run 入口，不是当前正式 SFT 框架。

依赖无关的本地/远端 dry-run smoke：

```bash
python3 -m piwm_train.sft \
  --data-dir data/piwm_dataset_pilot30_with_continuations \
  --output-dir data/piwm_results/sft_adapter_smoke \
  --dry-run
```

旧远端 GPU smoke，输出 `piwm_train.sft` 训练 summary：

```bash
python3 -m piwm_train.sft \
  --data-dir data/piwm_dataset_pilot30_with_continuations \
  --output-dir checkpoints/piwm_sft_pilot24 \
  --max-examples 24 \
  --epochs 1 \
  --gradient-accumulation-steps 8
```

如果显存或依赖不稳，用命令行显式记录 fallback model；不要改 `piwm_train/sft.py` 来硬编码临时路径：

```bash
python3 -m piwm_train.sft \
  --data-dir data/piwm_dataset_pilot30_with_continuations \
  --output-dir checkpoints/piwm_sft_pilot24_qwen25_fallback \
  --model-name Qwen/Qwen2.5-VL-7B-Instruct \
  --max-examples 24 \
  --epochs 1 \
  --gradient-accumulation-steps 8
```

## 7. summary 命令

刷新 sprint JSON 与 Markdown snapshot：

```bash
python3 -m scripts.summarize_sprint_results \
  --root . \
  --dataset-stats data/piwm_dataset_pilot30_with_continuations/_stats.json \
  --mock-eval data/piwm_results/pilot24_mock_pipeline_eval.json \
  --sft-summary data/piwm_results/sft_train_summary.json \
  --zero-shot data/piwm_results/pilot24_zero_shot_baselines.json \
  --summary-out data/piwm_results/sprint_summary.json \
  --markdown-out docs/background/neurips_sprint_result_snapshot_20260430.md
```

只读状态板：

```bash
python3 scripts/print_sprint_status.py
python3 scripts/print_sprint_status.py --json
```

远端运行时可用同一个脚本检查 GPU。没有 `nvidia-smi` 的本地机器会显示 `nvidia-smi not found`，不会失败。

## 8. 最小验证

不联网、不触发远端命令的本地验证：

```bash
python3 -m py_compile scripts/print_sprint_status.py
python3 scripts/print_sprint_status.py
```

提交前至少确认：

- priority24 index 与 `Archive_prompts_priority24/*/prompt.json` 数量一致；
- JSONL 行数符合当前任务预期；
- 结果 JSON 是 valid JSON；
- GPU 状态可见或明确显示 unavailable；
- 文档和命令没有真实密钥。
