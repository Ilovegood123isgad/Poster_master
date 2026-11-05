# Contributing

Thanks for improving Poster Master. This repository is a published skill package, so changes are
visible to every agent that installs it.

## What helps most

- **A real failure and its fix.** The best contributions come from a poster that went wrong:
  a QR that stopped decoding, a layout that failed at print size, a handoff that lost a fact.
- **Sharper decisions in the references.** If a reference document leaves a choice to taste, say
  what the decision depends on.
- **A safer script.** More edge-quality reporting, fewer false passes, clearer errors.
- **Documentation in both languages.** Chinese and English, same content.

## What does not help

- New dependencies for the editor or the core scripts.
- Templates, clip art, stock imagery, fonts, or model weights.
- Generic poster advice that no decision depends on.
- A workflow file that loads another workflow's procedure.

## Workflow

1. Open an issue describing the failure, not only the fix.
2. Work on a branch: <code>git checkout -b codex/short-description</code>.
3. Keep the change inside <code>skills/poster-master/</code> plus the documents that describe it.
4. Run the regression baseline (see <code>AGENTS.md</code>).
5. Bump the version in <code>skills/poster-master/SKILL.md</code> and
   <code>.claude-plugin/marketplace.json</code> when the change affects agents.
6. Rebuild the archive with <code>python tools/package_skill.py</code> and commit it.
7. Open a pull request describing the before and after.

## Commit messages

```text
fix: decode QR codes that were scaled with smoothing

The delivery check reported "detected but not decodable" for codes placed
through an interpolated resize. Nearest-neighbour sampling keeps the module
edges intact.
```

## Code of conduct

Be direct, be factual, and critique the work rather than the person. Assume the other side is
trying to ship something that works.
