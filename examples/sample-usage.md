# 示例用法

本目录中的图片由项目脚本自行生成，只用于验证视觉输入、结构化数据、动态 SVG 和离线 HTML 链路。它不是真实小红书封面，也不代表任何流量或销量。

```powershell
python scripts/create_example.py
python scripts/validate_report.py examples/sample-report.json
python scripts/generate_report.py examples/sample-report.json --output examples/sample-report.html
```

向支持图片理解的 Agent 上传 `synthetic-cover.png` 后，可以说：

> 使用爆款封面复刻器，拆解这张图片，生成手机实拍教程和三套差异化原创拍摄方案。
