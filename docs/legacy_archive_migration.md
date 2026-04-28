# 旧 Archive 迁移说明

当前新数据管线严格读取 `data_pipeline_spec.md` v1 结构：

```text
session/
├── frames/
└── prompt.json
```

当前仓库里的旧 `Archive` 是：

```text
session/
├── metadata.json
└── anchor/
    ├── anchor_log.json
    ├── prompt.txt
    └── frames/
```

这两种结构不兼容。为了不污染严格 loader，迁移被做成单独工具：

```bash
python3 -m piwm_data.migrate_legacy_archive \
  --legacy-root Archive \
  --write-template data/legacy_mapping_template.json
```

这会生成一个 mapping 模板。你需要手动填写每个 session 的规范枚举：

- `product_category`
- `persona_type`
- `aida_stage`
- `target_cue`

工具不会根据旧的 `S03_HOVER` / `S08_PICKUP` 等状态自动猜这些值，因为旧状态集和新规范枚举不是一一对应关系。

填写完成后运行：

```bash
python3 -m piwm_data.migrate_legacy_archive \
  --legacy-root Archive \
  --output-root Archive_v1 \
  --mapping data/legacy_mapping_template.json \
  --overwrite
```

然后用新数据管线读取迁移后的 `Archive_v1`：

```bash
python3 -m piwm_data.build_dataset \
  --archive-root Archive_v1 \
  --output-dir data/piwm_dataset \
  --frame-sample 3
```

迁移输出会包含：

- `frames/`：从旧 `anchor/frames/` 复制并重命名为 `000.jpg, 001.jpg, ...`
- `prompt.json`：规范输入文件
- `legacy_source.json`：保留旧 metadata / anchor_log，便于追溯

