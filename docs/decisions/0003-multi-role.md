# 0003 · 多岗位

日期：2026-11-19 · 状态：已采纳

## 背景

M0 只有 Agent Infra 一个岗位：类别、公司热度、排列顺序都直接挂在 `skill` 上，导出也是一套顶层文件。要加入 AI 应用、后端、SRE / 平台、前端、数据工程五个岗位，同时让通用能力点（`dist`、`k8s`、`cache` 等）在各岗位共用一份内容、学习进度跨岗位保留。下面的契约是数据调研、后端、前端和合并各环节共同遵守的约定。

### 数据库实现（migration 0002）

- 新表 `role`（6 行写死）、`role_skill`（岗位内的类别、公司、顺序）、`role_company`（岗位的公司顺序）；`cluster` 加 `role_family`；`job_posting` 唯一键改为 `(source_id, title, role_family)`（重建表，迁移时关闭外键、提交前跑 `foreign_key_check`，失败整体回滚）。
- `skill.cluster`、`skill.reference_companies`、`skill.sort` 保留但不再写入或读取，岗位相关的值都在 `role_skill`。
- agent-infra 仍由 `seed/import_reference.py` 导入；`seed/import_roles.py` 导入 `seed/roles/*.json`，先校验全部文件、有任何错误就整体拒绝、不写库。文件按岗位表顺序处理（决定资源「先到先得」的顺序）。

### import_roles 报错规则

未知 role；role 是 agent-infra 或两个文件同一 role；完整定义的 slug 撞已有 skill（上次由 import_roles 写入的除外，保证可重复导入）；两个文件都完整定义同一 slug；复用写了 slug/cluster/companies 以外的字段；完整定义缺 name/description/concepts/practice；引用不存在的 skill（复用、prereqs、path 里不属于本岗位的）、company（posting 或 skill.companies 不在本岗位 companies 里）、cluster；cluster 不带岗位前缀或属于别的岗位；同岗位颜色重复；公司没有 posting；posting 没有 url；新先修边两端都是 agent-infra 的 skill；全局先修成环。资源同标题时保留先到的 url，打印警告；先到的 url 为空而新记录有 url 时直接补上，不警告。

---

## 契约原文


实施前的现状：只有 agent-infra 一个岗位，数据来自 seed/reference.html（seed/import_reference.py 导入），backend/app/export.py 导出到 frontend/public/data/，前端 React + D3 力导向图。

## 岗位（role_family）

| slug | name_zh | 根节点标签 |
| --- | --- | --- |
| agent-infra | Agent Infra 工程师 | Agent Infra 工程师 |
| ai-app | AI 应用工程师 | AI 应用工程师 |
| backend | 后端工程师 | 后端工程师 |
| sre-platform | SRE / 平台工程师 | SRE / 平台工程师 |
| frontend | 前端工程师 | 前端工程师 |
| data-eng | 数据工程师 | 数据工程师 |

顺序即切换器里的顺序。

## 核心模型

- **能力点词表全局共享**：同一个概念在所有岗位用同一个 slug（如 `dist` 分布式系统、`k8s`、`os`、`net`、`lang`）。能力点的名称、描述、核心概念、练习、资料只定义一次。
- **按岗位区分的**：类别（cluster，每个岗位自己 5–8 个）、能力点在该岗位所属的类别、提到它的公司（热度）、在该岗位的排列顺序、建议学习顺序（roadmap）。
- **先修关系全局**：`[from, to]` 表示 from 是 to 的先修。某岗位的图只画两端都属于该岗位的边。
- **公司全局**：code 全局唯一。已有代码沿用（O=OpenAI, AN=Anthropic, CU=Cursor, CG=Cognition, A=阿里, B=百度, X=小红书, K=月之暗面, T=腾讯, JP=日本企业）。新公司 code = 英文短名大写、无空格（如 STRIPE、MERCARI、BYTEDANCE、GOOGLE）。
- **学习进度按能力点 slug 全局记**（localStorage key 仍是 `agent-infra-progress`），切换岗位后共享能力点的进度保留。

## 规则（必须遵守）

1. **现有 50 个 slug 永不改名，永远优先。** 复用前先读已有能力点的描述：内容对本岗位也成立才复用，否则另起 slug（例如前端的「状态管理」不能用 `state`，它是 Agent 会话状态模型；改用 `fe-state`）。
2. **跨岗位通用能力点用下面的预定 slug**（任何岗位需要这个概念都用它；最终只保留一份岗位中立的完整内容，其他岗位只引用）：
   `sql-db` 关系数据库与 SQL · `nosql` NoSQL 与 KV 存储 · `cache` 缓存 · `mq` 消息队列与事件流 · `api-design` API 设计（REST/gRPC/GraphQL） · `auth` 认证与授权（OAuth/OIDC/会话） · `testing` 自动化测试 · `ci-cd` CI/CD · `git-collab` Git 与代码协作 · `docker` 容器与镜像 · `cloud` 公有云基础（AWS/GCP） · `iac` 基础设施即代码 · `observability` 监控、日志与告警 · `perf` 性能分析与优化 · `security-basics` 应用安全基础（OWASP） · `sys-design` 系统设计 · `data-modeling` 数据建模 · `web-basics` Web 与浏览器基础 · `ts` TypeScript · `python` Python 工程 · `incident` 故障响应与复盘 · `prompt-eng` Prompt 工程 · `embedding-search` Embedding 与向量检索。
   已有的通用 slug 继续用：`os` `net` `dist` `k8s` `lang` `llm` `rag` `evals` `trace`（Agent 语境，复用前读描述）。
