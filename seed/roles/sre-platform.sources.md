# sre-platform 种子来源

调研日期：2026-11-19。所有 JD 正文都实际取到（调研时存档为纯文本，未入库），以下引用都出自这些正文。

## 1. JD 清单（19 份 / 12 家）

| # | 公司 | 地区 | 职位 | 链接 | 获取方式 | 发布/更新日期 |
|---|---|---|---|---|---|---|
| 1 | GitLab (GITLAB) | 美国 | Site Reliability Engineer, Infrastructure Platforms — AMER | https://job-boards.greenhouse.io/gitlab/jobs/8623389002 | Greenhouse API `boards/gitlab` | 2026-11-06 |
| 2 | GitLab (GITLAB) | 美国 | Senior Staff SRE, Architecture Engineering: Hosted Runners | https://job-boards.greenhouse.io/gitlab/jobs/8932489002 | Greenhouse API | 2026-11-17 |
| 3 | Reddit (REDDIT) | 美国 | Senior SRE, Site Experience | https://job-boards.greenhouse.io/reddit/jobs/8369767 | Greenhouse API `boards/reddit` | 2026-11-09 |
| 4 | Coinbase (COINBASE) | 美国 | Senior Software Engineer, Compute Platform | https://www.coinbase.com/careers/positions/7701645?gh_jid=7701645 | Greenhouse API `boards/coinbase`（absolute_url） | 2026-10-30 |
| 5 | Airbnb (AIRBNB) | 美国 | Staff Software Engineer, Cloud Infrastructure | https://careers.airbnb.com/positions/8257909?gh_jid=8257909 | Greenhouse API `boards/airbnb`（absolute_url） | 2026-11-10 |
| 6 | Cloudflare (CLOUDFLARE) | 美国公司（岗位在 Lisbon/London） | Systems Reliability Engineer - Core | https://boards.greenhouse.io/cloudflare/jobs/8324908?gh_jid=8324908 | Greenhouse API `boards/cloudflare` | 2026-11-09 |
| 7 | 阿里 (A) | 中国 | 阿里云智能-站点可靠性工程（SRE）-杭州 | https://careers.aliyun.com/off-campus/position-detail?positionId=100055600002 | talent.alibaba.com `position/search` 接口（带 XSRF token）；链接为各业务招聘官网详情页，2026-11-19 浏览器打开可见职位标题 | 2026-11-11 |
| 8 | 阿里 (A) | 中国 | 业务技术-高级开发工程师-SRE | https://talent-holding.alibaba.com/off-campus/position-detail?positionId=100045600001 | 同上；链接为各业务招聘官网详情页，2026-11-19 浏览器打开可见职位标题 | 2026-10-14 |
| 9 | 腾讯 (T) | 中国 | 云原生高级SRE工程师（深圳/北京） | https://careers.tencent.com/jobdesc.html?postId=2113089267273216000 | careers.tencent.com `api/post/ByPostId` | 2026-11-02 |
| 10 | 百度 (B) | 中国 | SRE工程师（J103236） | https://talent.baidu.com/jobs/detail/SOCIAL/552ea65a-df8b-4482-9cb7-9b5679752450 | talent.baidu.com `httservice/getPostListNew` | 2026-08-05 |
| 11 | 百度 (B) | 中国 | 云计算运维研发Devops工程师（J94372） | https://talent.baidu.com/jobs/detail/SOCIAL/603db4ae-3f52-48c2-9fe2-2b9bf6c53261 | 同上 | 2025-10-10 |
| 12 | 美团 (MEITUAN) | 中国 | Keeta技术-资深架构师（稳定性与AI平台方向） | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4223713449&highlightType=social | zhaopin.meituan.com `api/official/job/getJobDetail` | 2026-08-31 |
| 13 | 美团 (MEITUAN) | 中国 | 交易系统平台部-Java软件开发工程师(稳定性保障方向 L6-L7) | https://zhaopin.meituan.com/web/position/detail?jobUnionId=4828037725&highlightType=social | 同上 | 2026-10-28 |
| 14 | Mercari (MERCARI) | 日本 | Software Engineer (Site Reliability) - Mercari | https://apply.workable.com/mercari/j/76C6D83800/ | Workable API `v2/accounts/mercari/jobs/<code>` | 2026-05-22 |
| 15 | Mercari (MERCARI) | 日本 | Senior Platform Infrastructure Engineer - Mercari | https://apply.workable.com/mercari/j/D938A9A8ED/ | 同上 | 2026-07-17 |
| 16 | PayPay (PAYPAY) | 日本 | Cloud Platform Engineer | https://job-boards.greenhouse.io/paypay/jobs/5471535004 | Greenhouse API `boards/paypay` | 2026-11-16 |
| 17 | PayPay (PAYPAY) | 日本 | Cloud Platform Engineer (K8S&NW Specialist) | https://job-boards.greenhouse.io/paypay/jobs/5583571004 | 同上 | 2026-11-16 |
| 18 | PayPay (PAYPAY) | 日本 | Cloud Infrastructure Engineer / クラウドインフラエンジニア | https://job-boards.greenhouse.io/paypay/jobs/6130390004 | 同上 | 2026-11-16 |
| 19 | LINE ヤフー (LINEYAHOO) | 日本 | Site Reliability Engineer / ソーシャルコマース（LINEギフト・ショッピングタブ） | https://www.lycorp.co.jp/ja/recruit/career/job-categories/ly00366/ | WebFetch 官方招聘页（静态） | 页面无日期，2026-11-19 取得 |

