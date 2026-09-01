# Christian Studies 未决问题

**版本：** 0.4
**状态：** 活跃决策登记
**效力：** 已接受决议约束未来规划；未决建议不构成决定

> Agent 使用的英文主文档：[`Open-Questions.md`](Open-Questions.md)。

本文档保存需要共同讨论的产品与架构决定。依赖某项决定的工作，不能在决定完成之前开始。稳定 ID 使规划、规范、测试和提交能够引用同一个问题。

“建议起点”只是为了让讨论有一个具体方案，并不授权实施。已接受决议约束未来规划，但不表示迁移或实现已经完成。影响多个领域的决定保存在 [`Decisions/`](Decisions/README-zh.md) 中。

## 决策优先级

| ID | 决策 | 必须完成的阶段 | 状态 |
| --- | --- | --- | --- |
| OQ-001 | 产品边界 | 结构性重构前 | 已接受——ADR-0001/0004 |
| OQ-002 | 运行与部署形态 | 专用设备实现前 | 方向已接受——ADR-0001/0004；移动契约后续见 OQ-018 |
| OQ-003 | 持久存储与 Git | 结构性重构前 | 已接受——ADR-0001/0002/0004；引擎/Package 后续见 OQ-016/OQ-019 |
| OQ-004 | 规范化内容的权威表示 | 结构性重构前 | 已接受 |
| OQ-005 | 平台与书籍包边界 | 结构性重构前 | 已接受 |
| OQ-006 | 数据库角色 | 结构性重构前 | 已接受——ADR-0002；引擎后续见 OQ-016/OQ-017 |
| OQ-007 | 导入格式与审核边界 | 导入流水线前 | 已接受 |
| OQ-008 | 注释锚点身份 | 共享阅读器/数据模型前 | 已接受——ADR-0003 |
| OQ-009 | Context Service 契约 | Context 通用化前 | 已接受 |
| OQ-010 | 模型路由策略 | 多模型前 | 已接受 |
| OQ-011 | MCP 与技能信任模型 | 第一项外部能力前 | 已接受 |
| OQ-012 | 隐私与提供商资格 | 多提供商/工具前 | 已接受 |
| OQ-013 | 结构化笔记工作流 | 知识功能前 | 已接受，带评估门槛 |
| OQ-014 | 跨书知识身份 | 知识功能前 | 已接受；Graph 引擎后续见 OQ-017 |
| OQ-015 | 来源权利与仓库可见性 | 扩大导入/分享前 | 已接受 |
| OQ-016 | 内部版/外部版用户数据持久化引擎 | 内部版/外部版发布前 | 未决 |
| OQ-017 | 知识图谱投影引擎 | 图谱实现前 | 未决 |
| OQ-018 | 原生移动应用与交互边界 | 原生移动实现前 | Mobile-first 方向已接受，具体仍未决 |
| OQ-019 | 可迁移用户数据 Package 与同步边界 | Export/Import 实现前 | Export 先于 Sync 的方向已接受，具体仍未决 |
| OQ-020 | Dictionary 与 Grammar Source Provider 契约 | 语言学习原型前 | 未决 |
| OQ-021 | Language Learning Domain 与持久知识模型 | 保存语言知识前 | 未决 |
| OQ-022 | Managed Content 打包、权利与升级隔离 | 移动端内置内容前 | 未决 |
| OQ-023 | Voice Capability、Discussion Profile 与 Session Data | 第一项持久 Voice 功能前 | 未决 |

## OQ-001 产品边界

**问题：** Christian Studies 首先是个人本地优先环境、本地部署的多用户应用，还是托管式产品？

**为什么重要：** 账户、同步、存储、并发、安全、部署和授权方式都依赖这个边界。现在同时为三种产品设计，会在需求得到证明之前引入巨大成本。

**建议起点：** 第一版平台继续保持本地优先和单读者。身份与 API 的设计不要彻底封死未来的多用户扩展，但在没有单独产品决议之前，不实现账户、云同步或租户系统。

