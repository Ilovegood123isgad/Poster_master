---
name: poster-master
description: >
  Poster design workflow that turns a brief, a pile of client materials, or a one-line topic
  into a production-ready poster: written copy hierarchy, visual direction, artwork, a
  component-based editable source, and delivered PNG / SVG / layered PSD for print and social.
  Use when the user asks to create, design, make, produce, generate, redraw, revise, resize,
  adapt, localize, or export a poster / flyer / 宣传海报 / 招新海报 / 活动海报 / 品牌海报 /
  social poster / print poster, when they ask for poster size or resolution specs, QR-code and
  asset compliance checks, or when they mention poster-master.
metadata:
  version: "1.1.0"
  license: "MIT"
  official_repository: "https://github.com/Ilovegood123isgad/Poster_master"
---

# Poster Master Skill

Poster Master is a routed poster workflow. This entry owns global execution discipline and
route selection only; each selected route owns its procedure.

The deliverable of a poster is **not a picture**. It is a frozen brief, a copy hierarchy, a
visual direction, artwork, an editable component source, and a checked set of output files.
Every route ends at delivery, never at "here is a draft".

## Mandatory Load Order

**Hard rule — paths before commands.** Retain the host-provided absolute directory containing
this file as ${SKILL_DIR}. Per tool call, expand ${SKILL_DIR} and replace any
$skills/poster-master/ prefix with it. Never $cd, use the CWD, or assume a repo
checkout. If the absolute path is unavailable, ask for it; never search or guess.

1. Read this file.
2. Read `workflows/routing.md` through ${SKILL_DIR}/workflows/routing.md.
3. Select exactly one top-level route and its active profile from the routing authority.
4. Read only the resulting runtime authority and its explicitly triggered supporting documents.

| Selected route / profile | Runtime authority |
|---|---|
| Create a new poster | `workflows/new-poster.md` |
| Create a new poster — quick (no confirmation round trip) | `workflows/new-poster.md`, Quick profile |
| Revise an existing poster | `workflows/revise-poster.md` |
| Work inside the component editor (a tool, usable from any route) | `workflows/editor-refine.md` |
| Adapt, export, and deliver | `workflows/deliver.md` |

**Hard rule — selected authority only.** Do not load another route's procedure after routing.
Supporting documents refine one route; they never compete with it.

**One exception, and it is not a route change:** `editor-refine.md` is a *tool manual*. Load
it whenever you are about to start the editor, from inside Create or Revise, without leaving
the route you are in. The editor is how composition work happens; it is not a different job.
Never let the editor become a prerequisite either — every one of its exports has a
command-line equivalent, and a delivery must be reproducible without a browser.

## Inputs

Six inputs decide whether a poster can start. Classify each as **known**, **assumed**, or
**missing** before touching the artwork.

| Input | Why it is load-bearing |
|---|---|
| Purpose and channel | Print size, viewing distance, and file format follow from it |
| Audience | Decides the visual language and the copy density |
| One-sentence core message | Decides the hierarchy; a poster with two messages has none |
| Verified copy set | Facts must be confirmed, never inferred from a design mock |
| Assets and their rights | Every image, logo, and font has a licence state that gates use |
| Size, deadline, deliverable list | Decides how many versions exist and what "done" means |

Read `references/intake-and-brief.md` for the intake table, the question order, and
the difference between a missing fact and a design assumption. Read
`references/asset-intake.md` before accepting any file a client sends — "the client sent
it" is not "the asset is usable". Read `references/compliance-and-delivery.md` before a
claim, a person, or a payment path enters the copy.

**Missing facts are blocking only for the fields they touch.** If the copy set is unconfirmed
but the layout is being explored, continue with placeholder copy clearly marked as such in
the work file, and keep the delivery gate closed. Never silently fill a date, price, venue,
phone number, QR link, or a client's product claim with something that looks plausible.

## The Six Stages

Every route is one Plan → Do·Check·Act cycle over the same six stages. The stages belong to
the poster, not to the route; a revision route re-enters at the stage that owns the change.

