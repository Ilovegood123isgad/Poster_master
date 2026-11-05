# Editor

[中文](../editor.md) · [Docs index](README.md)

## What it is

<code>scripts/editor/</code> is the **component editor** for a poster: open a component source,
change element by element on a canvas, watch it live, and export PNG / SVG / layered PSD.

- Pure Node standard library — **no npm install, no network requests**.
- Binds to 127.0.0.1 only.
- The project stays the project: every asset comes from the project's <code>assets/</code> folder.

## Start it

```bash
node "<skill dir>/scripts/editor/server.js" --project "<project dir>" [--port 41735]
```

| Option | Meaning |
|---|---|
| <code>--project</code> | Project directory (required) holding <code>assets/</code>, <code>exports/</code> and the source |
| <code>--port</code> | Port, default 41735 |
| <code>--host</code> | Bind address, default 127.0.0.1 |

## Panels

| Panel | What it does |
|---|---|
| Canvas | True-size preview with zoom and element selection |
| Layers | Elements grouped by layer, click to highlight |
| Properties | Copy, colour, size, position, radius, stroke, opacity |
| Assets | Images in the project's <code>assets/</code>, replaceable in place |
| Export | PNG / SVG / layered PSD into the project's <code>exports/</code> |

## Component source format

```json
{
  "schemaVersion": 1,
  "name": "城市夜跑",
  "canvas": { "width": 1080, "height": 1440, "background": "#0B1020" },
  "meta": { "version": "v1", "carrier": "1080 × 1440 px (3:4 social)" },
  "elements": [
    {
      "id": "main-title",
      "label": "主标题",
      "group": "04 标题",
      "type": "text",
      "x": 90, "y": 372, "w": 900, "h": 160,
      "text": "城市夜跑",
      "fontSize": 148,
      "fontWeight": "700",
      "color": "#F4F6FB",
      "align": "center"
    }
  ]
}
```

### Element types

| type | Key fields | Notes |
|---|---|---|
| <code>text</code> | text, fontSize, fontFamily, fontWeight, color, align, lineHeight | Text box |
| <code>image</code> | src, x/y/w/h, resample | <code>resample: "nearest"</code> for QR codes |
| <code>rect</code> | fill, radius, stroke, strokeWidth | Rectangle / rounded rectangle |
| <code>ellipse</code> | fill, stroke | Ellipse |
| <code>line</code> | stroke, strokeWidth | Line |
| <code>arc</code> | stroke, start, end | Arc |

### Validation rules

- Element ids are unique and match <code>^[a-z0-9-]{2,64}$</code>.
- Only the six types above are allowed.
- Image <code>src</code> must resolve inside the project's <code>assets/</code>.
- Numbers must be finite and within ±100000.

A file that breaks a rule is rejected as a whole, with the element and the rule named — the editor
never renders half a poster and leaves you guessing.

## Exports

| Format | Content | Use |
|---|---|---|
| PNG | Canvas bitmap | Social, screen, review |
| SVG | Vector shapes with embedded bitmaps | Continuing in a vector tool |
| PSD | One layer per group | Designer refinement, print output |

PSD export runs <code>scripts/export_psd.py</code> and needs Python with Pillow. If
<code>python</code> is not on PATH, set <code>POSTER_EDITOR_PYTHON</code>.

## Editor vs headless renderer

| | Editor | <code>render_preview.py</code> |
|---|---|---|
| Purpose | Change a poster | Automate previews and batch renders |
| Runs in | Browser + Node server | Command line only |
| Needs | Node 18+ | Python + Pillow |
| Produces | PNG / SVG / PSD | PNG |

Both render the same source with the same rules. Use the headless renderer for review and batch
work; use the editor when a human is changing things.

## Safety boundaries

- The server binds to the loopback interface only.
- Every file read and write is confined to the project directory; path traversal is rejected.
- Absolute paths, URLs and <code>..</code> in a source are rejected.
- Nothing is uploaded; all processing stays local.
