# 0004 用真实职位替换参考实现中的截图 JD

日期：2026-11-19

## 背景

参考实现（`seed/reference.html`）的 SOURCES 里有 4 份 JD 只来自截图，没有链接：OpenAI、阿里、百度、小红书。站点要求每份 JD 都能追溯到真实的职位描述。

## 决定

- `seed/reference.html` 保持原样，作为原始存档。
- 新增 `seed/reference_overrides.json`：按 (公司代码, 原标题) 替换标题和链接。`seed/import_reference.py` 在导入 SOURCES 前应用，找不到原标题就报错。
- 每份替换的来源、选择理由和逐个能力点的原文核对见 `seed/reference_overrides.md`。
- 能力点 × 公司的人工映射（`reference_companies`）以真实 JD 为准：用户决定后，按 O、A 全部真实 JD 正文逐个重新核对（可增可删），B、X 去掉无原文证据的映射；调整写在 `reference_overrides.json` 的 `skill_companies` 一节，逐条证据见 `seed/reference_overrides.md`。
