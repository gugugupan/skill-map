# 五个岗位种子的合并记录

日期：2026-11-19。五份调研种子（ai-app、backend、sre-platform、frontend、data-eng）合并成本目录下的 `<role>.json` 和 `<role>.sources.md`。规则见 `docs/decisions/0003-multi-role.md`。agent-infra 的 50 个能力点没有改名，内容也没有改。

## 1. slug 统一

| 原 slug（岗位） | 合并到 | 理由 |
| --- | --- | --- |
| `algo-ds`（frontend） | `dsa` | 同一个概念，backend 先定义。 |
| `jvm-lang`（data-eng） | `jvm` | 同一个概念。在 `jvm` 的 concepts 里补了 Kotlin / Scala，资源补了《Effective Java》。 |
| `progressive-delivery`（backend） | `safe-release` | 都是灰度、金丝雀和自动回滚。在 `safe-release` 里补了特性开关，资源补了 Fowler 的 Feature Toggles。 |
| `analytics-ab`（frontend） | `tracking` + `ab-test` | 埋点和实验原来是分开的两个点（data-eng、ai-app）。按证据分配公司：`tracking` 是 VERCEL、PAYPAY、B，`ab-test` 是 RAMP。 |
| `ai-ui`（frontend） | `streaming-ui` + `ai-ux` | 流式渲染对应 `streaming-ui`；任务时间线、人工确认对应 `ai-ux`，已补进它的 concepts。`streaming-ui` 的公司是 O、T、A、B，`ai-ux` 是 O、T。 |

看过、但决定保留为独立能力点的：

- `stream-processing`：backend 和 data-eng 用的是同一个 slug，合成一份（见第 3 节），没有和别的点重复。
- `dist-txn` 和 `ledger`：前者讲通用的跨服务一致性（幂等、Saga、Outbox），后者讲金融账务（复式记账、对账）。保留边 `dist-txn → ledger`，`dist-txn` 的描述改写成不限于金融场景。
- `cache` 和 `http-cache`：前者是服务端缓存（Redis），后者是浏览器、CDN 和 Service Worker 缓存。
- `perf` 和 `web-vitals`、`render-perf`、`browser-render`：`perf` 是通用的测量与剖析方法，另外三个是前端专项。保留 `perf → web-vitals` 和 `perf → render-perf`。
- `observability` 和 `metrics-monitoring`、`log-pipeline`、`otel-tracing`、`data-observability`：`observability` 是总览，其余是专项，边是 `observability → *`。`trace` 是 agent-infra 里的 Agent 链路追踪，`otel-tracing` 不与它合并。
- `data-modeling` 和 `dim-modeling`：前者讲通用建模（范式、按访问模式建模、schema 演进），后者讲 Kimball 维度建模。保留边 `data-modeling → dim-modeling`。
- `traffic-edge` 和 `api-gateway`：前者是 DNS、CDN、WAF、L4/L7 负载均衡，后者是业务网关（鉴权、限流、灰度插件）。
- `finops` 和 `data-cost`、`oncall` 和 `incident`、`concurrency` 和已有的 `conc`、`linux-shell` 和已有的 `os`：侧重点不同，各自保留。

## 2. 公司

跨岗位出现的公司 code 和名称都一致，不需要改：A 阿里、B 百度、T 腾讯、O OpenAI、AIRBNB、COINBASE、MEITUAN 美团、NOTION、PAYPAY、RAMP、REDDIT、STRIPE。全局共 33 个公司 code，没有发现同一家公司用了两个 code 的情况（字节系岗位统一用 BYTEDANCE，高德、千问等归在 A）。

## 3. 多份完整定义的取舍

23 个 slug 被多个岗位完整定义过。每个只保留一份完整定义，放在下表的「定义所在岗位」里，其余岗位改成只写 `slug`、`cluster`、`companies`。描述都改写成不依赖岗位的说法（去掉「某公司要求……」），concepts 合并了各版本里的要点（4–5 条），资源取各版本里最权威的 1–3 条。

