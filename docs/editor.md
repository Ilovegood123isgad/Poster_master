# 编辑器

[English](en/editor.md) · [文档索引](README.md)

## 它是什么

<code>scripts/editor/</code> 是海报的**组件编辑器**：打开一个组件源稿，在画布上逐个元素改，
实时预览，并导出 PNG / SVG / 分层 PSD。

- 纯 Node 标准库，**没有 npm install，没有网络请求**。
- 只监听 127.0.0.1，不对外暴露。
- 项目目录始终是项目目录：所有素材来自项目内的 <code>assets/</code>。

## 启动

```bash
node "<技能目录>/scripts/editor/server.js" --project "<项目目录>" [--port 41735]
```

输出里会打印项目路径、源稿文件、导出目录和地址。

| 参数 | 说明 |
|---|---|
| <code>--project</code> | 项目目录（必填），里面有 <code>assets/</code>、<code>exports/</code> 和源稿 |
| <code>--port</code> | 端口，默认 41735 |
| <code>--host</code> | 监听地址，默认 127.0.0.1 |

## 界面分区

| 区域 | 能做什么 |
|---|---|
| 画布 | 真实尺寸预览，支持缩放与元素选中 |
| 图层列表 | 按分组排列的元素，点选即高亮 |
| 属性面板 | 改文案、颜色、字号、位置、尺寸、圆角、描边、透明度 |
| 素材区 | 列出项目 <code>assets/</code> 下的图片，可直接替换 |
| 导出区 | 导出 PNG / SVG / 分层 PSD 到项目 <code>exports/</code> |

## 组件源稿格式

源稿是一个 JSON 文件，扩展名 <code>.poster.json</code>：

```json
{
  "schemaVersion": 1,
  "name": "城市夜跑",
  "canvas": { "width": 1080, "height": 1440, "background": "#0B1020" },
  "meta": { "version": "v1", "carrier": "1080 × 1440 px（3:4 社交媒体）" },
  "elements": [
    {
      "id": "main-title",
      "label": "主标题",
      "group": "04 标题",
      "type": "text",
      "x": 90, "y": 372, "w": 900, "h": 160,
      "text": "城市夜跑",
      "fontSize": 148,
      "fontFamily": "Source Han Sans SC",
      "fontWeight": "700",
      "color": "#F4F6FB",
      "align": "center"
    }
  ]
}
```

### 元素类型

| type | 关键字段 | 说明 |
|---|---|---|
| <code>text</code> | text、fontSize、fontFamily、fontWeight、color、align、lineHeight | 文本框 |
| <code>image</code> | src、x/y/w/h、resample | 图片；<code>resample: "nearest"</code> 用于二维码 |
| <code>rect</code> | fill、radius、stroke、strokeWidth | 矩形 / 圆角矩形 |
| <code>ellipse</code> | fill、stroke | 椭圆 |
| <code>line</code> | stroke、strokeWidth | 直线 |
| <code>arc</code> | stroke、start、end | 圆弧 |

### 校验规则

- 元素 id 唯一，匹配 <code>^[a-z0-9-]{2,64}$</code>。
- 只允许上述六种类型。
- 图片 <code>src</code> 必须落在项目 <code>assets/</code> 内。
- 数值必须有限且在 ±100000 以内。

不满足规则时编辑器会**拒绝整个文件**并指出是哪条元素、哪条规则，
而不是渲染一半再让你猜。

## 导出

| 格式 | 内容 | 适合 |
|---|---|---|
| PNG | 画布位图 | 社交媒体、屏幕、审稿 |
| SVG | 矢量 + 内嵌位图 | 需要继续在矢量软件里改 |
| PSD | 每个分组一个图层 | 交给美工精修、印厂输出 |

PSD 导出通过 <code>scripts/export_psd.py</code> 完成，需要 Python 与 Pillow。
若 <code>python</code> 不在 PATH 里，设 <code>POSTER_EDITOR_PYTHON</code>。

## 编辑器 vs 无头渲染

| | 编辑器 | <code>render_preview.py</code> |
|---|---|---|
| 用途 | 改稿、逐元素调整 | 自动化出图、批量预览 |
| 运行 | 浏览器 + Node 服务 | 纯命令行 |
| 依赖 | Node 18+ | Python + Pillow |
| 产物 | PNG / SVG / PSD | PNG |

两者渲染同一份源稿，规则一致（尺寸、层级、字号、颜色）。
需要审阅或批量出图时用无头渲染；需要动手改时用编辑器。

## 安全边界

- 服务只绑定回环地址，不监听外网。
- 所有文件读写都限制在项目目录内，路径穿越会被拒绝。
- 源稿里的绝对路径、URL、<code>..</code> 都会被拒绝。
- 编辑器不上传任何素材，所有处理都在本地。
