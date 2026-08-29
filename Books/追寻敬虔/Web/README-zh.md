# 本地阅读版使用说明

> 中文审核说明。对应的英文执行说明：`README.md`。

## 初次准备

在仓库根目录运行：

```sh
python3 -m venv 'Books/追寻敬虔/Web/.venv'
'Books/追寻敬虔/Web/.venv/bin/python' -m pip install -r 'Books/追寻敬虔/Web/requirements.txt'
```

## 构建与检查

```sh
'Books/追寻敬虔/Web/.venv/bin/python' 'Books/追寻敬虔/Web/scripts/build.py'
'Books/追寻敬虔/Web/.venv/bin/python' -m unittest discover -s 'Books/追寻敬虔/Web/tests'
```

生成文件位于 `Books/追寻敬虔/Web/dist/`，并已设置为不纳入 Git。

## 在本地阅读

```sh
'Books/追寻敬虔/Web/.venv/bin/python' 'Books/追寻敬虔/Web/scripts/serve.py'
```

然后使用 Safari 或 Chrome 打开 `http://127.0.0.1:4173/chapters/01/`。顶部章节菜单可以在全部 20 章之间导航。

当前阅读版会确定性构建全部 20 章，并包含章节导航、三栏阅读布局、窄屏侧栏、三种阅读主题、脚注与经文交互、逐章笔记、“与 AI 讨论”和本地资料库。

正文与右侧研读栏之间的分隔条可以拖动，也可用左右方向键调整，双击会恢复默认宽度。笔记和 AI 讨论分别记忆自己的宽度。进入 AI 讨论时，左侧脚注/经文栏会自动收起；需要参照资料时可由顶部按钮将它以浮层方式打开，而不会重新挤压正文和讨论区。窄屏设备上的两个侧栏均以浮层显示。

本地服务提供逐章笔记数据层：`GET /api/chapters/{chapter}/notes` 读取纳入 Git 的 JSON 数据源，带修订号的 `PUT` 请求负责原子保存。在单个正文块内选择连续文字后，点击“写笔记”，即可在右栏创建、编辑或删除。第一版会拒绝跨块和重叠选区。

在同一正文块内选择文字后，浮层会同时显示“写笔记”和“与 AI 讨论”。选区可以包含经文或脚注链接。讨论以单独 JSON 文件保存在 `Notes/Discussions/<章节>/`，可继续旧讨论，也可在同一选区发起多个新讨论。

发送前会先显示本轮上下文预览：与选区相同或重叠的个人笔记默认纳入，可逐条排除；同段但不重叠的笔记只显示为候选。命中的中英文译名也会显示，精确命中可排除，歧义候选需明确勾选才会发送。本书其他章节的相关段落也会单独列出，可展开、跳转到原段、逐项排除，或选择“查找更多本书内容”。这些选择只影响当前一轮，不会修改或删除原笔记与书稿。

“资料库”标签可添加 Markdown、TXT、JSON 和可提取文字的 PDF。文件先显示转换预览，确认后才保存在 `Sources/` 并建立可重建索引；私密资料默认停用。资料库命中默认不发送，必须先为该资料明确授权外发，再在每轮上下文预览中逐条勾选。移除派生索引不会删除原件或转换稿。

AI 回复以安全的 Markdown 富文本显示，包括标题、列表、引用、强调、链接、代码块和表格。讨论 JSON 仍保存原始 Markdown，不保存派生 HTML；原始 HTML和危险链接协议不会被执行。用户自己的提问保持纯文本显示。

### 安全启动 AI 讨论

阅读器只从服务进程的 `OPENAI_API_KEY` 读取密钥。不要将 Key 写入仓库、`.env`、命令行参数或脚本。当 Key 以“网站密码”保存在 macOS“密码”App 中，可以按可见名称安全启动。当前项目条目名为 `OpenAPI Key`：

```sh
'Books/追寻敬虔/Web/.venv/bin/python' 'Books/追寻敬虔/Web/scripts/serve.py' \
  --keychain-internet-password-label 'OpenAPI Key'
```

阅读器会先按密码条目的标签查找，再尝试按网站字段查找。macOS 可能弹出密钥串访问确认；建议选择本次“允许”，不必选择“始终允许”。读取成功后，Key 只在这一个阅读器服务进程中作为 `OPENAI_API_KEY` 存在，不会出现在 shell 历史或日志中。

如果新版“密码”App 中的网站密码无法被 macOS `security` 命令找到，可以另建一个仅供阅读器使用的“通用密码”。先用非秘密占位值创建条目和限制性访问控制：

```sh
security add-generic-password \
  -a 'qfg-reader' \
  -s 'org.openai.qfg-reader' \
  -l 'OpenAI API Key — 追寻敬虔阅读器' \
  -T '' \
  -U \
  -w 'replace-me'
```

`-T ''` 表示不给任何应用永久免确认访问权。不要使用 `security ... -w` 的交互提示直接粘贴 OpenAI Key：该提示会把超过 128 个字符的输入截断。改用项目提供的安全助手；它会隐藏输入、要求粘贴两次，并在不把 Key 放入命令参数、shell 历史或磁盘的情况下，通过 macOS 钥匙串接口替换并验证完整值：

```sh
'Books/追寻敬虔/Web/.venv/bin/python' \
  'Books/追寻敬虔/Web/scripts/store_openai_key.py'
```

助手只显示 Key 的字符数和末四位，便于和 OpenAI 控制台核对。保存成功后启动阅读器：

```sh
'Books/追寻敬虔/Web/.venv/bin/python' 'Books/追寻敬虔/Web/scripts/serve.py' \
  --keychain-generic-password-service 'org.openai.qfg-reader'
```

未注入 Key 时，阅读和笔记仍可正常使用；只有首次点击“发送”时才会调用 OpenAI。完整规范见 [`AI-DISCUSSION-SPEC-zh.md`](AI-DISCUSSION-SPEC-zh.md)。
