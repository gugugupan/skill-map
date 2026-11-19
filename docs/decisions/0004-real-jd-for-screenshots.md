# 0004 用真实职位替换参考实现中的截图 JD

日期：2026-11-19

## 背景

参考实现（`seed/reference.html`）的 SOURCES 里有 4 份 JD 只来自截图，没有链接：OpenAI、阿里、百度、小红书。站点要求每份 JD 都能追溯到真实的职位描述。

## 决定

- `seed/reference.html` 保持原样，作为原始存档。
- 新增 `seed/reference_overrides.json`：按 (公司代码, 原标题) 替换标题和链接。`seed/import_reference.py` 在导入 SOURCES 前应用，找不到原标题就报错。
- 每份替换的来源、选择理由和逐个能力点的原文核对见 `seed/reference_overrides.md`。
- 能力点 × 公司的人工映射（`reference_companies`）暂不随替换调整：百度、小红书的新 JD 与截图基本一致；OpenAI、阿里换成了更窄的职位，映射里有不少能力点在新 JD 正文中找不到，是否调整由用户决定。

已按真实 JD 调整 O/A/B/X 映射，见 `seed/reference_overrides.md`。