**正式决定必须说明：** 主要用户、可信机器边界、协作预期、远程访问预期，以及哪些未来场景必须保留可能性。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 第一版平台是本地优先、单读者的个人环境。API 与身份设计保留未来多用户的可能性，但账户、云同步、租户和共同阅读不在当前范围内，除非以后通过新的产品决议。
- **理由：** 真实的个人使用已经证明价值；更广泛需求要先通过向读书会朋友介绍项目来验证。
- **后果：** 用户自己的机器是可信边界。协作版是未来可能的产品分支，不是第一版隐藏需求。
- **记录：** [ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution-zh.md)。
- **修订：** ADR-0004 保留个人产品边界，并把 iPhone 设为首个专用设备目标；它没有引入公开用户或远程账户。

## OQ-002 运行与部署形态

**问题：** 下一阶段继续使用浏览器加本地服务、打包成桌面应用，还是引入托管式 Web 部署？

**为什么重要：** 文件系统访问、秘密存储、升级、浏览器安全、离线使用和前端技术都依赖运行容器。

**建议起点：** 结构性重构期间保留 loopback 本地服务架构。应用接口应保持可打包，但 Electron、Tauri、原生移动端和托管部署都等到多书籍流程出现具体需求后再决定。

**正式决定必须说明：** 支持的操作系统、启动体验、离线预期、更新方式、秘密存储和远程访问策略。

### 决议

- **状态：** 2026-08-30 已接受。
- **修订后的选择方案：** 核心开发期间继续使用浏览器加 loopback 本地服务，并以它作为兼容性基线。首个专用设备版本以能够独立运行的 iPhone App 为目标；桌面端保留为以后可能的客户端。
- **澄清：** 个人版的“注册”是建立本地 Profile，不是创建远程账户。用户 API Key 通过批准的秘密边界在本机配置和保存。
- **后续细节：** 原生/Web 边界、iOS 基线、更新分发与移动交互契约由 OQ-018 决定。
- **记录：** [ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution-zh.md)。
- **修订：** [ADR-0004](Decisions/ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data-zh.md)
  已用设备本地的 iPhone 目标取代桌面优先的可分发目标。浏览器加 loopback 服务继续作为当前开发与兼容运行方式。原生 App 契约继续由 OQ-018 决定。

## OQ-003 持久存储与 Git

**问题：** 哪些数据继续作为 Git 管理的文件，哪些数据可以进入应用存储？

**为什么重要：** 项目最初就把 Git 作为功能。正文、笔记、讨论、授权和已接受知识，在体积、隐私、冲突和可迁移性方面有不同需求。

**建议起点：** 原件、审核 Markdown、参考资料、元数据、注释和已接受知识继续使用可迁移文件。个人安装继续以 Git 作为预期历史机制。搜索与任务可以使用派生或运行时存储。只有真实体积和使用方式证明有必要时，才考虑为大型讨论正文选择不同的持久表示。

**正式决定必须说明：** 每种实体的权威数据、Git 纳入与忽略规则、隐私预期、备份和导出、冲突行为，以及不同存储模式之间的迁移。

### 决议

- **状态：** 2026-08-30 已接受，持久化引擎另行决定。
- **选择方案：** 采用三个分发阶段。个人阶段的持久内容、笔记和讨论可以由 Git 管理；内部阶段的共享书籍/资料可以由 Git 管理，但每位读者的笔记与讨论只留在本地；外部应用不附带书籍，读者自行导入，只有允许再分发的圣经资源可以随应用提供。
- **当前权威：** 个人阶段现有注释和讨论 JSON 文件继续作为权威数据。
- **后续细节：** 内部版/外部版的用户数据持久化引擎由 OQ-016 决定。第一版可迁移 Export/Import Package 与后续同步边界由 OQ-019 决定。
- **记录：** [ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution-zh.md)、[ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles-zh.md) 和 [ADR-0004](Decisions/ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data-zh.md)。

## OQ-004 规范化内容的权威表示

**问题：** 审核后的 Markdown 是否继续作为规范化阅读正文的权威格式，还是让结构化 AST/JSON 文档成为权威？

**为什么重要：** 导入、编辑、渲染、锚点、Diff 质量、可迁移性和 ContextBuilder 都依赖权威表示。

