# PIWM 售货员中文标注包 v2

本目录用于把 30 条 balanced target-frontcam 5-act test 样本导入 Excel 或飞书多维表格，让 3 位中国售货员独立标注。

## 当前口径

- 5 个主动作：问候 / 询问需求 / 介绍信息 / 推荐商品 / 继续观察等待。
- 英文映射：问候=Greet，询问需求=Elicit，介绍信息=Inform，推荐商品=Recommend，继续观察等待=Hold。
- 售货员只看图片和中文场景，不看系统 stage、系统 best act 或候选动作标签。

## 文件

- `annotation_template_single_annotator.csv`：单个售货员填写模板，30 行。
- `annotation_template_three_annotators.xlsx`：三张独立填写页，分别为 `售货员A`、`售货员B`、`售货员C`。
- `annotation_template_three_annotators_with_images.xlsx`：同样的三人填写模板，但已把 90 张图片直接嵌入表格，适合预览和人工分发表。
- `frames/`：90 张抽帧图，命名为 `{sample_id}_{0/1/2}.jpg`。
- `theory_labels_holdout.csv`：系统理论标签，不给售货员看，只用于后续一致性和偏好分析。
- `theory_labels_holdout.jsonl`：同上，JSONL 版本，便于脚本读取。

## 统计口径

- target 包含 5 个动作：问候 / 询问需求 / 介绍信息 / 推荐商品 / 继续观察等待。
- 和 general probe 对比专家一致性时，报告两套 κ：`target_5act_all` 使用全部 30 条；`target_4act_without_greet` 排除 system best act 为 `Greet` 的 6 条，只和 general probe 的 4-act 口径直接对齐。
- `theory_labels_holdout.csv/jsonl` 只用于分析，不导入给售货员。

## 重新生成

如果只需要 CSV、帧图和隐藏标签：

```bash
python3 scripts/build_salesperson_annotation_pack_v2.py
```

如果要同时重建 Excel 工作簿，确保 Python 环境有 `openpyxl`；本机有 `uv` 时可直接运行：

```bash
uv run --with openpyxl python scripts/build_salesperson_annotation_pack_v2.py
```

## 飞书导入建议

1. 优先导入 `annotation_template_three_annotators.xlsx`。
2. 给三位售货员分别开放 `售货员A`、`售货员B`、`售货员C` 对应表或视图。
3. 三位售货员不要互相看对方结果，避免相互影响。
4. `第1张图`、`第2张图`、`第3张图` 可以保留路径，也可以在飞书中改成附件字段后上传 `frames/` 目录里的图片。

## 填写规则

- `现在是否应该主动介入`：填写“应该介入 / 不应该介入 / 不确定”。
- `你认为最合适的主动作`：从“问候 / 询问需求 / 介绍信息 / 推荐商品 / 继续观察等待”中选择一个。
- `这句话的主要目的`：填写这句话在沟通中的目的，例如“破冰建立关系”或“了解顾客需求”，不要写系统英文标签。
- 5 个适合度分数都必填，范围 1-5。
- 如果某个动作适合度 ≤ 2，请填写对应“不适合原因”。
- `为什么不选择第二合适做法`：第二合适做法由 5 个动作分数自动推导，售货员只需要写为什么最终没选它。
- 话术拆分最多填 3 段。例如：
  - 片段1：您好，看您在看饮料；片段1对应目的：问候
  - 片段2：是想看口味还是价格？片段2对应目的：询问需求

## 后处理

售货员完成后，从飞书导出 CSV，然后运行：

```bash
python3 scripts/convert_salesperson_annotation_export.py \
  --input exported_salesperson_a.csv \
  --holdout data/official/annotation_pack_v2/theory_labels_holdout.jsonl \
  --output data/official/annotation_pack_v2/converted_salesperson_a.jsonl
```
