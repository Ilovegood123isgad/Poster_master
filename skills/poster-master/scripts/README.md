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
node "${SKILL_DIR}/scripts/editor/open.js" --project "<project-dir>"     # 启动或复用，然后打印地址
node "${SKILL_DIR}/scripts/editor/open.js"                                # 重新打开上一次的项目
node "${SKILL_DIR}/scripts/editor/open.js" --open                         # 顺便用系统浏览器打开
node "${SKILL_DIR}/scripts/editor/open.js" --stop                         # 停止
```

`--project` 可以省略：它会记住上一次打开的项目。这样桌面上放一个快捷方式就够了——
不用记路径，双击就是"起服务并拿到地址"。

**用 `open.js`，不要直接起 `server.js`。** `server.js` 是前台进程，会占住终端；一旦那个窗口
被关掉，浏览器里就只剩 `ERR_CONNECTION_REFUSED`——这是实际发生过的事故。`open.js` 把服务
以脱离方式起在后台，**等到端口真的应答了才打印地址**，同一项目重复执行只复用、不再起第二个，
端口被占时自动往后找。

打开地址 `http://127.0.0.1:41735/`。服务只监听 loopback。源稿格式、元素类型与限制见
`../references/editor-source-format.md`；PSD 导出粒度与 dpi 见 `../references/psd-layer-spec.md`。

想在 DSH 的侧边栏里用：把聊天区的链接偏好设为「应用内侧边栏」，再点这个地址即可（DSH 内置的
`ui-sidebar-browser` 会为它开一个 tab）。前提仍然是**服务已经在跑**。

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
# 从截图里读码，并与客户给的链接逐字符比对
python "${SKILL_DIR}/scripts/qr_extract.py" --input "<screenshot.png>" --expect "<客户确认的链接>"

# 从确认过的链接重新生成一张干净的码
python "${SKILL_DIR}/scripts/qr_extract.py" --generate "<confirmed-link>" --output assets/qr.png --size 600
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
