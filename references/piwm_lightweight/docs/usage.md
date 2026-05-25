# Usage

```text
seed → manifest → prompt → video
seed → manifest → labeled → sft
```

动作空间与 stage 候选约束见 [design.md](design.md)，字段契约见 [schema.md](schema.md)。

---

## Environment

```bash
pip install openai requests
export OPENAI_API_KEY=...
export KLING_ACCESS_KEY=...
export KLING_SECRET_KEY=...
export KLING_BASE_URL=https://api-beijing.klingai.com
```

`python-dotenv` 可选；未安装时脚本仍可 dry-run。

---

## Step 1 — Seed → Manifest

seed 描述场景初始条件（AIDA 阶段、顾客背景、目标动作）。manifest 只描述当前顾客状态，不含机器动作。

```bash
python script/gen_manifest.py "interest 阶段，高犹豫，价格敏感" --id piwm_051
python script/gen_manifest.py "interest 阶段，高犹豫，价格敏感" --id piwm_051 --dry-run
python script/gen_manifest.py "..." -o -
```

## Step 2A — Manifest → Prompt

只读顾客观察字段，不引入 `best_action`，不暗示后续 intervention。

```bash
python script/gen_prompt.py data/manifest/piwm_051.json
python script/gen_prompt.py --dry-run
python script/gen_prompt.py --overwrite
```

## Step 2B — Manifest → Labeled

LLM 预测每个候选动作的 `next_aida_stage / next_bdi / delta_stage / delta_mental`；系统注入 `action_cost`，计算 `preference_score`，确定 `best_action`。

```bash
python script/gen_deliberation.py data/manifest/piwm_051.json
python script/gen_deliberation.py data/manifest/piwm_051.json --dry-run
python script/gen_deliberation.py data/manifest/piwm_051.json \
  --alpha 0.5 --beta 0.4 --gamma 0.2
```

## Step 3 — Prompt → Video

调用 Kling API，输出 `data/videos/synth/piwm_NNN.mp4`。

```bash
python script/gen_video.py                           # batch，跳过已有视频
python script/gen_video.py data/prompts/piwm_051.md  # single
python script/gen_video.py --dry-run
```

## Step 4 — Labeled → SFT

从 `data/labeled/` 生成 ms-swift 格式 JSONL（`data/sft/`）。帧文件不存在时自动从视频提取。

```bash
python script/gen_sft.py --dry-run --id piwm_001
python script/gen_sft.py                             # 全部（stage1 / stage2 / joint）
python script/gen_sft.py --stage 1
python script/gen_sft.py --overwrite-frames
```

---

## Other Scripts

```bash
# 批量刷新 labeled 字段
python script/upgrade_labeled.py --dry-run
python script/upgrade_labeled.py

# Pipeline 对齐、schema、score 约束检查
python script/check_quality.py

# 为已有 labeled 补充 LLM 1-5 score
python script/gen_scores.py
```

---

## Common Flow

```bash
python script/gen_manifest.py "desire 阶段，中等犹豫" --id piwm_051
python script/gen_prompt.py   data/manifest/piwm_051.json
python script/gen_video.py    data/prompts/piwm_051.md
python script/gen_deliberation.py data/manifest/piwm_051.json
```
