# Create a New Poster

Runtime authority for the *Create a new poster* route. Follow the six stages in order.
Each stage ends with a written artifact in the project folder, not with a chat message.

## Project folder

Create the project folder before stage 1 and use it for everything:

```bash
node "${SKILL_DIR}/scripts/new_project.js" --project "<project-dir>" --name "<项目名>" --size "<WxH>"
```

It writes the stage-1..6 templates, the asset ledger, and an empty component source. If the
folder already exists, the script refuses to overwrite and lists the files it would have
touched.

## Stage 1 — Goal

Produce `01-需求简报.md` from `templates/01-需求简报.md`.

1. Read the whole client text before asking anything. Extract contradictions, omissions, and
   expired information (old dates, a QR for a finished campaign) into an open-questions list.
2. Fill the brief: purpose, channel, viewing environment, audience, the **single** primary
   effect, at most two secondary effects, what is explicitly not being pursued, the one-line
   core message, the three things the viewer must remember, and the success criteria.
3. Separate the *first viewer* from the *decision maker*. A poster that must get a student to
   walk into a booth is aimed at the student, even if the client pays for it.
4. Distinguish the real carrier from the nominal one: an A2 print in a lit corridor, a phone
   screen, a WeChat article cover.

⛔ BLOCKING — stage 1 gate: present the brief and get explicit confirmation. The brief may
not name more than one primary effect, and it may not be approved with open contradictions
inside it.

## Stage 2 — Information

Produce the copy sheet from `templates/02-文案层级表.md`.

1. Collect every piece of copy the poster might carry: main title, subtitle, time, place,
   price, how to join, contact, QR, brand name, mandatory legal or safety note.
2. Tag each line **P0 must show / P1 should show / P2 may be weakened**, per channel version.
3. Mark the source of every P0 fact and its confirmation state. Confirmed by whom, on what date.
4. Build the open-questions list as a separate table. Design does not close open questions by
   choosing a plausible value.
5. Verify the QR code here, not in stage 6: decode it, compare the decoded string to the
   client's stated link, and regenerate a clean asset if the client only sent a screenshot.
   Follow `references/qr-and-brand-assets.md`.

⛔ BLOCKING — stage 2 gate: every P0 fact is confirmed, or the poster is explicitly labelled
as a draft that may not be delivered. Missing P0 facts are listed, not invented.

## Stage 3 — Direction

Produce the direction sheet: 3–5 visual keywords, the reasoning behind each, the palette
(with hex values), the type pairing, the key visual and where it comes from, the composition
sketch in words, the text-to-image ratio, the material and texture language, and the CTA
treatment.

Read `references/creative-direction.md` and
`references/style-and-components.md` before fixing the direction. Read
`references/audience-and-purpose.md` when the audience is not obvious from the brief.

Rules that are not negotiable at this stage:

- A reference case is a source of a principle, not a source of an asset. Record where it came
  from and what exactly was borrowed.
- The direction must fit the **actual** carrier: viewing distance, light, and what surrounds
  the poster.
- If the key visual is generated or repainted, state the boundary: brand marks, packaging
  text, product structure, and faces are not regenerated from a text description.
- Fonts, icons, and images must have a licence state before they enter the direction.

⛔ BLOCKING — stage 3 gate: the direction fits the carrier and the audience, and the user
accepts the keywords and the palette. One direction, not a mood board of five.

## Stage 4 — First draft

Produce at least one **readable** composition, then compare two or three if the direction
genuinely allows it.

1. Build the component source so the poster stays editable. Use the editor's element types
   from `references/editor-source-format.md`; a component source is the deliverable
   form of the artwork, not an extra.
2. Check the draft at **actual size and actual viewing distance**, not only zoomed in:
   - is the main title the first thing seen?
   - can the smallest required text be read at that distance?
   - do image, text, and logo collide?
   - does the CTA read as an action?
3. Record the intent of this version and what it is still testing, in
   `04-初稿说明.md`.
4. Check the competition: what else is on the same wall, the same feed, the same screen. If the
   goal is to blend in, a loud poster is the wrong poster.

## Stage 5 — Iteration

Produce `05-反馈记录.md` from `templates/05-反馈记录.md`.

1. Log each piece of feedback as: who gave it, what they objected to, the decision, the
   version, the date. Separate design feedback from factual corrections and from production
   constraints.
2. Re-verify the facts after every revision that touched copy. Copy changes are where wrong
   dates and prices enter.
3. Bump the version in the project README and in the component source.
4. When the project ends, write a production-verification card: which assumption held, which
   fell, what the next project should ask first.

## Stage 6 — Output

Follow `deliver.md` for the file set, the channel adaptation, and the delivery check.

## Quick profile

Quick is Create with the stage 1 and stage 2 user gates removed. Everything else is
unchanged.

- The brief, copy sheet, and open-questions list are still written, and every unconfirmed
  value is marked `待确认` in the file itself.
- The first draft is produced without asking for confirmation, then presented with the
  direction and the open-questions list together.
- The delivery gate stays closed until the open questions are answered. Quick never ships a
  poster with invented facts.

