# Changelog

The Chinese [CHANGELOG.md](CHANGELOG.md) is canonical; this is its English mirror.
Versions follow semver: a breaking change bumps major, a new capability bumps minor, a
fix bumps patch. The single source of truth for the version is `metadata.version` in
`skills/poster-master/SKILL.md`; `.claude-plugin/marketplace.json` and the archive file
name must match it, and `tools/check_links.py` enforces that.

## v1.1.0 — 2026-11-06

This release is about **making the delivered files trustworthy**. v1.0.0 produced files,
but one of them — a layered PSD — was unusable, and the delivery check reported it as
passing. Every item below has an automated check behind it.

### Fixed

- **The layered PSD works now.** Three independent defects:
  - every layer record declared its channel data two bytes short (the 2-byte compression
    word was not counted), which makes strict readers refuse the file and Photoshop show a
    scrambled stack;
  - the layer records were written in the wrong order — PSD records run bottom to top and
    the old writer reversed an already bottom-to-top list, so the background ended up in
    front of everything;
  - every layer carried an opaque background, hiding the layers below it, and layer names
    were encoded as latin-1, turning all Chinese names into `?`.
- **RLE compression** in the PSD writer: an A3, ten-layer file drops from 730 MB to a few
  tens of MB. Layer count is unlimited and real layer groups (`lsct`) are supported.
- **dpi is written** into the PSD (ResolutionInfo) instead of silently being 72.
- **The delivery check no longer passes a broken file.** `scripts/check_psd.py` reads the
  PSD back through `psd-tools` and verifies structure, dpi, readable layer names and that
  the stack composites to the render.
- **PNG writes its dpi** (`pHYs`), and the check compares it with the declared value.
- **QR false positive**: a detection box covering more than a third of the frame is no
  longer treated as a code.
- **Headless renderer** rewritten: weights 100–900 resolve to the right font *file*, not
  just a variation axis; per-element tiling instead of supersampling the whole canvas (an
  A3 no longer needs ~600 MB); `h = 0` rules are drawn; text supports rotation, scale and
  wrapping; dpi is written; the centring box is no longer scaled twice by the supersample
  factor.
- **The editor crashed on load**: `app.js` read `zoomIn`/`zoomOut`/`zoomFit` from a DOM map
  that never contained them, so the script threw, the page stayed blank and every export was
  unreachable.
- **Python detection** is now `POSTER_EDITOR_PYTHON` → `python3` → `python` → `py`, with a
  timeout and a readable error instead of a silent failure.
- `deliver.md`'s `export_psd.py --project` command did not match the script's arguments.
- `quick_validate.py` now exists (it was referenced in five documents but missing).
- 23 broken-markdown placeholder tokens in `scripts/README.md` are gone.

### Added

- **Image generation with your own key.** `setup_imagegen.py` asks for `base_url`,
  `api_key` and `model` in that order, stores the key at `~/.poster-master/imagegen.json`,
  never writes it into a project and never prints it. `--test` calls `GET /models` and costs
  nothing. `generate_artwork.py` writes a sidecar record with model, prompt, size and date.
  The package ships no key.
- `scripts/export_svg.py` — SVG export with text converted to outlines. Previously SVG could
  only be produced inside the browser, which no headless host can do.
- `references/capability-boundaries.md`, `references/image-generation.md`,
  `references/psd-layer-spec.md`.
- A pixel recipe table in `references/formats-and-sizes.md` (A3 at 300 dpi, bleed, safe area).
- Editor export menu: PNG 3×, layer granularity (per group / per element), dpi.
- `requirements.txt` now lists `fonttools` and `psd-tools`.

### Changed

- Delivery rules in `SKILL.md` went from 6 to 8: "a PSD must be verified" and "state the
  capability boundary" are new.
- The editor is a **tool**, usable from any route, and every one of its exports has a
  command-line equivalent.
- `check_links.py` also checks inline code paths and version consistency.

### Known limits

- CMYK conversion, bleed and proofing remain hand-offs, not features.
- PSD layers are raster, so text is not retypable; hand over the `.poster.json` for that.
- The editor UI got functional additions only, not a visual redesign.

## v1.0.0 — 2026-11-05

First release: the six-stage workflow, four routes, 12 references, 10 templates, a
dependency-free local editor, PNG / SVG / PSD export, an example project, a Claude Code
plugin manifest, and bilingual documentation.
