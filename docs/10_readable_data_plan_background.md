# PIWM Phase 2：可读版数据生产计划

更新时间：2026-04-28

## 1. 先说一句话

我们不是让 Kling “帮我们标注销售行为”。

我们要做的是：

> 先用销售专家规则决定“这个场景应该是什么状态、应该有哪些动作、每个动作会导致什么后果”，再让 Kling 把这个已经定义好的场景渲染成视频。

所以，Kling 的角色只是“画面生成器”。

真正的标签来源是：

- AIDA / 销售培训知识；
- 我们整理出来的状态机；
- 每条规则里的 cue、state、action、next_state、rationale。

这和 v6 论文里的说法一致：pedagogy 提供 conditional structure，Kling 只渲染视觉侧。

## 2. 我理解的当前论文主线

根据 [08_intro_related_work_v6.md](08_intro_related_work_v6.md)，当前论文不是单纯做一个销售视频数据集，而是在讲：

> PIWM 是一个面向店内主动销售辅助的 Proactive Intent World Model。它不只判断“现在要不要说话”，而是先理解顾客状态，再模拟不同干预动作会带来的后果，最后选择是否开口以及怎么开口。

论文里的三层结构是：

| 层 | 论文含义 | 数据里对应什么 |
|---|---|---|
| Perception | 从视频里看出顾客状态 | `frames + cue -> latent_state / AIDA / BDI` |
| Deliberation | 对每个候选动作预测后果 | `state + action -> next_state / risk / benefit / reward` |
| Action | 比较动作后选择策略，包括沉默 | `candidate_actions -> best_action / preference pair` |

这也是我们现在代码要补齐的原因：

- 如果只有 `rules.py` 里的硬编码，论文里“pedagogy-derived”这一条不够可信；
- 如果没有 Kling 生成视频，模型没有 multimodal observation；
- 如果没有 `transition_modeling`，PIWM 就像普通状态识别模型，不像 world model；
- 如果没有 `policy_preference`，模型不会学“哪个动作更好”。

## 3. 一个样本到底怎么来

一个样本不要从视频开始，而要从“专家规则单元”开始。

### Step 1：先抽一个专家规则单元

例如我们先决定：

```text
product_category = luxury_watch
persona_type     = price_sensitive_cautious
aida_stage       = interest
target_cue       = long_dwell_with_price_check
```

根据专家规则，这个 cue 会推导出：

```text
latent_state     = high_hesitation
intent           = compare_value_for_money
candidate_actions =
  - A1_silent_observe
  - A2_offer_value_comparison
  - A4_open_with_question
```

再根据 transition rules，得到每个动作的后果：

| action | next_state | reward | risk | benefit |
|---|---|---:|---|---|
| `A1_silent_observe` | `continued_hesitation` | 0.3 | low | medium |
| `A2_offer_value_comparison` | `engaged_dialogue` | 0.8 | low | high |
| `A4_open_with_question` | `engaged_dialogue` | 0.6 | low | high |

所以最佳动作是：

```text
best_action = A2_offer_value_comparison
```

这一步完全不需要 Kling。它是专家规则产生标签。

### Step 2：把这个规则单元写成视频生成 prompt

Kling 需要看到的不是 enum 名，而是自然语言画面描述。

同一个规则单元会变成这样的画面脚本：

```text
Camera:
  Multi-view in-store visual observation. In the main setting, use a
  salesperson-observable medium shot where the customer face, gaze,
  hands, product display, and price area are visible.

Scene:
  A premium watch display counter in a quiet retail store.

Customer:
  A cautious shopper stands in front of the watch display. The shopper
  repeatedly looks between the product and the price tag, pauses for a
  long time, lightly touches the watch, then pulls the hand back without
  asking for help.

Visible behavior:
  The key behavior is hesitation around price: long dwell time, repeated
  price checking, no immediate purchase decision.

Do not show:
  salesperson speaking, subtitles, brand names, extra bystanders, obvious
  checkout completion.
```

注意：prompt 里不直接写 `high_hesitation`、`price_sensitive_cautious` 这类标签。  
标签放在 `prompt.json` 里，视频里只渲染可见行为。

