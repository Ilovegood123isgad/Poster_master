# 变更日志

[English](CHANGELOG_EN.md) · 中文为准，英文版为镜像。

版本遵循语义化：破坏性变更升 major，新增能力升 minor，修复升 patch。
技能包版本的真源是 `skills/poster-master/SKILL.md` 的 `metadata.version`；
`.claude-plugin/marketplace.json` 与压缩包文件名必须与它一致，`tools/check_links.py` 会强制校验。

## v1.1.0 — 2026-11-05

这一版的主题是**让交付件可信**。v1.0.0 能产出文件，但其中一个分层 PSD 实际上是不可用的，
而交付检查把它判成了通过。以下每一条都配了自动化验证。

### 修复

- **分层 PSD 现在真的能用。** 三个独立缺陷：
  - 图层记录里的通道数据长度少算 2 字节（未包含压缩方式字段），导致 `psd-tools` 直接拒绝
    打开、Photoshop 层序错乱。改为按规范写入。
  - 图层记录顺序颠倒。PSD 的记录是自下而上，旧实现又反转了一次，于是背景跑到最前。
  - 每层都画了不透明背景，上层把下层全部遮住；以及图层名按 latin-1 编码，中文全部变成 `?`。
    现在图层透明、中文名走 `luni` 块。
- **PSD 写入改为 RLE 压缩**：A3 十层从 730 MB 降到三十几 MB，并支持任意层数与真正的图层组。
- **PSD 带上 dpi**：写入 ResolutionInfo 资源，不再一律 72 dpi。
- **交付检查不再给坏文件放行**：新增 `scripts/check_psd.py`，用 `psd-tools` 读回文件、校验
  通道、层名、dpi 与合成结果。坏的 PSD 现在会失败，而不是被报告为"可读取"。
- **PNG 写出 dpi**（`pHYs`），并在检查里核对声明值。
- **二维码检测假阳性**：检测框覆盖画面三分之一以上时不再判为二维码。
- **无头渲染器**：支持 100–900 字重（按字重选字体文件，不再只有常规/粗体）、按元素分块超采样
  （A3 不再需要 600 MB 内存）、绘制 `h=0` 的横线、支持文字旋转与缩放、修正居中框被超采样
  倍数二次放大的问题、`--dpi` 写入。
- **编辑器打开即崩**：`app.js` 访问了未映射的 `zoomIn/zoomOut/zoomFit` DOM，脚本中断，
  页面白屏、所有导出不可达。已修复。
- **服务器找不到 Python 就静默失败**：现在按 `POSTER_EDITOR_PYTHON` → `python3` → `python` → `py`
  依次探测，带超时和可读错误。
- `scripts/README.md` 里 23 处 `[[BT]]` 占位符已清除。
- `deliver.md` 里的 `export_psd.py --project` 命令与实际参数不符，已改为真实用法。
- `quick_validate.py` 现在真的存在（此前被 5 处文档引用但文件缺失）。

### 新增

- **生图通路，用你自己的密钥。** `setup_imagegen.py` 引导填写 `base_url` / `api_key` / `model`，
  密钥存在 `~/.poster-master/imagegen.json`，不进项目、不打印、不回显；
  `--test` 用 `GET /models` 验连通性且不消耗额度；`generate_artwork.py` 生成并写出含模型与
  提示词的 sidecar 记录。技能包本身不含任何密钥。
- `scripts/export_svg.py`：把文字转成轮廓的 SVG 导出（此前 SVG 只在浏览器里生成，服务端没有）。
- `references/capability-boundaries.md`：能做什么、不能做什么、交付说明该怎么写。
- `references/image-generation.md`：什么时候该生成、提示词结构、尺寸与边界、验收清单。
- `references/psd-layer-spec.md`：分层 PSD 的契约、粒度选择、分组如何改变层序。
- `references/formats-and-sizes.md` 增加像素配方表（A3@300dpi = 3508×4961、出血、安全区）。
- 编辑器导出菜单新增 PNG 3×、分层粒度（按组 / 按单个组件）与 dpi 输入。
- 编辑器从"独立路由"降级为"工具"：创建海报时也能用，且每一步都有命令行等价物。
- `requirements.txt` 增加 `fonttools` 与 `psd-tools`。

### 变更

- `SKILL.md` 的交付红线从 6 条扩到 8 条，新增"PSD 必须验证"与"声明能力边界"。
- 依赖说明拆分：编辑器零依赖不变；PSD 验证现在依赖 `psd-tools`，这是有意的。

### 已知限制

- CMYK 转换、出血、打样仍是移交项，工具链不做（见 `capability-boundaries.md`）。
- PSD 图层是栅格，文字不可回改；需要改字请交付 `.poster.json`。
- 编辑器界面只做了功能增强，未做视觉重设计。

## v1.0.0 — 2026-11-05

首次发布：六阶段工作流、四条路由、12 篇参考、10 份模板、零依赖本地编辑器、
PNG / SVG / PSD 导出、示例工程、Claude Code 插件清单与中英双语文档。
