# PIWM Visual Input Contract

更新时间：2026-05-16（加入 target_frontcam 后）

本文当前视觉设定为：

```text
PIWM 支持多视角店内视觉输入，用于主动导购 world model。
```

第一阶段执行优先级保持克制：

```text
主线：salesperson_observable
辅助：surveillance_oblique
target 域：target_frontcam
暂缓：first_person_pov
```

## 1. 推荐主线

第一版主线定义为：

```text
单个当前状态视频 -> 多图抽帧 -> 单轮样本 -> 推理时多次调用
```

正式字段：

```text
training_input_mode = multi_image_single_turn
```

含义：

- Kling 按 `viewpoint` 生成一条 current-state video；
- 从视频中抽 K 张关键帧，主实验 K=3；
- 三套训练数据共享同一组 sampled frames；
- 训练样本是单轮监督；
- 推理时同一 VLM 多次调用，完成 perception / deliberation / action。

`viewpoint` 第一版枚举：

| viewpoint | 含义 | 当前优先级 |
|---|---|---|
| `salesperson_observable` | 导购可观察的中近距离店内视角，脸/视线/手/商品可见 | P0 |
| `surveillance_oblique` | 固定高位或斜角监控/第三方视角，身体轨迹和商品区域清楚 | P1 |
| `third_party_side` | 旁观者侧面中景，脸部部分可见，手和商品可见 | P2 |
| `first_person_pov` | 导购第一人称 POV，顾客可能看向镜头 | 暂缓 |
| `target_frontcam` | 设备前置摄像头单视角，顾客正面/半正面面对智能售货柜或终端屏幕 | target 域 |

当前训练 JSONL 中 `viewpoint` 只进入 `meta`，不进入主 `input`，避免模型过度依赖视角标签。

`target_frontcam` 是 domain-specialization 视角，不替代主线 `salesperson_observable`。它的合规边界：

- 摄像机固定在设备/售货柜前侧，允许轻微仰角或广角变形；
- 必须能看到顾客头部朝向、身体是否前倾、是否靠近屏幕或取货口；
- 不要求看到真人导购，因为执行主体是 `target_terminal_logic`；
- 标签中必须保留 `viewpoint=target_frontcam`，并在 official payload 中写出 `view_class=target_frontcam`；
- 当前 `PIWM-Target-Frontcam-v1` 是 synthetic_unreviewed，人工 QA 前不能作为 QA-reviewed in-domain benchmark。

## 2. 为什么不直接主用单图或视频

| 模式 | 当前定位 | 原因 |
|---|---|---|
| 单图单轮 | ablation | 丢失 dwell、handling、comparison 等时间性 cue |
| 多图单轮 | 主线 | 能表达短时行为变化，兼容现有 frame-based pipeline |
| 单视频单轮 | 后续 ablation | 依赖 video-native VLM 支持，token 和训练成本高 |
| 多图多轮 | 后续增强 | 需要 history schema 稳定 |
| 多视频多轮 | 暂不做 | 数据与 QA 成本过高 |

## 3. Kling Prompt 必须服务抽帧

Prompt 不应只写：

```text
The customer hesitates.
```

而应写 behavior timeline：

```text
0-2s: customer approaches the display and notices the product.
2-5s: customer looks down at the price tag, pauses, then looks back at the product.
5-8s: customer lightly touches the product but does not pick it up.
8-10s: customer looks at the price area again and remains undecided.
```

这样抽帧策略才能稳定选择：

```text
cue_onset: 2s
cue_peak: 5s
cue_resolution: 8s
```

## 4. Prompt 层级

`prompt_builder.py` 输出至少包含四层：

| 层 | 内容 |
|---|---|
| Camera | 按 `viewpoint` 生成视角、时长、主体、可见区域 |
| Scene | 店铺、商品、空间布局 |
| Behavior timeline | 目标 cue 在时间轴上的可见行为 |
| Negative | 禁止标签泄露、额外人物、购买完成、夸张表演 |

禁止在 prompt 文本中泄露：

- `latent_state` / `state_subtype`；
- action label；
- reward；
- BDI 标签名；
- “this is high hesitation” 这类标注性文字。

## 5. Frame Manifest

每个生成 session 需要保存：

```text
frame_manifest.json
```

建议格式：

