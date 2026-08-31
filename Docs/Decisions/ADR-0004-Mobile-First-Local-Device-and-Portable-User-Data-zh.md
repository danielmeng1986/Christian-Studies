# ADR-0004：移动优先的本地设备与可迁移用户数据

**状态：** 已接受
**日期：** 2026-08-31
**决策者：** 项目所有者
**相关问题：** OQ-001、OQ-002、OQ-003、OQ-018、OQ-019
**修订：** ADR-0001 的运行方向与首个可分发目标

> Agent 使用的英文主文档：
> [`ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md`](ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md)。

## 背景

当前 Reader 的真实使用表明，长期产品机会不只是桌面端神学阅读应用。Christian Studies 是个人 AI 辅助阅读环境的第一个 Domain Profile；未来它可能服务语言学习和其他深度阅读。iPhone 预计会是最常用的实际阅读设备。

ADR-0001 正确确立了本地优先、单读者产品，也保留了浏览器加 loopback 服务作为当前开发运行方式；但其中“桌面优先的首个可分发产品”已不再符合新的产品优先级。

## 决议

### 产品与运行方向

长期产品方向是一个 **local-first、mobile-first 的个人 AI 辅助阅读环境**。Christian Studies 继续作为第一个真实 Domain，当前《追寻敬虔》Reader 继续作为兼容性基线。

第一个专用设备目标是能够完全本地运行的 iPhone App，核心能力不依赖 Mac Backend。阅读、本地搜索、本地圣经和字典查询、笔记、高亮、历史讨论与已接受知识在离线时仍应可用。只有明确需要联网的能力——例如调用 OpenAI API——才要求网络。

当前浏览器加 loopback 服务继续作为开发与需求发现环境。本决议不授权立即进行原生重写或平台提取。必须先由第二个具有代表性的真实 Use Case 证明哪些契约确实可复用。

### 第一阶段边界

第一阶段个人移动版不要求：

- App Store 发布或公开用户；
- 远程账户或 Google Login；
- Cloud Backend 或托管式 Source of Truth；
- 持续运行的 Mac Server；
- 强制使用 iCloud 同步。

第一阶段只使用一个 Local Profile。未来 Apple、Google 或其他登录方式可以作为 Identity Provider，但不能取代内部稳定的 Profile Identity。

### Secret 边界

用户自行提供 Provider Credential。在 iOS 上只能保存到 Keychain；其他平台必须使用等价且经过批准的 Secret Store。内容文件、普通配置、SQLite 字段、Context Manifest、Discussion、Export、Log 与命令参数都不能包含 Credential。非秘密配置可以记录 Provider 身份和 Credential 是否已经配置。

### Managed Content 与 User Data

第一阶段个人版可以把权利允许的书籍、圣经、字典、语法资料与其他可信资料作为 Managed Content 内置。阅读进度、高亮、笔记、讨论、保存的语言项目、已接受知识和偏好属于可变的用户拥有数据。应用升级不能替换或删除这些用户数据。

第一阶段以设备本地副本作为用户数据权威来源。运行时可以使用本地 SQLite，但长期迁移不能依赖复制不透明的整个数据库文件。第一项迁移能力是带 Manifest、具有明确版本并在可行处保持人类可读记录的显式 Export/Import Package。Export/Import 必须早于自动同步。

持久用户实体应使用稳定身份。未来基于变更的同步协议所需 Revision、Device 与删除元数据，必须在实现该协议前另行规范；本决议不要求立即重写当前用户数据 Schema。

可迁移 Discussion 不只是 Message List。持久记录必须在可获得时保留稳定 Discussion Identity、Book 与 Anchor/Selection Identity、时间、Model Metadata、Messages、Selected-context Reference 与 Evidence Manifest。Title 或 Summary 可以帮助回顾，但不能替代已经记录的 Evidence Provenance；Legacy Record 不能被补上虚构的 Context Metadata。

### Cloud 角色

未来如果引入 Cloud Infrastructure，它可以承担 Transport、Replication 或 Backup，但不能成为个人知识的唯一权威副本。自动同步、LAN Transfer、冲突解决和多设备身份都必须在实施前另有已接受规范。

## 后果

- Mobile Interaction 与窄屏行为成为核心产品关注点，但当前响应式行为仍是唯一已实现基线。
- Desktop Packaging 不再是首个专用设备版本的发布门槛；它仍可作为以后共享可迁移契约的客户端。
- 可迁移用户数据与安全本地 Credential 是第一版移动实现的正式验收领域。
- Export/Import 被有意安排在 Sync 之前，并且必须先通过验证。
- 是否可以内置某项来源仍取决于其权利和可见性元数据；本 ADR 不授予再分发权利。
- 平台与原生 App 实现仍受到真实使用证据、兼容 fixture 和下列开放契约的门槛约束。

## 未选方案

- 正常 iPhone 阅读必须依赖 Mac loopback 服务。
- 以远程账户或 Cloud Database 作为第一阶段用户数据权威来源。
- 从自动同步或覆盖整个 SQLite 文件开始。
- 把 Mobile-first 只理解为缩窄桌面布局。
- 在第二个具有代表性的 Use Case 出现前启动通用平台重写。

## 后续决策与验证

- OQ-018 在实施前定义原生移动交互和应用边界。
- OQ-019 定义可迁移 Export/Import Package、合并行为、恢复和兼容策略。
- Dictionary 与 Language Learning 契约继续作为独立 Open Questions，不能静默加入 Christian Studies Domain Model。
- 兼容性测试必须保持当前 Reader 的阅读、笔记、讨论、Context 和 Evidence Manifest 行为。
- Mobile 验收测试必须覆盖离线使用、升级安全的用户数据、Keychain 隔离、Export/Import 往返和失败恢复。
