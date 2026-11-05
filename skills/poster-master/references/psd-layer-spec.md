# The Layered PSD Contract

Read this before exporting a layered file, and before claiming one is deliverable.
A PSD that opens is not a PSD that is correct. Both statements below were once false
about this skill's own exporter, and both cost a real delivery.

## What a delivered PSD must satisfy

Five things, in this order. The first three are structural, the last two are the
ones a designer actually feels:

| # | Requirement | How it is verified |
|---|---|---|
| 1 | Every reader that is not Photoshop can parse it | `check_psd.py` opens it through `psd-tools` |
| 2 | The declared dpi is the real dpi | the ResolutionInfo resource reads back as 300, not 72 |
| 3 | Layer names are readable in the language they were written | Chinese names come back as Chinese, not `?` |
| 4 | The layer stack composites back to the artwork | `--compare <render.png>` reports a small pixel difference |
| 5 | The stack means what the design means | no element moved across another; groups do not reorder anything |

Requirement 5 is the one that silently breaks. See "Grouping changes the stack" below.

## Layer count is not fixed

There is no ten-layer limit and no target number. Choose the granularity that the job
needs:

| Granularity | One layer per | Use when |
|---|---|---|
| Group | a run of consecutive elements sharing a `group` | normal delivery; a designer moves regions |
| Element | a single element | the client will edit copy or move one object |
| Mixed | both, nested in folders | a few groups need internal access, the rest do not |

The editor exposes this as 分层粒度 in the export menu, alongside a dpi field. The
manifest accepts any depth of `children`, up to five levels, and up to four hundred
layers in total.

## Manifest schema

Layers are listed **bottom to top** — the order they are painted.

```json
{
  "width": 3508,
  "height": 4961,
  "dpi": 300,
  "compression": "rle",
  "output": "海报-分层.psd",
  "layers": [
    { "name": "背景", "path": "000-背景.png" },
    { "name": "主视觉", "path": "001-主视觉.png", "opacity": 0.9 },
    { "name": "文字", "children": [
        { "name": "主标题", "path": "002-主标题.png" },
        { "name": "副标题", "path": "003-副标题.png" }
    ]}
  ]
}
```

A node with `path` is one raster layer. A node with `children` is a real Photoshop layer
group. A layer may be hidden with `"visible": false`.

## Grouping changes the stack

A group becomes one layer only if its elements are **consecutive** in paint order.

```text
elements (bottom → top):  背景  顶部  主标题  标签  主视觉  信息  时间轴  信息  收获
```

`信息` appears twice, on both sides of `时间轴`. Merging it into one layer moves its
second half *below* the timeline and the stack no longer matches the artwork. Two
correct answers:

1. **split into runs** — `信息（段1/2）`, `时间轴`, `信息（段2/2）`, which keeps the order exact;
2. **reorder the design** so the group is contiguous, which is usually the better
   artwork anyway.

Never pick the third option, which is to merge anyway and hope. That is what produced
"每个层的前后是混乱的".

## The two-byte rule

Layer channel data is preceded by a 2-byte compression word, and the length declared in
the layer record **includes those two bytes**. Getting this wrong by two bytes shifts
every channel that follows: `psd-tools` refuses the file outright, and Photoshop shows a
scrambled stack. Photoshop is lenient enough to open it, which is exactly why the defect
survives a "let me just open it" check.

## Why RLE, not raw

Raw channels on an A3 canvas cost about 70 MB per layer; ten layers is 730 MB, which
nobody can send. PackBits RLE brings the same artwork to tens of megabytes. The exporter
compresses by default; `"compression": "raw"` exists only for debugging.

## Why `luni`

The legacy name field in a layer record is one byte per character in a MacRoman-ish
encoding. Chinese written there becomes `?`. The Unicode name travels in a separate
`luni` tagged block, and that is the name Photoshop actually displays. Both are written;
only the second one matters for CJK.

## Why ResolutionInfo

Without the 1005 image resource every reader assumes 72 dpi, so a correctly sized A3 at
3508 × 4961 opens as a 1.2 m poster. The exporter writes the dpi you pass; the delivery
checker fails a print file that has none.

## Verification is not optional

```bash
python "${SKILL_DIR}/scripts/check_psd.py" "<file.psd>" \
    --expect-dpi 300 --expect-size 3508x4961 --expect-layers 11 --compare "<render.png>"
```

Run it on the file you are about to send. `check_delivery.py` calls it as part of the
project check, so a malformed PSD fails the delivery gate instead of passing it.

## What a raster layer stack cannot do

Every layer is a bitmap. Text inside a layer is pixels, not editable type, and vector
shapes are rasterised. If the client needs to retype a headline, hand them the component
source (`.poster.json`) and the SVG, not the PSD alone. Say this in the delivery note
instead of letting them discover it.