### Step 3：Kling 生成当前状态视频

Kling 生成的是“当前状态观察视频”。

第一阶段不要求 Kling 为每个 action 再生成一个后续视频。原因很简单：

- 如果 1 个状态有 3 个候选动作，生成 3 条 continuation video，成本会立刻乘 3；
- 当前训练的 `transition_modeling` 输入是“当前帧 + action”，输出是文本形式的 next_state / risk / benefit；
- next_state 标签本来就来自专家规则，不需要视频模型替我们决定。

所以第一版闭环是：

```text
专家规则 -> 当前状态视频 -> 抽帧 -> 主 schema -> 三套训练 JSONL
```

不是：

```text
当前状态视频 -> Kling 自己想后果 -> 我们再拿来当标签
```

### Step 4：抽帧

Kling 输出：

```text
video.mp4
```

我们用 ffmpeg 抽成：

```text
frames/
├── 000.jpg
├── 001.jpg
├── 002.jpg
└── ...
```

主数据管线只看 `frames/` 和 `prompt.json`，不直接读 mp4。

### Step 5：构造主 schema

同一个 session 最后变成：

```text
Archive_generated/session_xxx/
├── prompt.json
├── video.mp4
├── kling_generation.json
└── frames/
    ├── 000.jpg
    ├── 001.jpg
    └── ...
```

其中 `prompt.json` 记录结构标签：

```json
{
  "session_id": "session_xxx",
  "product_category": "luxury_watch",
  "persona": {
    "type": "price_sensitive_cautious"
  },
  "aida_stage": "interest",
  "target_cue": "long_dwell_with_price_check",
  "kling_prompt": "..."
}
```

Python 管线读取它，生成主 schema：

```text
state_id
images
observable_cues
persona
aida_stage
latent_state
intent
proactive_score
candidate_actions
best_action
next_state_by_action
reward_by_action
provenance
```

### Step 6：导出三套训练数据

从同一条主 schema 导出：

| 文件 | 训练什么 |
|---|---|
| `state_inference.jsonl` | 看图识别当前顾客状态 |
| `transition_modeling.jsonl` | 给定状态和动作，预测动作后果 |
| `policy_preference.jsonl` | 学哪个动作比哪个动作更好 |

这就是 v6 里说的：

> Each generated record is canonicalized into a unified interaction schema and exported into supervision formats for the three hierarchy levels.

## 4. Kling 视频应该怎么“协调”

Kling 不能单独跑，必须被一个 sampler 管住。

我打算把它拆成四个小模块：

### 4.1 `scenario_sampler.py`

负责采样：

```text
scenario
product_category
persona_type
aida_stage
target_cue
```

采样不是随机乱抽，而是按 coverage 计划来：

- 每个 persona 至少覆盖若干 cue；
- 每个 AIDA stage 至少有样本；
- train / OOD split 里保留一些 product 或 persona 不出现在训练；
- 先小规模跑通，再扩大。

### 4.2 `prompt_builder.py`

负责把结构标签翻译成 Kling prompt。

它需要三个 prompt 层：

| 层 | 内容 |
|---|---|
| Camera layer | 镜头、视角、时长、画面限制 |
| Scene layer | 店铺类型、产品、环境 |
| Behavior layer | 目标 cue 的可见动作脚本 |

比如 `long_dwell_with_price_check` 必须稳定翻译成：

```text
long dwell, repeated price checking, hesitation, no checkout
```

而不是每次随便写。

### 4.3 `kling/generate_session.js`

负责真正调用 Kling。

这个文件现在已经有了，但它只是低层 API wrapper。  
它还不会自己构造好视频内容。

未来调用顺序应该是：

```text
scenario_sampler.py -> prompt_builder.py -> prompt.json
node kling/generate_session.js --prompt prompt.json
```

### 4.4 `extract_frames.py`

负责把 `video.mp4` 抽成 `frames/`。

它应该是独立脚本，不放进 Python 主 loader 里，避免 loader 依赖 ffmpeg。

## 5. 视频构造的关键原则

### 原则 1：视频只呈现“当前状态”，不呈现标签

不能让视频里出现：

