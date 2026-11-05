# Installation

[中文](../installation.md) · [Docs index](README.md)

## Three ways in

### 1. Claude Code marketplace

```text
/plugin marketplace add Ilovegood123isgad/Poster_master
/plugin install poster-master@poster-master
```

The manifest lives in <code>.claude-plugin/marketplace.json</code>; the skill itself lives in
<code>skills/poster-master/</code>.

### 2. Codex / any agent: download and unzip

1. Download [poster-master-skill-1.0.0.zip](../../dist/poster-master-skill-1.0.0.zip).
2. Unzip it; you get a <code>poster-master/</code> folder.
3. Put that whole folder into your skills directory:
   - Windows: <code>%USERPROFILE%\.codex\skills\</code> or <code>%USERPROFILE%\.claude\skills\</code>
   - macOS / Linux: <code>~/.codex/skills/</code> or <code>~/.claude/skills/</code>

The layout must be exactly this — <code>SKILL.md</code> on the first level:

```text
skills/
└─ poster-master/
   ├─ SKILL.md
   ├─ agents/openai.yaml
   ├─ workflows/
   ├─ references/
   ├─ templates/
   └─ scripts/
```

### 3. Git clone

```bash
git clone https://github.com/Ilovegood123isgad/Poster_master.git
cp -R Poster_master/skills/poster-master ~/.codex/skills/
```

## Verify the install

**No dependencies required:**

```bash
node "<skill dir>/scripts/new_project.js" --help
node --check "<skill dir>/scripts/editor/server.js"
```

**Python scripts:**

```bash
pip install -r "<skill dir>/requirements.txt"
python "<skill dir>/scripts/check_delivery.py" --help
```

**Package structure:**

```bash
python "<skill dir>/scripts/quick_validate.py" "<skill dir>"
```

## Dependency matrix

| Capability | Needs | Notes |
|---|---|---|
| Editor, project scaffolder | Node.js 18+ | Standard library only, zero npm dependencies |
| Headless rendering, PSD export, delivery checks | Python 3.9+, Pillow | <code>pip install -r requirements.txt</code> |
| QR detection and regeneration | numpy, opencv-python | Installed with requirements.txt |
| Background removal | rembg (optional) | Downloads a segmentation model on first use |

## Environment variables

| Variable | Purpose |
|---|---|
| <code>POSTER_EDITOR_PYTHON</code> | How the editor calls Python. Defaults to <code>python</code>. Set it to <code>python3</code> if that is what your machine has. |

## Common installation problems

**On Windows <code>python3</code> exits immediately with no output.**
That is the WindowsApps alias stub, not a real interpreter. Use <code>python</code>, or set
<code>POSTER_EDITOR_PYTHON=python</code>.

**"Port already in use".** Pick another one: <code>--port 41736</code>. The default is 41735 on
the loopback interface only.

**Unicode errors on a Chinese path.** Set <code>PYTHONUTF8=1</code> before running the Python
scripts.

**Images do not show in the editor.** <code>src</code> must point inside the project's
<code>assets/</code> folder — absolute paths and URLs are rejected.

**"Layer size mismatch" during PSD export.** Every layer bitmap must match the canvas size. The
editor satisfies this automatically; when calling <code>export_psd.py</code> by hand, a manifest
without width and height takes the size of its first layer.

## Upgrade

```bash
git -C ~/.codex/skills/poster-master pull
```

Or download the archive again and overwrite. The package writes no global configuration.

## Uninstall

Delete the <code>poster-master/</code> folder from your skills directory. Nothing else is left
behind.
