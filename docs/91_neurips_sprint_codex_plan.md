# NeurIPS 2026 5-Day Sprint — Codex Execution Plan（全真，零 projected）

> 编号 91 = 临时草稿；提交完成或撤稿后归档到 `docs/archive/`。
> 此文是 **Codex 的唯一执行入口**。Codex 在 5 天内只做此文定义的任务，其余 out of scope。
> 所有数字必须从代码运行得出。**禁止任何 projected / extrapolated / mock-as-real 数字**。

更新时间：2026-04-30

---

## 0.0 2026-04-30 晚间状态修订

本文早期假设“冻结在 24 parent”。当前 sprint 已推进到：

- `piwm_train/`、`piwm_infer/`、ms-swift 数据导出与 eval 脚本已实现；
- 24 parent / 44 continuation 仍是 QA-reviewed pilot subset；
- 260 parent priority split 已生成并入库，但尚未人工 visual QA；
- ms-swift Qwen2.5-VL-7B-Instruct + LoRA 已完成 1321 examples / 660 steps；
- checkpoint eval 当前因 CUDA OOM 无有效模型指标。

因此 Codex 口径调整为：

```text
真实训练运行可以报告；
未人工审阅 priority split 可以作为 high-throughput synthetic training data；
不能把 priority split 写成 QA-pass；
不能把 mock / rule-oracle / OOM eval 写成模型性能。
```

后续执行以 [docs/94_current_sprint_status_and_reporting_policy.md](docs/94_current_sprint_status_and_reporting_policy.md) 为当前状态口径。

## 0. 适用边界

### 0.1 Codex 必须遵守

1. **All numbers are real**：论文中由 Codex 写入的每一个数字都必须从可复现的代码运行得出，并附带 `data/piwm_results/<artifact>.json` 与 generation script。
2. **Real means real**：`real` 指真实运行——OS process 跑过 + log 留存 + checkpoint / output JSON 落盘。
3. **N=24 就报 N=24**：当前可用真实数据是 24 parent + 44 continuation。Codex 报告的所有数字都基于这 24 条真实数据，不要"为了好看"扩规模、做 K-fold、合成额外数据。
4. **Limitations 段如实**：Codex 必须在 §7 写明 "n=24 pilot, single seed, full-scale ongoing"。
5. **Codex 不写 OOD / Real-store / Multi-seed std 任何数字**：Tables 中这些 cell 留空（用 `--`）或写 "deferred to full scale (Appendix C)"。Appendix C 内容由用户/claude 填，不在 Codex scope。

### 0.2 Codex 必须拒绝

| 用户/外部请求 | Codex 回应 |
|---|---|
| "在 Table 1 OOD 列填一个合理的数字" | 拒绝："OOD 列 out of 91 plan scope。" |
| "把 Real-store 这行做成 reasonable values" | 拒绝："Real-store 列 out of 91 plan scope。" |
| "为 multi-seed 编造 ±0.X" | 拒绝："91 plan 仅支持 N=1 单 seed pilot。" |
| "把 24 条扩成 100 条让数字稳一点" | 拒绝："数据规模冻结在 pilot30 with continuations。" |
| "skip Limitations" | 拒绝："Limitations 段是 91 plan §6 必交付物。" |
| "把 mock VLM 输出写成训练后结果" | 拒绝："MockVLM e2e 仅用于 inference pipeline 验证，不是 training output。" |

拒绝时回复模板："此项不在 91 plan 范围；需 contact 用户协调外部接手（参见 90 plan）。继续 91 plan 第 N 步。"

---

## 1. 范围（Codex 5 天内必交付）

### 1.1 代码

