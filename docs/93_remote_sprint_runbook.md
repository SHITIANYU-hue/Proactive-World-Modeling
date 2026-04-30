# Remote Sprint Runbook

更新时间：2026-04-30

本 runbook 只记录远端执行入口和状态检查命令。不要在仓库、命令行历史或文档里写入真实 API key；Kling / 模型服务凭据只从远端 shell 环境或私有 secret 文件加载。

## 0. 当前 live 状态

远端数据盘项目路径：

```text
/root/lanyun-fs/ProactiveIntentWorldModel
```

当前已完成：

- `Archive_generated_priority24/`：24 条 parent videos，未人工 visual QA。
- `Archive_generated_priority256/`：236 条 parent videos，未人工 visual QA。
- `data/piwm_dataset_priority280_unreviewed/`：260 parent 入库，927 transition rows，260 policy rows。
- `data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl`：1321 SFT examples。
- `ms-swift` 4 x 4090 LoRA SFT 已完成：`checkpoint-660`。

当前未完成：

- priority280 的人工 visual QA。
- checkpoint 的有效 inference metric；当前 24 条 balanced eval 因 CUDA OOM 没有有效模型输出。

口径：

```text
priority280 = high-throughput synthetic train split, file-level QA done, visual QA pending.
pilot30 continuation = QA-reviewed pilot subset.
```

## 1. 路径约定

| 用途 | 路径 |
|---|---|
| 远端仓库与数据盘工作目录 | `/root/lanyun-fs/ProactiveIntentWorldModel` |
| 远端数据管线虚拟环境 | `/root/lanyun-fs/venvs/piwm` |
| 远端训练虚拟环境 | `/root/lanyun-fs/venvs/piwm-train-fast` |
| priority24 prompt index | `data/priority_generation_queue/prompt_index_priority24.jsonl` |
| priority24 prompt 目录 | `Archive_prompts_priority24/` |
| priority24 Kling 输出目录 | `Archive_generated_priority24/` |
| priority24 Kling batch summary | `data/priority_generation_queue/kling_batch_priority24_summary.json` |
| pilot30 + continuation 数据集 | `data/piwm_dataset_pilot30_with_continuations/` |
| sprint 结果目录 | `data/piwm_results/` |
| priority280 unreviewed dataset | `data/piwm_dataset_priority280_unreviewed/` |
| ms-swift combined SFT jsonl | `data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl` |
| latest SFT checkpoint | `data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660` |

本地和远端尽量保持同一相对路径。需要同步时，只同步代码、`data/priority_generation_queue/`、`Archive_prompts_priority24/`、必要的 QA 后产物和结果 JSON；不要把模型 cache、checkpoint 大目录或凭据文件混进 git。

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

## 6. SFT / ms-swift 命令

当前正式 sprint SFT 使用 `ms-swift`，不是 LLaMA-Factory。已完成 run：

```text
model: Qwen2.5-VL-7B-Instruct + LoRA
data: data/piwm_results/ms_swift_sprint_combined/ms_swift_sft.jsonl
examples: 1321
steps: 660 / 660
checkpoint: data/piwm_results/ms_swift_sft_qwen25vl7b_sprint_combined_4gpu/v0-20260430-200052/checkpoint-660
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
  --markdown-out docs/92_neurips_sprint_result_snapshot.md
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
