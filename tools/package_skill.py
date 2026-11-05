#!/usr/bin/env python3
"""Build the downloadable Poster Master skill package.

    python tools/package_skill.py [--source "<skill-dir>"] [--repo "<repo-root>"]

Without --source the script packages the skill that already lives in the
repository. With --source it first copies that skill into the repository, so
the published tree never drifts from the working copy.

The output is dist/poster-master-skill-<version>.zip: the skill folder at the
zip root, ready to drop into ~/.claude/skills or ~/.codex/skills.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

SKIP_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache", "node_modules"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def skill_version(skill_dir: Path) -> str:
    match = re.search(r'^\s*version:\s*"([^"]+)"', (skill_dir / "SKILL.md").read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else "0.0.0"


def copy_skill(source: Path, target: Path) -> int:
    if target.exists():
        shutil.rmtree(target)
    copied = 0
    for path in sorted(source.rglob("*")):
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            copied += 1
    return copied


def build_zip(skill_dir: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_dir():
                continue
            if any(part in SKIP_NAMES for part in path.parts) or path.suffix in SKIP_SUFFIXES:
                continue
            archive.write(path, path.relative_to(skill_dir.parent))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="打包 Poster Master 技能")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--source", help="要同步进仓库的技能目录（省略则使用仓库内已有的）")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    skill_dir = repo / "skills" / "poster-master"
    if args.source:
        source = Path(args.source).resolve()
        if not (source / "SKILL.md").is_file():
            sys.exit(f"源目录里没有 SKILL.md：{source}")
        count = copy_skill(source, skill_dir)
        print(f"已同步 {count} 个文件：{source} -> {skill_dir}")

    if not (skill_dir / "SKILL.md").is_file():
        sys.exit(f"找不到技能目录：{skill_dir}")

    version = skill_version(skill_dir)
    output = build_zip(skill_dir, repo / "dist" / f"poster-master-skill-{version}.zip")
    print(f"打包完成：{output}（{output.stat().st_size // 1024} KB，版本 {version}）")


if __name__ == "__main__":
    main()
