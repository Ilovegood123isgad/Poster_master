# Asset Intake and Rights

Read in stage 1 (intake) and stage 2 (copy and asset lock). Adapted from the project's
material-handling notes.

## "The client sent the file" is not "the asset is usable"

Every asset passes through seven checks before it may enter a delivered poster.

| Step | Question | Output | Blocks when |
|---|---|---|---|
| 1. Receipt log | Who supplied it, when, and is this the final version? | Original file, name, version, date | The source is unknown, or it is only a forwarded screenshot |
| 2. Type identification | QR, logo, person, product, venue, font, icon, or reference? | Asset-ledger classification | One file mixes several uses without being split |
| 3. Fact check | Are the text, product appearance, identity, link, and brand version correct? | Client confirmation record | A key fact can only be guessed visually |
| 4. Rights check | Is it permitted for this project, channel, region, and term? | Licence evidence or written confirmation | Unknown source, no portrait release, unclear font licence |
| 5. Technical check | Resolution, size, colour, transparency, editability, scannability? | Technical check result | It will blur in print, the QR will not decode, the logo is distorted |
| 6. Processing | Use as-is, cut out, retouch, extend, redraw, or replace? | Before/after versions and a note | The processing changes a fact and the client has not approved it |
| 7. Lock and deliver | Final version, permitted uses, reviewer, archive location? | Lock list and delivery package | A "temporary image", a "test code", or an unapproved font is still in the file |

## Asset states

Use these labels on every row of the asset ledger:

| State | Meaning |
|---|---|
| 待补原始文件 | Only a screenshot, a chat forward, or a platform preview exists |
| 待核事实 | Text, model, price, identity, or QR link not yet confirmed by the client |
| 待核授权 | Source or the permitted scope is unclear |
| 可直接用 | Fact, rights, and technical checks all passed |
| 需处理 | May be cut out, colour-matched, repaired, or extended without changing the fact |
| 需重绘/生成 | The original cannot serve the purpose, and the client approved the creation boundary |
| 拒用/替换 | Source, rights, or factual accuracy cannot be established |

## The ledger

One row per asset. It is the evidence, so it is written as the project proceeds, not at the end.

| Asset | Purpose / necessity | File or link | Format / size / resolution | Background / editability | Processing needed | Rights state | Confirmed by |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Naming

```text
<project>_<type>_<description>_<source>_<version>_<date>.<ext>
<project>_<type>_<description>_<processing>_<version>_<date>.<ext>
```

Examples:

```text
P20260927_QR_clientQQ_screenshot_original_v01_20260927.png
P20260927_QR_clientQQ_regenerated_from_confirmed_link_v02_20260927.svg
P20260927_PRODUCT_product_front_cutout_v01_20260927.png
```

## Before the layout starts, freeze

1. The mapping between original and processed assets.
2. The features that must survive untouched: logotype letterforms, packaging text, product
   structure, a person's face and identity.
3. Which processing the client approved.
4. Where the licence, release, and brand evidence live.
5. The final reviewer, the version, and the channels it applies to.

## Common asset traps

| Trap | What actually happened | Prevention |
|---|---|---|
| Logo recreated from a screenshot | Wordmark proportions and strokes are wrong | Ask for a vector or transparent PNG; otherwise refuse and request the source |
| QR cropped from a screenshot | Quiet zone cut off, module edges damaged | See `qr-and-brand-assets.md` |
| Person photo used without a release | Personal data and portrait rights | Ask for a release, or use a stock/AI image with a documented licence |
| Web image used because it was convenient | Licence unknown | Record the source; if the licence is unclear, do not ship it |
| Product generated from a description | The product does not match reality | Use the real product photo; generate only the background |
| Font from a random download | Cannot be embedded or licensed | Use a licensed family and record it |
| Low-resolution image enlarged for print | Blurred at final size | Check effective ppi at final size; replace or re-shoot |

## Review gates

Four gates, in order. Each gate must be clear before the next one starts.

1. **Intake gate** — every asset has a state; nothing is "probably fine".
2. **Rights gate** — every asset that will appear in a deliverable has a recorded licence,
   release, or brand evidence. Unknown = not used.
3. **Fact gate** — every P0 fact and every identity-bearing asset is confirmed by the client.
4. **Delivery gate** — the final files match the confirmed facts, and the ledger's lock list
   matches what is actually in the files.

High-risk items (a person's face, a product claim, a payment or health statement, a QR that
leads to a personal account) are named, given an owner, and either cleared or replaced —
never shipped with the risk still open.