```json
{
  "source_video": "video.mp4",
  "viewpoint": "salesperson_observable",
  "training_input_mode": "multi_image_single_turn",
  "frame_sampling_strategy": "cue_timeline_3point",
  "sampled_frames": [
    {"index": 0, "path": "frames/000.jpg", "timestamp_sec": 2.0, "role": "cue_onset"},
    {"index": 1, "path": "frames/001.jpg", "timestamp_sec": 5.0, "role": "cue_peak"},
    {"index": 2, "path": "frames/002.jpg", "timestamp_sec": 8.0, "role": "cue_resolution"}
  ]
}
```

## 6. QA Gate

QA 必须检查两层：

1. 整段视频是否合理；
2. sampled frames 是否足以支持标签。

`qa_report.json` 至少包含：

```json
{
  "viewpoint": "salesperson_observable",
  "video_level_pass": true,
  "sampled_frames_pass": true,
  "target_cue": "long_dwell_with_price_check",
  "viewpoint_pass": true,
  "required_visibility": {
    "face_visible": true,
    "gaze_visible": true,
    "hands_visible": true,
    "product_visible": true,
    "price_area_visible": true
  },
  "cue_visible_in_video": true,
  "cue_visible_in_sampled_frames": true,
  "label_leakage": false,
  "extra_subjects": false,
  "rejection_reason": null
}
```

如果视频整体有 cue，但 sampled frames 没有 cue，这条样本不能进入训练集。

不同 viewpoint 的人工 QA checklist 不同：

| viewpoint | 必须检查 |
|---|---|
| `salesperson_observable` | face / gaze / hands / product / price area |
| `surveillance_oblique` | body trajectory / dwell / hands or arm movement / product area |
| `third_party_side` | profile / head direction / hands / product |
| `first_person_pov` | customer face or gaze / interaction distance / product partial visibility |

## 7. 三套 JSONL 共享视觉输入

| JSONL | 视觉输入 |
|---|---|
| `state_inference.jsonl` | sampled frames |
| `transition_modeling.jsonl` | 同一组 sampled frames + 单个 action |
| `policy_preference.jsonl` | 同一组 sampled frames + candidate outcomes |

这对应论文 §3.5 的设计理由：一个 VLM 共享视觉 grounding，而不是三套互不相干的数据。

## 8. Definition of Done

| DoD | 验收 |
|---|---|
| Visual-1 | `prompt_builder.py` 输出 behavior timeline（已完成第一版） |
| Visual-2 | `extract_frames.py` 生成 `frame_manifest.json`（已完成第一版） |
| Visual-3 | QA 同时检查 video-level 与 sampled-frame-level（第一版已完成，需人工 review JSON） |
| Visual-4 | loader / build_dataset 只读取 QA pass 样本（已完成：build_dataset 默认要求 `overall_pass=true`） |
| Visual-5 | K=1 single-frame ablation 可由同一 video/frame manifest 派生 |
| Viewpoint-1 | scenario / prompt / frame_manifest / qa_report / JSONL meta 都有 `viewpoint`（已完成 V1-V4） |
| Viewpoint-2 | `prompt_builder.py` 按 viewpoint 生成 camera / negative（已完成） |
| Viewpoint-3 | QA gate 按 viewpoint 生成 visibility checklist（已完成第一版，人工填写） |
| Viewpoint-4 | `viewpoint` 只进 JSONL meta，不进主 input（已完成） |
| Viewpoint-5 | mixed-view Kling 真实小批量生成与 QA（已完成：10 条生成，6 条 QA pass） |

## 9. 当前 Phase 3 / Phase 4 产物

已实现：

```text
scripts/scenario_sampler.py
scripts/prompt_builder.py
data/scenario_manifest.jsonl
data/_scenario_stats.json
Archive_prompts_viewpoint_review/<session_id>/prompt.json
Archive_generated_pilot/<session_id>/video.mp4
Archive_generated_pilot/<session_id>/frames/*.jpg
Archive_generated_pilot/<session_id>/frame_manifest.json
Archive_generated_pilot/<session_id>/qa_report.json
data/piwm_dataset_pilot/*.jsonl
data/piwm_dataset/*.jsonl
scripts/run_kling_batch.py
Archive_generated_viewpoint_review/<session_id>/video.mp4
Archive_generated_viewpoint_review/<session_id>/frames/*.jpg
Archive_generated_viewpoint_review/<session_id>/qa_report.json
data/piwm_dataset_viewpoint_review/*.jsonl
data/scenario_manifest_pilot30.jsonl
Archive_prompts_pilot30/<session_id>/prompt.json
```

当前 manifest 规模：

