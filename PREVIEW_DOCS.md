# 文档预览

仓库内的 Markdown 文档可以直接在 GitHub 打开。要预览 MkDocs 网站，在仓库根目录运行：

```bash
pip install mkdocs mkdocs-material
mkdocs build --strict
mkdocs serve
```

浏览器打开 `http://127.0.0.1:8000`。导航由 `mkdocs.yml` 控制，包含方法、安装、输入、工作流、示例和 API 等内容。

修改后检查页面、链接和示例，按[文档维护说明](docs/BUILDING.md)验证。
构建成功只说明文档可以生成，不代表运行了配准实验或复现了论文指标。

GitHub Pages 的配置目标为 `https://czhu.github.io/space-map`。只有工作流发布成功并完成仓库 Pages 配置后，地址才可访问；请以[Actions 状态](https://github.com/czhu/space-map/actions)为准。
