# Scripts

Everything here is optional: the skill works as a written workflow without a single
script. Run a script only when a route needs its output.

Dependencies are split on purpose. The editor and the scaffolder are **Node standard
library only** — no `npm install`, no network. The Python scripts need the packages in
`../requirements.txt`. Image generation needs nothing extra but does need your own API
key.

| Script | What it does | Needs |
|---|---|---|
| `new_project.js` | Scaffold a poster project from the stage templates | Node 18+ |
| `editor/server.js` | The local component editor and its export endpoints | Node 18+ |
| `render_preview.py` | Headless render of a component source to PNG | Pillow, numpy |
| `export_svg.py` | Component source → SVG with text converted to outlines | Pillow, fontTools |
| `export_psd.py` | Write a layered PSD: any layer count, real groups, RLE, dpi | Pillow, numpy |
| `check_psd.py` | Read a PSD back and prove it parses, with names, groups, dpi | Pillow, numpy, psd-tools |
| `check_delivery.py` | Automated delivery checks over the exports folder | Pillow, psd-tools, OpenCV |
| `qr_extract.py` | Detect, decode, crop, and regenerate QR codes | OpenCV, numpy, Pillow |
| `cutout.py` | Background removal with an edge-quality report | rembg, Pillow |
| `generate_artwork.py` | Generate one artwork asset with your own image model | an API key (see below) |
| `setup_imagegen.py` | Guided one-time setup and connectivity test for that model | — |
| `imagegen_config.py` | Shared config resolution for the two scripts above | — |
| `quick_validate.py` | Validate this package: dead links, placeholders, syntax | — |

## Scaffold a project

```bash
node "${SKILL_DIR}/scripts/new_project.js" --project "<project-dir>" --name "<项目名>" --size 1024x1536
```

Writes the stage templates, an asset ledger, an `assets/` folder, an `exports/` folder,
and an empty component source. Existing files are not overwritten unless `--force` is
passed.

## Editor

```bash
node "${SKILL_DIR}/scripts/editor/server.js" --project "<project-dir>" [--port 41735]
```

Opens the project at `http://127.0.0.1:41735/`. The server binds to loopback only. Its
format, element types and limits are in `../references/editor-source-format.md`; its
PSD export controls are in `../references/psd-layer-spec.md`.

## Render without a browser

```bash
python "${SKILL_DIR}/scripts/render_preview.py" --project "<project-dir>" --width 1280
python "${SKILL_DIR}/scripts/render_preview.py" --source x.poster.json --output a3.png --dpi 300 --width 3508
```

Use `--dpi` whenever the file is for print: without it the PNG has no `pHYs` chunk and
every reader opens it at 72 dpi.

## Export a layered PSD

```bash
python "${SKILL_DIR}/scripts/export_psd.py" --project "<project-dir>"
python "${SKILL_DIR}/scripts/export_psd.py" <manifest.json>
```

Or from the editor's export menu, which offers per-group or per-element layers and a dpi
field. There is no fixed layer limit. Details and the manifest schema:
`../references/psd-layer-spec.md`.

## Prove the PSD is correct

```bash
python "${SKILL_DIR}/scripts/check_psd.py" "<file.psd>" \
    --expect-dpi 300 --expect-size 3508x4961 --compare "<render.png>"
```

Exit code 0 means the file parses through `psd-tools`, the layer names are readable, the
dpi is the one you asked for, and the layer stack composites back to the render. A PSD
that only "opens" is not a PSD that is correct.

## Delivery check

```bash
python "${SKILL_DIR}/scripts/check_delivery.py" --project "<project-dir>"
```

Per file: does it open, does the size match `delivery.json`, is the colour mode right,
does a print PNG carry its dpi, is the PSD structurally sound, is the SVG outlined, does
a QR code decode. Fix what it reports at the owning layer, then re-run it. Never edit the
output to make it pass.

## QR codes

```bash
python "${SKILL_DIR}/scripts/qr_extract.py" decode "<screenshot.png>"
python "${SKILL_DIR}/scripts/qr_extract.py" generate --url "<confirmed-link>" --output assets/qr.png --size 600
```

Decode first, compare character by character with the link the client wrote down, and
only then regenerate. A code that decodes in a file still has to be scanned on a real
phone at the real distance.

## Cutout

```bash
python "${SKILL_DIR}/scripts/cutout.py" --input "<photo.png>" --output "<out.png>"
```

`rembg` downloads a segmentation model (~176 MB) on first use, so this is not a
runtime-offline script. Treat the result as a first pass, never as a final cutout — see
`../references/asset-processing.md`.

## Image generation — your own model, your own key

The skill ships no key and calls no service until you configure one.

```bash
python "${SKILL_DIR}/scripts/setup_imagegen.py"        # 引导式填写，一次即可
```

It asks for three things, in this order, and explains each one:

1. **base_url** — an OpenAI-compatible endpoint, usually ending in `/v1`.
2. **api_key** — pasted at a hidden prompt, stored at `~/.poster-master/imagegen.json`.
3. **model** — an image model that endpoint actually serves; `--list-models` prints them.

Then test it without spending anything:

```bash
python "${SKILL_DIR}/scripts/setup_imagegen.py" --test
```

And generate:

```bash
python "${SKILL_DIR}/scripts/generate_artwork.py" \
    --prompt "深空中的悬浮岛，扁平矢量，薄荷绿与深青" \
    --size 1536x1024 --output assets/主视觉.png
```

`--dry-run` prints the exact request first. Every output gets a `.json` sidecar recording
model, prompt, size and date, so the asset ledger can cite it. What may and may not be
generated is not a matter of taste: read `../references/image-generation.md` and
`../references/asset-processing.md` before generating anything that is a fact.

Environment variables override the config file, which is convenient for CI or for
switching providers per shell: `POSTER_IMAGEGEN_API_KEY`, `POSTER_IMAGEGEN_BASE_URL`,
`POSTER_IMAGEGEN_MODEL`.
