# The Component Source Format

Read before writing or editing a component source by hand, and before scripting anything that
touches one.

## What it is

A component source is a JSON file that fully describes the poster: its canvas, its elements,
their geometry, their styling, and their order. The editor renders it, the SVG exporter
serialises it, and the PSD exporter groups it into layers. The PNG is a rendering of it — the
JSON is the truth.

## File conventions

- Extension: `.poster.json`. The name matches the poster:
  `<project>-组件源稿.poster.json`.
- Encoding: UTF-8, two-space indentation, trailing newline.
- Keep it in version control next to the exports, with the `assets/` folder it
  references.

## Top level

```json
{
  "schemaVersion": 1,
  "name": "骑行社团招新",
  "canvas": {
    "width": 1024,
    "height": 1536,
    "background": "#0d1b2a"
  },
  "meta": {
    "version": "v1",
    "carrier": "A2 打印 / 社交媒体 3:4",
    "notes": "主视觉为 AI 生成插画，人物与品牌标识未生成"
  },
  "elements": []
}
```

| Field | Required | Meaning |
|---|---|---|
| `schemaVersion` | yes | Currently `1`. A file with an unknown version is rejected, not guessed at. |
| `name` | yes | Display name of the poster |
| `canvas.width` / `canvas.height` | yes | Pixel size of the canvas |
| `canvas.background` | yes | Fill painted behind everything |
| `meta` | no | Version, carrier, and any note worth keeping with the file |
| `elements` | yes | Array, painted back to front — the first element is the bottom layer |

## Geometry convention

This is the rule that most often causes silent misalignment:

- `x` and `y` are the **top-left corner of the element's untransformed
  box**.
- `w` and `h` are its untransformed size.
- `angle` is degrees, and rotation happens about the **centre of the element**.
- `scaleX` and `scaleY` scale about the same centre.
- `opacity` is 0–1.

Rotation about the top-left corner is not supported. If you need it, wrap the element in a
group or pre-rotate the asset.

## Element types

### image

```json
{
  "id": "hero-visual",
  "type": "image",
  "label": "主视觉",
  "group": "主视觉",
  "src": "assets/hero.png",
  "x": 0, "y": 240, "w": 1024, "h": 700,
  "angle": 0, "scaleX": 1, "scaleY": 1, "opacity": 1,
  "resample": "nearest",
  "fit": "cover"
}
```

`src` must point inside the project's `assets/` folder. No absolute paths,
no URLs, no parent-directory references — the editor refuses anything else, so a project
folder stays portable.

`resample` is optional and defaults to `lanczos`. Set it to `"nearest"` for pixel-art
assets such as QR codes, where smoothing would blur the modules and break the code.

`fit` is optional and defaults to `"fill"`:

| Value | Behaviour | Use for |
|---|---|---|
| `fill` | stretches to the box and distorts | never for a photograph or a logo |
| `cover` | scales to fill the box, crops the overflow, no distortion | photographs, backgrounds |
| `contain` | scales to fit inside the box, letterboxes the rest | a whole product or a QR code that must not be cropped |

Stretching a photographed subject changes its proportions, which is a factual error rather
than a styling choice. Use `cover` unless the asset is genuinely meant to fill the frame.

### rect

```json
{
  "id": "info-card",
  "type": "rect",
  "label": "信息卡底",
  "group": "信息",
  "x": 72, "y": 1080, "w": 880, "h": 380,
  "fill": "#ffffff",
  "radius": 24,
  "stroke": "#e2e8f0",
  "strokeWidth": 2
}
```

### ellipse

```json
{
  "id": "accent-dot",
  "type": "ellipse",
  "label": "强调圆",
  "x": 800, "y": 120, "w": 120, "h": 120,
  "fill": "#f59e0b"
}
```

### text

```json
{
  "id": "main-title",
  "type": "text",
  "label": "主标题",
  "group": "标题",
  "x": 72, "y": 120, "w": 880,
  "text": "2026 秋季招新",
  "fontFamily": "Microsoft YaHei",
  "fontSize": 96,
  "fontWeight": "700",
  "lineHeight": 1.15,
  "align": "center",
  "fill": "#ffffff",
  "stroke": "#000000",
  "strokeWidth": 0
}
```

| Field | Meaning |
|---|---|
| `text` | The content. A newline character starts a new line. |
| `fontFamily` | A family name available on the machine that renders it |
| `fontSize` | Size in canvas pixels at 1:1 |
| `fontWeight` | `400` or `700` |
| `lineHeight` | Multiplier on the font size |
| `align` | `left`, `center`, or `right` — horizontal only; the text block grows downward from `y` |
| `strokeWidth` | 0 disables the outline |

Text width is measured from the font unless `w` is given. Keep `w` if the
layout depends on a fixed measure.

### line

```json
{
  "id": "rule",
  "type": "line",
  "label": "分隔线",
  "x": 72, "y": 300, "w": 200, "h": 0,
  "stroke": "#f59e0b",
  "strokeWidth": 6
}
```

`h` may be 0 for a horizontal rule. The line runs from `(x, y)` to
`(x + w, y + h)`.

### arc

```json
{
  "id": "ring",
  "type": "arc",
  "label": "装饰弧线",
  "x": 700, "y": 60, "w": 260, "h": 260,
  "start": 200,
  "end": 20,
  "stroke": "#f59e0b",
  "strokeWidth": 4
}
```

`start` and `end` are degrees, measured clockwise from 3 o'clock. The arc
is inscribed in the box `(x, y, w, h)`.

## Common fields

Every element accepts:

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Lower-case, digits and hyphens, 2–64 characters, unique in the file |
| `type` | yes | One of the six types above |
| `label` | yes | Human-readable name shown in the Layers panel |
| `group` | no | PSD layer group name. Elements sharing a group become one PSD layer. |
| `visible` | no | `false` hides the element without deleting it |
| `locked` | no | `true` prevents accidental dragging in the editor |
| `x`, `y`, `w`, `h` | yes | Geometry |
| `angle` | no | Degrees, default 0 |
| `scaleX`, `scaleY` | no | Default 1 |
| `opacity` | no | 0–1, default 1 |

## Limits enforced by the editor

- Canvas width and height must be positive integers.
- 1 to 200 elements.
- Unique element ids matching `^[a-z0-9-]{2,64}$`.
- Element types limited to the six above.
- Image sources must resolve inside `assets/`.
- Numeric values must be finite and within ±100000.

The editor rejects a file that breaks these rules rather than rendering half of it. When it
rejects a file, the message names the element and the rule.

## Layer order is meaning

Elements paint in array order: the first element is the bottom layer. The Layers panel in the
editor shows them reversed, so the top of the list is what the viewer sees first.

Reordering is a design decision. Moving a generated background above a title hides the title.

## What this format is not

- It is not a vector illustration format. The editor renders images, shapes, and text; it does
  not do bezier paths.
- It is not a PSD. The PSD export rasterises each group into one layer.
- It is not a layout engine. There are no constraints, no auto-layout, and no inheritance.
- It is not a design history. Keep versions in git or in numbered copies, not in the file.

