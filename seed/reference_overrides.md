# 参考实现截图 JD 的替换

`seed/reference.html` 的 `SOURCES` 里有 4 份 JD 只有截图、没有链接。导入时用 `seed/reference_overrides.json` 按（公司代码, 原标题）替换成真实的公开职位，`reference.html` 本身不改。

获取日期都是 2026-11-19，每个链接都在浏览器里打开确认过职位正文。

| 代码 | 原标题 | 新标题 | 链接 | 获取方式 |
| --- | --- | --- | --- | --- |
| O | Agent 基础设施（截图） | Software Engineer, Agent Infrastructure | https://jobs.ashbyhq.com/openai/c1316397-25bb-4add-9e9d-0e3ea8ba929a | Ashby 公开接口 `api.ashbyhq.com/posting-api/job-board/openai` |
| A | Agent 基础设施（截图） | 阿里云智能-agent sandbox运行时开发专家 | https://careers.aliyun.com/off-campus/position-detail?lang=zh&positionId=100013683001 | 阿里云社招站搜索「Agent」，在浏览器里读正文 |
| B | 云原生 Agent Infra 高级研发工程师（截图） | 云原生 Agent Infra 高级研发工程师 | https://talent.baidu.com/jobs/detail/SOCIAL/4b326f6b-2c39-461c-ae64-69b4201c680e | 百度招聘接口 `httservice/getPostListNew`（职位编号 J100117） |
| X | 大模型基建部 AgentSphere（截图） | 【2027校招】AI Agent Infra 工程师 | https://job.xiaohongshu.com/campus/position/22062 | 小红书招聘接口 `websiterecruit/position/pageQueryPosition` |

选择说明：

- **O**：标题直接对应 Agent Infrastructure 团队。它和已有的 Agent Runtime、Codex Core Agents 两份不是同一个职位。
- **A**：阿里各招聘站都没有叫「Agent 基础设施」的职位。阿里云社招有三个 Agent Sandbox 岗位（运行时开发、平台开发、管控技术），这里选了最贴近运行时和沙箱的「运行时开发专家」。
- **B**：标题和截图完全一致。
- **X**：正文第一句就是「我们是小红书大模型基建部（RAI Studio）…正在建设 AgentSphere」，可以确定是截图的来源。这是校招岗位。同样的内容也以【REDstar】AI Agent Infra 工程师（21899）发布过，两份正文有细微差别。社招里提到 AgentSphere 的只有「Agent 系统架构师」，偏架构设计，所以没选它。

## 能力点对照

范围：参考实现里 `jd` 字段含该公司代码的能力点。这里只做报告，`reference_companies` 映射没有改。「支持」列给新 JD 正文的原文短引；不支持的写「无」。

### O · Software Engineer, Agent Infrastructure（支持 7 / 24）

| 能力点 | 支持 |
| --- | --- |
| dist 分布式系统 | "complex, globally-distributed systems" |
| lang Go / Rust / Python | 无（只提到 FastAPI、gRPC，没有点名语言） |
| llm LLM 基础 | 无 |
| loop Agent Loop | 无 |
| multi Multi-Agent 与委托 | 无 |
| cua Computer / Browser Use | "Our systems power products such as Codex, Operator, tool use in ChatGPT" |
| durable Durable Execution | 无 |
| state 状态模型 | 无 |
| iso 隔离技术 | "virtualization and containerization technologies (e.g. Kata, Firecracker, gVisor, Sysbox)" |
| sandbox 代码执行沙箱 | "providing a workspace for AI models to execute code, debug issues" |
| identity Agent 身份与委托授权 | 无 |
| inject Prompt 注入与工具安全 | 无 |
| ctxeng Context Engineering | 无 |
| memory 分层记忆 | 无 |
| rag 检索与 RAG | 无 |
| tools 工具设计 | 无 |
| trace Tracing 与可观测 | 无 |
| evals Eval 体系 | 无 |
| cost 成本与延迟优化 | "Have a keen eye for performance and optimization" |
| abstraction 平台抽象设计 | 无 |
| devx 开发者体验与协作 | "work closely with both research and product at OpenAI" |
| virt 虚拟化与 eBPF | "infrastructure scalability, virtualization efficiency, and agentic capabilities" |
| async 异步执行与进度可见 | 无 |
| rollout 新模型接入与上线 | 无 |

