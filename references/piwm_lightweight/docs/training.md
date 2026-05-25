# PIWM SFT Training

## Two-Stage Design

```
Stage-1  frames(0/2/5/8/10s)                        →  state
Stage-2  frames + GT state + candidate_actions       →  best_action
```

两个 stage 独立训练，也支持 joint。数据格式统一用 ms-swift JSONL。

动作空间与 per-stage 候选约束见 [design.md](design.md)。

---

## Stage-1: State Identification

**输入**：5 帧图像（0 / 2 / 5 / 8 / 10s）

**输出**：

```json
{
  "aida_stage": "attention | interest | desire | action",
  "bdi": { "belief": "...", "desire": "...", "intention": "..." },
  "observable_behavior": "...",
  "facial_expression": "...",
  "body_posture": "..."
}
```

**数据来源**：`data/manifest/`　　**系统提示**：`docs/state_prompt.md`

---

## Stage-2: Action Selection

**输入**：5 帧图像 + GT state（文本） + candidate_actions 列表

**输出**：

```json
{
  "outcomes": {
    "<act>": {
      "next_aida_stage": "...",
      "next_bdi": { "belief": "...", "desire": "...", "intention": "..." },
      "score": 1
    }
  },
  "best_action": "<act>"
}
```

`score` 为 1–5 整数，best_action 固定为 5，其余按相对效果给分。

**数据来源**：`data/labeled/`　　**系统提示**：`docs/action_prompt.md`

Stage-2 训练时输入 GT state，inference 时输入 Stage-1 预测结果（distribution gap 暂时接受）。

---

## ms-swift 数据格式

```json
{
  "images": ["data/frames/piwm_NNN/t00.jpg", "t02", "t05", "t08", "t10"],
  "messages": [
    { "role": "system",    "content": "系统提示" },
    { "role": "user",      "content": "<image><image><image><image><image>指令" },
    { "role": "assistant", "content": "{序列化 JSON 字符串}" }
  ],
  "meta": {
    "source_id": "piwm_NNN",
    "split": "train | val",
    "stage": "stage1 | stage2",
    "aida_stage": "...",
    "candidate_actions": ["..."]
  }
}
```

`images` 按顺序对应 `<image>` token。`meta` 不参与训练，仅用于数据管理。

---

## 数据来源

| Stage | 来源 | 数量 |
|---|---|---:|
| Stage-1 | `data/manifest/` | 200 |
| Stage-2 | `data/labeled/` | 200 |

---

## DPO（暂不使用）

`data/labeled/` 中每个 outcome 保留 `preference_score`。当前 SFT 阶段不使用；若后续引入 DPO，可直接基于 `preference_score` 构造 chosen/rejected 对。
