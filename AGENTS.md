# Repository working rules

This file applies to the whole repository.

## What this repository is

A published agent skill package plus the documentation and download surface around it.
The runnable skill lives in <code>skills/poster-master/</code>. Everything else in this
repository supports it.

## Rules

1. **The skill directory is the product.** Changes to <code>skills/poster-master/</code> change
   what every agent gets. Keep its internal structure stable: <code>SKILL.md</code>,
   <code>workflows/</code>, <code>references/</code>, <code>templates/</code>,
   <code>scripts/</code>, <code>examples/</code>.
2. **One route, one procedure file.** Do not merge workflows or make a workflow depend on
   another workflow's procedure.
3. **References are focused.** One topic per document, written for an agent that has to make a
   decision. No copied manuals, no exhaustive catalogues.
4. **No client material, no fonts, no model weights, no generated caches.** The package ships
   shapes, text and one self-generated QR code only.
5. **The example project is the regression baseline.** After changing scripts, regenerate it and
   confirm <code>check_delivery.py</code> reports zero failures:

   ```bash
   node skills/poster-master/examples/build-demo.js
   python skills/poster-master/scripts/render_preview.py \
     --source skills/poster-master/examples/城市夜跑/城市夜跑-组件源稿.poster.json \
     --output skills/poster-master/examples/城市夜跑/exports/城市夜跑-v1-预览.png
   python skills/poster-master/scripts/check_delivery.py --project skills/poster-master/examples/城市夜跑
   ```

6. **Version bumps are explicit.** Update <code>version</code> in <code>SKILL.md</code> and the
   version in <code>.claude-plugin/marketplace.json</code> together, then rebuild the archive:

   ```bash
   python tools/package_skill.py
   ```

7. **Chinese first.** Repository documents default to Chinese, with an English mirror under
   <code>docs/en/</code> and <code>README_EN.md</code>. Add both when adding a document.
8. **Keep the editor dependency-free.** <code>skills/poster-master/scripts/editor/</code> runs on
   the Node standard library only — no npm dependencies, no network calls, loopback binding only.

## Before you push

```bash
python tools/package_skill.py
python skills/poster-master/scripts/quick_validate.py skills/poster-master
node --check skills/poster-master/scripts/editor/server.js
node --check skills/poster-master/scripts/editor/public/app.js
```

Commit messages describe the change in one line, then the reason in the body when the reason is
not obvious.
