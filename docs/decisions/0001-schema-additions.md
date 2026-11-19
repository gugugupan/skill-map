# 0001 · 数据模型补丁（M0 建表）

日期：2026-11-19 · 状态：已批准

设计文档「数据模型」一节只列了关键字段。M0 导入参考实现（`seed/reference.html`）时需要以下补充，均已由用户批准。

## 补丁

| 表 | 改动 | 原因 |
| --- | --- | --- |
| `cluster` | 新增表：`slug` PK、`name_zh`、`color`、`sort` | 8 个能力类别需要中文名、图谱配色和固定顺序；`skill.cluster` 外键指向它 |
| `skill` | `merged_into`（FK → `skill`，可空） | 文档要求合并时旧能力点「标为 merged 并指向新的」，需要一个字段存指向 |
| `skill` | `concepts`（JSON TEXT） | 参考实现每个能力点有「核心概念」列表 |
| `skill` | `practice`（TEXT） | 参考实现每个能力点有「练习」 |
| `skill` | `reference_companies`（JSON TEXT） | 参考实现里人工判断的「提到它的公司」，只作对照，不参与热度计算 |
| `skill` | `sort`（INT） | 保持导入顺序，前端按此排列 |
| `skill` | `aliases` 用 JSON TEXT 存数组 | SQLite 没有数组类型 |
| `job_posting` | `section_responsibilities` / `section_requirements` / `section_bonus`（TEXT） | 预处理后按「职责 / 要求 / 加分项」切段，抽取时据此判断 strength |
| `job_posting` | `first_seen_at` | 与每次抓取都会更新的 `fetched_at` 区分，用于趋势统计 |
| `job_posting` | `url`、`raw_text`、`content_hash` 可空 | M0 的 23 份 JD 只有标题和链接，正文待 M1 抓取；手动粘贴的 JD 可能没有链接 |
| `job_posting` | `url` 不加 UNIQUE；加 `UNIQUE(source_id, title)` | 同一链接可能对应多个岗位（如列表页），以「来源 + 标题」作为导入幂等键 |
| `source` | `code`（TEXT UNIQUE） | 参考实现用公司代码（如 `O`、`AN`）引用来源，导入时按它关联 |
| `source` | `url` 可空 | 手动来源没有统一链接 |
| `roadmap_step` | `roadmap_id`（FK）、`phase`（INT）、`phase_title`（TEXT）、`step_order`、`skill_id` | 文档里 `roadmap` / `roadmap_step` 合写在一行；拆开后 step 需要指向所属路线图；`PATH` 的 7 个阶段有标题；`order` 是 SQL 保留字，改名 `step_order` |
| `resource` | `url` 可空，`title` UNIQUE | M0 的资源只有标题，以标题作为导入幂等键 |
| `skill_edge` | `UNIQUE(from_skill, to_skill, type)` | 防止重复导入同一条关系 |

## CHECK 约束

只加在取值稳定的枚举上：`source.type`、`skill.status`、`posting_skill.strength`、`skill_edge.type`、`resource.type`。

`role_family` 不加 CHECK：之后会加 `ai-app`、`ml-infra-*` 等新值，而 SQLite 修改 CHECK 需要重建表。取值由应用代码校验。

## 其他实现细节

- `posting_skill` 主键为 `(posting_id, skill_id, extractor_version)`，让不同抽取版本的结果可以并存，便于升级前后对比。
- `job_posting.status` 默认 `open`；`resource.type` 可空（M0 资源类型未知）。
- 迁移为 `backend/migrations/NNNN_*.sql`，由 `app.db` 按编号顺序执行，`schema_migrations` 表记录已执行版本；每个文件在一个事务里执行。
