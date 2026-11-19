# 0002 · 参考实现导入：JD 数量与资源类型

日期：2026-11-19 · 状态：已采纳

## JD 数量是 23，不是 25

设计文档（以及 0001 补丁表）说 M0 有 25 份 JD。`seed/reference.html` 的 `SOURCES` 实际只有 23 个岗位（10 家公司：O 3、AN 4、CU 3、CG 2、A 1、B 1、X 1、K 2、T 3、JP 3）。以数据为准，导入和测试都按 23。

## 资源类型粗判（`seed/import_reference.py` 的 `resource_type`）

参考实现的资料只有名称，没有链接和类型。按名称关键词判断，先命中先用：

| 顺序 | 关键词 | type |
| --- | --- | --- |
| 1 | 论文 | `paper` |
| 2 | 课程 | `course` |
| 3 | 源码、代码、GitHub | `repo` |
| 4 | 文档、规范、手册、RFC、书名号《 | `doc` |
| 5 | 其他 | `blog` |

- 书名号《》是书，schema 没有 `book`，归到 `doc`。
- `RFC` 是规范，归到 `doc`；`代码` 用来覆盖「E2B 开源代码」。
- 已知的粗判误差：基准（SWE-bench、OSWorld、BEIR 等）、英文书名不带书名号的（The Kubebuilder Book、Chaos Engineering）、SRE Book 的章节都落到 `blog`。M0 只用于展示，等 M1 补链接时再修正。
- 同名资料（如 Anthropic「Building Effective Agents」）只存一条 `resource`，多个能力点通过 `skill_resource` 引用。
