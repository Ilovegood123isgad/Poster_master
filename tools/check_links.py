#!/usr/bin/env python3
"""Check that the repository points at files that exist.

    python tools/check_links.py

Two kinds of references are checked:

  * inside the skill package: references/workflows/templates/scripts paths
    mentioned in Markdown must resolve to a real file;
  * inside the repository: relative href and src targets in Markdown and in
    index.html must resolve to a real file.

Exit code is non-zero when something is broken.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "poster-master"

SKILL_REF = re.compile(
    r"(?:\.\./)?((?:references|workflows|templates|scripts|agents|examples)/"
    r"[A-Za-z0-9_\-.\u4e00-\u9fff/]+\.(?:md|json|py|js|txt|yaml|png))"
)
HTML_REF = re.compile(r'(?:href|src)="([^"#][^"]*)"')
MD_REF = re.compile(r"\]\((?!https?:|#)([^)]+)\)")


def check_skill_links() -> list[str]:
    problems: list[str] = []
    for path in sorted(SKILL.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in SKILL_REF.finditer(text):
            relative = match.group(1)
            target = (path.parent / relative).resolve()
            if not target.exists() and not (SKILL / relative).exists():
                problems.append(f"{path.relative_to(REPO)} -> {relative}")
    return problems


def check_repo_links() -> list[str]:
    problems: list[str] = []
    targets: list[Path] = [REPO / "index.html"]
    targets.extend(sorted(REPO.rglob("*.md")))
    for path in targets:
        if SKILL in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        refs = HTML_REF.findall(text) if path.suffix == ".html" else MD_REF.findall(text)
        for ref in refs:
            if ref.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            clean = ref.split("#", 1)[0]
            if not clean:
                continue
            if not (path.parent / clean).exists() and not (REPO / clean).exists():
                problems.append(f"{path.relative_to(REPO)} -> {ref}")
        # Documentation also names package files inline, e.g.
        # <code>references/psd-layer-spec.md</code>. Those are instructions a
        # reader will follow, so a typo is a broken link too.
        for match in SKILL_REF.finditer(text):
            relative = match.group(1)
            if not (SKILL / relative).exists():
                problems.append(f"{path.relative_to(REPO)} -> (技能包内) {relative}")
    return problems


def check_versions() -> list[str]:
    """One version, three places that must agree."""
    problems: list[str] = []
    skill_md = SKILL / "SKILL.md"
    if not skill_md.exists():
        return ["找不到 skills/poster-master/SKILL.md"]
    skill_text = skill_md.read_text(encoding="utf-8")
    found = re.search(r'^\s*version:\s*"([^"]+)"', skill_text, re.M)
    if not found:
        return ["SKILL.md 里读不到 metadata.version"]
    version = found.group(1)

    marketplace = REPO / ".claude-plugin" / "marketplace.json"
    if marketplace.exists():
        import json
        try:
            data = json.loads(marketplace.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problems.append(f"marketplace.json 解析失败：{error}")
            data = {}
        meta_version = (data.get("metadata") or {}).get("version")
        if meta_version and meta_version != version:
            problems.append(
                f"版本不一致：SKILL.md {version}，marketplace.json metadata {meta_version}"
            )
        for plugin in data.get("plugins") or []:
            plugin_version = plugin.get("version")
            if plugin_version and plugin_version != version:
                problems.append(
                    f"版本不一致：SKILL.md {version}，插件 {plugin.get('name')} {plugin_version}"
                )

    archive = REPO / "dist" / f"poster-master-skill-v{version}.zip"
    if not archive.exists():
        problems.append(f"缺少当前版本的压缩包：dist/{archive.name}（跑 tools/package_skill.py）")
    return problems


def main() -> None:
    problems = check_skill_links() + check_repo_links() + check_versions()
    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for problem in problems:
            print("  -", problem)
        sys.exit(1)
    print("引用与版本检查通过：本地链接全部有效，版本在技能包、插件清单与压缩包之间一致。")


if __name__ == "__main__":
    main()