**建议起点：** 继续让审核 Markdown 成为正文权威来源。把它解析成版本化中间文档模型，用于渲染、索引和锚点，但该模型仍是派生产物。天然属于记录的数据可以使用结构化文件，但不能形成第二份正文。

**正式决定必须说明：** 支持的 Markdown 方言、扩展语法、稳定身份机制、往返转换预期，以及哪些步骤必须人工批准。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 审核 Markdown 继续作为规范化正文的权威来源。版本化中间文档模型可以服务于渲染、索引和锚点，但始终是派生产物。天然属于记录的数据可以使用结构化存储，但不能产生第二份正文权威。
- **后果：** 导入结果必须经过人工批准；渲染器和索引必须从 Markdown 重建。具体 Markdown 方言和身份编码由 Reading Document Model 规范决定。
- **所需测试：** Parser fixture、确定性投影测试，以及证明派生表示不会成为正文唯一副本。

## OQ-005 平台与书籍包边界

**问题：** 哪些内容属于共享平台，哪些内容应随单本书籍包一起迁移？

**为什么重要：** 当前书籍拥有自己的 `Web/` 实现。继续这种结构会复制代码；但移动太多内容，也可能使书籍无法独立理解和版本管理。

**建议起点：** 书籍包以数据为中心并且可迁移，包括原件、审核内容、参考资料、元数据和明确归属的用户数据。通用转换器、UI、构建逻辑、模型客户端和索引进入共享平台。在移动任何持久文件之前，先使用兼容适配器包装当前书籍布局。

**正式决定必须说明：** 逻辑书籍包契约、物理仓库布局、用户数据所有权、包版本、发现机制和迁移路径。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 书籍包是以数据为中心、可迁移的单元，包含原件、审核内容、参考资料、元数据和明确归属的用户数据。通用转换器、UI、构建逻辑、模型客户端和索引属于共享平台。
- **迁移：** 移动持久文件前，先用兼容适配器包装当前《追寻敬虔》布局；物理布局和包 Schema 必须先有规范和测试。
- **后果：** 不运行应用代码也能理解一本书；共享应用行为不会复制进每一本书。

## OQ-006 数据库角色

**问题：** 平台是否使用 SQLite 或其他数据库？如果使用，它可以负责哪些内容？

**为什么重要：** 书籍目录、后台任务、搜索、全文检索和并发可以从数据库获益，但边界不清的数据库可能成为不透明的第二真相来源。

**建议起点：** SQLite 首先用于派生索引和本地运行状态，例如书籍目录投影与任务。持久书籍和用户数据继续保留在声明的可迁移文件中，直到经过测量的需求证明某个实体必须由事务数据库管理。

**正式决定必须说明：** 权威表与投影表、重建规则、备份和导出、schema 迁移、故障恢复，以及和 Git 的关系。

### 决议

- **状态：** 2026-08-30 已接受，具体引擎问题另行处理。
- **选择方案：** 引入本地 SQLite，用于权威的平台 Book Catalog；完成明确迁移后，也可以保存权威的平台管理书籍 Metadata。SQLite 还可以保存运行任务和派生的搜索/检索投影。
- **权威规则：** 按实体或数据表声明权威。即使检索和搜索索引与权威数据位于同一个数据库，它们仍然是派生数据。当前文件 Metadata 在迁移得到测试前仍是权威来源。
- **用户数据：** 当前注释/讨论 JSON 继续以文件为权威；未来引擎由 OQ-016 决定。Graph 存储由 OQ-017 决定。
- **记录：** [ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles-zh.md)。

## OQ-007 导入格式与审核边界

**问题：** 第一版通用导入流水线支持哪些格式？人工审核从哪里开始成为强制要求？

**为什么重要：** DOC、DOCX、PDF、EPUB、HTML 和 OCR 在忠实度和结构歧义上差别很大。过早宣称广泛支持会掩盖转换错误。

**建议起点：** 先支持 Markdown、DOCX、可提取文字的 PDF 和纯文本；现有旧版 DOC 流程作为受控兼容适配器保留。只有准备好代表性 fixture 后再增加 EPUB 和 OCR。所有格式都必须产生诊断和审核预览；任何抽取正文未经明确批准都不能成为权威内容。

