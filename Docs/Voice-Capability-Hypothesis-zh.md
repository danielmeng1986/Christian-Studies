# 语音能力假设

**版本：** 0.1
**状态：** 未来能力假设——不构成实施授权
**范围：** 围绕阅读的语音播放、语音识别、实时对话与语言练习 Session

> Agent 使用的英文主文档：
> [`Voice-Capability-Hypothesis.md`](Voice-Capability-Hypothesis.md)。

## 1. 目的与效力

本文记录一个可能把个人 AI 辅助阅读环境扩展为 **AI 辅助阅读与语言练习环境** 的方向。它保存产品意图、渐进实验、数据边界和未决问题，不授权选择提供商、Schema、移动框架、音频流水线或实施阶段。

Voice 不是 Text-to-Speech 的同义词。长期假设是：阅读、可信查阅、聆听、主动回忆、口语运用和围绕书籍的讨论可以形成一个连续学习闭环。

任何实现仍以代表性的英文或德文真实阅读 Use Case、相关 Open Question、兼容 fixture，以及在引入持久 Schema 或共享 Service 前通过正式决议为门槛。

## 2. 渐进式能力方向

| 阶段 | 读者的问题 | 候选成果 |
| --- | --- | --- |
| Voice 1 | 这个词是什么意思、怎么读？ | Dictionary Evidence、IPA/发音资料与标准发音播放 |
| Voice 2 | 这句话自然读出来是什么样？ | 自然、慢速或强调版播放，以及可选 Prosody 指导 |
| Voice 3 | 我能否主动使用这个表达？ | 围绕已保存目标进行简短情境口语练习 |
| Voice 4 | 我能否用目标语言讨论这本书？ | 围绕段落、章节、人物或论证进行有 Context 的语音讨论 |

这些阶段是证据门槛，不是一次完成整个系统的承诺。Language Learning Use Case 启动后，应先验证最小有用阶段；只有重复使用证明价值，才继续后续阶段。

### 2.1 Voice 1——单词发音

选择单词后可以组合显示：

- 可信 Dictionary 定义；
- IPA 或其他由 Provider 提供的发音信息；
- 来自合法录音或语音提供商的可播放发音。

Dictionary Evidence 与生成语音必须保持不同来源类型。在权利允许时，可以优先采用由 Dictionary 提供的真人录音；AI/TTS 始终是生成能力，不能冒充权威字典记录。

### 2.2 Voice 2——句子发音与 Prosody

选中的句子可以使用自然速度、较慢学习速度或刻意强调方式播放。可选指导可以说明句子重音、弱读、连读、停顿、语调与节奏。

生成音频和生成的 Prosody 解释都必须明确标示。本阶段的目标是帮助学习者理解自然语音为何如此表达，而不只是为文字生成声音。

### 2.3 Voice 3——词汇与表达练习

已保存的 Word、Expression、Collocation 或 Grammar Pattern 可以启动简短语音情景，引导学习者自然使用目标表达。优先交互是一小轮对话结束后集中反馈，而不是每句话都立刻打断纠正。

目标是能够在 Context 中主动调取并恰当使用表达，而不只是回忆定义或完成孤立造句。

### 2.4 Voice 4——围绕书籍的语音讨论

较成熟的学习者可以使用目标语言讨论当前 Passage、Chapter、Character 或 Argument。Context Service 可以组装 Book、当前阅读位置、相关前文、选定笔记、已接受语言知识，以及符合资格的 Source Provider Evidence。

此时语言逐渐成为讨论书籍内容的媒介，而不只是翻译或语法练习的对象。

## 3. Discussion Profile

Discussion 可以继续作为共享概念，但策略与评估目标根据 Profile 区分：

| Profile | 主要目标 | 典型关注点 |
| --- | --- | --- |
| Study | 理解内容 | 观点、推理、原文、证据与 Cross-reference |
| Language Tutor | 在讨论内容时改善语言 | Vocabulary、Grammar、Collocation、Naturalness 与 Register |
| Speaking Practice | 重复主动使用选定目标 | Fluency、主动调取、Target Expression 与延迟反馈 |
| Free Discussion | 保持自然的目标语言交流 | 交流连续性，以及较少的主动干预 |

