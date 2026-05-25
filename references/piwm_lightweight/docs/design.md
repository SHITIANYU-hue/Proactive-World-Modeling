# PIWM Data Design

## 1. Problem

智能零售设备持续观察顾客，需要在低打扰前提下学习：

1. 从视频可见行为推断 AIDA + BDI 状态。
2. 预测不同机器响应对顾客状态的影响。
3. 选择最合适的 proactive response。

顾客意图是内隐变量，只能通过目光、停留、姿态、手部动作间接推断。干预后真实反应难以采集，因此标注采用结构化 synthetic preference。

## 2. State Model

宏观状态：AIDA

| AIDA | 顾客状态 | 典型可见行为 |
|---|---|---|
| `attention` | 注意到设备，无明确兴趣 | 目光扫过，步伐放慢 |
| `interest` | 主动观察，开始比较 | 停步，目光来回扫视，轻微前倾 |
| `desire` | 有购买意愿，进入权衡 | 目光锁定，身体前倾，手部靠近 |
| `action` | 决定购买，进入操作 | 手臂伸出，动作直接坚定 |

微观状态：BDI

- `belief`：顾客对商品、价格、场景或设备的认知判断。
- `desire`：顾客当前想解决的问题。
- `intention`：顾客接下来最可能采取的行为。

## 3. Action Space

5 个高层 DialogueAct 类别：

| Act | 作用 |
|---|---|
| `hold` | 静默观察，不主动干预 |
| `greet` | 开场问候或收尾致谢 |
| `elicit` | 提问探询需求，帮助顾客聚焦关注方向 |
| `inform` | 提供比较、演示、参数或价格信息 |
| `recommend` | 给出推荐；涵盖安抚降压（降低决策焦虑）语义 |

Per-stage 允许的候选集（候选必须在此集合内，`hold` 必含）：

| aida_stage | 允许候选 |
|---|---|
| attention | hold, greet, elicit, inform |
| interest | hold, elicit, inform, recommend |
| desire | hold, inform, recommend |
| action | hold, greet, recommend |

## 4. Preference Score

见 [schema.md](schema.md)。

## 5. Response Realization

Response Realization 是 PIWM Core 下游的确定性映射层，将 best_action 转换为终端可执行的多模态输出。该层不参与训练，为 rule-based mapping。

**设计原则**：agent 辅助，顾客主导。每个 screen.action 的语义是"让信息可见/可及"，不替顾客做选择，不强占屏幕。

### 输入与输出

输入：`best_action`（Stage-2 输出）+ `aida_stage`（Stage-1 输出）

输出：

| 字段 | 类型 | 说明 |
|---|---|---|
| `screen.action` | enum | 屏幕布局指令 |
| `voice_style` | enum | TTS 语调风格 |

`voice_style` 枚举：`silent` · `soft` · `warm` · `neutral` · `assertive`

### Mapping Table

| best_action | aida_stage | screen.action | voice_style | 设计依据 |
|---|---|---|---|---|
| `hold` | attention | `idle_minimal` | silent | 顾客刚注意到，零打扰 |
| `hold` | interest / desire | `show_ambient_content` | silent | 顾客主动浏览中，保持存在感但不介入 |
| `hold` | action | `idle_minimal` | silent | 顾客已决策进入操作，退出视野 |
| `greet` | attention / action | `show_welcome_message` | warm | 开场问候或行动阶段的简短肯定，短促不阻断 |
| `elicit` | attention / interest | `show_discovery_prompt` | soft | 抛出引导性问题，顾客自主选择是否回应 |
| `inform` | any | `show_info_overlay` | neutral | 在当前视图上叠加关键信息，不替换内容，顾客主导是否深入探索 |
| `recommend` | interest | `highlight_recommended_item` | soft | 柔和高亮，建议性，不强制 |
| `recommend` | desire / action | `highlight_single_item_with_cta` | assertive | 顾客已有意愿，给出明确行动入口 |

### `screen.action` 枚举

| screen.action | 语义 |
|---|---|
| `idle_minimal` | 屏幕熄灭或极简待机，无任何内容 |
| `show_ambient_content` | 展示非打扰性背景内容（品牌图、场景图等），终端自定义具体素材 |
| `show_welcome_message` | 展示开场欢迎语或简短肯定语，短小不阻断 |
| `show_discovery_prompt` | 展示引导性提问（如"您在找哪类商品？"），顾客可选择互动或忽略 |
| `show_info_overlay` | 在当前商品展示上叠加关键信息（参数、价格、评分），半透明非全屏，顾客主导探索深度 |
| `highlight_recommended_item` | 软高亮推荐商品，无强制行动按钮 |
| `highlight_single_item_with_cta` | 强高亮单品并附行动按钮（加购 / 了解更多） |