**正式决定必须说明：** 首发格式、不支持的特性、转换质量门槛、审核流程、图片/表格/脚注处理和失败行为。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 通用流水线先支持 Markdown、DOCX、可提取文字的 PDF 和纯文本。旧版 DOC 作为受控兼容适配器保留。准备好代表性 fixture 后再增加 EPUB 与 OCR。
- **审核边界：** 每个适配器都必须生成诊断和转换预览。只有明确人工批准后，抽取正文才能成为权威内容。
- **所需测试：** 逐格式忠实度 fixture、歧义可见性、原件保存，以及不支持结构的失败行为。

## OQ-008 注释锚点身份

**问题：** 当 Markdown、解析方式或渲染方式变化时，怎样让笔记和讨论继续附着在正确原文上？

**为什么重要：** 当前确定性的块顺序 ID 加引用上下文很实用，但插入新块后可能整体移动。平台级阅读器需要明确的长期身份和迁移契约。

**建议起点：** 在审核内容层加入稳定的阅读单元与块 ID，同时保留准确引用、前后文选择器和来源修订哈希。提供迁移和重新定位工具，绝不能静默接受有歧义的匹配。DOM 路径不能作为持久身份。

**正式决定必须说明：** ID 保存位置、导入时如何生成、人工编辑如何保持、恢复顺序、歧义 UI 和迁移测试。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 每个经过审核的语义块（通常为段落）分配稳定且不透明的 UUID。段内精确选区继续使用准确文字、Offset、前后文和来源修订。第一版平台不要求每个句子都有持久 UUID。
- **后果：** 相邻位置插入新内容不会改变该块的持久身份；修订和歧义检查仍然必要。跨块锚点需要后续 Schema 扩展。
- **记录：** [ADR-0003](Decisions/ADR-0003-Stable-Block-Anchoring-zh.md)。

## OQ-009 Context Service 契约

**问题：** 证据发现、Context 选择、Prompt 渲染、模型路由和讨论持久化之间的稳定边界是什么？

**为什么重要：** `ContextBuilder` 是项目的核心优势。如果它继续和某个 UI 或模型提供商混在一起，就很难复用、测试和改进。

**建议起点：** 定义与提供商无关、带版本的 `ContextRequest`、`EvidenceCandidate`、`ContextPreview`、`ContextBundle` 和 `EvidenceManifest` 契约。把发现与排序，同用户选择、预算、Prompt 渲染和模型执行分开。发送前冻结并哈希所选证据。

**正式决定必须说明：** Schema、扩展机制、必要证据顺序、预算行为、缓存规则、修订验证和评估 fixture。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 定义与提供商无关、带版本的 `ContextRequest`、`EvidenceCandidate`、`ContextPreview`、`ContextBundle` 和 `EvidenceManifest` 契约。分离发现/排序、用户选择、预算、Prompt 渲染、模型执行和持久化。
- **完整性规则：** 发送前冻结并哈希所选证据；来源过期或无法解析时拒绝发送，不能静默替换。
- **迁移：** 在兼容测试保护下分层重构当前 `ContextBuilder`，不把契约绑定到某个 UI 或提供商。

## OQ-010 模型路由策略

**问题：** 系统怎样在准确性、费用、延迟、隐私和用户偏好之间平衡并选择模型？

**为什么重要：** Router 可以降低成本或改善困难问题，但也可能产生比单模型更不透明、更不一致、更难评估的行为。

**建议起点：** 先基于明确的任务特征使用小型确定性策略，并提供“经济”“自动”“深入”等用户模式，同时允许用户覆盖。只有同时满足来源隐私和能力要求的模型才能进入候选。在使用一个 AI 决定另一个 AI 之前，必须先有评估证据。

**正式决定必须说明：** 任务类别、支持的提供商和模型、用户模式、质量下限、费用上限、降级、日志和评估标准。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 先使用小型确定性路由策略，并提供“经济”“自动”“深入”三种用户模式。在隐私和能力约束仍得到满足时，允许用户覆盖自动选择。
- **限制：** 在评估证明有价值之前，不增加一个 AI 来选择另一个 AI。优先修复 Context 质量，再提升模型能力。
- **所需测试：** 使用固定阅读任务比较依据性、聚焦程度、费用、延迟、降级和模式覆盖。