地区：美国 5 家（GitLab、Reddit、Coinbase、Airbnb、Cloudflare），中国 4 家（阿里、腾讯、百度、美团），日本 3 家（Mercari、PayPay、LINE ヤフー）。

看过但没用：Reddit「Senior Software Engineer, Infrastructure Engineering」（正文混入产品/A-B 实验内容，不像平台岗）；腾讯「云原生算力平台SRE工程师」（以 GPU/CUDA/NCCL 为主，偏 AI 算力）；腾讯 AI Infra / Agent 沙箱 SRE 系列（AI 专项，已在 agent-infra 岗覆盖）。

## 2. 证据表（能力点 × 公司 × JD 原文短引）

| 能力点 | 公司 | 原文短引（≤20 词） |
|---|---|---|
| os（复用） | CLOUDFLARE | Deep understanding of Linux/Unix operating system internals (e.g., storage subsystems, memory management) |
| os | B | 深入理解Linux操作系统；具备较好的计算机网络和体系结构基础 |
| net（复用） | CLOUDFLARE | core networking protocols (TCP/IP, DNS, BGP) |
| net | A | 熟悉 TCP/IP 协议栈、路由及负载均衡技术 |
| lang（复用） | GITLAB | Strong programming skills in Go or another systems language |
| lang | T | 熟练掌握 Go、Python 等至少一种编程语言 |
| dist（复用） | REDDIT | thrives in large-scale distributed systems |
| dist | COINBASE | design, implement, and operate distributed infrastructure systems |
| sys-troubleshoot | GITLAB | You can trace production failures across system layers and use measurements to validate fixes |
| sys-troubleshoot | T | 结合指标、日志与链路信息提出假设、验证根因 |
| perf | CLOUDFLARE | Analyse system bottlenecks, optimise kernel and network stacks |
| perf | LINEYAHOO | 中規模以上のWebアプリケーションに対してパフォーマンスを改善した経験 |
| sys-design | REDDIT | ensure Reddit is highly available and performant under massive global load |
| sys-design | MERCARI | Strong system design and distributed systems fundamentals: consistency, replication, capacity planning, failure modes |
| observability | GITLAB | using metrics, logs, and SLOs to detect symptoms early rather than just outages |
| observability | REDDIT | observability systems including metrics, logging, tracing, and alerting |
| metrics-monitoring | COINBASE | CNCF ecosystem (e.g., Helm, Prometheus, ArgoCD, Envoy) |
| metrics-monitoring | PAYPAY | Observability: Prometheus, Grafana, OpenTelemetry, Quickwit |
| log-pipeline | MERCARI | log analysis, alert summarization, RCA, remediation |
| log-pipeline | A | 负责可观测性、监控告警、日志分析、链路追踪、异常诊断等能力建设 |
| otel-tracing | REDDIT | Familiarity with technologies such as Prometheus, Grafana, OpenTelemetry, Envoy |
| otel-tracing | MERCARI | monitoring, alerting, and tracing on Datadog tied to user impact |
| aiops | MERCARI | Build autonomous AI agents for detection, triage, and recovery |
| aiops | T | 结合告警、工单、日志与知识库建设诊断 Agent，建立效果评估、权限控制与人工确认机制 |
| aiops | B | 对齐混部技术方向(Docker等)、AIOps 等 |
| slo | MERCARI | Define and operate SLOs and SLIs for critical user journeys, using error budgets |
| slo | LINEYAHOO | SLI/SLOの設計・運用および継続的な信頼性向上 |
| oncall | GITLAB | Participate in on-call, triage alerts, follow and improve runbooks |
| oncall | PAYPAY | Participate in an on-call rotation to provide 24/7 support for critical platform issues |
| incident | A | 能够在 Sev0/Sev1 重大故障中承担关键支持角色，并参与技术复盘 |
| incident | GITLAB | Take part in incident response and post-incident reviews |
| resilience | REDDIT | improve redundancy, graceful degradation, traffic management, and capacity planning |
| resilience | A | 了解服务治理、限流降级、熔断隔离、容灾备份、故障恢复等稳定性保障机制 |
| capacity | MEITUAN | 推动单机压测、全链路压测、容量水位探测、弹性、限流和容量托管等能力落地 |
| capacity | CLOUDFLARE | Participate in architecture reviews, capacity planning, and proactive system health monitoring |
| dr | MEITUAN | 深度参与美团SET化迭代建设，建设行业级的容灾架构 |
| dr | PAYPAY | Architect and build Infrastructure with AWS regional level failure tolerance |
| chaos | MEITUAN | 对可观测性、混沌工程、容量保障有落地经验 |
| chaos | T | 建设可用区级故障防护、备份恢复与容灾演练 |
| toil-automation | GITLAB | Build automation and tooling that reduces toil and replaces manual work |
| toil-automation | T | 研发集群生命周期管理、巡检、自愈、变更与诊断工具 |
| cloud | COINBASE | Hands-on experience with AWS and/or GCP infrastructure services (e.g., EC2, EKS, IAM, VPC, networking) |
| cloud | MERCARI | Production experience with Google Cloud (compute, networking, managed services) |
| iac | MERCARI | Deep Terraform experience at scale - authoring custom modules, running blast-radius-aware migrations |
| iac | A | 有使用 Terraform、CloudFormation 等基础设施即代码（IaC）工具的经验 |
| cloud-governance | PAYPAY | Multi AWS organization management, managing 50+ AWS accounts and 100+ users |
| cloud-governance | MERCARI | admission policy ... (RBAC, network policies, OPA / Gatekeeper) ... workload identity |
| finops | MERCARI | FinOps sensibility - understanding cloud spend drivers |
| finops | GITLAB | Partner with Finance, Product, and the billing platform team on usage metering and cost attribution |
| traffic-edge | REDDIT | Experience with CDN optimization, edge reliability, traffic engineering, or global infrastructure |
| traffic-edge | PAYPAY | troubleshoot an end-to-end request path across CloudFront, WAF, load balancers |
| virt（复用） | B | 了解容器化技术、 OpenStack、虚拟化网络、KVM、分布式存储等相关技术 |
| virt | GITLAB | autoscaled or dynamically scheduled compute, such as VM fleets, serverless platforms |
| infra-security | PAYPAY | Strong understanding of cloud security best practices in Fintech Industry |
| infra-security | MERCARI | Strengthen reliability governance through engineering (risk assessment, audit response, compliance-as-code) |
| config-mgmt | CLOUDFLARE | configuration management and infrastructure-as-code tools (e.g., Ansible, Terraform, SaltStack) |
| config-mgmt | A | 有发布流程、配置管理、资源治理、平台工具开发或稳定性体系建设经验者优先 |
| docker | AIRBNB | containerization and orchestration technologies, such as Docker and Kubernetes |
| docker | LINEYAHOO | コンテナ技術に関する知識・運用経験 |
| k8s（复用） | AIRBNB | Kubernetes. You live and breathe Kubernetes. You have operated it at scale. |
| k8s | COINBASE | 3+ years building and operating Kubernetes or similar compute orchestration systems |
| k8s-cluster-ops | MERCARI | Co-own the GKE cluster lifecycle: upgrades, node-pool strategy, add-on management |
| k8s-cluster-ops | PAYPAY | Perform upgrades and patching of EKS clusters and associated components |
| k8s-controller | PAYPAY | experience developing, testing, and maintaining custom controllers/operators and CustomResourceDefinitions |
| k8s-controller | GITLAB | Terraform modules, Kubernetes operators or controllers, or production automation |
| autoscaling | PAYPAY | Karpenter (cluster autoscaling) and Argo CD (GitOps continuous delivery) |
| autoscaling | AIRBNB | autoscaling and capacity management tools |
| k8s-net | MERCARI | Kubernetes networking (CNI, Services, ingress, network policy), DNS, HTTP/2, mTLS |
| k8s-net | T | 深入控制面、etcd、调度、容器运行时、CNI/CSI、内核与 eBPF 等链路 |
| service-mesh | COINBASE | Built largely on CNCF technologies including Kubernetes and Istio |
| service-mesh | PAYPAY | Implement and manage service mesh solutions (e.g., Istio, Linkerd) |
| tenant（复用） | MERCARI | Kubernetes at multi-tenant scale |
| tenant | GITLAB | evaluate workload isolation, balancing security and compatibility with performance and cost |
| cpdp（复用） | GITLAB | lead work across the runner control plane, worker provisioning, and job execution |
| cpdp | MEITUAN | 面向 Keeta 多控制面等复杂变更场景，建设变更风险识别、检查和拦截能力 |
| testing | PAYPAY | advanced software engineering practices, including unit/integration testing |
| testing | CLOUDFLARE | CI/CD pipelines and automated testing strategies for infrastructure |
| ci-cd | GITLAB | ship changes safely through CI/CD and GitOps |
| ci-cd | LINEYAHOO | GitHub Actions、Jenkins、Drone、CircleCI、Argo CD、SonarQube などを用いたCI/CDパイプライン構築経験 |
| gitops | GITLAB | ship changes safely through CI/CD and GitOps |
| gitops | PAYPAY | Argo CD (GitOps continuous delivery) |
| safe-release | A | 推动标准化发布、灰度控制、回滚策略、限流降级、容灾备份等工程实践落地 |
| safe-release | GITLAB | Plan migrations with representative workload tests, safe capacity handovers, and rollback paths |
| idp | MERCARI | build the developer-facing "kits" that let hundreds of engineers spin up new microservices |
| idp | COINBASE | Build developer-facing tooling and workflows that improve how engineers across Coinbase interact with Kubernetes |
| idp | PAYPAY | Terraform, Github Actions, ... ArgoCD, OpenTelemetry, Wiz, Backstage |
| sql-db | MEITUAN | 精通Mysql、Redis、MQ等基础服务及中间件技术 |
| sql-db | LINEYAHOO | データベース周りの知識・運用・チューニング経験 |
| cache | REDDIT | Kafka, ClickHouse, Cassandra, Redis, or similar distributed infrastructure technologies |
| cache | A | 具备扎实的数据结构、算法、操作系统、网络、数据库、缓存、消息中间件等基础 |
| mq | CLOUDFLARE | Experience with any of our existing tooling, such as Kafka and Temporal |
| mq | MEITUAN | 精通Mysql、Redis、MQ等基础服务及中间件技术 |
| stateful-ops | CLOUDFLARE | Postgres, PgBouncer, and Stolon / Kafka / Zookeeper / Ceph & Rook |
| stateful-ops | B | 熟悉大模型框架、高性能通信、os/kernel、openstack、kvm、分布式存储 |

