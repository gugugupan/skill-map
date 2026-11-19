# JD 驱动的能力地图与学习路线平台 · 设计文档

> 来源：[Claude Docs 设计文档](https://claude.ai/artifact/1GDrEsFwgWdXE4TuvNMo84)（2026-11-19 · Pan）

## 架构变更（M0 起生效，覆盖下文与之冲突的内容）

M0 起改为 **GitHub Pages 静态站**，不再使用 FastAPI / 本地平台：

- 管线脚本（Python）把数据存进 SQLite，`export` 步骤导出静态 JSON 到 `frontend/public/data/`。
- React 前端构建后由 GitHub Actions 发布到 GitHub Pages：<https://gugugupan.github.io/skill-map/>。
- 学习进度存在浏览器 `localStorage`。
- 没有常驻后端。下文中的「API」「FastAPI」「本地平台」应理解为「导出的静态 JSON」与「管线脚本」。

## 背景与目标

本项目要做一个本地平台：持续采集 AI 工程相关的 JD，用 LLM 把同类岗位归纳成一份稳定的能力点词表，为每个能力点挂上学习资源，最后生成可跟踪进度的学习路线。

参考实现是一个手工完成的 [Agent Infra 知识图谱](https://claude.ai/artifact/4JMjymCo3o3HNGSYQhrVei)：10 家公司、23 份 JD，归纳出 50 个能力点和 52 条先修关系。它证明了这种形式有用，但每次更新都要人工搜索、改代码、重新发布。现有公开路线图（如 roadmap.sh）基于作者经验，偏应用层，也没有公司维度。

| 目标 | 成功标准（初始值，可调整） |
| --- | --- |
| 自动采集 | 配置好的来源每周自动拉取，新 JD 去重后入库 |
| 稳定归纳 | 同一份 JD 重跑抽取，映射到的能力点基本一致 |
| 可追溯 | 每个能力点都能回溯到 JD 原文中的证据片段 |
| 资源关联 | 每个高热度能力点至少有 3 条经过筛选的学习资源 |
| 路线图 | 按岗位方向生成分阶段计划，进度可跟踪 |

## 非目标与范围

v1 只服务一个用户、在本地运行，聚焦「理解市场要求什么能力、该怎么学」。

- 不做求职投递、简历匹配或岗位推荐。
- 不做通用课程平台：资源只做索引和摘要，不搬运全文。
- 不抓取需要登录的站点（如 LinkedIn），遵守各站点的 robots.txt 和使用条款。
- v1 不做多用户和权限；数据结构保留扩展空间即可。
- 首个岗位方向是 Agent Infra，其他方向（AI 应用工程师、训练与推理 Infra）在框架跑通后再加。

## 整体架构与数据流

系统是一条单向管线：来源进来，经过五步处理成为带热度的能力点，再派生出资源和路线图。

> [图：系统架构 · 9 个组件] LLM 只做分类、抽取和打分，其余都是确定性代码，中间结果写入 SQLite：数据来源（招聘系统 API / URL 抓取 / 手动粘贴与截图）→ 采集与去重 → 预处理 → 岗位分类（LLM）→ 抽取与归一化（LLM，新能力点进出审核队列）→ 聚合 → 资源匹配（搜索 + LLM 打分）→ 路线图生成（拓扑排序 + LLM）→ Web 界面（图谱 · 路线图 · 审核）。

唯一的人工环节是审核队列：抽取时发现的新能力点要人工确认后才进入词表。

## 数据模型

核心是 `posting_skill` 这张关联表：一份 JD 映射到哪些能力点、证据是哪句原文、要求强度如何。热度、趋势、路线图都从它算出来。

| 表 | 关键字段 | 说明 |
| --- | --- | --- |
| `source` | id, name, type, url, company, region | 来源。type 取值：`ats_api` / `scrape` / `manual` |
| `job_posting` | id, source_id, company, title, location, url, posted_at, fetched_at, raw_text, content_hash, lang, role_family, status | 原始 JD。`content_hash` 用于去重，`status` 标记是否仍在招 |
| `skill` | id, slug, name_zh, name_en, cluster, description, aliases[], status | 能力点词表。status 取值：`active` / `proposed` / `merged` |
| `posting_skill` | posting_id, skill_id, evidence_span, strength, confidence, extractor_version | JD 与能力点的映射。strength 取值：`required` / `preferred` / `bonus` |
| `skill_edge` | from_skill, to_skill, type | 能力点之间的关系。type 取值：`prereq` / `related` |
| `resource` | id, url, title, type, lang, summary, quality_score, fetched_at, added_by | 学习资源。type 取值：`doc` / `paper` / `blog` / `course` / `repo` |
| `skill_resource` | skill_id, resource_id, rank, reason | 能力点与资源的关联及排序理由 |
| `roadmap` / `roadmap_step` | role_family, params, phase, order, skill_id | 生成的路线图及其阶段 |
| `progress` | skill_id, status, notes, updated_at | 个人学习进度 |

设计约定：

- `role_family` 是枚举，初始值为 `agent-infra`，后续加 `ai-app`、`ml-infra-training`、`ml-infra-inference`。
- 能力点词表必须版本化。合并两个能力点时，旧的标为 `merged` 并指向新的，不物理删除，历史映射保持可查。
- 每条映射记录 `extractor_version`（模型 + prompt 版本），方便升级后选择性重跑。

## 管线设计

原则：LLM 只负责抽取和判别，结构、排序和统计都放在确定性代码里。这样结果可复现，成本可控，也方便测试。

1. **采集**
   - 优先使用招聘系统的公开接口：Greenhouse Job Board API、Lever Postings API、Ashby Job Board API。很多海外 AI 公司用这几家，接口稳定，无需爬页面。
   - 中文和日文站点结构各异，v1 支持两种方式：输入 URL 抓取单页，或直接粘贴文本、截图（截图用多模态模型转文本）。
   - 去重：对规范化后的正文计算 `content_hash`；同一岗位出现在多个渠道时，按（公司、标题、地点）合并。
2. **预处理**
   - HTML 转纯文本，检测语言（中、日、英）。
   - 切分为「职责」「要求」「加分项」三段，后续用来判断 `strength`。
3. **岗位分类**：LLM 把 JD 归到某个 `role_family`，不相关的岗位标记后跳过。
4. **能力抽取与归一化（核心难点）**
   - 第一步，LLM 用结构化输出从 JD 中抽取原子能力短语，附带原文证据和强度。
   - 第二步，对每个短语用 embedding 在词表中召回 top-k 候选，再让 LLM 判断是否匹配其中之一。
   - 无匹配的短语作为 `proposed` 能力点进入审核队列，由人工批准、合并或丢弃。
   - 这样做的好处：「沙箱隔离」「安全执行环境」「sandboxing」会落到同一个能力点上，热度统计才有意义。
5. **聚合**
   - 热度 = 提到该能力点的 JD 数 ÷ 该方向 JD 总数。
   - 支持按公司、地区、时间窗口切片；趋势 = 近 90 天热度与之前对比。
6. **资源匹配**
   - 为每个能力点生成搜索词，调用搜索 API，抓取候选页面。
   - LLM 按相关性、深度、时效打分并写一句推荐理由。
   - 优先官方文档、论文和原作者文章；人工收藏的资源排在最前。
   - 定期检查链接是否失效。
7. **路线图生成**
   - 阶段顺序由 `skill_edge` 拓扑排序决定，再按热度和用户已掌握情况调整。
   - LLM 只负责写每个阶段的说明和练习题，不决定顺序，保证同样的输入得到同样的路线。

## 前端视图

六个视图，其中能力地图沿用参考实现的交互方式。

| 视图 | 内容 | 关键交互 |
| --- | --- | --- |
| JD 库 | 所有 JD，带公司、地区、方向、日期 | 筛选；查看原文并高亮被抽取的证据片段 |
| 能力地图 | 力导向图，节点大小 = 热度，虚线 = 先修 | 按公司、地区、时间窗口筛选；点击进入详情 |
| 能力详情 | 描述、证据片段、公司分布、趋势、资源 | 标记学习状态；跳转到原 JD |
| 资源库 | 全部资源，按能力点分组 | 收藏、置顶、标记失效 |
| 路线图 | 分阶段学习计划 | 选择方向；勾选完成；重新生成 |
| 审核队列 | `proposed` 能力点及其来源短语 | 批准、合并到已有能力点、丢弃 |

## 技术选型建议

建议从最轻的单机方案起步，数据量上来后再换存储。以下均为建议，可按个人偏好替换。

| 层 | 建议 | 理由 |
| --- | --- | --- |
| 后端语言 | Python + FastAPI | 抓取、解析、LLM 生态最完整 |
| 存储 | SQLite + sqlite-vec；之后可迁到 Postgres + pgvector | 本地零运维，向量检索够用 |
| 调度 | cron 或 APScheduler | 每周采集、每日检查链接即可 |
| 抓取 | httpx；需要渲染的页面用 Playwright | 覆盖静态和动态页面 |
| LLM | Claude API，结构化输出 | 抽取与判别需要稳定的 JSON |
| Embedding | 支持中日英的多语言模型（如 bge-m3 本地运行，或托管服务） | 跨语言归一化的关键 |
| 搜索 | 任一搜索 API（如 Brave、Tavily、Exa） | 资源匹配用 |
| 前端 | React + Vite + D3 | 图谱交互可复用参考实现 |
| 测试 | pytest + 一份人工标注的金标准集 | 衡量抽取和归一化质量 |

## 种子数据与参考实现

[参考实现](https://claude.ai/artifact/4JMjymCo3o3HNGSYQhrVei)的数据可以直接作为初始词表和来源，省去冷启动。Claude Code 无法打开 claude.ai 链接，所以需要先把页面的 HTML 下载下来，放进仓库的 `seed/reference.html`。

页面脚本中有四个可直接解析的数组：

| 数组 | 内容 | 导入到 |
| --- | --- | --- |
| `N` | 50 个能力点：id、所属类别、名称、描述、核心概念、练习、资料、提到它的公司 | `skill`、`resource`、`skill_resource` |
| `PRE` | 52 条先修关系 | `skill_edge` |
| `SOURCES` | 10 家公司、23 份 JD 的标题和链接 | `source`、`job_posting`（待抓取正文） |
| `PATH` | 7 个阶段的建议学习顺序 | 作为路线图生成的校验基线 |

8 个能力类别：工程基础、Agent 核心机制、运行时、沙箱与安全、上下文与工具、评测与可观测、平台与控制面、前沿与工作方式。

注意：参考实现中「提到它的公司」是人工判断的，导入后应以管线重新抽取的结果为准，人工数据只作对照。

## 里程碑

M2 是整个项目的关键：归一化不稳定，后面的热度和路线图都没有意义。

> [图：里程碑 · 5 个阶段，2 个关口] M0 种子与骨架（建表、导入参考实现、图谱读数据）→ 关口：图谱能从数据库完整显示 → M1 采集 → M2 抽取与归一化（关键）→ 关口：金标准集上映射结果稳定 → M3 聚合与视图 → M4 资源与路线图。

M0 完成后就有一个可用的本地版参考实现；M1 和 M2 之后数据才开始自动更新。

## 风险与开放问题

最大的风险是能力点词表失控：重复、粒度不一、随模型漂移。审核队列和版本化就是为它设计的。

| 风险 | 应对 |
| --- | --- |
| 能力点重复或粒度不一 | 固定词表 + embedding 召回 + 人工审核；定期跑相似度检查，提示可合并的能力点 |
| 模型或 prompt 升级导致结果漂移 | 记录 `extractor_version`；升级前在金标准集上对比，达标再全量重跑 |
| 站点条款与反爬 | 优先公开招聘接口；遵守 robots.txt；限速；不抓登录后内容 |
| LLM 成本 | 按 `content_hash` 缓存结果，只处理新增或变更的 JD；分类用小模型 |
| 中日英混合 | 词表存中英双名和别名；使用多语言 embedding |
| 样本偏差（大厂多、小公司少） | 热度按公司去重统计；页面上标明样本量 |
| 资源链接失效 | 每日检查，失效的降权并提示替换 |

开放问题：

- [ ] 金标准集由谁标注、标多少份？建议先人工标 20 份作为起点。
- [ ] 能力点粒度标准是什么？比如「gVisor」是独立能力点，还是「隔离技术」下的概念？
- [ ] 是否要把参考实现中的「核心概念」也建成二级节点？
- [ ] 未来是否开源？若开源，JD 原文的存储和展示需要再评估版权问题。

## 给 Claude Code 的执行说明

把本文档导出为 Markdown，放到仓库的 `docs/DESIGN.md`，并在 `CLAUDE.md` 中引用它。以下是给 Claude Code 的约定和第一批任务。

约定：

- 按里程碑推进，每个里程碑结束前先跑测试和金标准评测，再进入下一个。
- 单元测试中不调用真实 LLM，用录制好的响应做 mock；真实调用只出现在评测脚本中。
- 所有 prompt 放在 `prompts/` 目录，文件名带版本号；`extractor_version` 由模型名和 prompt 版本拼成。
- LLM 输出一律用 JSON schema 约束，并在代码中校验。
- API Key 从环境变量读取（`ANTHROPIC_API_KEY` 等），不写入仓库。
- 采集模块必须限速，并在请求头中标明用途。
- 遇到设计文档未覆盖的取舍，先在 `docs/decisions/` 下写一条简短记录，再实现。

第一批任务（M0）：

- [ ] 初始化仓库结构：`backend/`、`frontend/`、`prompts/`、`seed/`、`docs/`、`eval/`。
- [ ] 按「数据模型」一节建表，写好迁移脚本。
- [ ] 写 `seed/import_reference.py`，从 `seed/reference.html` 解析 `N`、`PRE`、`SOURCES`、`PATH` 并导入。
- [ ] 写一个最小的 API：列出能力点、能力点详情、先修关系。
- [ ] 前端先复刻参考实现的图谱视图，数据改为从 API 读取。
