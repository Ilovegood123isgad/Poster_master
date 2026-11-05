# The Six-Stage Workflow

The stages belong to the poster, not to the tool. Every route — new, revised, adapted — is the
same six stages; a revision re-enters at the stage that owns the change.

Each stage produces a file in the project folder. A stage that produces only a chat message has
not happened.

## Stage 1 — Goal

**Produces** `01-需求简报.md`

**Do**

1. Read the whole client text; extract contradictions, omissions, and stale information.
2. Choose **one** primary effect from the effect taxonomy. At most two secondary effects.
3. Write the core message with the formula:
   *For [who], in [context], make them understand [value], and believe [evidence], so they
   [action].* Simplified: *Make [who] [do what] in [context] because [value].*
4. Write the success criteria as something observable — a count, a rate, a time, or a
   recorded reaction.
5. Name the carrier and the viewing distance, and separate the first viewer from the payer.
6. Write the non-goals.

**Do not** start with colours, fonts, or a reference image. Style chosen before the goal is
the single most common cause of a poster that looks good and does nothing.

⛔ Gate: the brief is confirmed.

## Stage 2 — Information

**Produces** `02-文案层级表.md` and `02-待确认问题.md`

**Do**

1. Collect every candidate line of copy. Use the information-type taxonomy in
   `information-hierarchy.md`: propagation facts, action entries, identification
   assets, rule constraints, carrier delivery, decision ownership.
2. Tag each line **P0 must show / P1 should show / P2 may be weakened**, separately per channel
   version.
3. Record the source and confirmation state of every P0 fact.
4. Verify the QR now, not at the end. See `qr-and-brand-assets.md`.
5. Write the open-questions table.

⛔ Gate: every P0 fact is confirmed, or the work is explicitly labelled a draft that may not
be delivered.

## Stage 3 — Direction

**Produces** `03-创意方向.md`

**Do**

1. Derive 3–5 visual keywords from the goal, the audience, and the carrier — not from what
   is trending. Each keyword states **why** it follows from the brief.
2. Split into: main style, supporting style, and specific components. A style is not one
   filter; it is a set of decisions about type, colour, image, and structure.
3. Fix the palette with hex values and a role for each colour (background, primary, accent,
   text, background-of-subhead).
4. Choose the type pairing and say why: weight, width, and the size hierarchy.
5. Choose the key visual and say where it comes from: supplied asset, processed asset,
   illustration, or generated. State the generation boundary.
6. Write the composition in words: what is where, what the eye hits first, second, third.
7. Write the text-to-image ratio, the material and texture language, and the CTA treatment.
8. List the references and what exactly was borrowed from each; list what is explicitly not
   being used.

⛔ Gate: one direction, accepted, that fits the real carrier.

## Stage 4 — First draft

**Produces** the component source, plus `04-初稿说明.md`

**Do**

1. Build the draft in the component source so it stays editable. See
   `editor-source-format.md`.
2. Produce at least one **readable** composition. When the direction genuinely permits it,
   produce two or three structurally different options — different composition, not different
   colour.
3. Test at actual size and actual viewing distance:
   - main title first?
   - smallest required text legible?
   - no collisions between image, text, and logo?
   - CTA reads as an action, not as decoration?
4. Record the intent of the version and what it is still testing.
5. Check against the competition in the same wall, feed, or screen.

## Stage 5 — Iteration

**Produces** `05-反馈记录.md`

**Do**

1. Log every piece of feedback: who, what, decision, version, date. Separate design feedback
   from factual corrections from production constraints.
2. Re-verify the copy after every copy change.
3. Bump the version everywhere it appears — project README, component source, file names.
4. Classify feedback as accepted, deferred, or rejected, with a reason.
5. When the project ends, write the production-verification card: which assumption held under
   real conditions, which fell, and what the next project should ask first.

## Stage 6 — Output

**Produces** the delivery set plus `06-交付检查表.md`

**Do**

1. Fix the per-version delivery list: carrier, pixel size, colour mode, DPI, bleed, and the
   keep/drop/rewrite rules for copy.
2. Export PNG per variant, SVG where a scalable file is needed, PSD where layers must stay
   editable.
3. Run `../scripts/check_delivery.py` and fix what it reports at the owning layer.
4. Complete the manual half of the checklist: distance legibility, fact accuracy, real-device
   QR test, rights, print proof, naming and archive.
5. Close the project: update the README, append to the iteration log, promote reusable
   findings into the references.

⛔ Gate: the delivery checklist passes. Items that were not checked are marked as such.

## The cycle

Each stage is one Plan → Do·Check·Act cycle:

- **Plan** — every input the stage needs exists as a file or a recorded decision.
- **Do** — produce the stage artifact.
- **Check** — run the stage's own gate.
- **Act** — repair at the shallowest layer that owns the fault, then resume.

Do not carry work across an unclosed gate. Do not prepare a later stage's artefacts before
its own step.

