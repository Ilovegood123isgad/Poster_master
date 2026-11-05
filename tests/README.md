# Tests

Regression tests for the skill package. They run in CI on Ubuntu and Windows, and you can
run the same thing locally:

```bash
python tests/run_all.py
```

They are plain scripts, not a framework: each file prints `PASS`/`FAIL` per assertion and
exits non-zero on failure. Nothing here needs a network connection, a particular font, or a
client project.

## Why these exist

The v1.0.0 release shipped a layered PSD that no strict reader could parse, a delivery check
that reported it as passing, an editor that crashed before it rendered anything, and a
renderer that silently dropped every horizontal rule. Every one of those defects survives a
manual "looks fine to me" review and dies to a single assertion. That is the whole argument
for this directory.

## What each file covers

| File | Covers |
|---|---|
| `test_psd_roundtrip.py` | Write a PSD, read it back through `psd-tools`: layer order, layer groups, Chinese names, dpi, and that the stack composites to the intended artwork |
| `test_editor_psd.py` | Start the real server, POST a layer tree, validate the file that comes out; old `layers` payload still accepted; over-deep nesting refused |
| `test_render.py` | `h = 0` rules are drawn, weight 300 vs 900 resolve to different faces, `--dpi` writes `pHYs`, rotation applies to text, centring lands on the box centre |
| `test_svg_export.py` | The exported SVG has no `<text>`, has real paths, carries no `font-family` dependency, and matches the canvas |
| `test_imagegen.py` | Config resolution, key masking, `--dry-run`, a real call against a local stub, wrong-key handling, and that the key never appears in output or in the sidecar |

`run_all.py` runs them in order and summarises.

## What is deliberately not here

- **Client material.** No test depends on a real customer project. Those runs live outside
  the repository and must not be committed.
- **Photoshop.** Not scriptable here. `psd-tools` stands in: it is the strictest reader we can
  gate on in CI, and it is what rejected the broken v1.0.0 file. A human still has to open a
  delivered PSD once.
- **A real image-generation provider.** `test_imagegen.py` uses a local stub. A real
  endpoint needs your own key, and CI must never hold one.

## Adding a test

Keep it offline, keep it under a few seconds, and assert on the behaviour that broke rather
than on the implementation. If a test needs a fixture, generate it in a temp directory inside
the test — nothing in `tests/` should write into the package.
