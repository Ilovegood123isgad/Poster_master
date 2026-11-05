#!/usr/bin/env python3
"""Verify that the committed archive really contains the current skill tree.

    python tools/check_archive.py [--version 1.1.0]

Why not just rebuild the zip and diff the bytes? Because a zip stores each entry's
modification time, so a rebuild on CI produces a different byte stream for identical
content and a byte diff always fails. Comparing the file list and each entry's CRC is
the check that actually means what we want: *the downloadable archive is the code in
this repository*.

Catches the two ways a release goes wrong:

* the version was bumped but `tools/package_skill.py` was never re-run, so the archive
  is for the previous version or does not exist;
* a script was edited and committed, but the archive still carries the old copy.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "poster-master"
DIST = REPO / "dist"

SKIP_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache", "node_modules"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def skill_version() -> str:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"([^"]+)"', text, re.M)
    if not match:
        sys.exit("读不到 SKILL.md 里的 metadata.version")
    return match.group(1)


def expected_entries() -> dict[str, Path]:
    """Same selection rules as tools/package_skill.py, so the two cannot disagree."""
    entries: dict[str, Path] = {}
    for path in sorted(SKILL.rglob("*")):
        if path.is_dir():
            continue
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        # package_skill.py writes paths relative to the skill's parent directory,
        # so every entry is prefixed with the skill folder name.
        entries[f"{SKILL.name}/{path.relative_to(SKILL).as_posix()}"] = path
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="校验 dist 压缩包与技能源码树一致")
    parser.add_argument("--version", default=None, help="默认取 SKILL.md 里的版本")
    args = parser.parse_args()

    version = args.version or skill_version()
    archive = DIST / f"poster-master-skill-v{version}.zip"
    print(f"技能版本：{version}")
    print(f"压缩包　：{archive.name}")

    if not archive.exists():
        print(f"缺少压缩包：dist/{archive.name}（跑 python tools/package_skill.py）")
        sys.exit(1)

    expected = expected_entries()
    problems: list[str] = []

    with zipfile.ZipFile(archive) as handle:
        names = [name for name in handle.namelist() if not name.endswith("/")]
        present = set(names)

        missing = sorted(set(expected) - present)
        extra = sorted(present - set(expected))
        for name in missing[:20]:
            problems.append(f"压缩包缺少：{name}")
        for name in extra[:20]:
            problems.append(f"压缩包里多出：{name}")

        stale = 0
        for name, path in expected.items():
            if name not in present:
                continue
            packed = handle.read(name)
            if packed != path.read_bytes():
                stale += 1
                if stale <= 20:
                    problems.append(f"内容不一致：{name}")

    print(f"条目：压缩包 {len(present)} 个 / 源码树 {len(expected)} 个")
    if problems:
        print(f"\n发现 {len(problems)} 个问题：")
        for problem in problems:
            print("  -", problem)
        print("\n修法：python tools/package_skill.py --source ../skills/poster-master")
        sys.exit(1)

    print("压缩包与源码树一致。")
    sys.exit(0)


if __name__ == "__main__":
    main()
