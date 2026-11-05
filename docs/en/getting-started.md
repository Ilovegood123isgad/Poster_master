# Getting started

[中文](../getting-started.md) · [Docs index](README.md)

## One complete walk-through

The brief: **"The cycling club needs a recruitment poster next week. A3, sign-up link
https://example.com/join, and the night-ride photo I sent is the key visual."**

### Step 0 — install the skill

See [Installation](installation.md). When it is done, <code>SKILL.md</code> exists in the skill
directory.

### Step 1 — let the agent pick a route

```text
$poster-master Make a recruitment poster for the cycling club. A3, sign-up link https://example.com/join,
key visual is assets/night-ride.jpg, registration closes on 26 October.
```

The agent reads <code>SKILL.md</code>, then <code>workflows/routing.md</code>, and selects
**new poster**. If you add "do not ask me anything, just make it", it takes the Quick profile and
skips the confirmation round trip.

### Step 2 — answer the questions that actually change the design

| Question | Why it is unavoidable |
|---|---|
| Where does it run? Campus screen, printed board, social post? | Decides size, bleed, colour mode, file format |
| How far away is it read? One metre, three metres? | Decides the type scale of the headline |
| What is the minimum information? Time, place, quota, gear? | Decides what goes in the information card |
| Is that link final? A short link, or one with tracking parameters? | The code must be regenerated from the confirmed link |
| Who owns the image and the font? Commercial and print rights? | An asset with an unknown rights state never ships |

Confirmed content is marked as a **fact**. Assumed content is marked as an **assumption**. The two
never share a label.

### Step 3 — receive the stage artefacts

```text
my-project/
├─ 01-需求简报.md
├─ 02-文案层级表.md
├─ 02-待确认问题.md
├─ 03-创意方向.md
├─ 04-初稿说明.md
├─ 05-反馈记录.md
├─ 06-交付检查表.md
├─ 素材台账.md
├─ assets/
├─ exports/
└─ project-name-组件源稿.poster.json
```

### Step 4 — draft and revise

A draft is judged at its real size, not by how good the thumbnail looks. Revisions go through the
**revise** route, re-entering the stage that owns the change, and every decision is written into
<code>05-反馈记录.md</code>.

### Step 5 — deliver

```bash
python "<skill dir>/scripts/check_delivery.py" --project "<project dir>"
```

The report separates what was **verified** (dimensions, colour mode, file integrity, QR
decodability) from what still needs **a human** (distance legibility, copy facts, scanning the code
on a phone, font and image rights).

## The two commands you will use most

```bash
# 1. Scaffold a project
node "<skill dir>/scripts/new_project.js" --project "<project dir>" --name "Name" --size 1080x1440

# 2. Open the editor (edit elements, export PNG / SVG / PSD)
node "<skill dir>/scripts/editor/server.js" --project "<project dir>" --port 41735
```

## No browser? Still fine

```bash
python "<skill dir>/scripts/render_preview.py" \
  --source "<project dir>/project-name-组件源稿.poster.json" \
  --output "<project dir>/exports/preview.png"
```

## Next

- [Workflow](workflow.md) for the detail behind each stage
- [Editor](editor.md) for editing the source and exporting
- [FAQ](faq.md) when something breaks
