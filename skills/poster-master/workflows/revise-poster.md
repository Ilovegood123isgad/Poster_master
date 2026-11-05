# Revise an Existing Poster

Runtime authority for the *Revise an existing poster* route. A revision is a controlled
change to an artefact that already exists — not a regeneration.

## Step 1 — Locate and freeze the artefact

Identify the file, its version, and its owner. Read the project folder's README, brief, and
feedback log before changing anything. Record the current state so the revision is
reversible:

```bash
cp "<poster-file>" "<poster-file>.v<old>"
```

If the poster has a component source, that source is the artefact to edit; the exported PNG
is a rendering of it, not the truth.

## Step 2 — Classify the request

| Class | Examples | What changes |
|---|---|---|
| Copy change | New date, new price, corrected title | Stage 2 re-verify, then layout reflow |
| Asset swap | New photo, new logo, new QR | Stage 2 re-verify, then composition check |
| Layout change | "Too crowded", "the title should be bigger" | Stage 3 direction review, then stage 4 |
| Style change | "Make it more premium" | Stage 3 direction **re-opened**; treat it as a new direction |
| Format change | A4 → Xiaohongshu, print → screen | This is **Deliver**, not Revise |
| Compliance fix | Wrong QR, unlicensed font, missing margin | Fix at the owning layer; do not restyle |

For a style change, re-open the stage 3 gate. Re-styling without re-deciding the direction
produces a poster that is internally consistent but still answers the wrong question.

## Step 3 — Make the change at the owning layer

- Text and facts live in the copy sheet, then flow to the component source.
- Composition lives in the component source.
- A wrong fact is fixed by confirming it with the client, not by editing the layout.

Use the editor route (`editor-refine.md`) for composition and asset changes when a
component source exists. Use direct source editing for a copy-only change.

## Step 4 — Re-check, not just re-render

After the change:

1. Re-read every text on the poster against the copy sheet, character by character. Copy edits
   introduce the errors that survive review.
2. Check that the change did not break the hierarchy or push text outside the safe area.
3. Check the new asset's rights state if it is new.
4. If the QR changed, re-run the QR verification.

## Step 5 — Re-issue

Bump the version, write what changed into the feedback log, and re-deliver through
`deliver.md`. A revision that is not re-delivered leaves the client holding the
old file.

