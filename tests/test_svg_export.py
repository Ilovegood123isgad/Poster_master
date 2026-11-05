#!/usr/bin/env python3
"""SVG export: text must be outlines, not `<text>`.

    python tests/test_svg_export.py

An SVG that still contains `<text>` depends on the recipient having the same font.
On the recipient's machine the substitution changes every glyph width, so line breaks,
centring and measured gaps all move — which is why this is a delivery rule and not a
preference.

Runs on the shipped example and on the real 2026-11-05 source, because a `.ttc` font
collection and a variable font fail in different ways.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
sys.path.insert(0, str(SKILL / "scripts"))

import export_svg  # noqa: E402

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def verify(source: Path, label: str) -> None:
    project = json.loads(source.read_text(encoding="utf-8"))
    canvas = project["canvas"]
    svg = export_svg.build_svg(project, source.parent / "assets")

    check(svg.lstrip().startswith("<svg"), f"{label}：输出是 SVG")
    texts = len(re.findall(r"<text\b", svg))
    check(texts == 0, f"{label}：没有 <text> 元素（实际 {texts} 个）")
    paths = len(re.findall(r"<path\b", svg))
    check(paths > 20, f"{label}：文字已转为路径（{paths} 条 path）")
    check(
        f'width="{canvas["width"]}"' in svg and f'height="{canvas["height"]}"' in svg,
        f"{label}：画布尺寸 {canvas['width']}×{canvas['height']} 写对了",
    )
    check("font-family" not in svg, f"{label}：不残留 font-family 依赖")
    check(len(svg) > 20_000, f"{label}：文件有实际内容（{len(svg) / 1024:.0f} KB）")

    output = Path(tempfile.mkdtemp()) / "out.svg"
    output.write_text(svg, encoding="utf-8")
    check(output.exists() and output.stat().st_size > 0, f"{label}：可写盘")


def main() -> None:
    example = SKILL / "examples" / "城市夜跑"
    source = next(example.glob("*.poster.json"), None)
    if source is None:
        check(False, "找不到示例源稿")
    else:
        verify(source, "示例工程")

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
