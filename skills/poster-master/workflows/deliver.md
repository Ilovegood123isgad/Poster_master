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

```bash
node "${SKILL_DIR}/scripts/editor/server.js" --project "<project-dir>"   # then export from the UI
python3 "${SKILL_DIR}/scripts/export_psd.py" --project "<project-dir>"    # layered PSD
```

Export PNG for every pixel variant, SVG when the recipient needs a scalable file, and PSD
when the recipient needs to keep editing layers. Name files
`<project>-<version>-<carrier>.<ext>` so that the delivery list and the folder
agree.

## Step 3 — Run the delivery check

```bash
python3 "${SKILL_DIR}/scripts/check_delivery.py" --project "<project-dir>"
```

It reports, per file: pixel dimensions against the expected size, colour mode, file
integrity, and — where a QR code is detectable in the artwork — whether it decodes. The QR
check is a machine check, not a substitute for scanning on a real phone at real distance;
both are recorded.

Fix what it reports at the owning layer, then re-run it. Never edit the check output to make
it pass.

## Step 4 — The manual half of the check

The automated check cannot judge these. Confirm each one explicitly and record the result in
`templates/06-交付检查表.md`:

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

