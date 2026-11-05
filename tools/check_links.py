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
    return problems


def main() -> None:
    problems = check_skill_links() + check_repo_links()
    if problems:
        print(f"发现 {len(problems)} 个失效引用：")
        for problem in problems:
            print("  -", problem)
        sys.exit(1)
    print("引用检查通过：技能包与仓库文档中的本地链接全部有效。")


if __name__ == "__main__":
    main()
