# Capability Boundaries

Read this before promising a file, and before a delivery report claims something was
verified. It exists because the previous version described a print pipeline it did not
have, and an agent following that text would have told a client that a screen-resolution
RGB file was print-ready.

The rule is simple: **state what the toolchain actually produces, and move everything else
to an explicit hand-off.**

## What this skill produces directly

| Output | Real state | Verified by |
|---|---|---|
| Component source `.poster.json` | the editable truth of the artwork | `editor-source-format.md` |
| PNG at any pixel size | RGB, with `pHYs` dpi when `--dpi` is passed | `check_delivery.py` |
| SVG | vector shapes, raster images embedded as base64 | `check_delivery.py` |
| Layered PSD | RGB, one raster layer per group or element, real folders, RLE, dpi resource | `check_psd.py` |

## What it does not do

| Not done | Why | What to do instead |
|---|---|---|
| CMYK conversion | needs an ICC workflow and a proof | export RGB + a PSD, hand the colour conversion to the printer or to Photoshop/Illustrator |
| Bleed and trim marks | needs the supplier's template | size the canvas to trim + bleed, and check it with `delivery.json`'s `bleed_px` |
| Outlined text inside the **editor's** SVG export | the browser writes `<text>` | use `scripts/export_svg.py`, which converts text to paths |
| Editable text layers in the PSD | every layer is a bitmap | hand over the `.poster.json` when copy must be retyped |
| Upscaling to print resolution | no interpolation makes detail | generate larger, shoot larger, or change the layout |
| Colour proofing | physical | proof on the real substrate |
| Font licence clearance | legal | record the licence in the asset ledger before delivery |

## The honest size table

| Carrier | Pixels at 300 dpi | Where the artwork comes from |
|---|---|---|
| A4 210 × 297 mm | 2480 × 3508 | renderer, editor, or generation |
| A3 297 × 420 mm | 3508 × 4961 | renderer or editor; generation is a guide only |
| A2 420 × 594 mm | 4961 × 7016 | editor or renderer only |
| A1 594 × 841 mm | 7016 × 9933 | editor or renderer; check memory |
| 1080 × 1440 social | 1080 × 1440 | anything |

Add 3 mm bleed on each side before export when the printer asks for it: that is
`+35 px` at 300 dpi on every edge.

## How to phrase a delivery

Wrong, and it has shipped:

> 已交付印刷级分层 PSD。

Right:

> 已交付 RGB 分层 PSD（3508 × 4961，300 dpi，11 层，可逐层编辑），
> 文字为位图不可改字；CMYK 转换与出血需按印厂模板另行处理，
> 可编辑源稿是 `.poster.json`，SVG 已转曲。

Say which file, which size, which dpi, which layer count, what is *not* editable, and what
the next step is. A delivery report that separates **verified**, **produced**, and
**handed off** is worth more than one that says "done".
