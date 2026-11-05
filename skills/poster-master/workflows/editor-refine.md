# Refine in the Component Editor

Runtime authority for the *Refine in the component editor* route. The editor is where
composition work happens; it is not where direction is decided.

## Step 1 — Confirm the runtime

```bash
node "${SKILL_DIR}/scripts/editor/server.js" --project "<project-dir>" [--port 41735]
```

The server prints the URL it is listening on. It binds to 127.0.0.1 only; nothing is exposed
to the network.

- Requires Node.js 18 or newer. No `npm install` — the editor uses only the Node
  standard library.
- If Node is unavailable, say so and fall back to `revise-poster.md` with direct
  source editing. Do not attempt a substitute runtime the user did not ask for.

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
| Exports | PNG at 1× or 2×, SVG with the key visual embedded, layered PSD grouped by component group. |

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

Export PNG, SVG, and PSD from the editor, then run the delivery check from
`deliver.md`. Record which component source version produced the delivered files.

