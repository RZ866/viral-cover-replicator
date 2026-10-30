# 爆款封面复刻器

版本 1.0.0。一个面向商品摄影新手的多模态 Agent Skill：上传参考封面后，由宿主 AI 拆解构图、机位、光线、背景与道具，生成低成本手机实拍教程、动态布景图、拍摄纠偏和三套原创重构方案。

## 功能亮点

- 封面摄影拆解：明确区分可观察事实、合理推测、建议参数和未知信息。
- 实拍复刻：准备清单、十步搭建、手机参数、布景与布光 SVG、拍摄 SOP。
- 多轮纠偏：参考图与实拍图比较，每轮只处理影响最大的三个问题。
- 差异化原创：低成本、场景重构和深度原创三条不同路线。
- 原创成片诊断：同时检查摄影质量与视觉差异，不冒充平台原创审核。
- 离线报告：单文件 HTML、18 个章节、移动端、打印和安全转义。

适合小红书和抖音电商商家、手机摄影新手及内容运营。静物商品是重点，同时可分析人物、风景、美食和生活方式照片。

## 完整流程

```text
上传参考图 → 摄影拆解 → 实拍教程 → 上传第一轮实拍 → 三项纠偏
→ 最多三轮调整 → 三套原创方案 → 上传原创成片 → 原创诊断 → HTML 报告
```

需要拍摄的节点会暂停等待图片，不会在用户未拍摄时假装完成纠偏。

## 安装

支持 `skills` 命令的 Agent 可以直接从 GitHub 安装：

```bash
npx skills add https://github.com/RZ866/viral-cover-replicator
```

在支持自主安装 Skill 的 Codex、WorkBuddy 等工具中，也可以直接说：

```text
帮我安装这个 Skill：https://github.com/RZ866/viral-cover-replicator
```

把整个目录复制到 `~/.codex/skills/viral-cover-replicator`。不要只复制 `SKILL.md`；保留 `references`、`schemas`、`scripts` 和 `assets`。重新开始一轮 Codex 对话后即可发现。

其他支持 `SKILL.md` 的 Agent 可导入完整目录。图片理解、文件执行和报告预览取决于宿主环境。

## 使用示例

```text
使用爆款封面复刻器，拆解我上传的这张图片，生成手机实拍教程和三套差异化原创拍摄方案。
```

```text
对比这张参考图和我的实拍图，告诉我下一轮最应该调整的三个地方。
```

```text
参考这张封面的摄影方法，帮我重新设计三套中度创新的原创商品封面拍摄方案。
```

支持 JPG、JPEG、PNG、WebP 和常见截图。默认手机、低预算、自然光、家庭或办公室环境，不需要 API Key、平台登录或 Cookie。

## 开发者运行

仅需 Python 3.10+ 标准库：

```text
python scripts/validate_report.py examples/sample-report.json
python scripts/generate_report.py examples/sample-report.json --output examples/sample-report.html
python -m unittest discover -s tests -v
```

报告生成脚本不负责识图。宿主 AI 先把真实视觉观察写入 JSON，脚本再验证与渲染。示例 JSON 是结构与渲染测试数据，不代表真实视觉识别测试。

## 报告、限制与隐私

生成的 HTML 为单文件，CSS 和 SVG 全部内联；本地图片经过类型、大小和目录检查后嵌入 data URI。无远程脚本、CDN、分析代码或自动上传，可离线打开、打印或另存 PDF。

单图无法准确还原真实焦距、距离、设备和灯光功率。视觉理解依赖宿主模型；宿主读不到图片时必须停止视觉结论。多轮记录依赖本地 JSON。项目不推断曝光、点击、销量，不保证平台审核或原创判定。用户图片只在本机读取。

## 许可与版本

代码与原创文档采用 MIT 许可证。运行时只使用 Python 标准库，没有捆绑第三方素材。版本变化见 [CHANGELOG.md](CHANGELOG.md)。