```text
n_scenarios = 1920
train = 1112
dev = 148
test = 140
ood_product = 240
ood_persona = 280
salesperson_observable = 1536
surveillance_oblique = 384
```

审阅用 prompt：

```text
Archive_prompts_viewpoint_review/_prompt_index.jsonl
```

当前 10 条 mixed-view prompt 审阅包：

```text
salesperson_observable = 8
surveillance_oblique = 2
```

真实 mixed-view Kling 小批量结果：

```text
Archive_generated_viewpoint_review/
videos = 10
sampled_frames = 30
qa_pass = 6
qa_rejected = 4
```

通过 QA 并进入正式数据集：

```text
data/piwm_dataset_viewpoint_review/
main_schema.jsonl = 6
state_inference.jsonl = 6
state_inference_with_cue.jsonl = 6
transition_modeling.jsonl = 16
policy_preference.jsonl = 6
```

按视角统计：

```text
salesperson_observable: 5 pass / 8 generated
surveillance_oblique: 1 pass / 2 generated
```

被拒绝样本的主要原因：

| 原因 | 数量 | 说明 |
|---|---:|---|
| target cue 不可见 | 1 | `brief_glance_walking_past` 生成成了近似静止浏览 |
| viewpoint visibility 不合格 | 2 | `salesperson_observable` 下脸/视线被裁切或遮挡 |
| prompt label leakage | 1 | 旧 prompt 中出现内部状态词 `disengaged`，已从未来模板中移除，但该旧视频不入库 |

当前结论：

- `salesperson_observable` 是第一阶段主线可行视角，但 prompt 需要继续加强“脸/视线/手/商品/价格区同框”约束；
- `surveillance_oblique` 可以作为 P1 辅助视角，pass 样本能进入数据集，但不应在主训练中过早扩大比例；
- `brief_glance_walking_past` 这类短时 cue 对 K=3 抽帧更敏感，后续需要更强 timeline 或更密集抽帧 ablation。

## 10. Pilot30 Prompt 审阅包（历史状态）

当前已生成下一轮 Kling 前置审阅包：

```text
data/scenario_manifest_pilot30.jsonl
data/_scenario_stats_pilot30.json
Archive_prompts_pilot30/_prompt_index.jsonl
Archive_prompts_pilot30/<session_id>/prompt.json
```

覆盖统计：

```text
n_prompts = 30
salesperson_observable = 21
surveillance_oblique = 9
每个 cue = 3 条
products = 8 类全覆盖
splits = train/dev/test/ood_product/ood_persona 全覆盖
forbidden_label_hits = 0
```

历史注记：本节最初记录的是 Kling 调用前的 prompt 审阅状态。截至 2026-04-30 晚，`Archive_generated_pilot30/` 已生成 30 条视频并完成 manual QA；其中 24 条 parent 与 44 条 continuation 进入 `data/piwm_dataset_pilot30_with_continuations/`。当前新的未人工 visual QA 主体是 priority280 high-throughput synthetic split，见 [docs/current/current_sprint_status_and_reporting_policy.md](docs/current/current_sprint_status_and_reporting_policy.md)。

如果后续重新生成 prompt，仍应先做 prompt 人工审阅，确认：

- camera section 是否与 viewpoint 一致；
- target cue 是否能在 10 秒行为时间轴中被看见；
- negative constraints 是否排除了上一轮的裁脸、遮挡、静止化和标签泄露问题。

mixed-view batch dry-run：

```text
Archive_generated_viewpoint_review/_batch_summary_dry_run.json
```

可复现命令：

```bash
python3 -m scripts.scenario_sampler \
  --out data/scenario_manifest.jsonl \
  --stats-out data/_scenario_stats.json \
  --viewpoints salesperson_observable surveillance_oblique \
  --viewpoint-ratio 0.8 0.2

python3 -m scripts.scenario_sampler \
  --out data/scenario_manifest_viewpoint_review10.jsonl \
  --stats-out data/_scenario_stats_viewpoint_review10.json \
  --limit 10 \
  --balanced-cues \
  --viewpoints salesperson_observable surveillance_oblique \
  --viewpoint-ratio 0.8 0.2

python3 -m scripts.prompt_builder \
  --manifest data/scenario_manifest_viewpoint_review10.jsonl \
  --out-root Archive_prompts_viewpoint_review \
  --overwrite

python3 -m scripts.run_kling_batch \
  --prompt-index Archive_prompts_viewpoint_review/_prompt_index.jsonl \
  --out-root Archive_generated_viewpoint_review \
  --summary-out Archive_generated_viewpoint_review/_batch_summary_dry_run.json \
  --dry-run

python3 -m scripts.run_kling_batch \
  --prompt-index Archive_prompts_viewpoint_review/_prompt_index.jsonl \
  --out-root Archive_generated_viewpoint_review \
  --summary-out Archive_generated_viewpoint_review/_batch_summary.json \
  --overwrite

python3 -m piwm_data.build_dataset \
  --archive-root Archive_generated_viewpoint_review \
  --output-dir data/piwm_dataset_viewpoint_review \
  --frame-sample 3
```