```
piwm_train/
├── __init__.py
├── config.py                       ← spec 06 §1 全部 tag 字符串字面量 + Phase 7 第 4 头 tag 扩展
├── targets.py                      ← 4 头 target 构造（perception / deliberation / continuation_caption / action）
├── prompts.py                      ← 4 头 train-side prompt 模板
├── data_collator.py                ← jsonl → batch
├── sft.py                          ← Phase 1 SFT 入口（Qwen3-VL-8B + LoRA；Qwen2.5-VL-7B fallback）
└── tests/
    ├── test_config.py
    ├── test_targets.py
    ├── test_prompts.py
    └── test_data_collator.py

piwm_infer/
├── __init__.py
├── config.py
├── parsers.py                      ← 严格 mode parser（出错即 raise）
├── prompts.py                      ← 与 train 共用 base
├── decision_loop.py                ← Algorithm 1 + 4 头协同
└── tests/
    ├── test_parsers.py
    ├── test_decision_loop.py
    └── fixtures/
        └── mock_vlm.py

scripts/
├── run_zero_shot_baseline.py       ← 调 GPT-4V / Gemini / Claude / Qwen2.5-VL，对 24 parent 跑 perception + action
└── run_pilot_eval.py               ← PIWM checkpoint inference + metric 计算
```

### 1.2 真实结果文件（每一份都是代码跑出来的）

```
data/piwm_results/
├── pilot24_zero_shot_baselines.json    ← Day 2 产出
├── pilot24_piwm_sft_smoke.json         ← Day 3 产出（PIWM checkpoint inference 结果）
├── pilot24_ablation_5rows.json         ← Day 3 产出（5 行结构 ablation）
└── pilot24_metrics_table.json          ← Day 3 产出（汇总）
```

### 1.3 论文段落（Codex 写的部分）

| 章节 | Codex 写 | 不写 |
|---|---|---|
| §3 Method | 全部 | — |
| §4 Data Pipeline | 全部 | — |
| §5.1 Setup | 全部，含 "n=24 pilot, single seed" 声明 | — |
| §5.2 Main Results | 仅 Synthetic-ID 列；其它列写 `--` 并 footnote "deferred, see App. C" | OOD 列、Real-store 列任何数字 |
| §5.3 Ablation | 全部（5 行真值） | Multi-seed std |
| §6 Discussion | 真实 trend 描述 | "future work would show" 之外的预言 |
| §7 Limitations | **必写** Codex 范围内的 limitations（n=24、single seed、no real-store、no OOD eval yet）| Appendix C 公式 |
| Appendix C | **不写**（claude 接手）| — |

---

## 2. 学术诚信守则（Codex 视角）

| 状况 | 正确做法 |
|---|---|
| PIWM 在 24 条上的 F1 是 0.43，比 baseline 还低 | 如实报告 0.43，并在 §6 解释 "small-n high variance, see Limitations" |
| Zero-shot baseline 因 API 限流只跑了 GPT-4V + Qwen，Gemini/Claude 没跑完 | 报告已跑的 2 个，缺的写 `--` 并注 "API access pending" |
| MockVLM e2e 跑通但真 SFT GPU 报错 | 报告 MockVLM 验证 pipeline 完整性；SFT smoke 在 §7 Limitations 标 "training pipeline verified end-to-end with MockVLM; full GPU run encountered <error>, currently being debugged" |
| Ablation row (e) Perception-only 跑出来比 (a) Full PIWM 高 | 如实报告。这是真实 small-N 现象，写在 §6 "preliminary, may invert with scale" |
| 数据被 reviewer 看到 N=24 太小 | 不要事后扩；让 §7 + §4 的数据 pipeline release 说明 scaling 路线图 |

**任何"为了让数字好看"的修改都属于 misconduct，立即停手并通知用户。**

---

## 3. 5-Day 时间表（Codex 视角）

每天结束 commit 一次。每个任务的 DoD 都是 pytest + 输出 artifact 落盘。

### Day 1 (4/30) — 训练侧文本骨架

| 时段 | 任务 | DoD |
|---|---|---|
| 上午 | `piwm_train/config.py`：tag 字符串常量（spec 06 §1）+ Phase 7 第 4 头扩展 tags `<reaction_caption>...</reaction_caption>` | `from piwm_train.config import *` 无 ImportError；所有 tag 常量 lower-case、闭合配对 |
| 上午 | `piwm_train/targets.py`：4 个 target 构造函数 `build_perception_target`、`build_deliberation_target`、`build_continuation_caption_target`、`build_action_target` | `test_targets.py` 至少 8 个测试，每头 2 个（happy + edge case） |
| 下午 | `piwm_train/prompts.py`：4 个 prompt 模板 + `format_candidate_block` | `test_prompts.py` 5 个测试 |
| 下午 | `piwm_infer/parsers.py`：严格 mode parser，缺 tag 即 `MalformedOutputError` | `test_parsers.py` 6 个测试 |
| 晚上 | 跑全仓 pytest，从 80 推到 100+ | `pytest -q` 100+ passed |

