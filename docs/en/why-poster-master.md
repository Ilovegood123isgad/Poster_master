# Why it is built this way

[中文](../why-poster-master.md) · [Docs index](README.md)

This document is for **people who want to change the skill**. Boundaries first, then what you may
change.

## What it is not

Not a poster template library. Templates give fixed layouts; this skill faces a different brief
every time.

Not a one-shot prompt. Poster work spans days, people and conversations, so the process, the
artefacts and the state live in the project folder, not in a chat scrollback.

Not an image generation service. The package binds to no model; it governs what happens after
generation: fact checks, asset admission, QR regeneration, delivery checks.

## Three decisions

### Routing instead of one universal flow

Creating, revising, refining in the editor and delivering have completely different contexts. A
universal flow would re-run intake for a changed date. So <code>SKILL.md</code> only owns
routing; each route owns its own procedure file, and cross-loading is explicitly forbidden.

### Mandatory load order

The entry point holds global discipline and the routing table only. Details live in
<code>workflows/</code>, <code>references/</code> and <code>templates/</code>, so any single call
loads only what that task needs.

### Machine checks for machine questions

Dimensions, colour mode, file integrity and QR decodability have definite answers, so scripts
answer them. What stays human is the four things a machine cannot judge: distance legibility,
copy facts, scanning on a real phone, and whether an asset may be used. The delivery report names
those four instead of writing "checked".

## Why these six red lines

| Red line | The rework behind it |
|---|---|
| Never redraw or eyeball a QR | A screenshot with a cropped quiet zone, or an expired link |
| Do not restyle product appearance or packaging copy | Changing one word changes a claim |
| Every asset has a rights state | A font that cannot be licensed for print |
| Print and social are separate files | One artwork that is "fine" in both channels and wrong in each |
| Run the delivery check | The size was wrong and nobody noticed |
| Embed or license the font | The client's machine did not have it |

These are hard constraints, not advice. They are the value of the package.

## Repository shape

The repository follows the public structure of
[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master): marketplace manifest, the skill under
<code>skills/</code>, bilingual documentation, a landing page, a downloadable archive.
The real user of this kind of package is another agent, so the repository has to be installable,
discoverable and readable — not merely pretty.

## What you may change

| To change | Edit | Mind |
|---|---|---|
| Process and question order | <code>skills/poster-master/workflows/</code> | Keep one procedure file per route |
| Domain judgement | <code>skills/poster-master/references/</code> | One topic per document, decision-oriented |
| Project document templates | <code>skills/poster-master/templates/</code> | Keep <code>new_project.js</code> in sync |
| Script behaviour | <code>skills/poster-master/scripts/</code> | Re-run the example project afterwards |
| Entry point and red lines | <code>skills/poster-master/SKILL.md</code> | Do not delete red lines to save effort |

Do not introduce generic scaffolding (<code>tests/</code>, CI templates, worktree conventions),
model weights, third-party fonts, or client material.

## How to verify a change

```bash
python "<skill dir>/scripts/quick_validate.py" "<skill dir>"
node "<skill dir>/examples/build-demo.js"
python "<skill dir>/scripts/render_preview.py" \
  --source "<skill dir>/examples/城市夜跑/城市夜跑-组件源稿.poster.json" \
  --output "$TMPDIR/preview.png"
python "<skill dir>/scripts/check_delivery.py" --project "<skill dir>/examples/城市夜跑"
```

The delivery check must report **zero failures**. The example project is the regression baseline:
if it fails, the skill is broken.