- state 名字；
- action 名字；
- AIDA 标签；
- 字幕；
- 可读说明文字。

模型必须从视觉行为中推断状态。

### 原则 2：persona 要通过行为表达，不靠刻板人口属性

`price_sensitive_cautious` 不应该写成某种年龄、性别、族裔。

它应该写成：

```text
carefully checks price, hesitates before touching product,
compares options, avoids immediate purchase commitment
```

### 原则 3：target cue 必须是画面核心

如果样本标签是 `long_dwell_with_price_check`，视频就必须明显显示：

- 停留时间长；
- 看价格；
- 犹豫；
- 没有快速购买。

如果 Kling 生成的视频看不出这个 cue，这条样本应该进入 QA reject。

### 原则 4：动作后果来自专家规则，不来自 Kling 猜测

Kling 不是 world model。  
PIWM 才要学习 world model。

所以 `next_state_by_action` 必须来自专家规则表，而不是让 Kling 生成完以后我们去脑补。

### 原则 5：先做 current-state video，后续再考虑 action-continuation video

第一阶段：

```text
1 个当前状态视频 + 多个 action 的文本后果标签
```

后续如果要增强，可以为少量关键动作生成 continuation videos：

```text
current video + action A -> continuation video A
current video + action B -> continuation video B
```

但这不是当前 P0，否则数据成本会爆炸。

## 6. 和专家知识模块的关系

专家知识模块不是为了“多写几个漂亮 JSON”。

它的作用是让以下链路成立：

```text
教材 / SOP / AIDA
  -> conditional_rules.jsonl
  -> 编译出 rules.py 的运行时规则表
  -> sampler 抽样
  -> prompt_builder 构造 Kling prompt
  -> Kling 生成视频
  -> build_dataset 导出三套训练数据
```

如果没有 `conditional_rules.jsonl`，那 Kling prompt 就只是我们临时写的视觉描述，论文里的 “pedagogy-derived state machine” 就没有代码证据。

## 7. 当前代码和论文 v6 的差距

当前代码已经有：

- 主 schema；
- `rules.py` 规则表；
- 三套 exporter；
- Kling API wrapper；
- 36 个测试通过。

但还缺：

| v6 论文 claim | 当前代码状态 | 需要补 |
|---|---|---|
| pedagogy-derived action space | 现在是 `rules.py` 硬编码 | `expert_corpus/conditional_rules.jsonl` |
| AIDA + BDI | 现在只有 `aida_stage` 和 `intent` | 后续批次加显式 BDI |
| Kling renders visual side | 现在只能读已有 `prompt.json` 调 Kling | `scenario_sampler.py` + `prompt_builder.py` |
| unified interaction schema | 已有 | 需要接入专家来源 provenance |
| three supervision formats | 已有 | 后续加 BDI 后再升级字段 |
| OOD split | 还没有 | sampler 加 split 策略 |

## 8. 我建议的真实执行顺序

### 第一批：专家规则先落地

目标：

```text
conditional_rules.jsonl 能覆盖当前 rules.py 的五张表
```

这样论文里的专家知识链路先不空。

### 第二批：视频 prompt 构造器

目标：

```text
给定 product/persona/aida/cue，自动生成稳定 Kling prompt
```

这一步才真正解决“怎么构造视频”。

### 第三批：Kling 生成闭环

目标：

```text
sample -> prompt -> Kling -> video.mp4 -> frames -> dataset jsonl
```

### 第四批：BDI 显式化

目标：

```text
schema 输出 belief / desire / intention
```

这一步对论文很重要，但我建议放在视频闭环之后，避免同时改太多。

## 9. 现在最需要你判断的点

我认为当前应该坚持这个判断：

> 第一版视频只生成当前状态，不生成每个 action 的后续视频。

因为这更符合当前训练设计，也更省成本。

如果你希望论文更强地展示“动作后果是视频级别的”，那就要改成更贵的设计：

```text
每个 current state 生成 1 个观察视频，
再为每个关键 action 生成 1 个 continuation video。
```

这个设计更强，但数据量和质量控制成本至少乘以候选动作数。

我目前建议先不这么做。