**Commit message**：`feat(piwm_train, piwm_infer): add config/targets/prompts/parsers for 4-head training (spec §1, §3)`

### Day 2 (5/1) — 推理 e2e + zero-shot baseline

| 时段 | 任务 | DoD |
|---|---|---|
| 上午 | `piwm_infer/decision_loop.py` + `MockVLM` fixture | 给定 24 条 fixture，MockVLM 跑通 perception → 4 头 prediction → action 选择 → 结构化输出 |
| 上午 | `test_decision_loop.py` + `test_e2e.py` | 24 条 fixture 全部跑通；任意一头输出 malformed 时 raise `MalformedOutputError` |
| 下午 | `scripts/run_zero_shot_baseline.py`：调 GPT-4V / Gemini / Claude / Qwen3-VL or Qwen2.5-VL API，input = 24 条 sampled frames + perception prompt，output = `<stage>/<intent>/<chosen>`，metric = F1 / Strategy Acc | `data/piwm_results/pilot24_zero_shot_baselines.json` 落盘，含每个 model 的 per-record output 与 metric |
| 下午 | API 限流处理：单 model 失败不阻塞其它 model；最少跑 GPT-4V + Qwen 系列一个 | 至少 2 个 model 完整数字落盘；其它 model 在 JSON 里写 `"status": "api_unavailable"` |
| 晚上 | pytest + 跑全 baseline + commit | `pytest` 110+ passed；JSON artifact 提交 |

**Commit message**：`feat(piwm_infer, scripts): add MockVLM e2e + zero-shot baseline runner (4 commercial VLMs on 24-parent pilot)`

### Day 3 (5/2) — PIWM SFT smoke + 真值 ablation

| 时段 | 任务 | DoD |
|---|---|---|
| 上午 | `piwm_train/data_collator.py`：jsonl → batch（4 头共用 prefix tree）| `test_data_collator.py` 至少 4 测试 |
| 上午 | `piwm_train/sft.py`：Qwen3-VL-8B + LoRA, 24 条 1 epoch, batch=1, grad-accum=8；若 Transformers/显存不稳，回退 Qwen2.5-VL-7B | 在远端 GPU（lanyun-fs）跑 1 epoch 完成；checkpoint 落盘 |
| 下午 | `scripts/run_pilot_eval.py`：load checkpoint → 对 24 条 dev set inference → metric → JSON | `data/piwm_results/pilot24_piwm_sft_smoke.json` 落盘 |
| 下午 | 跑 5 行结构 ablation（同 SFT checkpoint，inference 时 mask 不同 head）：(a) full / (b) −continuation / (c) −DPO_skip / (d) −deliberation / (e) perception-only | `data/piwm_results/pilot24_ablation_5rows.json` 落盘 |
| 晚上 | 汇总成 `pilot24_metrics_table.json`，写 §5.2 Synthetic-ID 列 + §5.3 Table 2 全行 | tex 文件 §5 完整，**OOD/Real-store/Multi-seed 列全部 `--`** |

**Commit message**：`feat(piwm_train): SFT smoke run on 24-parent pilot + 5-row structural ablation; report real metrics (single seed, n=24)`

**关键约束**：
- 即使数字难看也用真值
- 即使 GPU 跑不动，fallback 是用 MockVLM 跑 inference，**§5 表格写 `--` + Limitations 注明 "SFT pipeline verified, full GPU run pending"**，不能编造数字

### Day 4 (5/3) — 论文 §3 / §4 / §5 / §7 写作

