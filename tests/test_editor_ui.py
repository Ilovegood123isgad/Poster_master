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

    # 6. narrow-screen layout: panels become drawers, the canvas keeps the space
    check('id="layersToggle"' in html and 'id="propsToggle"' in html,
          "顶栏有两个面板开关")
    check('id="panelScrim"' in html, "有抽屉遮罩层")
    check("@media (max-width: 1180px)" in css, "style.css 有窄屏断点（1180px）")
    check('data-left="0"' in css and 'data-right="0"' in css,
          "面板开合状态由 data-left / data-right 驱动")
    check("@media (min-width: 1181px)" in css,
          "宽屏的 display:none 被限定在宽屏（否则窄屏抽屉没有滑入过渡）")
    for name in ("applyPanels", "togglePanel", "resetPanelsForWidth", "isNarrow"):
        check(f"function {name}" in app, f"app.js 有 {name}")
    check("state.autoFit" in app, "缩放跟随窗口变化由 state.autoFit 控制")

    # 7. the layer row appends three children, so the grid must have three columns.
    #    It once declared four and pushed every name into an 18px column — the
    #    panel showed "行." instead of "行动文字".
    layer_rule = re.search(r"\.layer\s*\{([^}]*)\}", css)
    columns = re.search(r"grid-template-columns\s*:\s*([^;]+);", layer_rule.group(1)) if layer_rule else None
    check(columns is not None and len(columns.group(1).split()) == 3,
          f".layer 的列数与 DOM 子元素数量一致（3 列），实际：{columns.group(1).strip() if columns else '读不到'}")

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