| Stage | Frozen output | Gate before leaving |
|---|---|---|
| 1. Goal | Target audience, primary effect, core message, success criteria | Brief accepted; primary effect is one, not three |
| 2. Information | Copy set with priority tags; open-questions list | Every P0 fact is confirmed or explicitly parked |
| 3. Direction | 3–5 visual keywords, palette, type, key visual, references | The direction fits the real carrier and audience |
| 4. First draft | At least one readable composition, with intent recorded | Readable at actual size; hierarchy survives distance |
| 5. Iteration | Versioned feedback log with decisions | Facts re-verified; open questions closed or listed for delivery |
| 6. Output | Channel-specific PNG / SVG / PSD plus a delivery check | The delivery checklist passes; nothing is assumed verified |

Full stage procedure, artifacts, and templates:
`references/six-stage-workflow.md`.

## Global Execution Discipline

1. **Serial execution** — follow the selected authority's steps in order. A completed
   non-blocking step may continue directly to the next eligible step.
2. **Blocking means stop** — at every ⛔ BLOCKING gate, wait for explicit user confirmation.
   Do not decide on the user's behalf.
3. **No cross-phase bundling** — do not combine work across an unclosed gate.
4. **Gate before entry** — verify every listed prerequisite before entering a step.
5. **No speculative execution** — do not prepare later-stage artifacts before their owning step.
6. **Deterministic routing** — do not add a route-choice question when the routing authority
   already resolves the request. If a route prerequisite is missing, state it and stop that route.
7. **Act at the owning layer** — repair a failure at the shallowest layer that owns the fault:
   the layout for a layout fault, the copy sheet for a copy fault, the source artifact for a
   tool failure; then resume from the route's declared pointer. Do not silently downgrade a
   required artifact.
8. **Facts are not design decisions** — a wrong date, price, or QR link is a defect, not a
   style choice. It is fixed by confirming with the client, never by redrawing.

## Global Communication Rules

- Match the user's language and the source material's language unless the user overrides it.
- Report state with evidence: say which file, which version, which check, and which date.
- Separate **verified**, **designed**, and **assumed** in every status report. Never describe a
  draft as approved, a mock as a final, or an unmeasured QR code as working.
- Write the project record into the project folder as you go (templates in `templates/`),
  not only into the chat. The chat scrolls away; the project folder is the deliverable.

## The Component Editor

`scripts/editor/` is a dependency-free local editor: Node standard library only, no
`npm install`, no network. It opens a component source, renders it on a canvas, and
exports PNG, SVG, and a layered PSD.

```bash
node "${SKILL_DIR}/scripts/editor/open.js" --project "<project-dir>"
```

Start it with `open.js`, never with `server.js`. `server.js` runs in the foreground and dies
with its terminal, which leaves the browser showing `ERR_CONNECTION_REFUSED` — the editor then
looks broken when nothing is wrong with it. `open.js` starts it detached, waits until the port
answers, prints the URL, reuses an already-running instance, and moves to another port when the
default is taken.

It is a **tool, not a separate job**. Use it during Create and Revise as well as when the
user asks for layered files. Its source format, element types, and limits:
`references/editor-source-format.md`. Its export controls — per-group or per-element
layers, dpi — and the PSD contract: `references/psd-layer-spec.md`.

The canvas is full width in a browser window; in a narrow one (a DSH sidebar tab runs about
700–1000 px) the two side panels become drawers and start closed, so the artwork keeps the
space. `L` toggles layers, `I` toggles the inspector, `Esc` closes the drawer.

Two hard lessons about the editor:

1. **Every editor operation needs a command-line equivalent.** An SVG export that only
   exists behind a browser button is an export that does not exist in a sandbox, in CI, or
   on a headless host. `scripts/render_preview.py`, `scripts/export_svg.py`, and
   `scripts/export_psd.py` exist so that nothing in the delivery path depends on a UI.
2. **Never block on the editor.** If the host cannot start a local server or open a
   browser, say so and continue with the CLI path. The component source is the artefact;
   the canvas is one way to look at it.

## Image Generation (Optional, User's Own Key)

When the direction needs a key visual that no supplied asset can provide, generation is
usually the right tool — hand-coding the subject in Python is not. It is **optional and
user-configured**: this skill ships no key and calls no service until the user sets one up.

