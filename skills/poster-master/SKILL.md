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
  version: "1.0.0"
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
| Refine in the component editor | `workflows/editor-refine.md` |
| Adapt, export, and deliver | `workflows/deliver.md` |

**Hard rule — selected authority only.** Do not load another route's procedure after routing.
Supporting documents refine one route; they never compete with it.

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
the difference between a missing fact and a design assumption.

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
exports PNG, SVG, and layered PSD.

```bash
node "${SKILL_DIR}/scripts/editor/server.js" --project "<project-dir>" [--port 41735]
```

Use it when the poster needs a component source a designer can open and adjust, when a
revision must not be re-generated from scratch, or when the user asks for layered files. Its
source format, element types, and limits:
`references/editor-source-format.md`.

The editor is an optional companion, not a prerequisite. Never assume the host can reach a
Windows project directory or start a local server — if the editor route is selected and the
runtime is unavailable, say so and continue with the non-editor route.

## Runtime Dependencies

The editor and the project scaffolder are pure Node standard library — they run with no
install step. The Python scripts (rendering, delivery checks, PSD export, QR handling,
background removal) need the packages listed in `requirements.txt`:

```bash
pip install -r "${SKILL_DIR}/requirements.txt"
```

Run them only when a route needs them. `cutout.py` additionally needs `rembg`, which
downloads a segmentation model on first use; install it deliberately, not by default.

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
   mark. Unknown rights means the asset is not used in a deliverable.
4. **Print and social are different files.** One artwork is never silently reused across
   channels; read the carrier-specific rules in
   `references/formats-and-sizes.md`.
5. **Run the delivery check, do not eyeball it.**
   `python3 "${SKILL_DIR}/scripts/check_delivery.py" --project "<project-dir>"`
   verifies dimensions, colour mode, file integrity, and QR readability where a code is
   present. Report its output; do not claim checks that were not run.
6. **Font licensing and embedding.** A font that cannot be embedded or licensed for the use
   must be replaced before delivery; a missing font on the client's machine is not an
   acceptable excuse.

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