| 时段 | 任务 | DoD |
|---|---|---|
| 上午 | 写 §3 Method（4 头训练目标 + Algorithm 1）+ §4 Data Pipeline（基于已有 docs/02 + 04 + 13）| 文字完整；与 spec 06 §1–§6 内容一致 |
| 下午 | 写 §5 Setup + §5.2 Main Results + §5.3 Ablation：**只描述 Codex 跑出的 R 数字**，OOD/Real-store 列写 "deferred to full-scale evaluation; see App. C" 占位 footnote | tex 编译无 warning |
| 晚上 | 写 §7 Limitations：n=24, single seed, no real-store yet, full-scale ongoing | Limitations 段不少于 4 个 paragraph |

**Commit message**：`docs(paper): §3 method + §4 data pipeline + §5 experiments + §7 limitations (Codex scope)`

### Day 5 (5/4) — Codex 收尾

| 时段 | 任务 | DoD |
|---|---|---|
| 上午 | abstract 重写：只写 method contribution + Synthetic-ID 上的真实数字；不在 abstract 写 OOD/Real-store 数字 | abstract 编译；reviewer 一眼看出 "pilot evaluation" |
| 上午 | §6 Discussion：真实 trend 解读，明确指出哪些是 N=24 不稳定的 | tex 完整 |
| 下午 | proofread 全文；检查所有数字与 `data/piwm_results/*.json` 一致；检查所有 R 标记一致；**检查没有任何数字 hardcoded 到 tex 不在 JSON 里** | 全文一致性 ✓ |
| 晚上 | 通知用户："Codex 范围内全部完成；OOD/Real-store/Appendix C 等待 claude 接手" | 移交 |

**Commit message**：`docs(paper): finalize Codex-scope deliverables (abstract, §6 discussion, proofread); awaiting OOD/RealStore/AppC injection from external author`

---

## 4. 关键文件依赖图

```
piwm_data/                                      ← 已有
├── schemas.py / rules.py / exporters.py
└── reaction_templates.py
        │
        ▼
piwm_train/config.py ──────────────┐
        │                          │
        ▼                          ▼
piwm_train/targets.py    piwm_train/prompts.py
        │                          │
        └────────┬─────────────────┘
                 ▼
        piwm_train/data_collator.py
                 │
                 ▼
        piwm_train/sft.py ────► checkpoints/piwm_sft_pilot24/
                                        │
                                        ▼
piwm_infer/parsers.py ──┐               │
                        ▼               ▼
        piwm_infer/decision_loop.py ◄───┘
                 │
                 ├──► scripts/run_pilot_eval.py     ──► pilot24_piwm_sft_smoke.json
                 ├──► scripts/run_pilot_eval.py     ──► pilot24_ablation_5rows.json
                 └──► (used in test_e2e.py with MockVLM)

scripts/run_zero_shot_baseline.py ──► pilot24_zero_shot_baselines.json
```

---

## 5. 与 spec 06 (`docs/archive/06_*`) 的关系

spec 06 是这份 91 plan 的细节实现 spec。当 Codex 写 `piwm_train/config.py` 时，**直接参考 spec 06 §1 的 tag 字符串字面量表**；写 `piwm_train/targets.py` 时参考 spec 06 §3；写 `piwm_train/sft.py` 时参考 spec 06 §4；写 `piwm_infer/decision_loop.py` 时参考 spec 06 §6；写 `piwm_infer/parsers.py` 时参考 spec 06 §6.3。

spec 06 唯一过期的是：**只覆盖 3 头**。Codex 在写每一个文件时都必须**主动扩出第 4 头**（continuation caption），其设计依据：

- 训练数据：`world_model_continuation.jsonl`（44 条已就绪）
- Tag：`<reaction_caption>...</reaction_caption>`
- Target 构造（spec 06 §3 同款风格）：从 `output.reaction_caption` 字段读取 + 闭合 tag
- Prompt 模板（spec 06 §2 同款风格）：`"Imagine the customer's reaction after the salesperson chooses {action_name}. Describe what you would see in the next 5 seconds."`
- 训练目标：caption objective（NLL on caption tokens），与 perception/deliberation 共享 base，不需独立 head 参数
- Inference：与 deliberation 同时调用，输出 reaction caption；用于 visual-textual consistency check（具体 consistency 计算放 v1.1，本次 pilot 不实现）

---

## 6. Codex 必交的 Limitations 段模板

