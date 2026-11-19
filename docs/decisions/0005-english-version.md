# 0005 英文版

日期：2026-11-19 · 状态：已采纳

## 背景

站点内容全是中文（能力点、类别、学习路线、资料标题、公司名）。要加英文版，同时不改动现有中文数据和导入流程。

## 决定

- 翻译放在 `seed/i18n/en.json`，不进 SQLite。导出时把它叠加到中文数据上：`data/` 保持原样（逐字节不变），另写一份布局完全相同的 `data/en/`，`en/meta.json` 的 `generated_at` 与中文一致。
- 翻译的字段：岗位 name / root_label；能力点 name / description / concepts / practice；含中日文字符的资料标题；各岗位的类别名、公司名、学习路线阶段标题。职位标题是真实 JD 标题，不翻译；slug、颜色、url、热度、先修关系不变。
- 文件格式：`roles`、`clusters`、`companies`、`skills` 按 slug / code 为键；`phases` 按岗位给出与阶段一一对应的标题数组；`resources` 以中文原标题为键。
- 导出时严格校验，有问题就列出全部问题并失败，不写任何文件：每个导出的岗位、类别、公司、能力点都必须有条目且没有多余的键；concepts 和阶段数量必须与中文一致（按下标对应）；`resources` 的键必须恰好是含中日文字符（含《》「」等全角标点）的资料标题，已是英文的标题不列出、保持原样；翻译后资料标题全局唯一（含未翻译的英文标题），同一能力点的 concepts、同一岗位的阶段标题不重复；能力点英文名不超过 28 个字符（图上标签宽度）。
- 命令行：`python -m app.export --i18n FILE`，默认 `seed/i18n/en.json`；`scripts/build_data.sh` 显式传入。函数调用不传 i18n 时只导出中文，并删除旧的 `en/`，避免两边不一致。
- 前端 fixtures 是手写的中文样例，其英文版由 `scripts/build_fixture_en.py` 按 `scripts/fixtures/en.json` 生成，复用同一套校验和替换逻辑。
