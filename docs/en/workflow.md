# Workflow

[中文](../workflow.md) · [Docs index](README.md)

## Mandatory load order

1. <code>SKILL.md</code> — global discipline, inputs, six stages, delivery red lines.
2. <code>workflows/routing.md</code> — route selection.
3. The one selected route — only its procedure file.
4. Supporting documents, only when that route triggers them.

**Do not read another route's procedure.** Supporting documents refine one route; they never
compete with it.

## Route selection

| You want to | Route | Procedure |
|---|---|---|
| Make a new poster from a brief or raw material | New poster | <code>workflows/new-poster.md</code> |
| The same, without the confirmation round trip | New poster, Quick profile | same file + Quick notes |
| Change copy, colour or size of an existing poster | Revise poster | <code>workflows/revise-poster.md</code> |
| Adjust element by element in the editor | Editor refine | <code>workflows/editor-refine.md</code> |
| Adapt to channels, produce versions, run the check | Deliver | <code>workflows/deliver.md</code> |

Routing is deterministic. When the request already resolves the route, do not ask the user to
choose.

## The six stages

Every route is one cycle over the same six stages. **The stages belong to the poster, not to the
route** — a revision re-enters at the stage that owns the change.

### Stage 1 — Goal

**Frozen:** audience, primary effect, core message, success criteria.

**Gate:** brief accepted; one primary effect, not three. "Looks premium" is not an effect;
"a passer-by reads the time and place from three metres away" is.

### Stage 2 — Information

**Frozen:** copy set tagged by priority (P0 must-read / P1 secondary / P2 optional), plus an
open-questions list.

**Gate:** every P0 fact is confirmed, or explicitly parked and carried into delivery. Layout may
proceed with placeholder copy, but the delivery gate stays closed.

### Stage 3 — Direction

**Frozen:** 3–5 visual keywords, palette, type, key visual, references.

**Gate:** the direction fits the real carrier and the real audience. A direction sheet is a list
of decisions, not a list of adjectives.

### Stage 4 — First draft

**Frozen:** at least one readable composition, with the intent recorded.

**Gate:** readable at actual size; the hierarchy survives distance.

### Stage 5 — Iteration

**Frozen:** a versioned feedback log where every note has a decision.

**Gate:** facts re-verified; open questions closed or listed for delivery.

### Stage 6 — Output

**Frozen:** channel-specific PNG / SVG / PSD plus a delivery check.

**Gate:** the checklist passes; nothing is described as verified that was not.

## Gates and blocking

At every ⛔ BLOCKING gate the agent stops and waits. It does not decide for you.

Typical blocking points:

- The brief is with the client and awaiting approval.
- A P0 fact is missing and cannot be replaced by a reasonable assumption.
- The QR link differs from the one the client stated.
- The rights state of an asset is unknown.
- The delivery check fails.

Non-blocking steps may continue without asking.

## How to report status

Every report separates three kinds of information:

| Kind | Meaning |
|---|---|
| **Verified** | There is a file, a version, a check result, a date |
| **Designed** | An agent decision, and it can be changed |
| **Assumed** | Provisional, waiting for confirmation |

Never call a draft approved, a mock final, or an untested QR working.

## Stage to reference mapping

| Stages | References |
|---|---|
| 1–2 | <code>intake-and-brief.md</code>, <code>audience-and-purpose.md</code>, <code>information-hierarchy.md</code> |
| 3 | <code>creative-direction.md</code>, <code>style-and-components.md</code> |
| 4–5 | <code>formats-and-sizes.md</code>, <code>asset-intake.md</code>, <code>asset-processing.md</code> |
| 6 | <code>compliance-and-delivery.md</code>, <code>qr-and-brand-assets.md</code>, <code>editor-source-format.md</code> |