### A · 阿里云智能-agent sandbox运行时开发专家（支持 10 / 25）

| 能力点 | 支持 |
| --- | --- |
| os Linux 与 OS | 「扎实的操作系统内核、计算机网络与体系结构基础」 |
| net 计算机网络 | 「扎实的操作系统内核、计算机网络与体系结构基础」 |
| dist 分布式系统 | 无 |
| k8s 云原生与 K8s | 无 |
| lang Go / Rust / Python | 「精通 Go / C++ / Rust / Python 中的至少一种」 |
| llm LLM 基础 | 无 |
| loop Agent Loop | 无 |
| patterns 执行架构模式 | 无 |
| multi Multi-Agent 与委托 | 无 |
| ckpt Checkpoint 与恢复 | 无 |
| sched 调度与弹性 | 「打造毫秒级启动的轻量化 Web 沙箱」（冷启动） |
| conc 高并发与资源治理 | 「端侧管控服务的极致轻量化与高并发承载能力」 |
| iso 隔离技术 | 「轻量级容器（如 Kata Containers, Firecracker）」 |
| sandbox 代码执行沙箱 | 「统一沙箱管理引擎研发」 |
| identity Agent 身份与委托授权 | 无 |
| tenant 多租户隔离 | 无 |
| ctxeng Context Engineering | 无 |
| rag 检索与 RAG | 无 |
| tools 工具设计 | 无 |
| skills Skills / CLI / SDK | 「具备 Agent 平台构建、Skills开发、MCP部署等实战经验者优先」 |
| trace Tracing 与可观测 | 无 |
| evals Eval 体系 | 「熟悉当前开源 Agent 评测框架（如 WebArena, OSWorld等）」 |
| cost 成本与延迟优化 | 无 |
| rl Agentic RL 基础设施 | 「熟悉业界主流的Agent Infra、Agent Sandbox、Agent RL等技术」 |
| serving 推理服务 | 无 |

### B · 云原生 Agent Infra 高级研发工程师（支持 23 / 25）

| 能力点 | 支持 |
| --- | --- |
| os Linux 与 OS | 「扎实的计算机网络和操作系统基础知识，熟悉 Linux」 |
| net 计算机网络 | 「扎实的计算机网络和操作系统基础知识」 |
| dist 分布式系统 | 「熟悉经典分布式计算/存储/调度系统的原理和使用」 |
| k8s 云原生与 K8s | 「有 Kubernetes 实际使用经验，掌握 Operator 原理和应用」 |
| lang Go / Rust / Python | 「熟悉 Go / Python / C++ 至少一门编程语言」 |
| llm LLM 基础 | 「掌握 AI 基础知识」 |
| loop Agent Loop | 「了解 Agent 的执行模型、工具调用、上下文管理」 |
| multi Multi-Agent 与委托 | 「建设 Multi-Agent、海量 Agent 沙箱实例的编排、调度、观测与治理能力」 |
| harness Harness 工程 | 「掌握基础的上下文工程、Harness 工程」 |
| cua Computer / Browser Use | 「构建并上线过 Coding Agent、Browser Use、Computer Use 等 Agent 应用」 |
| durable Durable Execution | 无 |
| sched 调度与弹性 | 「有 Serverless / 弹性调度 / 分布式任务编排方向的设计开发经验」 |
| conc 高并发与资源治理 | 「持续提升执行平台的功能丰富度、并发能力、弹性伸缩效率」 |
| iso 隔离技术 | 「Docker/containerd/KataContainer/gVisor/Firecracker 等」 |
| sandbox 代码执行沙箱 | 「参与智能体沙箱、网关和可观测等产品的设计和研发」 |
| tenant 多租户隔离 | 「研究并落地高安全等级的多租户隔离方案」 |
| ctxeng Context Engineering | 「掌握基础的上下文工程」 |
| tools 工具设计 | 「了解 Agent 的执行模型、工具调用、上下文管理」 |
| mcp MCP | 「Skill/MCP/Plugin 等核心概念」 |
| skills Skills / CLI / SDK | 「构建面向 Agent 的产品接口与开发体验，包括 CLI、MCP、SDK、Skill 等能力」 |
| trace Tracing 与可观测 | 「有 AI 推理/训练/Agent 执行链路可观测的实践经验」 |
| cpdp Control Plane 与 Data Plane | 无 |
| rl Agentic RL 基础设施 | 「支撑 Agentic 应用、Agentic RL 的规模化落地」 |
| serving 推理服务 | 「有构建大规模模型训练/推理/Agentic RL 系统以及性能优化经验」 |
| agentic Agentic 工作方式 | 「用 Agentic 的方法端到端地交付结果是团队默认工作方式」 |