## OQ-011 MCP 与技能信任模型

**问题：** MCP Server 和技能如何注册、授权、调用和审计？

**为什么重要：** 工具可能读取私密 Context、访问账户或网络、写入数据，并返回包含进一步指令的内容。

**建议起点：** 所有能力在注册前默认关闭。声明输入数据类别和副作用，使用最小权限，默认只读，外发或写入需要明确批准，并把工具结果作为不可信的分类证据记录到 Manifest 中。

**正式决定必须说明：** 能力 Manifest、权限持续时间、用户提示、秘密访问、沙箱、写入策略、来源追踪和失败行为。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 能力在注册前默认关闭，使用最小权限并默认只读。外发和写入需要明确权限。工具结果始终是不可信的分类证据，并记录在 Manifest 中。
- **后果：** 导入内容不能自行取得工具权限。每项能力必须在使用前声明输入、副作用、秘密、权限持续时间、来源和失败行为。

## OQ-012 隐私与提供商资格

**问题：** 系统怎样决定哪些内容可以发送给哪个模型、工具或提供商？

**为什么重要：** 书籍来源、个人笔记、讨论和补充文档可能具有不同的隐私与权利限制。如果不知道提供商资格，仅仅逐轮选择还不够。

**建议起点：** 给每项来源和用户数据类别分配持久的外发策略，维护提供商 allowlist，并同时要求“来源具备资格”和“本轮明确纳入”。新的私密补充资料默认禁止外发。

**正式决定必须说明：** 数据分类、提供商策略、本地模型行为、授权持久化、撤销、审计记录和 UI 文字。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 为每项来源和用户数据类别分配持久外发策略，维护提供商 allowlist，同时要求来源具备资格且本轮明确纳入。新的私密补充来源默认禁止外发。
- **后果：** 派生 Chunk 只能继承、不能扩大原来源权限。授权可以撤销；需要用户选择时，UI 必须在外发前显示提供商和数据类别。

## OQ-013 结构化笔记工作流

**问题：** “更结构化的笔记”具体指什么？AI 建议如何变成用户接受的知识？

**为什么重要：** 结构可能指标签笔记、提纲、原子命题、人物/概念、论证图或摘要。一次构建所有形式会造成知识模型不清，也可能把 AI 工作错误归属于用户。

**建议起点：** 从带证据链接的综合笔记，以及稳定的人物、概念和经文实体开始。AI 建议进入独立审核队列；只有用户明确接受或编辑，才形成持久知识。

**正式决定必须说明：** 第一批知识类型、必要引用、建议 Schema、审核操作、作者身份、修订历史和拒绝行为。

### 决议

- **状态：** 2026-08-30 已接受，带评估门槛。
- **选择方案：** 先评估读完一章后，已有注释和讨论是否具有足够质量，能够产生有用综合。第一批结构化输出从带证据链接的综合笔记，以及稳定的人物、概念和经文实体开始。
- **审核边界：** AI 输出进入独立建议队列；只有用户明确接受或编辑后，才形成持久知识。
- **门槛：** 在章节级实验确认“读者理解了什么、收获了什么”之前，不设计更广泛的本体模型。

## OQ-014 跨书知识身份

**问题：** 不同书中的同一个人物、著作、概念或经文段落，怎样识别和连接？

**为什么重要：** 只用文件名作为身份很脆弱；只存在数据库中的知识图谱又不透明。译名差异和神学歧义也使自动合并不安全。

**建议起点：** 为已接受知识实体分配稳定 ID，并提供人类可读的 Markdown 页面、别名和证据链接。图谱与搜索索引都是派生投影。歧义合并必须审核，同一个标签不能自动证明含义相同。

**正式决定必须说明：** 实体类型、ID 规则、别名、合并/拆分流程、引用边、Markdown 表示和索引重建。

### 决议

- **状态：** 2026-08-30 已接受；投影引擎仍未决定。
- **选择方案：** 已接受知识实体分配稳定 ID，并使用带别名和证据链接的人类可读 Markdown 页面。歧义合并必须审核，同名不能自动证明同义。
- **投影规则：** 搜索和图谱存储默认是派生投影。Graph 数据库是候选，不是已接受的 Source of Truth。
- **后续：** 只有真实图查询与规模明确后，才由 OQ-017 选择 Graph 投影引擎。
- **记录：** [ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles-zh.md)。