## 3. 归纳取舍

- **没复用 `sre`**：它的描述是腾讯 Agent 沙箱 SRE 和日本 Agent JD 的语境。通用 SRE 拆成 `slo`、`oncall`、`chaos`、`incident`（预定）、`toil-automation` 几个点。按粒度规则（1–3 周一个点），一个「SRE」点装不下。
- **没复用 `trace`、`devx`、`sched`、`conc`、`abstraction`**：它们的描述都是 Agent 语境。分布式追踪另起 `otel-tracing`，开发者平台另起 `idp`，伸缩另起 `autoscaling`。
- **复用了 `os` `net` `dist` `lang` `k8s` `virt` `tenant` `cpdp`**：内容对平台岗同样成立（`virt` 的 KVM/eBPF、`tenant` 的噪声邻居、`cpdp` 的控制面数据面拆分）。只是描述里点名的公司是 Agent 岗的公司，merge 时可以考虑把描述改得更中性。
- **预定通用 slug**：用了 12 个（perf、sys-design、observability、incident、cloud、iac、docker、testing、ci-cd、sql-db、cache、mq），都按规则写了完整内容。没用 `security-basics`（OWASP 应用安全和平台岗要的密钥、策略、合规不是一回事），另起了 `infra-security`。
- **AIOps 保留**：岗位是「非 AI 专项」，但 Mercari、腾讯、百度、美团、LINE ヤフー、Coinbase、GitLab 都把「用 AI 做运维」写进了 2026 年的 SRE JD，所以保留 `aiops` 这个工具性能力点，放进可观测性类别和最后一个阶段。
- **先修**：60 条，无环，没有两端都在现有 50 个 slug 里的边（`docker→k8s`、`k8s-net→tenant`、`k8s-controller→cpdp` 都只有一端在现有词表）。`os→virt` 和 `k8s→cpdp` 是已存在的全局边，这里没重复加。`virt` 在本文件里没有新边，靠全局的 `os→virt` 连进图。
- **path**：6 个阶段，覆盖 31 个能力点。

## 4. 不确定处

- **百度、美团的职位页链接**是根据官网前端路由拼出来的（百度 bundle 里有 `/jobs/detail/:type/:id`，美团 bundle 里有 `/position/detail?jobUnionId=`）。正文是从官网接口取的，但这两个页面是 JS 渲染，WebFetch 没法验证页面本身能打开。
- **LINE ヤフー** 的正文来自 WebFetch 的摘录（模型转述加原文引号），不是原始 HTML 全文。页面上没有发布日期。
- **Cloudflare** 是美国公司，但这个职位的工作地点是 Lisbon 和 London。如果「美国」是指岗位所在地，那么美国就只有 4 家。
- **百度 J94372** 发布于 2025-10，比较旧，但接口里仍在招。
- **美团 4828037725** 是业务稳定性方向的 Java 岗，只用它来支撑 `dr`、`sql-db`、`cache`、`mq`、`capacity`。
- **company 归属**按正文里的关键词手工确认过。Tech Stack 列表里出现的技术（例如 PayPay 的 RDS、ElastiCache、SQS）算作「要求」；公司介绍和福利段落里的词（cost、security 等）已排除。

## 合并后的变化

合并时统一了跨岗位的 slug 和内容，详见同目录 `MERGE.md`。
