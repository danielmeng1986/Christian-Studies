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

当前阅读版会确定性构建全部 20 章，并包含章节导航、三栏阅读布局、窄屏侧栏、明亮／暗色／护眼三种主题、左栏脚注与经文交互，以及逐章保存的笔记闭环。右栏默认显示最近更新的三条笔记，可展开全部或再次收起。

本地服务提供逐章笔记数据层：`GET /api/chapters/{chapter}/notes` 读取纳入 Git 的 JSON 数据源，带修订号的 `PUT` 请求负责原子保存。在单个正文块内选择连续文字后，点击“写笔记”，即可在右栏创建、编辑或删除。第一版会拒绝跨块和重叠选区。
