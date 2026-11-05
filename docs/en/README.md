# Poster Master documentation

[中文](../README.md)

Poster Master is an agent skill package. It turns "make a poster" into an executable, checkable,
archivable workflow, and it ships a dependency-free local editor.

## The shape of the work

```text
brief / client material
   ↓  stage 1 Goal       audience, primary effect, core message
   ↓  stage 2 Information copy hierarchy + open questions
   ↓  stage 3 Direction  keywords, palette, type, key visual
   ↓  stage 4 Draft      at least one readable composition
   ↓  stage 5 Iteration  a versioned feedback log
   ↓  stage 6 Output     PNG / SVG / layered PSD + delivery check
component source (editable) · process documents (archivable) · delivery report
```

## Documentation map

| Document | Read it when |
|---|---|
| [Getting started](getting-started.md) | First run: one complete walk-through |
| [Installation](installation.md) | Installing the skill and its dependencies |
| [Workflow](workflow.md) | You want the detail behind each stage and gate |
| [Editor](editor.md) | You want to edit the source and export formats |
| [FAQ](faq.md) | You hit a specific error or an unclear behaviour |
| [Why it is built this way](why-poster-master.md) | You are about to change the skill itself |

## Reference documents inside the package

The package carries 12 reference documents that an agent loads **after** it has picked a route:

| Reference | Covers |
|---|---|
| <code>references/six-stage-workflow.md</code> | The full procedure, artefacts and template mapping |
| <code>references/intake-and-brief.md</code> | Question order, missing facts vs design assumptions |
| <code>references/information-hierarchy.md</code> | Information hierarchy and P0/P1/P2 tagging |
| <code>references/audience-and-purpose.md</code> | How audience and channel decide the visual language |
| <code>references/creative-direction.md</code> | What makes a direction sheet executable |
| <code>references/style-and-components.md</code> | Reuse rules for styles and components |
| <code>references/formats-and-sizes.md</code> | Carrier differences: print, social, digital screens |
| <code>references/asset-intake.md</code> | Asset admission, rights state, naming, ledger |
| <code>references/asset-processing.md</code> | Order of operations for cutout, retouch, extend, generate |
| <code>references/qr-and-brand-assets.md</code> | The red lines for QR codes and brand assets |
| <code>references/compliance-and-delivery.md</code> | Compliance, font licensing, delivery checks |
| <code>references/editor-source-format.md</code> | Component source format and element types |

## One line to an agent

```text
$poster-master Use this skill to make a recruitment poster. Material is in ./assets, size A3, link https://example.com/join
```

The agent reads <code>SKILL.md</code> and selects the route itself. You do not need to memorise
any of this.
