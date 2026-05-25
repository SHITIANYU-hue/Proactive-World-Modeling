# PIWM Data Index

## Data Layers

| Layer | Count | Range |
|---|---:|---|
| seed | 200 | piwm_001 – piwm_200 |
| manifest | 200 | piwm_001 – piwm_200 |
| labeled | 200 | piwm_001 – piwm_200 |
| prompts | 200 | piwm_001 – piwm_200 |
| video | 149 | piwm_001–138, piwm_149–159 |

## 文档导航

- [design.md](design.md)：任务设定、AIDA 状态模型、5-class 动作空间、per-stage 候选约束、Response Realization 层设计。
- [schema.md](schema.md)：manifest / labeled / prompt 的字段契约与 preference score 公式。
- [training.md](training.md)：两阶段 SFT 设计与 ms-swift 数据格式。
- [usage.md](usage.md)：脚本运行方式与常用命令。

---

## 分布统计

### AIDA 阶段

| Stage | Count |
|---|---:|
| attention | 48 |
| interest | 65 |
| desire | 55 |
| action | 32 |

### Best Action

| Best Action | Count |
|---|---:|
| hold | 48 |
| recommend | 47 |
| elicit | 38 |
| greet | 35 |
| inform | 31 |

### Stage × Best Action

|  | hold | greet | elicit | inform | recommend |
|---|---:|---:|---:|---:|---:|
| attention | 16 | 16 | 16 | 0 | 0 |
| interest | 15 | 0 | 22 | 18 | 10 |
| desire | 11 | 0 | 0 | 13 | 31 |
| action | 7 | 19 | 0 | 0 | 6 |

---

## Archive

`piwm_1001 – piwm_1118`（118 条）：队友独立生成的扩展批次，schema 与主数据集不同，全部 video-pending。仅作归档，不参与当前训练流程。数据位于 `data/labeled/piwm_1001*.json` – `piwm_1118*.json`。
