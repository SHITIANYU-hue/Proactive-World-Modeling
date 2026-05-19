# PIWM Paper Data Section Blueprint

更新时间：2026-05-17 CST

本文是论文数据部分的当前写作蓝图。它把 general synthetic 数据、target-frontcam 数据、真实拍摄数据、World Model continuation、动作空间 v2 和 QA 口径放到同一条叙事里，避免论文、代码、拍摄文档各说一套。

当前 EMNLP 口径已经确定为强主会式的低资源 target specialization：不等待 200 条 video-pending 样本成片，不把 target 规模包装成 300+，而是明确写成 88 条 target train + 30 条项目负责人 QA-reviewed target test 的跨域适配实验。

## 1. 数据目标

PIWM 数据集不是普通的视觉问答数据，也不是单步 sales action 分类数据。核心目标是让模型学习：

```text
current visual evidence
  -> customer intent state
  -> proactive guidance action
  -> action-conditioned future reaction
```

论文中应强调三点：

1. 当前状态来自可见证据，而不是纯文本标签。
2. 策略动作采用 6 个 `DialogueAct` 及参数，不再依赖旧的扁平 A1-A8 标签。
3. World Model 监督要求同一当前状态下，不同动作导致不同未来反应。

## 2. 数据层级

| 层级 | 训练 / 评估对象 | 主字段 | 论文用途 |
|---|---|---|---|
| State Inference | 当前顾客状态识别 | `visual_state`, `aida_stage`, `bdi`, `latent_state` | 证明模型能读懂店内意图状态 |
| Policy Preference | 动作选择与偏好 | `dialogue_act`, `act_params`, `best_action`, `candidate_actions` | 证明模型能选择合适主动响应 |
| Transition Modeling | 动作条件未来预测 | `candidate_action`, `candidate_dialogue_act`, `next_state`, `reward` | 支撑 World Model claim |
| Continuation / Future Verification | 未来反应视觉证据 | `visible_reaction`, `continuation QA`, `future_verification` | 支撑“动作会改变未来”的视觉证据 |
| Real Shooting Clip | 真实拍摄素材入库 | `ShootingClipRecord`, `assets`, `qa` | 连接真实拍摄、后期标注与正式数据 |

## 3. 当前数据资产口径

权威总账见 `docs/current/dataset_inventory.md`。论文中不要从零散目录抓数字，必须以该文档和落盘 `_stats.json` 为准。

| 数据名 | 角色 | 当前口径 |
|---|---|---|
| `PIWM-Train-Synth-v1` | 主 synthetic 训练集 | 可训练，不写成 QA-reviewed |
| `PIWM-Train-Synth-v2` | general retail guidance schema v2.2 训练入口 | 543 parent / 2554 examples；不是新增视频规模 |
| `PIWM-Target-Frontcam-v1` | target 域设备前置摄像头数据 | 118 records / 708 examples；30-record test split 已项目负责人 QA 复核，88 train records 仍是 synthetic_unreviewed |
| `PIWM-Target-PromptReady-v1` | target 域扩展生成队列 | 318 prompt-ready records，其中 200 条 video-pending，不能当作 filmed multimodal training data |
| `PIWM-Train-Full-v2` | 下一次 fresh 训练入口 | 合并 state、policy、continuation/FV |
| `PIWM-Eval-QA-v1` | 主 QA 评估集 | 可写成 QA-reviewed subset |
| `PIWM-WorldModel-v1` | World Model continuation 证据 | 用于 transition、continuation、future verification |
| `PIWM-RealShoot-v1` | 新真实拍摄计划数据 | 拍摄脚本已齐，入库前不写实测规模 |

## 4. 动作空间与数据格式

论文方法和数据部分统一使用 v2 表达：

```json
{
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "co_acts": [],
  "realization": {
    "surface_text": "...",
    "screen": {"action": "show_comparison_or_details"},
    "voice_style": "neutral",
    "light": "soft_focus_on_comparison_cards",
    "cabinet_motion": null,
    "duration_ms": 4000
  },
  "best_action": "A2_offer_value_comparison"
}
```

写作规则：

- 正文写 `DialogueAct + params`。
- 附录或兼容说明写旧 `A1-A8 / T-state`。
- `PIWM-Train-Synth-*` 当前仍保留 human-salesperson guidance 逻辑；`PIWM-Target-Frontcam-v1` 才是 target terminal / smart vending 视角。
- 终端执行写 `TerminalRealization`，不要把 target terminal 数据反写成真人导购肢体动作。
- 表格中保留旧动作 alias，只是为了复现实验和兼容历史数据。

