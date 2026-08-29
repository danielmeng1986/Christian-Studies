# 《追寻敬虔》AI ContextBuilder 开发交接说明

状态：M4 完成后的交接基线
日期：2026-08-29  
下一阶段：M5——预览、预算与可追溯闭环
Roadmap：[`AI-CONTEXT-ROADMAP-zh.md`](AI-CONTEXT-ROADMAP-zh.md)  
产品规范：[`AI-CONTEXT-SPEC-zh.md`](AI-CONTEXT-SPEC-zh.md)  
AI 执行合同：[`AI-CONTEXT-SPEC.md`](AI-CONTEXT-SPEC.md)

## 1. 当前完成状态

- M0 已完成：payload、安全边界、prompt 和现有讨论行为已有脱敏回归基线。
- M1 已完成：`ContextBuilder` 已独立，书籍身份从 `Metadata/book.yml` 读取。
- M2 已完成：标题路径、选中 block、前后正文 block 和服务器端锚点验证已经进入 context envelope。
- M3 已完成：相关个人笔记和译名身份命中已进入 envelope/manifest，发送前可预览并做本轮排除或候选确认。
- M4 已完成：20 章及其脚注关系已进入确定性跨章节检索，命中可预览、展开、跳转、扩展和逐项排除。
- 当前讨论继续使用 OpenAI Responses API、`store: false`、`truncation: disabled` 和流式输出。
- 当前 `promptVersion` 为 2；版本 1 的讨论仍可读取，并在下一次继续讨论时升级。
- 当前 `contextSchemaVersion` 与 `sourceRegistryVersion` 为 1，`retrievalVersion` 为 2。

## 2. 关键代码位置

| 文件 | 职责 |
| --- | --- |
| `Web/scripts/context_builder.py` | `ContextRequest`、`ContextBundle`、书籍元数据、block map、reading focus、envelope、manifest、preview、估算 |
| `Web/scripts/context_retrieval.py` | 20 章/脚注检索单元、确定性查询词、来源感知排序、数量限制和定位 |
| `Web/scripts/discussions.py` | 讨论 schema、消息状态、prompt adapter、Responses API 客户端和流式解析 |
| `Web/scripts/serve.py` | 本地 HTTP API、文件持久化、权限与请求编排 |
| `Web/scripts/build.py` | Markdown → HTML；`data-block-id` 的权威生成规则 |
| `Web/src/assets/app.js` | 浏览器选区、UI 标题路径摘要、笔记与讨论交互 |
| `Web/tests/test_context_builder.py` | ContextBuilder、block map、UTF-16、章节边界和链接投影测试 |
| `Web/tests/test_discussions.py` | payload、prompt、安全、旧讨论兼容和错误映射测试 |
| `Web/tests/fixtures/` | 纯虚构、脱敏的上下文与评估 fixture |

## 3. 当前请求路径

```text
Browser selection
  → POST discussion API
  → validated discussion document
  → ContextRequest.from_discussion(...)
  → ContextBuilder.build(...)
  → ContextBundle.envelope
  → discussions.build_response_input(...)
  → OpenAI Responses API
```

`ContextBuilder` 必须保持：

- 不调用 OpenAI；
- 默认不联网；
- 不写书稿、笔记或讨论文件；
- 相同输入产生相同结果；
- 不在锚点失效时自动选择“相似段落”；
- 任何新增资料都带来源类型、ID、locator 和 revision/hash。

## 4. M2 的 block 与选区语义

- block ID 必须与 `build.py` 一致：标题和段落按 Markdown token 顺序共享递增编号。
- 当前 HTML 只给 heading 和 paragraph 分配 block ID；引用与列表中的段落仍是 `p` block。
- 浏览器选区偏移是 UTF-16 code units；Python 端不得按 Unicode code point 直接切片。
- 普通链接和经文链接的可见文字属于选区投影。
- 脚注链接的可见标号不属于 canonical selection text。
- `previousBlock` / `nextBlock` 指前后非空 paragraph；标题本身被选中时仍使用相邻 paragraph。
- 章节、block、exact、prefix 或 suffix 不匹配时抛出 `ContextBuildError`；流式客户端映射为 `context_invalid`。

## 5. M3 的完成实现

M3 按“确定性证据 → payload/API → 最小预览”完成，没有升级讨论持久化 schema。

### 5.1 个人笔记

1. 通过服务器显式提供的只读 note source 读取当前章节笔记，不能让 `ContextBuilder` 猜测全局路径。
2. 复用现有 anchor 与 UTF-16 语义，实现：
   - `exact`：同 block、相同起止偏移与 exact；
   - `overlap`：同 block 且范围相交；
   - `sameBlock`：同 block 但不相交。
3. 默认纳入 `exact` 与 `overlap`；`sameBlock` 只作为候选，不默认发送。
4. 每条证据标记 `evidenceType: user_note`、relation、note ID、body、sourceRevision、updatedAt。
5. envelope 写入 `personalStudy.notes`；manifest 写入实际纳入的 `noteIds`。
6. M3 的简化 UI 预览应列出相关笔记并允许单条排除；排除只影响该轮，不得删除或修改笔记。

