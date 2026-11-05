#!/usr/bin/env python3
"""Component source → SVG with text converted to outlines.

    python export_svg.py --source "<project>.poster.json" --output exports/海报.svg
    python export_svg.py --project "<project-dir>"

Why outlines: a delivered SVG must not depend on the recipient having your fonts.
Leaving ``<text>`` in the file means the recipient sees a substitute face and every
line break, every alignment and every measured gap is wrong. Converting glyphs to
paths makes the file look the same everywhere, and makes it legal to hand over when
the font's licence does not permit redistribution as a font.

Differences from the browser-side export in the editor:

* text becomes paths, not ``<text>``;
* rotation and scale are written as an SVG ``transform`` instead of being baked;
* the font is resolved through the same table the renderer uses, so the SVG and the
  PNG agree on metrics.

Dependencies: Pillow is not needed; fontTools is.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import sys
import xml.sax.saxutils as sax
from pathlib import Path

try:
    from fontTools.misc.transform import Transform
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
except ImportError:
    sys.exit("缺少依赖：fonttools。请先运行 pip install -r requirements.txt")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_preview import _candidates, parse_color, weight_of  # noqa: E402

_font_cache: dict[tuple[str, int], TTFont] = {}


def load_ttfont(family: str, weight: int) -> TTFont:
    key = (family, weight)
    if key in _font_cache:
        return _font_cache[key]
    path = None
    for candidate in _candidates(family, weight, None):
        if Path(candidate).exists():
            path = candidate
            break
    if path is None:
        raise SystemExit(
            f"字体不可用：「{family}」。请在 assets/fonts.json 里登记字体文件，"
            "或改用本机已安装的字族。"
        )
    try:
        font = TTFont(path)
    except Exception as error:                              # noqa: BLE001
        # A .ttc is a collection of faces; fontTools refuses it without an index.
        if "collection" in str(error).lower() or "font number" in str(error).lower():
            font = TTFont(path, fontNumber=0)
        else:
            raise
    if "fvar" in font:
        # Instantiate the variable axis at the requested weight so the outlines are
        # exactly the weight the design asked for.
        font = instantiateVariableFont(font, {"wght": weight}, inplace=True)
    _font_cache[key] = font
    return font


def colour_attrs(colour, opacity: float) -> tuple[str, str]:
    r, g, b, a = parse_color(colour, (0, 0, 0, 255))
    return f"#{r:02x}{g:02x}{b:02x}", f"{a / 255 * opacity:.3f}"


def escape(text: str) -> str:
    return sax.escape(text, {'"': "&quot;"})


def element_transform(item: dict) -> str:
    """Rotation and scale about the element centre, as an SVG transform."""
    angle = float(item.get("angle", 0) or 0)
    scale_x = float(item.get("scaleX", 1) or 1)
    scale_y = float(item.get("scaleY", 1) or 1)
    if not angle and scale_x == 1 and scale_y == 1:
        return ""
    x = float(item.get("x", 0))
    y = float(item.get("y", 0))
    width = float(item.get("w", 0) or 0)
    height = float(item.get("h", 0) or 0)
    centre_x = x + width / 2
    centre_y = y + height / 2
    parts = [f"translate({centre_x:g} {centre_y:g})"]
    if angle:
        parts.append(f"rotate({angle:g})")
    if scale_x != 1 or scale_y != 1:
        parts.append(f"scale({scale_x:g} {scale_y:g})")
    parts.append(f"translate({-centre_x:g} {-centre_y:g})")
    return " ".join(parts)


def text_to_paths(item: dict, opacity: float) -> str:
    family = item.get("fontFamily", "")
    weight = weight_of(item)
    font = load_ttfont(family, weight)
    glyphset = font.getGlyphSet()
    cmap = font.getBestCmap()
    units = font["head"].unitsPerEm

    size = float(item.get("fontSize", 24))
    scale = size / units
    line_height = size * float(item.get("lineHeight", 1.2))
    align = item.get("align", "left")
    x0 = float(item.get("x", 0))
    y0 = float(item.get("y", 0))
    box_w = float(item.get("w", 0) or 0)
    lines = str(item.get("text", "")).split("\n")

    fill, fill_alpha = colour_attrs(item.get("fill", "#000000"), opacity)
    stroke_width = float(item.get("strokeWidth", 0) or 0)
    stroke_attr = ""
    if stroke_width > 0 and item.get("stroke"):
        stroke, stroke_alpha = colour_attrs(item.get("stroke"), opacity)
        stroke_attr = (f' stroke="{stroke}" stroke-opacity="{stroke_alpha}"'
                       f' stroke-width="{stroke_width:g}" paint-order="stroke"')

    out = [f'<g fill="{fill}" fill-opacity="{fill_alpha}"{stroke_attr}>']
    for index, line in enumerate(lines):
        widths = []
        for char in line:
            name = cmap.get(ord(char))
            widths.append(glyphset[name].width * scale if name else size * 0.5)
        total = sum(widths)
        if align == "center" and box_w:
            pen_x = x0 + (box_w - total) / 2
        elif align == "right" and box_w:
            pen_x = x0 + box_w - total
        else:
            pen_x = x0
        baseline = y0 + size * 0.8 + index * line_height
        for char, advance in zip(line, widths):
            name = cmap.get(ord(char))
            if name:
                pen = SVGPathPen(glyphset)
                glyphset[name].draw(TransformPen(
                    pen, Transform(scale, 0, 0, -scale, pen_x, baseline)))
                commands = pen.getCommands()
                if commands:
                    out.append(f'<path d="{commands}"/>')
            pen_x += advance
    out.append("</g>")
    return "".join(out)


def shape_svg(item: dict, opacity: float, assets: Path) -> str:
    kind = item.get("type")
    x = float(item.get("x", 0))
    y = float(item.get("y", 0))
    width = float(item.get("w", 0) or 0)
    height = float(item.get("h", 0) or 0)
    stroke_width = float(item.get("strokeWidth", 0) or 0)
    transform = element_transform(item)
    wrapper_open = f'<g transform="{transform}">' if transform else ""
    wrapper_close = "</g>" if transform else ""

    def stroke_attrs(default_width: float = 1.0) -> str:
        if not item.get("stroke") or stroke_width <= 0:
            return ""
        stroke, alpha = colour_attrs(item.get("stroke"), opacity)
        return (f' stroke="{stroke}" stroke-opacity="{alpha}"'
                f' stroke-width="{stroke_width or default_width:g}"')

    if kind == "rect":
        fill, alpha = colour_attrs(item.get("fill"), opacity)
        radius = float(item.get("radius", 0) or 0)
        body = (f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}"'
                f' rx="{radius:g}" ry="{radius:g}" fill="{fill}" fill-opacity="{alpha}"'
                f'{stroke_attrs()}/>')
    elif kind == "ellipse":
        fill, alpha = colour_attrs(item.get("fill"), opacity)
        body = (f'<ellipse cx="{x + width / 2:g}" cy="{y + height / 2:g}"'
                f' rx="{width / 2:g}" ry="{height / 2:g}" fill="{fill}" fill-opacity="{alpha}"'
                f'{stroke_attrs()}/>')
    elif kind == "line":
        stroke, alpha = colour_attrs(item.get("stroke") or item.get("fill"), opacity)
        body = (f'<line x1="{x:g}" y1="{y:g}" x2="{x + width:g}" y2="{y + height:g}"'
                f' stroke="{stroke}" stroke-opacity="{alpha}"'
                f' stroke-width="{stroke_width or 1:g}"/>')
    elif kind == "arc":
        stroke, alpha = colour_attrs(item.get("stroke"), opacity)
        start = float(item.get("start", 0) or 0)
        end = float(item.get("end", 360) or 0)
        while end <= start:
            end += 360
        cx, cy = x + width / 2, y + height / 2
        rx, ry = width / 2, height / 2
        a1, a2 = math.radians(start), math.radians(end)
        p1 = (cx + rx * math.cos(a1), cy + ry * math.sin(a1))
        p2 = (cx + rx * math.cos(a2), cy + ry * math.sin(a2))
        large = 1 if (end - start) % 360 > 180 else 0
        body = (f'<path d="M {p1[0]:.2f} {p1[1]:.2f} A {rx:g} {ry:g} 0 {large} 1'
                f' {p2[0]:.2f} {p2[1]:.2f}" fill="none" stroke="{stroke}"'
                f' stroke-opacity="{alpha}" stroke-width="{stroke_width or 1:g}"/>')
    elif kind == "image":
        source = Path(str(item.get("src", "")))
        if not source.is_absolute():
            source = assets / source.name
        if not source.exists():
            print(f"  警告：图片不存在 {source}", file=sys.stderr)
            return ""
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".webp": "image/webp"}.get(source.suffix.lower(), "image/png")
        data = base64.b64encode(source.read_bytes()).decode("ascii")
        body = (f'<image x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}"'
                f' preserveAspectRatio="none" opacity="{opacity:g}"'
                f' href="data:{mime};base64,{data}"/>')
        wrapper_open = wrapper_close = ""      # opacity already applied
    else:
        print(f"  警告：未知元素类型 {kind!r}", file=sys.stderr)
        return ""

    return wrapper_open + body + wrapper_close


def build_svg(project: dict, assets: Path) -> str:
    width = int(project["canvas"]["width"])
    height = int(project["canvas"]["height"])
    background, _ = colour_attrs(project["canvas"].get("background", "#ffffff"), 1.0)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}"/>',
    ]
    for item in project.get("elements", []):
        if item.get("visible") is False:
            continue
        opacity = float(item.get("opacity", 1) or 0)
        if opacity <= 0:
            continue
        if item.get("type") == "text":
            inner = text_to_paths(item, opacity)
            transform = element_transform(item)
            if transform:
                parts.append(f'<g transform="{transform}">{inner}</g>')
            else:
                parts.append(inner)
        else:
            parts.append(shape_svg(item, opacity, assets))
    parts.append("</svg>")
    return "\n".join(part for part in parts if part)


def main() -> None:
    parser = argparse.ArgumentParser(description="把组件源稿导出为文字转曲的 SVG")
    parser.add_argument("--source")
    parser.add_argument("--output")
    parser.add_argument("--project", help="项目文件夹（自动找 *.poster.json）")
    args = parser.parse_args()

    if args.project:
        project_dir = Path(args.project).resolve()
        matches = sorted(project_dir.glob("*.poster.json"))
        if not matches:
            sys.exit(f"{project_dir} 里没有 *.poster.json")
        source = matches[0]
        output = Path(args.output) if args.output else project_dir / "exports" / "矢量.svg"
    else:
        if not args.source or not args.output:
            sys.exit("用法：python export_svg.py --source <源稿> --output <svg>")
        source = Path(args.source)
        output = Path(args.output)

    project = json.loads(source.read_text(encoding="utf-8"))
    svg = build_svg(project, source.parent / "assets")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    texts = svg.count("<text")
    print(f"SVG 已导出：{output}（{len(svg) / 1024:.0f} KB，"
          f"{'文字已全部转轮廓' if texts == 0 else f'仍有 {texts} 个 <text>'}）")


if __name__ == "__main__":
    main()