3. **粒度**：一个能力点 = 1–3 周能学完的主题。具体工具、库名放进 concepts，不单独成点（Redis 放进 `cache` 的 concepts）。
4. **先修**：禁止添加两端都在现有 50 个 slug 里的边（会改动 agent-infra 的图）。其他边全局共享。
5. **岗位的公司** = 该岗位种子 `companies` 数组（顺序即 chip 顺序），每个公司至少 1 条 posting；每个 skill 的 `companies` 必须是它的子集。
6. **JD 唯一性按岗位**：同一公司同名职位可以出现在不同岗位，互不覆盖。
7. **资源**：`resource.title` 全局唯一，同标题先到先得（后来的 url 不覆盖，导入时打印警告；先到的 url 为空时用后来的补上）。种子里不写 type，导入时沿用 `resource_type(title)` 推断。
8. **role 表 6 行**（slug、name_zh、root_label、sort）由 migration 按上方岗位表写死；种子里出现未知 role slug 直接报错。

## A. 种子格式：seed/roles/<role>.json

```json
{
  "role": {"slug": "backend", "name_zh": "后端工程师"},
  "clusters": [{"slug": "backend-data", "name": "数据存储", "color": "#2A8C82"}],
  "companies": [{"code": "STRIPE", "name": "Stripe"}],
  "postings": [{"company": "STRIPE", "title": "Backend Engineer, Payments", "url": "https://..."}],
  "skills": [
    {"slug": "pg-internals", "name": "关系数据库内核", "cluster": "backend-data",
     "description": "…", "concepts": ["…", "…", "…", "…"], "practice": "…",
     "resources": [{"title": "PostgreSQL 官方文档", "url": "https://www.postgresql.org/docs/"}],
     "companies": ["STRIPE", "MERCARI"]},
    {"slug": "dist", "cluster": "backend-dist", "companies": ["STRIPE"]}
  ],
  "prereqs": [["dist", "pg-internals"]],
  "path": [{"title": "基础", "skills": ["lang", "net"]}]
}
```

- cluster slug 必须带岗位前缀（`backend-data`），避免跨岗位冲突；颜色从这组里选，同一岗位内不重复：#5B6B7A #3D5A99 #2A8C82 #B23A48 #C08A1E #6E8A2A #7A4F8A #2F7FB8。
- 复用已有能力点：只写 `slug`、`cluster`、`companies` 三个字段（第二个 skill 示例），不重写内容。新能力点写全部字段。
- skill 的 slug：小写、短横线，英文，语义清楚（如 `pg-internals`、`react-rendering`）。
- `postings` 每条必须是真实打开过的公开 JD 页面，url 必填；不要编造。
- `companies` 里的代码必须在 `companies` 或已有代码里。
- `path` 4–7 个阶段，覆盖该岗位所有能力点中最重要的 20–35 个。
- `resources` 每个新能力点 1–3 条，优先官方文档、经典书、知名论文；url 能找到就填，找不到可以省略 url 字段。

## B. 导出格式：frontend/public/data/

```
data/roles.json                       → [{slug, name, root_label, counts:{companies, postings, skills, edges}}]  按上表顺序，只列有数据的岗位
data/meta.json                        → {generated_at}
data/skills.json                      → [{slug,name,description,concepts:[],practice,resources:[{title,url|null,type}],prereqs:[slug],unlocks:[slug]}]  全局词表，只含 active
data/roles/<role>/clusters.json       → [{slug,name,color}]  按 sort
data/roles/<role>/companies.json      → [{code,name}]
data/roles/<role>/sources.json        → [{code,name,jobs:[{title,url|null}]}]
data/roles/<role>/skills.json         → [{slug,cluster,companies:[code],heat:int}]  按该岗位的 sort；heat = companies 长度
data/roles/<role>/edges.json          → [{from,to,type}]  两端都在该岗位里的边
data/roles/<role>/roadmap.json        → {phases:[{title,skills:[slug]}]}
```

全局 `skills.json` 里的 prereqs/unlocks 是全局的；前端在某岗位里显示先修和可进入时，只列属于该岗位的。旧的 data/clusters.json 等顶层文件不再生成。