### X · 【2027校招】AI Agent Infra 工程师（支持 30 / 31）

| 能力点 | 支持 |
| --- | --- |
| os Linux 与 OS | 无 |
| dist 分布式系统 | 「在 Agent 系统、分布式系统、机器学习系统…至少一个方向具备显著深度」 |
| lang Go / Rust / Python | 「熟悉 Python / C++ / Rust / Go 中至少一门语言」 |
| llm LLM 基础 | 「持续适配模型能力演进」 |
| loop Agent Loop | 「将模型适配、Agent Loop、上下文组装、记忆、工具调用、审批和遥测等能力解耦」 |
| patterns 执行架构模式 | 「支持 ReAct、Workflow、Planner–Executor、Multi-Agent 等不同执行架构」 |
| multi Multi-Agent 与委托 | 「持续跟踪 Agent Runtime、Harness、Memory、Evaluation、Multi-Agent 等前沿方向」 |
| harness Harness 工程 | 「Harness Kernel 与执行架构研发」 |
| durable Durable Execution | 「保证运行实例可以被替换，但任务状态和执行结果不会丢失」 |
| state 状态模型 | 「研究 Session、Event、Turn、Deployment、Workspace 等状态模型」 |
| ckpt Checkpoint 与恢复 | 「状态持久化、断点恢复、故障迁移」 |
| iso 隔离技术 | 「为代码执行和工具调用提供隔离、可审计、可治理的安全边界」 |
| sandbox 代码执行沙箱 | 「有代码执行沙箱、工具调用系统…的实践经验」 |
| identity Agent 身份与委托授权 | 「完善 Sandbox、Credential、Agent Identity、委托授权」 |
| cred Credential 管理 | 「完善 Sandbox、Credential、Agent Identity、委托授权」 |
| inject Prompt 注入与工具安全 | 「长任务可靠执行、状态恢复、异构 Agent 治理、工具安全」 |
| ctxeng Context Engineering | 「探索 Context Engineering、分层记忆、Retrieval / RAG」 |
| memory 分层记忆 | 「探索 Context Engineering、分层记忆、Retrieval / RAG」 |
| rag 检索与 RAG | 「探索 Context Engineering、分层记忆、Retrieval / RAG」 |
| tools 工具设计 | 「建设 Tool、Skill、MCP Server 等能力的注册、版本、发现和调用体系」 |
| mcp MCP | 「建设 Tool、Skill、MCP Server 等能力的注册、版本、发现和调用体系」 |
| skills Skills / CLI / SDK | 「建设 Tool、Skill、MCP Server 等能力的注册、版本、发现和调用体系」 |
| registry Tool Registry 与 Gateway | 「建设 Tool、Skill、MCP Server 等能力的注册、版本、发现和调用体系」 |
| trace Tracing 与可观测 | 「建设数据集、评估器、Trace、Experiment、Run Version」 |
| evals Eval 体系 | 「建设数据集、评估器、Trace、Experiment、Run Version」 |
| gate 上线 Gate 与回归 | 「回归分析、上线 Gate、线上抽样和 Bad Case 回流能力」 |
| cpdp Control Plane 与 Data Plane | 「能够区分…Control Plane 与 Data Plane」 |
| lifecycle Agent 资产与生命周期 | 「定义统一的 Agent Artifact、资产模型和生命周期协议」 |
| abstraction 平台抽象设计 | 「具备系统抽象能力」 |
| research 研究品位 | 「具备良好的研究品位」 |
| hybrid 混合部署与自托管 | 「支持不同框架、不同 Runtime 以及 Managed / BYO Agent 的统一纳管」 |

## 结论

- B、X 的新 JD 和原截图几乎一一对应，映射基本成立。
- O、A 换成了范围更窄的职位：O 偏训练/部署底座和虚拟化，A 偏沙箱运行时。原截图里提到的 Agent 应用层能力（上下文、记忆、评测、身份等）在新 JD 里多数找不到原文支撑。要不要据此调整 `reference_companies`，需要另行决定。
