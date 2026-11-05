# Adapt, Export, and Deliver

Runtime authority for the *Adapt, export, and deliver* route. This is stage 6 of any route and
may also be entered on its own.

## Step 1 — Fix the delivery list

One poster has one carrier. Before exporting, write down for each version:

| Field | Meaning |
|---|---|
| Version | e.g. `v1-print-A2`, `v1-social-xhs` |
| Carrier | Print at A2 / WeChat article cover / Instagram feed / phone screen |
| Pixel size | Exact width × height in px, not "roughly square" |
| Colour | RGB for screen, CMYK or the supplier's instruction for print |
| Resolution | Effective DPI at final physical size |
| Bleed and safe area | Only if the supplier asks |
| Must keep / may drop / may rewrite | Per-version copy rules from stage 2 |

Never reuse one export for several carriers by accident. Read
`references/formats-and-sizes.md` for the size and DPI rules and the common carrier
recipes.

## Step 2 — Produce the files

Every file must be producible **without a browser**. The editor is a convenience, not the
only route: a delivery that depends on a UI button cannot be repeated in CI, on a headless
host, or by the next person.

```bash
# PNG, sized to the carrier, with the dpi written into the file
python "${SKILL_DIR}/scripts/render_preview.py" --project "<project-dir>" --width 3508 --dpi 300

# SVG for a recipient who needs vector: text converted to outlines
python "${SKILL_DIR}/scripts/export_svg.py" --project "<project-dir>"

# Layered PSD: per-group or per-element layers, real folders, dpi resource
python "${SKILL_DIR}/scripts/export_psd.py" --project "<project-dir>"
```

Or open the editor and use its export menu, which offers the same three plus the layer
granularity and the dpi field:

```bash
node "${SKILL_DIR}/scripts/editor/server.js" --project "<project-dir>"
```

Choose the layer granularity by what the recipient will do: per group when a designer moves
regions, per element when they will edit one object. There is no fixed layer count. See
`references/psd-layer-spec.md`.

Export PNG for every pixel variant, SVG when the recipient needs a scalable file, and PSD
when the recipient needs to keep editing layers. Name files
`<project>-<version>-<carrier>.<ext>` so that the delivery list and the folder
agree.

Write the sizes and dpi into `delivery.json`, because that is what the check compares
against:

```json
{"files": [{"file": "海报-v1-print-A3.png", "width": 3508, "height": 4961,
            "colour": "RGB", "dpi": 300, "use": "A3 印刷主文件"}]}
```

If the printer asked for bleed, add `"bleed_px"`, `"trim_width"` and `"trim_height"` and the
check verifies the arithmetic instead of guessing.

## Step 3 — Prove the layered file, then run the delivery check

```bash
python "${SKILL_DIR}/scripts/check_psd.py" "<exports/海报-v1-分层.psd>" \
    --expect-dpi 300 --expect-size 3508x4961 --compare "<exports/海报-v1-print-A3.png>"

python "${SKILL_DIR}/scripts/check_delivery.py" --project "<project-dir>"
```

The PSD check is not optional. It proves the file parses through `psd-tools`, that the
Chinese layer names are still readable, that the dpi is not silently 72, and that the layer
stack composites back to the artwork. A PSD that merely opens in Photoshop can still have a
scrambled stack or unusable layer names.

The delivery check reports, per file: pixel dimensions against the expected size, colour
mode, file integrity, the PNG's dpi, the PSD's structure and layer names, whether the SVG
still depends on fonts, and — where a QR code is detectable in the artwork — whether it
decodes. The QR check is a machine check, not a substitute for scanning on a real phone at
real distance; both are recorded.

Fix what it reports at the owning layer, then re-run it. Never edit the check output to make
it pass.

## Step 4 — The manual half of the check

The automated check cannot judge these. Confirm each one explicitly and record the result in
`templates/06-交付检查表.md`. The four review gates this closes are in
`references/compliance-and-delivery.md`; a gate that is "mostly clear" is not clear.

1. **Legibility at distance.** Viewed from the real viewing distance, is the main title the
   first thing read? Is the smallest required text readable?
2. **Facts.** Every date, price, place, contact, and claim matches the confirmed copy sheet.
3. **QR on a real device.** Scanned on at least two phones, at the real viewing distance,
   at the intended brightness.
4. **Rights.** Font licence, image licence, portrait release, brand mark — all recorded.
5. **Colour and print.** Proofed on the actual substrate or screen, not only on the monitor.
6. **Naming and archive.** File names match the delivery list; the project folder holds the
   source, the exports, and the records.

## Step 5 — Close the project

- Update the project README: status, produced files, verification results, unresolved issues.
- Append to the project iteration log: what was decided, what was verified, what failed.
- Write the production-verification card: which assumptions held under real conditions.
- If the work produced a reusable rule, update the corresponding reference file rather than
  leaving it in the chat.