## OQ-015 来源权利与仓库可见性

**问题：** 在原件或生成阅读版本进入 Git、同步或分享之前，需要记录哪些权利与可见性元数据？

**为什么重要：** 即使读者合法拥有一本书，它仍可能受版权保护。仅限本机、私有远程仓库和公开发布具有不同后果。

**建议起点：** 导入时记录取得方式、权利依据、允许用途和仓库可见性。受版权保护的原件与完整派生正文默认只在本地或私有环境使用；没有记录授权或公版状态时，不得公开分发。

**正式决定必须说明：** 权利元数据 Schema、可见性类别、Git/远程规则、导出检查、遮蔽或排除行为和审核责任。

### 决议

- **状态：** 2026-08-30 已接受。
- **选择方案：** 导入时记录取得方式、权利依据、允许用途和仓库可见性。受版权保护的原件与完整派生正文默认只限本地/私有使用；没有记录授权或公版状态时，不得公开分发。
- **应用要求：** 导入、导出、同步和分发界面必须展示并执行这项声明，不能只依靠文档提醒。
- **所需测试：** 发行包与导出检查必须拒绝或排除不符合目标操作权利和可见性要求的内容。

## OQ-016 内部版/外部版用户数据持久化引擎

**问题：** 个人文件阶段之后，应该由哪一种嵌入式或外部数据库管理注释与讨论？

**为什么仍未决定：** 内部版和外部版需要本地隐私、JSON 文档忠实度、修订冲突、备份/导出、迁移和轻松部署。当前真实使用数据还没有证明 JSON 文件不足，也没有证明哪种数据库取舍最重要。

**候选：** 继续使用带 Schema 版本的 JSON 文件；使用具有可靠 JSON 文档操作的嵌入式数据库；或者只有未来多用户产品边界需要时才采用服务型数据库。

**评估标准：** 无损 JSON 语义、事务、修订冲突、迁移工具、备份/导出、可迁移性、加密能力、桌面打包、运维成本，以及代表性笔记和讨论上的性能。

**必须完成的阶段：** 内部版或外部版改变用户数据权威来源之前。

## OQ-017 知识图谱投影引擎

**问题：** 应该用哪种技术（如果确有必要）实现派生的跨书知识图谱和图查询？

**为什么仍未决定：** Graph 数据库可能适合实体关系，但项目目前还没有足够的已接受知识量，也没有具体查询模式来证明需要某个引擎。现在选型会把知识身份决定和存储实现混为一谈。

**候选：** SQLite 中的派生邻接/索引表、嵌入式 Graph 引擎，或独立 Graph 数据库。除非以后有新决议，已接受的 Markdown 知识继续作为默认权威来源。

**评估标准：** 需要支持的图查询、来源边、可重建性、本地部署、备份/导出、生态成熟度、查询复杂度和实际数据规模。

**必须完成的阶段：** 实现超出简单派生索引的持久图谱投影之前。

## OQ-018 原生移动应用与交互边界

**问题：** 怎样用原生应用架构和交互契约实现已经接受的 Mobile-first 方向，同时不把 Reading Core 绑定到单一 Apple UI，也不提前重写当前 Reader？

**为什么仍未决定：** ADR-0004 已选择完全本地运行的 iPhone App 作为首个专用设备目标，但没有选择 SwiftUI、嵌入式 Web Runtime、共享渲染层、Package 布局、后台行为或具体的选区/Bottom Sheet 交互。这些决定需要第二个真实阅读 Use Case 和兼容 fixture。

**建议起点：** Reader 始终是主界面。文字选区可以在临时移动面板中显示 Look Up、Explain、Grammar、Translate、Ask AI、Note 与 Save 等上下文动作，关闭后回到原阅读位置。这只是交互假设，不是已经实现的契约。

**正式决定必须说明：** 原生/Web 边界、iOS 基线、书籍 Package 访问、离线行为、导航和位置恢复、选区模型、无障碍、升级/迁移、Secret Storage 与兼容 fixture。