这些 Profile 可以共享 Book Identity、Stable Anchor、Context Service、Model Provider 与 Source Provider，但不能静默共享 Prompt Policy、评估标准、纠错风格或 Session Output。准确 Profile 契约继续由 OQ-021 与 OQ-023 决定。

## 4. Voice Session 作为 Learning Event

一次完成的 Session 可以产生彼此分类清楚的记录：

- 完整或明确经过编辑/压缩的 Transcript；
- 以内容为中心的 Discussion Summary；
- 带例子和不确定性说明的 Language Feedback；
- Target Expression 使用结果；
- AI 对 Expression、Grammar Point 或重复错误提出的建议；
- Future-practice Signal；
- Language、Profile、Duration、Context Reference、Model/Provider 与 Consent State 等 Session Metadata。

Language Feedback 应区分使用得好的内容、带原表达与改进表达的具体问题，以及哪些 Target Expression 已经或尚未主动使用。对不确定或仅属风格偏好的判断，应保留不确定性，不能全部表述成语言错误。

这些记录具有不同作者身份和权威级别。Transcript 不自动成为经过验证的 Source Text；Feedback 和 Summary 属于 AI-generated Material。知识建议只有在用户接受或编辑后，才能成为持久的已接受 Knowledge，从而保持现有 Human-reviewed Knowledge 边界。

Future-practice Signal 可以记录已经成功主动使用、尚未使用、重复出现的错误，以及以后值得再次练习的目标。其 Schema、Retention 与 Export 行为必须在持久化前决定。

## 5. 音频保留与隐私假设

Raw Audio 默认应是临时数据。长期价值预计主要来自 Transcript、Summary、Feedback、已接受 Knowledge、Usage Record 与 Session Metadata。用户可以明确选择保存一个命名的 **Speaking Sample** 用于纵向比较；这类音频属于敏感的 User-owned Data，必须有明确的保留、删除、Export 与 Provider Transmission 规则。

麦克风采集、转写、语音生成和实时对话可能跨越不同的本地或外部 Provider Boundary。需要授权时，UI 必须在采集或发送前让用户理解当前边界和外发材料。Credential 继续只进入批准的 Secret Storage，绝不能进入音频、Transcript、Manifest 或 Export。

## 6. Capability 与 Domain 边界

候选共享 Capability Layer 包含：

```text
Capabilities
├── Speech Playback
├── Speech Recognition
├── Realtime Conversation
└── Practice Session
```

Domain Profile 决定如何使用这些能力。Language Learning 可以配置 Target Expression、Feedback Policy 和 Practice Goal；Christian Studies 以后可以使用段落朗读、语音提问或散步时继续讨论。任何 Domain 都不能因为最先使用某项能力，就自动拥有通用语音 Transport 或 Provider Adapter。

这种分离仍然是目标假设，并不证明四项能力都应进入 Shared Core。只有两个真实 Workflow 证明存在稳定契约后，某项职责才能进入共享架构。

## 7. 专门发音评估

自然对话、一般发音建议、Fluency Feedback 与语言表达反馈可能适合通用 Voice Model。Phoneme-level Assessment、声学测量、严格评分和语言实验室级诊断属于另一项 Specialized Capability。

第一批 Voice 阶段不能暗示通用 Speech 或 Realtime Model 能够可靠给出量化音素分数。此类评估在提供前必须有独立 Provider Evaluation、Ground-truth Fixture、错误策略和明确的用户限制说明。

## 8. 证据与决策门槛

第一项持久 Voice 实现开始前：

1. 真正使用一本具有代表性的英文或德文书；
2. 找到最小且重复出现的 Voice 需求，而不是一次实现四个阶段；
3. 解决 OQ-020、OQ-021 与 OQ-023 中相关部分；
4. 规定 Capture、Provider Transmission、Retention、Deletion、Export 与 Recovery 行为；
5. 定义兼容性和评估 Fixture，包括 Accessibility 与失败行为；
6. 如果实验改变共享架构或持久数据权威，通过 ADR 或范围明确的实施规范正式接受。

在这些门槛完成前，Voice 只是已记录的未来能力。它不能挤占当前真实阅读、第二本书证据门槛、Portable User Data 或工作中的 Reader 基线。
