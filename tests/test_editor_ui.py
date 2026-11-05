#!/usr/bin/env python3
"""Guard the editor's markup wiring, without a browser.

    python tests/test_editor_ui.py

Why this exists: v1.1.0 shipped an editor whose preview overlay was always
visible, because `.preview-overlay { display: grid }` beat the `hidden`
attribute — the author `display` wins over the user-agent `[hidden]` rule. The
server answered 200, `app.js` had no error, and every HTTP check passed. The
symptom was "the editor does not open"; the cause was one CSS specificity rule.

A headless screenshot caught it. This test catches the *shape* of it cheaply:
every element the app toggles with `hidden` must still carry the attribute, and
the stylesheet must keep the rule that makes it win.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
PUBLIC = SKILL / "scripts" / "editor" / "public"
HTML = PUBLIC / "index.html"
CSS = PUBLIC / "style.css"
APP = PUBLIC / "app.js"

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def main() -> None:
    for path in (HTML, CSS, APP):
        if not path.exists():
            sys.exit(f"缺少 {path}")

    html = HTML.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")

    # 1. the rule that makes `hidden` win over an author `display`
    check(
        re.search(r"\[hidden\]\s*\{[^}]*display\s*:\s*none\s*!important", css) is not None,
        "style.css 里有 `[hidden] { display: none !important }`",
    )

    # 2. elements the app toggles still start hidden
    for element_id in ("previewOverlay", "exportMenu"):
        pattern = rf'id="{element_id}"[^>]*\bhidden\b'
        check(re.search(pattern, html) is not None, f"#{element_id} 初始带 hidden 属性")

    # 3. the overlay really does set a display value — the reason the rule is needed
    overlay = re.search(r"\.preview-overlay\s*\{([^}]*)\}", css)
    check(
        overlay is not None and "display" in overlay.group(1),
        ".preview-overlay 自己设置了 display（所以必须有全局 hidden 兜底）",
    )

    # 4. the export menu still exposes everything the docs promise
    for token, description in (
        ('data-export="png1"', "PNG 1×"),
        ('data-export="png2"', "PNG 2×"),
        ('data-export="png3"', "PNG 3×"),
        ('data-export="svg"', "SVG"),
        ('data-export="psd"', "PSD"),
        ('id="psdGranularity"', "分层粒度"),
        ('id="psdDpi"', "dpi 输入"),
        ('id="psdNote"', "层数提示"),
    ):
        check(token in html, f"导出菜单包含 {description}")

    # 5. the crash that made the editor unusable in v1.0.0 must not come back
    for name in ("zoomIn", "zoomOut", "zoomFit", "zoomLabel"):
        check(
            re.search(rf"{name}\s*:\s*document\.getElementById", app) is not None,
            f"app.js 的 dom 映射包含 {name}",
        )
    check("updatePsdNote" in app, "app.js 有 updatePsdNote（层数提示会刷新）")
    check(
        re.search(r"function buildSvg\(elements,\s*includeBackground", app) is not None,
        "buildSvg 支持 includeBackground（否则 PSD 每层都带不透明底）",
    )

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
