# Christian Studies

> 一个建立在透明、可控 Context 之上的 AI 辅助阅读环境。

[English README](README.md)

Christian Studies 最初只是一个使用 Git 管理的基督教书籍阅读笔记库，用来保存阅读过程中产生的想法与记录。第一本书是巴刻的《追寻敬虔》。它的原始材料是一份旧版 Word 书稿，持续阅读时不便导航，也不便围绕原文做细致笔记，于是项目首先把书稿规范化为 Markdown。Markdown 改善了阅读和版本管理；随后，确定性生成的 HTML 阅读器补上了纯 Markdown 无法提供的交互能力。

项目现在可以直接选中文字写笔记、就地查看脚注和经文，并围绕当前段落与 AI 讨论。它最重要的成果并不是接入了某一个模型，而是通过可追溯来源的 `ContextBuilder`，自行控制究竟把哪些证据交给模型。实际使用表明，即使不联网，只要本地 Context 选择准确、层次清楚，AI 的回答也可以更加准确、聚焦且实用。

因此，这个项目正在从单本书阅读器发展为一个 **AI-assisted Reading Environment（AI 辅助阅读环境）**。Christian Studies 是第一个真实 Domain Profile；Language Learning 是最重要的候选第二 Use Case。

## 当前能力

目前可工作的《追寻敬虔》阅读器已经具备：

- 从经过审核的 Markdown 确定性生成全部 20 章；
- 章节导航和响应式阅读布局；
- 可交互的脚注与经文；
- 纳入 Git、带修订检查的文本注释；
- 可持久化的 AI 讨论；
- 用户可见、可回溯来源的 Context 预览；
- 跨章节检索和人物译名解析；
- 需要明确授权、索引可重建的本地补充资料库；
- 在本地提供服务，并确保 API 凭证不进入浏览器或仓库。

具体实现与启动方法见
[`Books/追寻敬虔/Web` 使用说明](Books/追寻敬虔/Web/README-zh.md)。

## 产品方向

未来的平台将逐步覆盖完整的书籍研读生命周期：

```text
导入原始书籍
    ↓
保存原件并规范化为经过审核的 Markdown
    ↓
验证并构建交互式阅读版本
    ↓
阅读、写笔记，并与掌握明确来源的 AI 讨论
    ↓
形成经过人审、可以跨书复用的结构化知识
```

未来 Reading Core 可以负责导入、转换、验证、索引、Context 组装、分类明确的 Source Provider、模型编排，以及受控的 MCP 或技能调用。Domain Profile 使 Christian Studies 与未来 Language Learning 行为保持分离。只有第二个代表性真实 Use Case 证明契约共享后，才进行这些边界的提取。

已经接受的第一版产品边界是本地优先、单读者。开发与需求发现继续使用浏览器加 loopback 本地服务；首个专用设备目标是能够独立运行的 iPhone App，桌面端作为以后可能的客户端。Local-first 表示当前设备拥有核心阅读能力和权威个人数据，而不是 Mac Server 必须持续运行。Export/Import 早于 Sync，Cloud 只作为可选 Infrastructure，不是个人知识的所有者。

这是目标方向，不是当前已经生效的架构。大规模重构必须经过正式决议、兼容 fixture、版本化契约和迁移计划。

## 核心原则

- 保存原始材料及其来源链。
- 在未来决议明确改变这一规则之前，经过审核的 Markdown 始终是规范化阅读正文的权威来源。
- 生成的 HTML 和索引都是可丢弃、可重建的产物。
- 笔记和讨论属于用户数据。
- AI Context 必须可见、分类明确、可回溯来源并感知修订版本。
- 优先通过改进证据选择提高回答质量，再考虑增加模型成本和复杂度。
- 模型提供商、MCP 工具和技能必须位于明确的能力与授权边界之后。
- 采用渐进式重构，并在迁移期间保持当前阅读器可用。
- 保持设备本地 User Data 可迁移，并把 Provider Credential 隔离在经过批准的 Secret Storage 中。
- 只有第二个真实 Use Case 证明契约共享后才进行通用化。

## 文档入口

- [`AGENTS.md`](AGENTS.md)：Agent 必读的工作入口。
- [`Docs/README.md`](Docs/README.md)：权威文档导航。
- [`Docs/Product-Plan-zh.md`](Docs/Product-Plan-zh.md)：产品阶段与重构计划
  （[English](Docs/Product-Plan.md)）。
- [`Docs/Platform-Architecture-Proposal-zh.md`](Docs/Platform-Architecture-Proposal-zh.md)：目标平台架构草案
  （[English](Docs/Platform-Architecture-Proposal.md)）。
- [`Docs/Open-Questions-zh.md`](Docs/Open-Questions-zh.md)：大规模重构前需要共同决定的问题
  （[English](Docs/Open-Questions.md)）。
- [`Docs/Decisions/README-zh.md`](Docs/Decisions/README-zh.md)：已经接受的架构决议。

当前有效架构仍由 `Docs/` 中的规范定义。目标架构草案本身不授权任何实现修改。

## 项目状态

单本书环境已经可以工作，并经过了真实阅读使用。当前阶段是继续阅读《追寻敬虔》、记录问题，并在问题形成明确主题后批量处理。必须先真正使用一本具有代表性的英文或德文第二本书，才能宣称共享契约或启动 Platform Extraction。原生移动、Portable Data、Dictionary/Grammar Source Provider、Language Knowledge 与 Managed Content 细节继续作为有门槛的决策，而不是当前重写任务。