| slug | 定义所在岗位 | 改成引用的岗位 |
| --- | --- | --- |
| api-design | backend | ai-app、frontend、data-eng |
| cache | backend | ai-app、sre-platform |
| ci-cd | sre-platform | backend、frontend、data-eng |
| cloud | sre-platform | ai-app、backend、data-eng |
| data-modeling | data-eng | backend |
| docker | sre-platform | ai-app、backend、data-eng |
| git-collab | frontend | backend、data-eng |
| iac | sre-platform | backend、data-eng |
| incident | sre-platform | backend、data-eng |
| mq | backend | ai-app、sre-platform、data-eng |
| nosql | backend | data-eng |
| observability | sre-platform | ai-app、backend、frontend、data-eng |
| perf | sre-platform | backend、frontend |
| prompt-eng | ai-app | frontend |
| python | data-eng | ai-app |
| resilience | sre-platform | backend（名称定为「限流、熔断与降级」，容灾多活归 `dr`） |
| security-basics | backend | frontend（合入 XSS、CSRF、CSP） |
| sql-db | backend | ai-app、sre-platform、data-eng（合入 CTE、窗口函数） |
| stream-processing | data-eng | backend（名称从「流处理（Flink）」改为「流处理」） |
| sys-design | backend | ai-app、sre-platform |
| testing | backend | ai-app、sre-platform、frontend、data-eng |
| ts | frontend | ai-app |
| web-basics | frontend | ai-app |

另外，`auth`、`embedding-search`、`dsa`、`jvm`、`safe-release`、`tracking`、`ab-test`、`streaming-ui`、`ai-ux`、`dist-txn` 各自只有一份定义，但描述也改成了岗位中立的写法。

资源标题统一：「OpenTelemetry 官方文档」改为「OpenTelemetry 文档」，「FinOps Foundation 框架」改为「FinOps Framework」，「patterns.dev 渲染模式」改为「patterns.dev」。这几处是同一个 URL 用了不同标题。另外，以下 agent-infra 资源原来没有 URL，现在由岗位种子补上（`import_roles.py` 遇到同标题、原记录无 URL 时会补）：DDIA、The Kubebuilder Book、Playwright 文档、HashiCorp Vault 文档、Google《Site Reliability Engineering》。

## 4. 先修边

先修关系是全局的。每个岗位文件写入两端都属于该岗位的全部边，所以一个岗位加的边，在同时包含两端的其他岗位里也会出现。

删掉的边：

- `api-design → llm`、`git-collab → agentic`：两者之间没有真实的依赖关系。
- `dist → cache`：用缓存不需要先学分布式理论。
- `web-basics → observability`：通用能力点 `observability` 不应依赖前端专项。
- `sys-design → resilience`：与 backend 的 `resilience → sys-design` 方向相反。保留后者，系统设计是综合题。
- `browser-render → perf`、`devtools-debug → perf`：通用能力点 `perf` 不挂前端专项先修，改为 `browser-render → web-vitals`、`devtools-debug → web-vitals`、`devtools-debug → render-perf`。
- 拆分 `analytics-ab` 和 `ai-ui` 后不合理的展开边：`observability → tracking`、`data-fetch → ai-ux`、`fe-state → ai-ux`、`prompt-eng → streaming-ui`。

新增的边：`tracking → ab-test`，以及上一条里的三条前端边。

检查结果：

- 全局先修关系（含 agent-infra 的 52 条）无环。
- 没有两端都是 agent-infra 能力点的新边。
- 每个岗位的 path 都不违反先修，包括经由 agent-infra 边的传递依赖。

为此调整了 path：

- ai-app：`agentic` 移到「Agent 与工作流」阶段。原因是 `ctxeng`、`memory` 经由 `harness` 依赖它。
- sre-platform：`oncall` 移到「可靠性工程」阶段，排在 `slo` 之后。
- frontend：`http-cache` 移到「体验、性能与线上质量」阶段，排在 `web-vitals` 之前。
- 另有四个阶段的内部顺序按先修关系重新排了。

## 5. JD 核对

5 个岗位的 102 份 posting 都在 2026-11-19 用公开 API 或静态页重新核对过。没有下线的，没有删除任何 JD 或公司。用到的接口：Greenhouse、Ashby、Lever、Workable、腾讯 ByPostId、百度 getPostListNew、美团 getJobDetail、阿里 position/search、网易 queryPage、字节 search/job/posts。小差异：Datadog「Senior Software Engineer」和 Airbnb「Staff Software Engineer, Cloud Infrastructure」的 API 标题末尾多一个空格；阿里「娱驰BG-资深大前端/ 跨端开发专家」的 API 标题后面带部门后缀。