### 5.2 译名解析

1. 只读加载 `References/追寻敬虔译名对照表.json`。
2. 检索输入至少包括 selection、current question、heading path；必要时才加入 neighboring paragraphs。
3. 支持 Unicode/空白/大小写、`Owen, John` 与 `John Owen` 的检索形式。
4. 输出 `exact`、`alias` 或 `candidate`，并保留原字符串、索引形式和 `sourceLine`。
5. 多候选不得静默合并；低置信度候选不得默认进入 AI 请求。
6. 命中写入 `referenceResolution.entities`；manifest 写入实际使用的 `translationSourceLines`。
7. developer instructions 已明确：译名命中只解决身份，不能证明人物观点。

## 6. M4 的完成实现

1. 第一版采用纯内存确定性检索，不建立 SQLite 文件。20 章规模下重建开销可控，也避免索引同步和新增持久化状态；以后若资料库规模扩大，可在相同检索单元合同下替换候选生成后端。
2. 检索文档复用 `build_block_map` 的 block ID 与可见文字投影，并额外保留 chapter title、heading path、source revision、经文 ID、相关脚注 ID、脚注正文与脚注修订哈希。
3. 排序信号依次覆盖精确人物/别名、明确著作或引用短语、相同经文、特征性短语、问题主题词；标题路径命中获得加权。只有满足至少一个强确定性信号的候选才进入结果。
4. 当前章节整体从“本书其他章节”结果中排除；默认 5 段，用户选择扩展后最多 10 段，每章最多 2 段。
5. passage ID 采用 `qfg:{chapterId}:{blockId}`，每项同时携带 source revision；HTML block 现在具有同名 `id`，预览可直接跳转。
6. 预览中的排除、扩展数量都属于本轮瞬时请求字段。M4 没有升级讨论 schema，也没有提前实现 M5 的正式 freeze 或逐轮 manifest 持久化。

固定评估位于 `Web/tests/fixtures/cross-chapter-retrieval-cases.json`，覆盖人物、著作/主题、经文和无结果查询。当前指标：Precision@5 84.88%，无结果正确率 100%，重复率 0%，定位有效率 100%。

## 7. M5 开始前需要做的设计决定

- 预览结果如何以短期构建标识冻结，并在发送时验证所有跨章节 source revision 没有变化。
- 逐轮 manifest 与可选可变证据快照如何进入 discussion schema 2，同时保持 schema 1 的只读与继续讨论兼容。
- 字符估算何时替换为实际 tokenizer 或保守 token 估算，以及超限时的交互顺序。
- 如何自动验证预览、最终 manifest 与 Responses API payload 三者一致，而不把完整章节重复持久化。

## 8. 用户数据保护

以下当前 Git 改动属于用户的真实阅读数据，不是待清理的开发产物：

- `Books/追寻敬虔/Notes/Annotations/05.json`
- `Books/追寻敬虔/Notes/Discussions/`

要求：

- 不修改、格式化、迁移、删除、暂存或提交这些文件；
- 自动测试只使用 `TemporaryDirectory` 和 `Web/tests/fixtures/`；
- 可以进行只读兼容审计，但不得在输出中显示选区、问题、回答或笔记正文；
- 若未来需要真实 schema 迁移，必须先提供 dry run、备份策略和用户确认。

## 9. 验证命令

使用项目虚拟环境：

```sh
'Books/追寻敬虔/Web/.venv/bin/python' -m unittest \
  'Books/追寻敬虔/Web/tests/test_context_builder.py' \
  'Books/追寻敬虔/Web/tests/test_discussions.py'

'Books/追寻敬虔/Web/.venv/bin/python' -m unittest discover \
  -s 'Books/追寻敬虔/Web/tests' -p 'test_*.py'

'Books/追寻敬虔/Web/.venv/bin/python' \
  'Books/追寻敬虔/Web/scripts/build.py'

node --check 'Books/追寻敬虔/Web/src/assets/app.js'
node --check 'Books/追寻敬虔/Web/dist/assets/app.js'
```

完整测试需要绑定临时 `127.0.0.1` 端口。M4 完成时：

- 聚焦检索与上下文测试 32 项通过；
- 全套测试 56 项通过；
- 20 章构建成功；
- 当前 3 个真实讨论通过只读锚点兼容审计。

## 10. 推荐给下一任务的起始提示

```text
继续《追寻敬虔》AI ContextBuilder Roadmap，实施 M5：预览、预算、冻结和 manifest 闭环。
先完整阅读 Web/AI-CONTEXT-HANDOFF-zh.md、AI-CONTEXT-ROADMAP-zh.md、
AI-CONTEXT-SPEC-zh.md 和 AI-CONTEXT-SPEC.md。严格保护真实的 05.json 与
Notes/Discussions/，测试只用临时目录和脱敏 fixture。先设计短期预览构建标识与
discussion schema 2 的逐轮 manifest，再实现发送时重新验证和冻结、预算超限交互、
preview/manifest/payload 一致性测试以及 schema 1 的显式兼容，最后运行全套测试并更新 Roadmap 状态。
```
