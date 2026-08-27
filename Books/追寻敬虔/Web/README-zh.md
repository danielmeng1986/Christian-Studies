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

然后使用 Safari 或 Chrome 打开 `http://127.0.0.1:4173/chapters/05/`。

当前 MVP 已包含第五章的确定性构建、章节菜单预留、三栏阅读布局、窄屏侧栏、明亮／暗色／护眼三种主题，以及左栏脚注交互。笔记持久化将在后续 Roadmap 阶段实现。