每个岗位从证据表里抽 5 条（共 25 条，每个岗位至少 1 条中国公司），核对 JD 正文里有没有职位标题和引文关键词：25 条全部通过。frontend 的 `pkg-monorepo` 那条证据引的是不在 postings 里的阿里千问岗位（positionId=100009540002），正文里同样能找到。

### 待浏览器核对的链接

阿里链接已替换（2026-11-19）：原来的 `talent.alibaba.com/off-campus/position-detail?positionId=…` 整条 `/off-campus/*` 路由会重定向到首页。12 条阿里链接都换成了对应业务招聘官网的同路径详情页（`https://<业务站>/off-campus/position-detail?positionId=<同一 positionId>`），并在浏览器里逐条打开确认能看到职位标题：阿里云 `careers.aliyun.com`、淘天 `talent.taotian.com`、阿里健康 `careers.alihealth.cn`、千问事业部 `talent.quark.cn`、高德 `talent.amap.com`、菜鸟驿站 `talent-post.alibaba.com`、ATH 事业群 `careers-tongyi.alibaba.com`；没有独立详情页的（飞猪站只有首页）或没有独立站的（智元科技、娱驰BG、诚云科技、业务技术）用控股集团站 `talent-holding.alibaba.com`。没有删除任何阿里 posting。

这些链接是按站点路由拼出来的，curl 只拿到 SPA 外壳。对应职位已经用 API 确认在架，但还没在浏览器里看过页面能否正常显示。字节的链接用的是 `/experienced/` 路由，而它的搜索接口要求站点 `society`，所以要特别确认这个路由能打开。百度详情页是服务端渲染，curl 能拿到正文，已直接核实，不在清单里。

