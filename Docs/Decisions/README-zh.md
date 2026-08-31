# 架构决议记录

[English index](README.md)

本目录保存影响多个 Christian Studies 规范，或需要长期保留决策理由的已接受决定。

英文 ADR 是 Agent 使用的决议主文档，每份 ADR 都有完整中文审阅版。修改决议时，必须在同一次修改中同步两个语言版本，以及所有受影响的当前规范和规划文档。

| ADR | 决议 | 状态 | 相关问题 |
| --- | --- | --- | --- |
| [ADR-0001 中文](ADR-0001-Product-Deployment-and-Distribution-zh.md) / [English](ADR-0001-Product-Deployment-and-Distribution.md) | 产品边界、原运行方向与分发阶段（由 ADR-0004 修订） | 已接受 | OQ-001–OQ-003 |
| [ADR-0002 中文](ADR-0002-Data-Authority-and-Database-Roles-zh.md) / [English](ADR-0002-Data-Authority-and-Database-Roles.md) | 数据权威、Git 策略与数据库角色 | 已接受 | OQ-003、OQ-006、OQ-014 |
| [ADR-0003 中文](ADR-0003-Stable-Block-Anchoring-zh.md) / [English](ADR-0003-Stable-Block-Anchoring.md) | 稳定块身份与精确选区 | 已接受 | OQ-008 |
| [ADR-0004 中文](ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data-zh.md) / [English](ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md) | 移动优先的本地设备与可迁移用户数据 | 已接受 | OQ-001–OQ-003、OQ-018–OQ-019 |

已接受 ADR 记录的是方向，不表示迁移或实现已经发生。在核心规范被有计划地修订之前，当前运行行为继续由现有核心规范管理。

ADR-0004 只修订 ADR-0001 中把桌面应用指定为首个专用设备目标的部分。ADR-0001 的本地优先、单读者边界，当前浏览器/loopback 开发运行方式，以及延后的公开版与协作版阶段继续有效。
