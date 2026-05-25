# Data Schema

动作标签统一使用 5-class：`greet | elicit | inform | recommend | hold`。

## Manifest

`data/manifest/piwm_<id>.json` — 描述当前顾客状态，不包含动作决策。

```json
{
  "session_id": "piwm_001",
  "persona": "一名下班后路过便利区的年轻上班族",
  "persona_visual": "25 岁左右的女性，扎马尾，穿深蓝色西装外套和白衬衫，单肩背一个黑色小包",
  "aida_stage": "interest",
  "bdi": {
    "belief": "设备里可能有合适商品，但还需要比较信息",
    "desire": "想确认哪一款最符合当前需求",
    "intention": "继续停留浏览，在决定前保持谨慎"
  },
  "observable_behavior": "目光在多个位置之间切换，身体轻微前倾",
  "facial_expression": "表情自然克制，带轻微思考",
  "body_posture": "正面朝向镜头，站姿稳定，双手在画面内",
  "timeline": {
    "t_0_2": "顾客走近并停下",
    "t_2_5": "目光稳定看向前方并短暂下移",
    "t_5_8": "视线在不同位置自然切换",
    "t_8_10": "继续停留，保持思考状态"
  }
}
```

## Labeled

`data/labeled/piwm_<id>.json` — 在 manifest 基础上追加候选动作与 synthetic preference。

```json
{
  "session_id": "piwm_001",
  "...manifest fields...",
  "candidate_actions": ["hold", "elicit", "inform"],
  "outcomes": {
    "hold": {
      "next_aida_stage": "interest",
      "next_bdi": {
        "belief": "...",
        "desire": "...",
        "intention": "..."
      },
      "preference_score": 0.0
    },
    "elicit": {
      "next_aida_stage": "interest",
      "next_bdi": { "belief": "...", "desire": "...", "intention": "..." },
      "preference_score": 0.21
    },
    "inform": {
      "next_aida_stage": "interest",
      "next_bdi": { "belief": "...", "desire": "...", "intention": "..." },
      "preference_score": 0.04
    }
  },
  "best_action": "elicit",
  "realization": {
    "screen_action": "show_discovery_prompt",
    "voice_style": "soft"
  }
}
```

字段规则：

| Field | Required | 说明 |
|---|---|---|
| `candidate_actions` | yes | 2–3 个 5-class 标签，含 hold |
| `outcomes[*].next_aida_stage` | yes | 该动作后预测的 AIDA 阶段 |
| `outcomes[*].next_bdi` | yes | 该动作后预测的 BDI（belief/desire/intention） |
| `outcomes[*].preference_score` | yes | 系统计算的 synthetic preference score |
| `best_action` | yes | `argmax(preference_score)` |
| `realization.screen.action` | yes | 由 `best_action` + `aida_stage` 确定性推导，见 [design.md](design.md) §5 |
| `realization.voice_style` | yes | 同上 |

## Preference Score

```text
preference_score = alpha * delta_stage + beta * delta_mental - gamma * action_cost
clip to [-1, 1]
default: alpha=0.4, beta=0.5, gamma=0.2
```

- `delta_stage / delta_mental`：LLM 预测，范围 [-1, 1]
- `action_cost`：系统按 5-class 代表值注入：hold=0.02, greet=0.05, elicit=0.20, inform=0.28, recommend=0.45
- `preference_score / best_action`：系统计算

`delta_stage / delta_mental / action_cost` 不写入最终 labeled 文件。

## Prompt

`data/prompts/piwm_<id>.md` — 由 manifest 渲染的视频生成脚本，描述 intervention 前顾客观察片段，不包含动作信息。