## 5. 真实拍摄设计

真实拍摄按 12 个 customer state，每个状态拍 A/B 两版。A 版为合适终端响应，B 版为失当或对照响应。

| 状态组 | 目的 | 脚本入口 |
|---|---|---|
| S01-S03 早期进入 | 测试何时不打扰、何时开放询问 | `docs/current/piwm_real_shooting_scripts_S01_S12.md` |
| S04-S08 商品评估 | 测试演示、比较、参数澄清 | `docs/current/piwm_real_shooting_scripts_S01_S12.md` |
| S09-S11 卡住或离开 | 测试挽回、降压、错误强推 | `docs/current/piwm_real_shooting_scripts_S01_S12.md` |
| S12 购买后闭环 | 测试成交后体验闭合 | `docs/current/piwm_real_shooting_scripts_S01_S12.md` |

每条成片入库为一个 `ShootingClipRecord`。核心状态 `S03/S05/S07/S11` 同时需要 FPV 和 HERO；其他状态至少需要 FPV。

## 6. QA 与入库门槛

真实拍摄素材进入 QA-reviewed 集前必须满足：

| Gate | 要求 |
|---|---|
| Start State | 前 3 秒能看出 `shooting_state`，A/B 起点一致 |
| Terminal Response | 屏幕/语音/灯效能对应 `TerminalRealization` |
| Reaction | 后 5 秒能看出顾客未来反应 |
| Label Completeness | `dialogue_act`, `act_params`, `legacy_action`, `t_state` 一致 |
| Privacy | 无敏感个人信息、无不可用商标露出 |
| Viewpoint | 核心状态 HERO 视角齐全 |

失败素材可以保留在 raw archive，但不能进入 official eval，也不能写成 QA-pass 数据。

## 7. 推荐论文表格

### Table: Dataset Composition

| Split | Source | Parent States | Rows | QA-reviewed | Purpose |
|---|---|---:|---:|---|---|
| Train-Synth | Synthetic video + rule templates | TBD from inventory | TBD | No | SFT / policy warmup |
| Eval-QA | QA-reviewed synthetic subset | TBD | TBD | Yes | Main evaluation |
| Target-Frontcam | Device front-camera target domain | 118 | 708 SFT examples | Test split only | Domain specialization |
| Target-PromptReady | Target generation queue | 318 | prompt-ready only | No | Future video generation |
| WorldModel | Continuation subset | TBD | TBD | Yes | Future prediction |
| RealShoot | S01-S12 A/B scripts | TBD after filming | TBD | After QA | Real-world validation |

### Table: Action Space

| DialogueAct | Example Params | Role |
|---|---|---|
| `Greet` | `phase=close` | polite opening / closing |
| `Elicit` | `openness=open, slot=need_focus` | collect intent |
| `Inform` | `content_type=comparison/demo` | provide factual help |
| `Recommend` | `target=item, pressure=firm/soft` | recommend item |
| `Reassure` | `focus=time` | reduce pressure |
| `Hold` | `mode=silent/ambient` | wait or remain non-intrusive |

### Table: Real Shooting A/B Design

| State | A Response | B Response | Expected Contrast |
|---|---|---|---|
| S05 犹豫比较 | `Inform(comparison)` | `Recommend(firm)` | clarification vs pressure |
| S07 主动操作 | `Inform(demo)` | `Hold(ambient)` | support vs abandonment |
| S11 放弃倾向 | `Reassure + Hold` | `Recommend(firm)` | low-pressure pause vs accelerated exit |

## 8. 维护机制

新增或修改数据前，按这个顺序更新：

1. 修改契约：`docs/contracts/action_space_realization_contract.md` 或 `docs/contracts/data_schema_v2_contract.md`
2. 修改代码 schema：`piwm_data/rules.py`、`piwm_data/schemas.py`
3. 补测试：`piwm_data/tests/test_rules.py`、`piwm_data/tests/test_schemas.py`
4. 更新脚本或总账：`docs/current/piwm_real_shooting_scripts_S01_S12.md`、`docs/current/dataset_inventory.md`
5. 更新入口：`docs/README.md`、`RESEARCH_LOG.md`
6. 运行 `python3 -m pytest piwm_data/tests piwm_train/tests piwm_infer/tests`

任何字段如果没有测试约束，就不算稳定数据格式。
