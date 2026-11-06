# Changelog

The Chinese [CHANGELOG.md](CHANGELOG.md) is canonical; this is its English mirror.
Versions follow semver: a breaking change bumps major, a new capability bumps minor, a
fix bumps patch. The single source of truth for the version is `metadata.version` in
`skills/poster-master/SKILL.md`; `.claude-plugin/marketplace.json` and the archive file
name must match it, and `tools/check_links.py` enforces that.

## v1.1.1 — 2026-11-06

The theme of this release is **stopping the delivery gate from signing off broken files**,
plus the repository infrastructure carried over from the previous unreleased section.

### Fixed: six classes of false pass in the delivery gate

v1.1.0's checker signed off broken files with "0 failures" and still printed "自动检查通过".
Each case below was reproduced with a constructed file, then closed:

- **A PSD with an inverted layer stack passed.** `check_delivery.py` hard-coded `expect_layers`
  and `compare` to `None`, so the layer-count check and the composite comparison inside
  `check_psd.py` were dead code. Both now come from `delivery.json`; without a `reference` the
  run reports "layer order unverified" instead of implying it passed.
- **An indexed (P) print PNG passed.** The colour-mode branch returned immediately after a
  warning, skipping the dpi and bleed checks below it. It now continues.
- **An empty `exports/` passed.** It was a warning, so `errors` stayed at 0. It is now a failure:
  "nothing to check" is not a pass.
- **A PSD checked without `psd-tools` passed.** The structural fallback reported no failures. It
  now fails and states "PSD unverified" — cannot verify is not the same as verified.
- **An entry written as `"exports/海报.png"` silently disabled every check for that file.**
  `read_delivery` keyed entries by the raw `file` string while lookups used `path.name`, so a
  path prefix never matched: size, colour, dpi and layer count were all skipped, and the report
  still said 0 failures. Both spellings are now registered. This was the worst of the six —
  the output looked like it had checked something.
- **A delivery list naming a file that is not in `exports/`.** Those entries asserted nothing at
  all yet reported 0 failures. Now a failure, stating the list and the folder disagree.

Wording changed to match: a run with warnings no longer claims "自动检查通过"; it says there
are no failures but N unresolved items, which are unverified, not passed.

### Added

- `templates/delivery.template.json`: a delivery-list template showing the correct
  `expect_layers` / `reference` usage, the all-three-together bleed fields, and the reminder
  that `file` must match the real name in `exports/`.
- `tests/test_delivery_gate.py`: one "must FAIL" assertion per broken-file class, plus one
  "a correct PSD must still PASS" case so the fix cannot degenerate into "everything fails" —
  14 assertions. Restore the v1.1.0 implementation and 11 of them go red.
- `tests/run_all.py` now runs it: 8 suites become 9.

### Docs

- `scripts/README.md` documents the `expect_layers` / `reference` fields and states that an empty
  export folder, a missing dependency, a missing reference and a list that does not match the
  folder are all failures.
- `workflows/deliver.md` points at the template and shows the two PSD fields.
- `SKILL.md` rules 5 and 6 follow: warnings are not a pass, and `check_delivery` needs the same
  two fields.

### Repository infrastructure (previous unreleased section, shipped with this version)

- **CI**: `.github/workflows/ci.yml` runs on Ubuntu and Windows — package validation, link and
  version consistency, archive consistency, the example regression (rebuild → render → delivery
  check → outlined SVG), and `tests/run_all.py`.
- **Tests in the repository**: `tests/` holds portable suites (PSD round-trip, delivery gate,
  editor pipeline, rendering, SVG outlining, image generation). All offline, all fast, none of
  them containing client material. They previously lived outside the repository, where CI could
  not see them — which is the same as having no gate.
- **`tools/check_archive.py`**: verifies that the `dist` archive matches the skill tree. It does
  not rebuild and diff, because a zip stores each entry's modification time and a rebuild always
  produces different bytes.
- **Packaging normalises line endings**: `tools/package_skill.py` writes text as LF. Previously
  the archive carried whatever line endings the packager's machine had, so one commit produced
  different archives on Windows and Linux.
- `tools/make_release.py` gains `--update-body` and `--replace-asset`.

## v1.1.0 — 2026-11-05

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