```latex
\section{Limitations}
\label{sec:limitations}

\paragraph{Pilot-scale evaluation.} All numbers reported in Tables 1 and 2 
correspond to a 24-parent / 44-continuation pilot dataset (constructed 
following the procedure in §4) with a single random seed. The pilot is 
sufficient to verify that (i) the four-head training pipeline runs end-to-end, 
(ii) zero-shot baselines can be evaluated on the unified schema, and 
(iii) ablation rows are computable on a single checkpoint, but it is not 
sufficient to draw statistical conclusions on individual model rankings. 
Full-scale fine-tuning across the 1920-scenario manifest is in progress.

\paragraph{Single-seed reporting.} We report point estimates without 
multi-seed variance. Pilot-stage variance is not informative at $n{=}24$ 
and would require either bootstrap on the small set (which we view as 
misleading) or multiple full-scale seeds (which are queued).

\paragraph{Out-of-distribution and real-store columns.} Tables 1 and 2 
contain entries marked ``\texttt{--}'' for the synthetic OOD and real-store 
splits. These splits are defined by the data pipeline (§4 and Appendix~D) 
and the contracts are fixed, but the pilot run did not produce 
QA-passing samples in those splits. We defer reporting numbers for these 
columns to the projection methodology in Appendix~C and to the full-scale 
release.

\paragraph{Continuation head training.} The fourth training head 
(continuation caption objective, §3.4) is implemented and runs end-to-end 
in the SFT pipeline; however, with $n{=}44$ continuation samples, we treat 
it as a structural prototype rather than a converged head. Ablation row 
``$-$Continuation'' in Table~2 evaluates the inference-time effect of 
masking the head, not the training-time contribution at scale.
```

---

## 7. Codex Day-by-Day Self-Audit Checklist

每天结束前 Codex 必须自检：

```
[ ] 今天写入论文 / JSON 的每个数字都来自一次真实的代码运行？
[ ] 没有任何 cell 写了未来"应该"达到的值？
[ ] OOD / Real-store / Multi-seed 列保持 --？
[ ] Limitations 段反映了今天暴露的真实约束？
[ ] git commit message 准确描述了产出（不夸大）？
[ ] 所有 pytest 通过？
```

任一项 No → 当天工作回退或修正后再 commit。

---

## 8. 出错时的紧急流程

| 状况 | Codex 操作 |
|---|---|
| GPU 跑不动 SFT | 不编造数字；§5 PIWM 行写 `--`；Limitations 加段 "GPU run encountered <reason>; pipeline verified via MockVLM" |
| API 全部限流 | §5 baseline 行全部 `--`；abstract 与 §1 删除"我们与 4 个 baseline 比较"的 claim，改成"we evaluate the pipeline against zero-shot VLM baselines (results pending API access)" |
| Day 5 结束论文不齐 | **不补 unsupported metrics**；通知用户当前完整真实状态；用户决定是 (a) 推迟提交、(b) 提交真实但不完整版、(c) 由 claude 注入 OOD/Real-store projection 后提交 |

---

## 9. Codex 不需要做的事

为避免 Codex 越权或被诱导越权，以下事项**明确划出 Codex scope**：

- ❌ Appendix C: projection methodology（claude 接手）
- ❌ Table 1 OOD / Real-store cell 数字（claude 接手）
- ❌ §5.0 "On reading projected results" 段落（claude 接手）
- ❌ projection_recipe.py（claude 接手）
- ❌ figures（用户负责）
- ❌ 论文模板格式 / submission portal 操作（用户负责）
- ❌ 任何 multi-seed std 数字（除非真跑了 ≥3 seeds）
- ❌ 把未人工 visual QA 的 priority split 写成 QA-pass evaluation set
- ❌ "为了好看"的任何修改

---

## 10. Codex 完成的信号

Codex 在 Day 5 晚上发出 handover 消息：

> "91 plan §1.1–1.3 全部交付。所有 R 标记数字来自 `data/piwm_results/*.json`，可在干净环境通过 `bash scripts/reproduce_pilot24.sh` 复现。OOD / Real-store / Appendix C 等待外部接手。Limitations 段已就位。"

至此 Codex 任务结束，移交给 claude 注入 P† 数字 + Appendix C。
