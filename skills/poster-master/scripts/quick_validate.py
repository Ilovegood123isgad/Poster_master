#!/usr/bin/env python3
"""Structural validation for this skill package.

    python quick_validate.py "<skill-dir>"

Run this after changing anything in the package and before packaging a release.
It answers one question: would an agent that follows these files hit a dead end?

Checks, in the order a failure hurts most:

1. `SKILL.md` exists, has YAML front matter, and declares `name` and `description`.
2. The directories the entry point promises exist.
3. Every file path mentioned in the documentation actually exists — including
   paths inside inline `<code>` spans and fenced code blocks, which is where
   dead references normally hide.
4. No broken-markdown placeholder tokens (a bad export once shipped 23 of them).
5. Every JSON file parses.
6. Every Python script compiles; every Node script passes `node --check` when
   Node is available.
7. The scripts referenced by the docs are listed in `scripts/README.md`.

Exit code 0 = valid. Anything else is a real defect, not a style note.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_DIRS = ["workflows", "references", "templates", "scripts"]
# The broken-export placeholder, assembled so this file does not contain it.
PLACEHOLDER = "[[" + "BT]]"
SCRIPT_REFERENCES = re.compile(r"(?:\.\./|scripts/|\$\{SKILL_DIR\}/)(?:scripts/)?([a-z0-9_]+\.(?:py|js))", re.I)
DOC_REFERENCES = re.compile(
    r"(?:\.\./)?(references|workflows|templates|scripts|examples)/"
    r"([^\s`\"'()<>\[\]，。；、]+\.(?:md|json|js|py|yaml|txt))",
    re.I,
)


class Validator:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked = 0

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    # ---- 1. entry point --------------------------------------------------

    def check_skill_md(self) -> dict:
        path = self.root / "SKILL.md"
        if not path.exists():
            self.error("缺少 SKILL.md")
            return {}
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            self.error("SKILL.md 没有 YAML front matter")
            return {"text": text}
        end = text.find("\n---", 3)
        if end < 0:
            self.error("SKILL.md 的 front matter 没有结束标记")
            return {"text": text}
        front = text[3:end]
        meta: dict[str, str] = {}
        pending_block: str | None = None
        block: list[str] = []
        for line in front.splitlines():
            if pending_block:
                if line.strip() and (line.startswith(" ") or line.startswith("\t")):
                    block.append(line.strip())
                    continue
                meta[pending_block] = " ".join(block).strip()
                pending_block, block = None, []
            match = re.match(r"\s*([A-Za-z_]+)\s*:\s*(.*)", line)
            if not match:
                continue
            key, value = match.group(1), match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                pending_block = key
                continue
            meta[key] = value.strip('"\'')
        if pending_block:
            meta[pending_block] = " ".join(block).strip()
        for key in ("name", "description"):
            if not meta.get(key):
                self.error(f"SKILL.md front matter 缺少 {key}")
        if meta.get("name") and meta["name"] != "poster-master":
            self.warn(f"SKILL.md 的 name 是 {meta['name']}，通常应为 poster-master")
        description = meta.get("description", "")
        if len(description) < 40:
            self.warn("description 偏短，触发条件可能不足以让 agent 选中这个技能")
        return {"text": text, "meta": meta}

    # ---- 2. directories --------------------------------------------------

    def check_dirs(self) -> None:
        for name in REQUIRED_DIRS:
            if not (self.root / name).is_dir():
                self.error(f"缺少目录 {name}/")

    # ---- 3. references ---------------------------------------------------

    def iter_docs(self) -> list[Path]:
        docs = [self.root / "SKILL.md"]
        for folder in ("workflows", "references", "templates", "scripts", "examples"):
            directory = self.root / folder
            if directory.is_dir():
                docs.extend(sorted(directory.rglob("*.md")))
        return [path for path in docs if path.exists()]

    def check_references(self) -> None:
        for doc in self.iter_docs():
            text = doc.read_text(encoding="utf-8", errors="replace")
            relative_doc = doc.relative_to(self.root)
            for match in DOC_REFERENCES.finditer(text):
                folder, tail = match.group(1), match.group(2)
                target = self.root / folder / tail
                if target.exists():
                    self.checked += 1
                    continue
                # also try relative to the document (workflows/x.md -> ../references/y.md)
                sibling = (doc.parent / folder / tail).resolve()
                if sibling.exists():
                    self.checked += 1
                    continue
                self.error(f"{relative_doc} 引用了不存在的文件：{folder}/{tail}")

    # ---- 4. placeholders -------------------------------------------------

    def check_placeholders(self) -> None:
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (
                ".md", ".py", ".js", ".json", ".yaml", ".yml", ".css", ".html", ".txt"
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if PLACEHOLDER in text:
                count = text.count(PLACEHOLDER)
                self.error(f"{path.relative_to(self.root)} 有 {count} 处占位符残留")

    # ---- 5. JSON ---------------------------------------------------------

    def check_json(self) -> None:
        for path in self.root.rglob("*.json"):
            if any(part.startswith(".") for part in path.parts):
                continue
            try:
                json.loads(path.read_text(encoding="utf-8"))
                self.checked += 1
            except json.JSONDecodeError as error:
                self.error(f"{path.relative_to(self.root)} JSON 解析失败：{error}")

    # ---- 6. scripts ------------------------------------------------------

    def check_scripts(self) -> None:
        scripts = self.root / "scripts"
        if not scripts.is_dir():
            return
        for path in sorted(scripts.glob("*.py")):
            completed = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True, text=True,
            )
            if completed.returncode != 0:
                self.error(f"{path.name} 语法错误：{completed.stderr.strip().splitlines()[-1:]}")
            else:
                self.checked += 1
        node = shutil.which("node")
        if node:
            for path in sorted(list(scripts.glob("*.js")) + list(scripts.rglob("*.js"))):
                if "node_modules" in str(path):
                    continue
                completed = subprocess.run([node, "--check", str(path)],
                                           capture_output=True, text=True)
                if completed.returncode != 0:
                    self.error(f"{path.relative_to(self.root)} 语法错误")
                else:
                    self.checked += 1
        else:
            self.warn("没有 node，跳过 JavaScript 语法检查")

    # ---- 7. script inventory --------------------------------------------

    # ---- 7. script inventory --------------------------------------------

    def check_orphans(self) -> None:
        """A reference nobody links to is a reference nobody will read."""
        mentioned = "\n".join(
            doc.read_text(encoding="utf-8", errors="replace") for doc in self.iter_docs()
        )
        for folder in ("references", "workflows"):
            directory = self.root / folder
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.md")):
                if path.name in ("index.md", "routing.md"):
                    continue
                if path.name not in mentioned:
                    self.warn(f"{folder}/{path.name} 没有被任何文档引用")

    def check_script_inventory(self) -> None:
        readme = self.root / "scripts" / "README.md"
        if not readme.exists():
            self.error("缺少 scripts/README.md")
            return
        listed = readme.read_text(encoding="utf-8")
        for path in sorted((self.root / "scripts").glob("*.py")):
            if path.name not in listed:
                self.warn(f"scripts/{path.name} 没有登记在 scripts/README.md 里")
        for path in sorted((self.root / "scripts").glob("*.js")):
            if path.name not in listed:
                self.warn(f"scripts/{path.name} 没有登记在 scripts/README.md 里")

    def run(self) -> int:
        self.check_skill_md()
        self.check_dirs()
        self.check_references()
        self.check_placeholders()
        self.check_json()
        self.check_scripts()
        self.check_orphans()
        self.check_script_inventory()

        for message in self.warnings:
            print(f"[WARN] {message}")
        for message in self.errors:
            print(f"[FAIL] {message}")
        print("-" * 68)
        if self.errors:
            print(f"结论：{len(self.errors)} 项失败，{len(self.warnings)} 项提示，已验证 {self.checked} 个对象")
            return 1
        print(f"Skill is valid! 涉及 {len(self.warnings)} 项提示，已验证 {self.checked} 个对象")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="poster-master 技能包结构校验")
    parser.add_argument("path", nargs="?", default=str(Path(__file__).resolve().parents[1]),
                        help="技能包根目录（默认本脚本的上级目录）")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not root.is_dir():
        sys.exit(f"不是目录：{root}")
    sys.exit(Validator(root).run())


if __name__ == "__main__":
    main()
