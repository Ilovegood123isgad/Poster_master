# Refine in the Component Editor

Runtime authority for the *Refine in the component editor* route. The editor is where
composition work happens; it is not where direction is decided.

## Step 1 — Confirm the runtime

```bash
node "${SKILL_DIR}/scripts/editor/open.js" --project "<project-dir>"
```

`open.js` starts the server **detached**, waits until the port actually answers, and then
prints the URL. Run it twice and it reuses the running instance instead of starting a second
one; if the default port is taken it walks forward. Stop it with `--stop`.

Do not start `server.js` directly. It is a foreground process: closing the terminal it lives
in leaves the browser tab showing `ERR_CONNECTION_REFUSED`, which is the most common way this
editor appears "broken". The runtime is fine; the server just is not running.

- Requires Node.js 18 or newer. No `npm install` — the editor uses only the Node
  standard library.
- If Node is unavailable, say so and fall back to `revise-poster.md` with direct
  source editing. Do not attempt a substitute runtime the user did not ask for.
- To show the editor inside the DSH sidebar, point the chat's link preference at
  "in-app sidebar" and click the printed URL — but only after `open.js` reports the address.

## Step 2 — Open the project

The editor expects a project folder containing a component source. Point `--project`
at that folder, or at the folder that holds the source file. On startup it loads the source,
reports how many components were found, and surfaces any element it could not parse instead
of rendering a broken canvas.

## Step 3 — What the editor does

| Panel | Use it for |
|---|---|
| Layers | Select, reorder, hide, lock, and group components. The order here is the order in the file, and the file is the order in the PSD groups. |
| Canvas | Drag to move, use the handles to scale and rotate. Arrow keys nudge by 1 px, Shift+arrow by 10 px. |
| Inspector | Edit geometry, colour, typography, opacity, and text. Changes apply immediately. |
| Preview | Full-bleed preview of the artwork without the editor chrome, for judging the poster as a viewer sees it. |
| Exports | PNG at 1×, 2× or 3×; SVG with the key visual embedded; layered PSD with a choice of granularity and dpi. |

### Panels on a narrow screen

In a full browser window both side panels sit next to the canvas. In a narrow one — a DSH
sidebar tab is about 700–1000 px — they become drawers over the canvas and start closed, so
the artwork gets the whole width. The two buttons at the right of the top bar open them;
`L` and `I` do the same, `Esc` closes. Only one drawer is open at a time, and the canvas
refits itself whenever the space changes.

### The export menu

Two settings there change the file itself, so set them deliberately:

- **分层粒度 (layer granularity)** — 按组件分组 gives one layer per group, which is what a
  designer needs to move regions. 按单个组件 gives one layer per element, grouped into
  folders, for when the client will edit one object. There is no fixed layer limit; the
  menu shows the exact count before you export.
- **dpi** — written into the PSD's ResolutionInfo and into the PNG's `pHYs`. Without it
  every reader assumes 72 dpi and an A3 opens at 1.2 m. Use 300 for print, 72 for screen.

A group whose elements are split around another group is exported as separate 「段」 layers.
That is correct, not a bug: merging it into one layer would move elements across each other
and scramble the stack. See `references/psd-layer-spec.md`.

## Step 4 — Rules while editing

1. **Save often.** The editor writes the component source on save; unsaved edits are lost on
   reload.
2. **Do not break the copy.** Editing text in the inspector is convenient and dangerous —
   re-read the changed string against the copy sheet before saving.
3. **Keep the safe area.** Elements pushed to the edge may be cut by the carrier's crop or
   bleed. Check `references/formats-and-sizes.md`.
4. **Layer order is meaning.** The topmost component covers the ones below it. When a
   generated image has to sit behind a title, move it in the Layers panel, not by nudging
   pixels.
5. **Do not use the editor to fake a fact.** A QR that does not decode is not fixed by making
   it darker.

## Step 5 — Export and hand off

Export PNG, SVG, and PSD from the editor, then run the checks from `deliver.md`:

```bash
python "${SKILL_DIR}/scripts/check_psd.py" "<exports/….psd>" --expect-dpi 300 --compare "<render.png>"
python "${SKILL_DIR}/scripts/check_delivery.py" --project "<project-dir>"
```

Record which component source version produced the delivered files. If the editor could not
produce something — a browser-only SVG that still carries `<text>`, for instance — use the
CLI equivalents (`scripts/export_svg.py`) rather than shipping the weaker file.