历史 pilot 已完成最小闭环验证：已调用 Kling、正式抽帧、生成 `qa_report.json`，并让 2 条 QA pass session 进入 `data/piwm_dataset/`；另保留同源 `data/piwm_dataset_pilot/` 作为本轮 pilot 镜像。当前 mixed-view 小批量已进一步把可入库样本扩展到 6 条。

## 11. Phase 4 Smoke Test 与 Pilot 观察

2026-04-29 先用 3 条 prompt 跑通 Kling v3.0 测试，并按 2s / 5s / 8s 抽帧，然后用 `scripts.qa_gate` 生成 `qa_report.json`。第一轮 smoke test 的主要价值是暴露失败模式：

```text
Archive_generated_test/piwm_1321b89375  long_dwell_with_price_check  QA fail: sampled frames do not confirm repeated price checking
Archive_generated_test/piwm_717d50917f  repeated_product_handling    QA fail: physical inconsistency around glass counter access
Archive_generated_test/piwm_85415216b6  comparing_two_products       QA fail: sampled frames do not confirm explicit comparison
```

随后修正 prompt，明确 demo sample 与 glass display 的物理关系，并补跑 pilot。当前正式 pilot 结果：

```text
Archive_generated_pilot/piwm_b2f76367fe  checking_phone_likely_research  QA pass
Archive_generated_pilot/piwm_f35ac530da  checking_phone_likely_research  QA pass
Archive_generated_pilot/piwm_717d50917f  repeated_product_handling        QA fail: sampled frames do not confirm cue
```

当前入库结果：

```text
data/piwm_dataset_pilot/
  main_schema.jsonl                 2 rows
  state_inference.jsonl             2 rows
  state_inference_with_cue.jsonl    2 rows
  transition_modeling.jsonl         5 rows
  policy_preference.jsonl           2 rows

data/piwm_dataset/
  main_schema.jsonl                 2 rows
  state_inference.jsonl             2 rows
  state_inference_with_cue.jsonl    2 rows
  transition_modeling.jsonl         5 rows
  policy_preference.jsonl           2 rows
```

可视审阅材料：

```text
Archive_generated_pilot/qa_pass_contact_sheet.jpg
Archive_generated_pilot/_one_complete_qa_pass_data_preview.json
```

初步结论：

- 10 秒 current-state video 是可行的；
- `multi_image_single_turn` 方向仍然成立；
- 固定 3 帧对动作足够显性的 cue 可用，例如 checking phone research；
- 固定 3 帧对细微时间性 cue 不够稳定，例如 repeated price checking；
- Phase 4 不应把 `K=3` 写死为唯一策略，应支持 cue-aware sampling：
  - 默认 `K=3`：2s / 5s / 8s；
  - subtle temporal cue 使用 `K=4` 或 `K=5`；
  - prompt 需要强化“可见价格标签、手指指向、头部/视线来回切换”等可抽帧证据。

因此，当前结构保留：

```text
single current-state video under selected viewpoint -> sampled frames -> single-turn training row
```

但 Phase 4 的 `frame_manifest.json` 必须记录 `sampled_frames` 的 timestamp、role 和 sampling strategy，QA gate 必须检查 sampled frames 是否支撑 target cue。

当前 QA gate 行为：

```text
scripts/qa_gate.py
  -> checks prompt.json / video.mp4 / frame_manifest.json / sampled frames
  -> checks prompt label leakage
  -> combines qa_manual_review.json for cue visibility and physical consistency
  -> writes qa_report.json
```

`build_dataset` 默认只读取：

```text
qa_report.overall_pass == true
```

如需生成调试预览，可临时使用：

```bash
python3 -m piwm_data.build_dataset --allow-unreviewed ...
```

但 `--allow-unreviewed` 产物不得作为正式训练数据。