```bash
python "${SKILL_DIR}/scripts/setup_imagegen.py"     # asks for base_url, api_key, model
python "${SKILL_DIR}/scripts/setup_imagegen.py" --test
```

Ask the user for three things, in this order, because each one decides the next: the
OpenAI-compatible `base_url`, their API key (hidden prompt, stored at
`~/.poster-master/imagegen.json`, never in the project and never in the chat), and the model
name that endpoint actually serves. Then:

```bash
python "${SKILL_DIR}/scripts/generate_artwork.py" --prompt "…" --size 1536x1024 --output assets/主视觉.png
```

**If the user has not configured a provider, say so and offer the alternatives.** Do not
improvise a subject by scripting geometry unless the user explicitly accepts that quality
ceiling. What may be generated — atmosphere yes, facts no — is
`references/image-generation.md`, and it is not a style preference.

## Runtime Dependencies

The editor and the project scaffolder are pure Node standard library — they run with no
install step. The Python scripts need the packages listed in `requirements.txt`:

```bash
pip install -r "${SKILL_DIR}/requirements.txt"
```

`psd-tools` is part of that list on purpose: it is the PSD gate. Without it, nothing in the
skill can prove a layered file opens outside Photoshop. `cutout.py` additionally needs
`rembg`, which downloads a segmentation model on first use; install it deliberately. Image
generation needs no package, only a configured key.

## Non-Negotiable Delivery Rules

These are the rules that most often make a poster unusable after approval. They are not style
preferences and are never skipped to save time.

1. **QR codes are never redrawn, AI-generated, or eyeballed.** Decode the original, confirm the
   decoded string against the client's stated link character by character, regenerate a clean
   asset from the confirmed link, and test on a real phone. See
   `references/qr-and-brand-assets.md`.
2. **Product appearance, packaging text, people's faces, and logos are not restyled freely.**
   Retouching is allowed only where it does not change the fact and the client approved it.
3. **Every asset has a rights state** — image source, portrait release, font licence, brand
   mark, and the terms of any generation service used. Unknown rights means the asset is not
   used in a deliverable.
4. **Print and social are different files.** One artwork is never silently reused across
   channels; read the carrier-specific rules in
   `references/formats-and-sizes.md`.
5. **Run the delivery check, do not eyeball it.**
   `python3 "${SKILL_DIR}/scripts/check_delivery.py" --project "<project-dir>"`
   verifies dimensions, colour mode, file integrity, dpi, PSD structure, SVG outlining, and
   QR readability where a code is present. Report its output; do not claim checks that were
   not run.
6. **A PSD that opens is not a PSD that is correct.**
   `python3 "${SKILL_DIR}/scripts/check_psd.py" "<file.psd>" --expect-dpi 300 --compare "<render.png>"`
   must pass before a layered file is delivered: it has to parse through `psd-tools`, carry
   readable layer names, report the dpi that was asked for, and composite back to the
   artwork. See `references/psd-layer-spec.md`.
7. **Fonts.** A font that cannot be embedded or licensed for the use must be replaced before
   delivery. A delivery SVG has its text converted to outlines
   (`scripts/export_svg.py`); an SVG that still carries `<text>` depends on the recipient's
   machine and the delivery check reports it.
8. **State the boundary, do not promise past it.** CMYK, bleed, colour proofing and editable
   text layers are hand-offs, not features. `references/capability-boundaries.md` lists what
   is produced directly, what is not, and the wording to use in a delivery note. Never call a
   screen-resolution RGB file print-ready.

## Repository Compatibility

- This package is a workflow/skill, not a generic application scaffold. Do not create
  `.worktrees/`, `tests/`, branch workflows, or generic engineering
  structure by default.
- Keep required workflow, reference, script, and template files inside this skill directory.
  Repository-level documents may point into the package; package runtime files must not depend
  on repository-level instructions.
- On Windows, if `python3` never starts (the WindowsApps stub exits 9009 with no
  output), rerun the same command with `python`.
- Do not bundle large model weights, `node_modules`, client material, or generated
  caches into the skill package. The editor has no runtime dependency on purpose.