**必须完成的阶段：** 原生移动实现之前。平台提取继续以第二个具有代表性的真实 Use Case 为门槛。

## OQ-019 可迁移用户数据 Package 与同步边界

**问题：** 用户数据的版本化可迁移表示是什么？目标设备已经存在相关数据时，Import 应如何处理？

**已接受方向：** ADR-0004 要求显式 Export/Import 早于自动同步，禁止把覆盖整个数据库作为长期协议，并保持 Cloud Infrastructure 可选。Package 细节和合并策略仍未决定。

**建议起点：** Export 包含 Manifest，以及 Progress、Highlight、Note、Discussion、已接受 Knowledge 和 Attachment 的人类可读或有明确规范的记录。使用稳定 Entity ID，保留兼容的未知字段，验证 Checksum 与 Schema Version，预览冲突，并在 Import 前保存可恢复备份。Provider Credential 不能进入 Export。

**正式决定必须说明：** Package 布局与 Schema、包含/排除数据、Identity 与 Revision 规则、Import 模式、重复/冲突行为、Attachment、完整性与加密、降级/前向兼容、恢复和权利过滤。

**必须完成的阶段：** Export/Import 实现之前。LAN Transfer、LAN Sync、AirDrop/Share Sheet 或 Cloud Replication 只有经过独立的 Transport 与 Threat Model 决议后，才能传输该 Package 或未来 Change Set。

## OQ-020 Dictionary 与 Grammar Source Provider 契约

**问题：** Dictionary 与 Grammar Evidence 应怎样参与 Search、Context Builder、Citation、Licensing、离线打包和 AI Discussion？

**为什么仍未决定：** Dictionary 是正式 Evidence Source，不只是 UI 附件；但目前尚未用真实语言学习书籍验证 Provider Schema、授权策略、Language Pair、Lookup Normalization 或 Citation Contract。

**建议起点：** 定义共享 `SourceProvider` 契约，其结果必须有明确类型、Source Link、Revision、Rights，并且可以独立显示。Dictionary 与 Grammar Provider 负责提供证据；模型可以解释和比较，但不能伪装成字典条目。

**正式决定必须说明：** Provider Identity 与 Version、支持的 Language Pair、Headword/Expression Lookup、Morphology、Sense 与 Example Provenance、离线/Index 规则、授权与 Export 限制、Context Priority、失败行为和评估 fixture。

**必须完成的阶段：** 语言学习原型把 Dictionary 或 Grammar 结果作为持久证据之前。

## OQ-021 Language Learning Domain 与持久知识模型

**问题：** 哪些语言学习 Entity 和 Workflow 属于 Domain Profile？哪些契约经证据证明可以与 Christian Studies 共享？

**为什么仍未决定：** Lexeme、Expression、Collocation、Grammar Pattern、Usage Contrast、Example、Personal Example 与 Mistake 都是合理候选，但在真实英文或德文阅读前设计它们，会重复 Roadmap 想要避免的过早抽象。

**建议起点：** 使用一本具有代表性的英文或德文书，验证从选区、可信查阅、AI 解释、个人造句、审核、保存到再次遇见的完整流程。AI Proposal 与用户已接受 Knowledge 必须分开；只有真实证据支持时才复用 Stable Anchor、Evidence、Provenance 与 Discussion 契约。

**正式决定必须说明：** 第一批知识类型、Stable Identity 与再次遇见记录、Source Sentence/Anchor Link、Personal Example Review、AI Authorship、接受与纠错流程、Cross-language Relation、Portable Export，以及 Study、Language Tutor、Speaking Practice 或 Free Discussion 的哪些 Output 属于 Language Learning Domain。

**必须完成的阶段：** 实现持久语言学习 Knowledge 或通用 Cross-domain Ontology 之前。

## OQ-022 Managed Content 打包、权利与升级隔离

**问题：** 怎样把书籍、圣经、字典、语法资料与其他可信材料内置到个人设备，同时不与可变 User Data 混淆，也不违反权利约束？

**为什么仍未决定：** ADR-0004 允许个人阶段内置权利合适的资料，但 Package 布局、授权记录、升级 Diff、移除行为和 User Data 生存规则仍未规范。

