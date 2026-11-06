# 变更日志

[English](CHANGELOG_EN.md) · 中文为准，英文版为镜像。

版本遵循语义化：破坏性变更升 major，新增能力升 minor，修复升 patch。
技能包版本的真源是 `skills/poster-master/SKILL.md` 的 `metadata.version`；
`.claude-plugin/marketplace.json` 与压缩包文件名必须与它一致，`tools/check_links.py` 会强制校验。

## v1.1.1 — 2026-11-06

这一版的主题是**让交付门禁不再放行坏文件**，并收尾上一轮留下的仓库基础设施。

### 修复：交付门禁的六类假通过

v1.1.0 的检查器会用"0 失败"签发出坏文件，还会打印"自动检查通过"。以下六类均用构造文件复现后堵住：

- **图层顺序颠倒的 PSD 被判通过。** `check_delivery.py` 把 `expect_layers` 与 `compare` 固定传 `None`，于是 `check_psd.py` 里的图层数校验与合成比对成了死代码。现在从 `delivery.json` 读 `expect_layers` 与 `reference` 并透传；未声明 `reference` 时明确报"图层顺序未验证"，不再默认合格。
- **P 模式印刷 PNG 被判通过。** 色彩模式分支只 WARN 就 `return`，把后面的 dpi 与出血检查整段跳过。现在 WARN 后继续检查。
- **空 `exports/` 被判通过。** 原来只记一条提示，`errors` 仍为 0。现在判 FAIL——"没有东西可查"不是通过。
- **没有 `psd-tools` 被判通过。** 原来降级到结构解析并报 0 失败。现在判 FAIL 并写明"PSD 未验证"：无法验证不等于已验证。
- **清单条目写成 `"exports/海报.png"` 时整条检查静默失效。** `read_delivery` 原样用 `file` 做键，而查找用 `path.name`，前缀一加就匹配不上——尺寸、色彩、dpi、图层数全部跳过，输出仍是 0 失败。现在同时注册纯文件名，两种写法都生效。这一类最危险：报告看上去"检查过了"。
- **清单声明了 `exports/` 里不存在的文件。** 这些条目一条断言都没执行，却报 0 失败。现在判 FAIL，明确指出"清单与实物不一致"。

同时修正话术：存在提示时不再说"自动检查通过"，改为"没有失败项，但有 N 项提示尚未解决——那是未验证，不是通过"。

### 新增

- `templates/delivery.template.json`：交付清单模板，含 `expect_layers` / `reference` 的正确写法、出血三件套的配套要求，以及"file 必须与 exports 里的真实文件名一致"的提示。
- `tests/test_delivery_gate.py`：六类坏文件各一条"必须 FAIL"断言，另加一条"正确的 PSD 必须仍然 PASS"，共 14 条断言。把 v1.1.0 的实现放回去，其中 11 条会变红。
- `tests/run_all.py` 接入该测试，仓库内测试文件从 8 个增加到 9 个。

### 文档

- `scripts/README.md` 补 `delivery.json` 的 `expect_layers` / `reference` 字段表，并写清空目录、缺依赖、缺参考图、清单与实物不一致都算失败。
- `workflows/deliver.md` 的清单示例改为指向模板，并补上 PSD 的两个必填字段。
- `SKILL.md` 规则 5、6 同步：有提示不算通过；`check_delivery` 里也要声明 `expect_layers` 与 `reference`。

### 仓库基础设施（原"未发布"段，随本版一起发布）

- **CI**：`.github/workflows/ci.yml` 在 Ubuntu 与 Windows 上跑结构校验、链接与版本一致性、
  压缩包一致性、示例工程回归（重建 → 渲染 → 交付检查 → SVG 转曲）以及 `tests/run_all.py`。
- **仓库内回归测试**：`tests/` 收进可移植测试（PSD 往返、交付门禁、编辑器链路、渲染、SVG 转曲、
  生图），全部离线、秒级、不含客户素材。此前测试都在仓库外，CI 看不到，等于没有闸门。
- **`tools/check_archive.py`**：校验 `dist` 压缩包与技能源码树一致。不用「重建后 `git diff`」，
  因为 zip 记录每个条目的修改时间，重建必然产生不同字节流。
- **打包统一换行**：`tools/package_skill.py` 在打包与同步时把文本类文件规范成 LF。此前压缩包
  会带上打包机器的换行符，同一个 commit 在 Windows 与 Linux 打出的包内容不同。
- `tools/make_release.py` 增加 `--update-body` 与 `--replace-asset`。

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