| 岗位 | 公司 | 职位 | 链接 |
| --- | --- | --- | --- |
| ai-app | BYTEDANCE | 大模型应用开发工程师 - 飞书项目 | https://jobs.bytedance.com/experienced/position/7667047344642640133/detail |
| ai-app | BYTEDANCE | 大模型应用开发工程师-抖音生态与运营 | https://jobs.bytedance.com/experienced/position/7478147326294051090/detail |
| ai-app | BYTEDANCE | AI大模型应用开发专家-飞书多维表格 | https://jobs.bytedance.com/experienced/position/7594826319935588661/detail |
| ai-app | T | 微信基础-大模型应用开发工程师 | https://careers.tencent.com/jobdesc.html?postId=2110621118984531968 |
| ai-app | T | 混元-大模型应用开发工程师（北京/深圳） | https://careers.tencent.com/jobdesc.html?postId=2053738190963126272 |
| ai-app | T | 企业微信-AI应用后台开发工程师-智能助理应用(成都/北京) | https://careers.tencent.com/jobdesc.html?postId=2026648914832293888 |
| backend | T | 微信支付-后台开发工程师 | https://careers.tencent.com/jobdesc.html?postId=2112097242642034688 |
| backend | T | 微信-后台开发工程师-电商方向 | https://careers.tencent.com/jobdesc.html?postId=2078639812935593984 |
| backend | T | 微信-接入服务后台开发工程师 | https://careers.tencent.com/jobdesc.html?postId=2095697889002176512 |
| backend | T | 企业微信-后台高级开发工程师-（成都） | https://careers.tencent.com/jobdesc.html?postId=2093322000989859840 |
| backend | MEITUAN | 后端开发工程师（履约运力方向） | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4915020619&highlightType=social |
| backend | MEITUAN | 接入网关-高级后端开发工程师 | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4656453224&highlightType=social |
| backend | MEITUAN | 点评技术—高级后端开发工程师（公信力方向） | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4935087880&highlightType=social |
| backend | NETEASE | 资深服务端开发（社区业务） | https://hr.163.com/job-detail.html?id=60238&lang=zh |
| backend | NETEASE | Codewave-服务端开发工程师 | https://hr.163.com/job-detail.html?id=79001&lang=zh |
| sre-platform | A | 阿里云智能-站点可靠性工程（SRE）-杭州 | https://careers.aliyun.com/off-campus/position-detail?positionId=100055600002 |
| sre-platform | A | 业务技术-高级开发工程师-SRE | https://talent-holding.alibaba.com/off-campus/position-detail?positionId=100045600001 |
| sre-platform | T | 云原生高级SRE工程师（深圳/北京） | https://careers.tencent.com/jobdesc.html?postId=2113089267273216000 |
| sre-platform | MEITUAN | Keeta技术-资深架构师（稳定性与AI平台方向） | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4223713449&highlightType=social |
| sre-platform | MEITUAN | 交易系统平台部-基础平台技术中心-Java软件开发工程师(稳定性保障方向 L6-L7) | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4828037725&highlightType=social |
| frontend | A | 智元科技-前端开发工程师-广州 | https://talent-holding.alibaba.com/off-campus/position-detail?positionId=100052760004 |
| frontend | A | ATH事业群-AI 前端开发工程师-杭州 | https://careers-tongyi.alibaba.com/off-campus/position-detail?positionId=100045840004 |
| frontend | A | 娱驰BG-资深大前端/ 跨端开发专家 | https://talent-holding.alibaba.com/off-campus/position-detail?positionId=100036840002 |
| frontend | A | 千问事业部-AI视频剪辑前端开发专家-智能创作 | https://talent.quark.cn/off-campus/position-detail?positionId=100010060039 |
| frontend | A | 高德-前端开发工程师-共享专项 | https://talent.amap.com/off-campus/position-detail?positionId=5000014035 |
| frontend | A | 诚云科技-前端开发工程师-融媒体 | https://talent-holding.alibaba.com/off-campus/position-detail?positionId=100055580006 |
| frontend | T | 《无畏契约》-前端开发工程师-（AI & 创新互动方向） | https://careers.tencent.com/jobdesc.html?postId=2088182151676870656 |
| frontend | T | 智能体-桌面端开发负责人-WorkBuddy | https://careers.tencent.com/jobdesc.html?postId=2102397717010624512 |
| data-eng | T | 微信小游戏-数据开发工程师 | https://careers.tencent.com/jobdesc.html?postId=2110620275749076992 |
| data-eng | T | 电商-数据仓库开发工程师 | https://careers.tencent.com/jobdesc.html?postId=2098594911686410240 |
| data-eng | T | 微信基础-大数据工程师-AI方向 | https://careers.tencent.com/jobdesc.html?postId=2110191971174891520 |
| data-eng | T | 智能体-数据治理高级工程师-WorkBuddy | https://careers.tencent.com/jobdesc.html?postId=2092162824909537280 |
| data-eng | A | 菜鸟驿站-资深数据开发工程师-杭州 | https://talent-post.alibaba.com/off-campus/position-detail?positionId=100039480002 |
| data-eng | A | 飞猪-高级数据开发工程师/专家-搜推广 | https://talent-holding.alibaba.com/off-campus/position-detail?positionId=100041700001 |
| data-eng | A | 淘天集团-高级数据开发工程师-财务信息化 | https://talent.taotian.com/off-campus/position-detail?positionId=100032460002 |
| data-eng | A | 阿里健康-数据开发-北京 | https://careers.alihealth.cn/off-campus/position-detail?positionId=100047160002 |
| data-eng | MEITUAN | Keeta 大数据开发 | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4828413893&highlightType=social |
| data-eng | MEITUAN | 骑行-数据开发工程师 | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4885047275&highlightType=social |
| data-eng | MEITUAN | 商业增值-大数据开发工程师（广告方向） | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4686125855&highlightType=social |

共 39 条：腾讯 14、阿里 12、美团 8、字节 3、网易 2。

## 6. 最终计数（导出结果）

| 岗位 | 公司 | JD | 能力点（其中本岗位定义） | 边（含 agent-infra 边） | 阶段 |
| --- | --- | --- | --- | --- | --- |
| agent-infra | 10 | 23 | 50 | 52 | 7 |
| ai-app | 11 | 18 | 45（17） | 68 | 6 |
| backend | 10 | 24 | 45（25） | 62 | 6 |
| sre-platform | 12 | 19 | 46（33） | 72 | 6 |
| frontend | 11 | 21 | 45（32） | 65 | 5 |
| data-eng | 10 | 20 | 45（30） | 66 | 6 |

全局 `skills.json` 共 187 个能力点：agent-infra 原有 50 个，新增 137 个。
