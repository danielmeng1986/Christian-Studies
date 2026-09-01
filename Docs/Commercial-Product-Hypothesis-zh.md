# 商业产品假设：以书籍为中心的语言学习

**版本：** 0.1
**状态：** 探索性产品假设——不是 Roadmap 或实施承诺
**范围：** 从共享阅读平台能力中可能形成的语言阅读与口语产品

> Agent 使用的英文主文档：
> [`Commercial-Product-Hypothesis.md`](Commercial-Product-Hypothesis.md)。

## 1. 假设与当前边界

Christian Studies 继续首先作为服务项目所有者的个人阅读与神学研究项目。未来可能从共享 Reading Platform 与 Voice Capability 中形成一个独立产品：

> 面向已经具备一定英语或德语基础、希望通过真实书籍继续提高的学习者的 **AI-assisted Language Reading & Speaking Platform**。

这只是一项产品假设，不是市场已经得到证明，也不授权建设商业基础设施。项目继续坚持 **Build for one real user first**、延迟抽象与延迟商业化。

## 2. 产品判断

候选产品首先不是传统语言课程，其核心是 **Book-centered Learning Loop**：

```text
Read
  ↓
Understand
  ↓
Look Up
  ↓
Listen
  ↓
Save
  ↓
Speak
  ↓
Discuss
  ↓
Review
  ↓
Encounter Again
```

差异化假设是 **Context Continuity**，而不是功能清单。读者从一句话出发，经过可信查阅、单词和句子发音、AI 解释、保存表达、口语练习、章节讨论与经审核个人知识时，不应丢失连接这些行为的 Book、Passage、Source 或 Learning Target。

## 3. Domain 分离

```text
Shared Reading Platform Core
├── Christian Studies
│   └── 个人 / 研究 Domain
└── Language Learning Product
    └── 消费者 / 潜在商业 Domain
```

语言产品不能因为使用同一平台，就包含 Christian Theology Book、Bible-specific Content 或项目所有者的 Personal Christian Studies Knowledge。它只能复用经真实证据证明共享的契约，例如 Reader Behavior、Context Service、Stable Anchoring、Discussion、Source Provider、Knowledge Proposal、Provenance、Portable Data、Mobile Runtime 与 Voice Capability。

Commercial Account、Telemetry、Cloud Storage、Content Licensing 与商业运营不能作为隐藏需求反向进入 Christian Studies Domain。

## 4. 候选 Book Learning Package

未来 Publisher 或 Content Partner 提供的内容可能不只是 EPUB 或 Text File。候选 **Book Learning Package** 可以包含：

```text
Book Learning Package
├── Original Text
├── Language
├── CEFR 与难度 Metadata
├── Chapter Metadata
├── Vocabulary Guidance
├── Grammar Metadata
├── Discussion Prompts
├── Optional Pronunciation Metadata
└── Rights 与 License Metadata
```

平台可以提供 Contextual Explanation、Dictionary Integration、Voice、Vocabulary Tracking、Speaking Practice、Book Discussion、Reviewed Knowledge 与 Adaptive Assistance。Package Metadata 属于带来源链的 Curated Content；AI 生成的增强内容必须保持明确标示并可审阅。

这仍然只是一项假设，不改变当前 Canonical Book Format，也不授权创建新 Schema。任何实现必须受 OQ-015、OQ-020、OQ-022 和未来商业内容决议约束。

## 5. 难度与 CEFR 假设

未来书库可以使用 A1–C2 CEFR 等级帮助发现和 Onboarding，但不应假定一本书只有一个精确难度。难度可能随 Book、Chapter、Passage、Vocabulary 或 Grammar Feature 而变化。`B1+` 之类的标签只是指导，不是精确测量或保证。

Learner Profile 与 Content Difficulty 以后可以帮助系统决定何时主动提供更多帮助、何时减少打断。任何 Adaptive Behavior 都需要透明策略、用户控制和评估，并避免用未经审核的 AI 分类取代 Publisher 或人工判断。

## 6. Onboarding 与初始内容

产品价值实验不应要求新用户先上传 EPUB 才能看到核心体验。候选首次使用流程是：

```text
Choose language
  ↓
Choose level
  ↓
Choose a free book
  ↓
Start reading
```

初始内容可以来自 Public Domain、Self-created Material 或 Explicitly Licensed Content。每一项仍需 Rights、Provenance 与 Distribution Metadata。验证 Dictionary Lookup、Word Pronunciation、Sentence Voice、AI Explanation、Expression Saving 与 Speaking Practice 是否形成有用闭环，不应以先取得 Publisher License 为前提。

## 7. 远期商业可能性

只有在产品价值和权利约束得到更好理解后，才考虑 Licensed Book、Publisher Partnership、Book Sale、Subscription 与 Revenue Sharing。长期假设是 Publisher 提供内容，Platform 提供学习体验。

当前 Roadmap 明确不包含：

- DRM 或 Publisher Portal；
- Payment、Subscription、Sale 或 Revenue Sharing；
- Public Account 或商业 Cloud Infrastructure；
- App Store Commercialization；
- 商业 Analytics、Growth System 或 Support Operation；
- 仅仅为了让假设显得完整而提前开展授权谈判。

## 8. 验证门槛

在认真启动商业产品开发前，项目所有者应使用系统完整读完至少一本英文或德文原版书；最好进一步读完两本不同难度或类型的书。真实使用应形成下列证据：

- 哪些 AI Action 被反复使用；
- 哪些概念上很吸引人的能力很少使用；
- Speaking Practice 能否成为习惯；
- 哪些 Expression 值得保存并再次遇见；
- AI 何时应出现、何时应保持安静；
- 哪种纠错方式可以保持阅读沉浸；
- Voice Session 多长最自然；
- 学习功能是否破坏文学阅读；
- 累积 Knowledge 是否改善以后的阅读和表达。

之后可以通过访谈或范围很小的明确实验继续 Commercial Discovery，但 Account、Payment、Licensing System 或 Cloud Tenancy 都需要新的正式产品决议。项目所有者的真实使用是必要门槛，但不能单独证明市场需求。

## 9. 升级为正式方向的条件

只有满足下列条件，才能把本假设升级为活跃交付阶段：

1. 已完成整本书真实使用门槛；
2. 重复问题与目标学习者已有证据支持；
3. Christian Studies 与 Commercial Domain 的数据边界已经规定；
4. 与实验有关的 Rights、Privacy、Voice、Portable Data 与 Distribution 问题已经解决；
5. 新决议明确分配开发范围，并规定不做什么。

在此之前，本假设只负责保存机会，不与当前真实用户阅读工作争夺优先级。