**建议起点：** 每个 Managed Content Package 都有稳定 Identity、Version、Checksum、Provenance、Rights/Visibility Record 和声明的 Index。它的安装或升级与 User Data Store 分离；不能因为 Package 升级或移除就删除用户记录。

**正式决定必须说明：** Package Manifest、Signature/Integrity、Licensing 与 Visibility、Content Version 与 Anchor Migration、内置和用户导入材料的区别、Index Rebuild、应用升级行为、Rollback 与 Orphaned User Data 处理。

**必须完成的阶段：** 在移动 Build 中内置书籍或可信参考资料集合之前。

## OQ-023 Voice Capability、Discussion Profile 与 Session Data

**问题：** 哪些 Speech 职责属于共享 Capability，哪些 Policy 属于 Domain Profile，哪些 Voice Session Output 可以成为持久 User Data 或经过审核的 Knowledge？

**为什么仍未决定：** Word Playback、Sentence Prosody、Expression Practice 与 Book-based Voice Discussion 在延迟、离线、Provider、Privacy、Interaction、Evaluation 与 Retention 方面有不同要求。目前还没有代表性的 Language Learning Book 证明哪些阶段会被重复使用。现在选择 Provider 或 Schema，会把渐进式假设提前变成未经验证的平台承诺。

**建议起点：** 把 Speech Playback、Speech Recognition、Realtime Conversation 与 Practice Session Orchestration 保留在候选 Capability Layer；由 Domain Profile 定义 Study、Language Tutor、Speaking Practice 与 Free Discussion Policy。只实现有证据支持的最小阶段。Transcript、Summary、Feedback、Target-use Record、Practice Signal 与 Session Metadata 应分类保存；Raw Audio 默认只临时存在，Speaking Sample 只有用户明确选择时才保存。

**正式决定必须说明：** 第一 Voice 阶段与 Use Case、本地/外部 Provider Boundary、支持语言、离线降级、延迟与中断行为、Microphone 与 Transmission Consent、Discussion Profile Contract、Transcript Authorship、Output Schema、Retention/Deletion、Portable Export、Accessibility、Evaluation Fixture 与失败恢复。Phoneme-level Scoring 需要单独评估的 Specialized Capability，不能从通用 Voice Support 推断得出。

**必须完成的阶段：** 第一项持久 Voice 功能、保留 Transcript/Audio 或共享 Voice Service 实现之前。第二本代表性书籍与真实使用门槛继续有效。详见[语音能力假设](Voice-Capability-Hypothesis-zh.md)。

## ADR 队列

下列只是候选记录，不是已接受决定或实施权威：

| 候选 ADR 主题 | 触发条件 |
| --- | --- |
| 原生移动应用边界与 Reader 交互 | 第二个代表性 Use Case 与兼容 fixture 完成后解决 OQ-018 |
| 可迁移用户数据 Package、Import 与恢复 | Export/Import 实现前解决 OQ-019 |
| Source Provider Evidence 与信任契约 | Dictionary/Grammar 集成前解决 OQ-020 |
| Language Learning Knowledge 的接受与再次遇见 | 持久语言知识实现前解决 OQ-021 |
| Managed Content 打包与升级隔离 | 移动端内置内容前解决 OQ-022 |
| Voice Capability 边界、Discussion Profile 与 Session Lifecycle | 第一项持久 Voice 功能前解决 OQ-023 |
| 基于 Change 的 LAN 或 Cloud Replication | Export/Import 已工作且真实多设备需求得到验证后 |

## 决议模板

问题得到接受后，在该问题下追加记录，或链接到单独 ADR：

```markdown
### Decision / 决议

- Status / 状态: Accepted
- Date / 日期: YYYY-MM-DD
- Chosen option / 选择方案:
- Rationale / 理由:
- Rejected alternatives / 未选方案:
- Consequences / 后果:
- Migration impact / 迁移影响:
- Security/privacy impact / 安全与隐私影响:
- Documents to update / 需要更新的文档:
- Tests or evaluations required / 所需测试或评估:
```

之后更新优先级表、中英文版本、产品规划、目标架构草案，以及受到决定影响的当前有效规范。
