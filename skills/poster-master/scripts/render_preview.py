#!/usr/bin/env python3
"""Poster Master — headless renderer for a component source.

    python render_preview.py --source 城市夜跑-组件源稿.poster.json --output 预览.png [--scale 1]

Renders a component source to PNG without a browser, using the same geometry
rules as the editor: x/y is the top-left of the untransformed box, rotation and
scale happen about the element centre, and elements paint in array order.

This is a convenience renderer for agents and quick checks. The editor remains
the reference renderer and the tool that produces the delivered exports.

Fonts are resolved from the operating system. Missing fonts fall back to the
default bitmap font, which changes metrics — install a CJK font for an accurate
preview.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("缺少依赖：Pillow。请先运行 pip install -r requirements.txt")

FONT_CANDIDATES = [
    ("Microsoft YaHei", "C:/Windows/Fonts/msyh.ttc"),
    ("Microsoft YaHei", "C:/Windows/Fonts/msyhl.ttc"),
    ("Arial", "C:/Windows/Fonts/arial.ttf"),
    ("Noto Sans CJK SC", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
BOLD_CANDIDATES = [
    ("Microsoft YaHei", "C:/Windows/Fonts/msyhbd.ttc"),
    ("Arial", "C:/Windows/Fonts/arialbd.ttf"),
    ("Noto Sans CJK SC Bold", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("DejaVu Sans Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

_font_cache: dict = {}


def resolve_font(family: str, size: int, bold: bool):
    key = (family or "", size, bold)
    if key in _font_cache:
        return _font_cache[key]
    candidates = BOLD_CANDIDATES if bold else FONT_CANDIDATES
    prefix = (family or "").lower()[:6]
    preferred = [entry for entry in candidates if entry[0].lower().startswith(prefix)] if prefix else []
    font = None
    for _, path in preferred + candidates:
        if Path(path).exists():
            try:
                font = ImageFont.truetype(path, max(1, size))
                break
            except OSError:
                continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font


def parse_color(value, default=(0, 0, 0, 255)):
    if not value or value == "none":
        return None
    text = str(value).strip()
    if text.startswith("#"):
        text = text[1:]
        if len(text) == 3:
            text = "".join(char * 2 for char in text)
        if len(text) == 6:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        if len(text) == 8:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4, 6))
    return default


def legacy_text(item) -> bool:
    return bool(item.get("psdGroup") and not item.get("group"))


def text_box(draw, item) -> tuple:
    """Return (x, y, box_width, height) of the text block."""
    font = resolve_font(item.get("fontFamily", "Microsoft YaHei"), int(item.get("fontSize", 24)), item.get("fontWeight") == "700")
    lines = str(item.get("text", "")).split("\n")
    line_height = float(item.get("fontSize", 24)) * float(item.get("lineHeight", 1.2))
    width = max((draw.textlength(line, font=font) for line in lines), default=0)
    height = line_height * len(lines)

    if legacy_text(item):
        align = item.get("align", "left")
        x = item.get("x", 0)
        if align == "center":
            x -= width / 2
        elif align == "right":
            x -= width
        y = item.get("y", 0) - height / 2
        return x, y, width, height

    x = item.get("x", 0)
    y = item.get("y", 0)
    box_width = float(item.get("w", 0) or 0)
    if box_width < width:
        box_width = width
    return x, y, box_width, height


def draw_text_element(canvas: Image.Image, item: dict, x: float, y: float, width: float,
                      height: float, scale: int, opacity: float) -> None:
    """Draw text on a tight glyph tile, so no line is clipped by font metrics."""
    font = resolve_font(item.get("fontFamily", "Microsoft YaHei"),
                        int(round(float(item.get("fontSize", 24)) * scale)),
                        item.get("fontWeight") == "700")
    fill = parse_color(item.get("fill"))
    stroke = parse_color(item.get("stroke"))
    stroke_width = int(round(float(item.get("strokeWidth", 0) or 0) * scale))
    font_size = float(item.get("fontSize", 24)) * scale
    line_height = font_size * float(item.get("lineHeight", 1.2))
    align = item.get("align", "left")
    legacy = legacy_text(item)

    prepared = []
    for index, line in enumerate(str(item.get("text", "")).split("\n")):
        advance = font.getlength(line)
        bbox = font.getbbox(line, anchor="ls")
        baseline = font_size * 0.8 + index * line_height
        if legacy:
            draw_x = 0.0
        elif align == "center":
            draw_x = width * scale / 2 - advance / 2
        elif align == "right":
            draw_x = width * scale - advance
        else:
            draw_x = 0.0
        prepared.append((line, draw_x, baseline, bbox))

    left = min(entry[3][0] + entry[1] for entry in prepared)
    top = min(entry[2] + entry[3][1] for entry in prepared)
    right = max(entry[3][2] + entry[1] for entry in prepared)
    bottom = max(entry[2] + entry[3][3] for entry in prepared)
    tile_w = max(1, int(math.ceil(right - left)) + 2)
    tile_h = max(1, int(math.ceil(bottom - top)) + 2)

    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    for line, draw_x, baseline, bbox in prepared:
        tile_draw.text((draw_x - left + 1, baseline - top + 1), line, font=font, fill=fill,
                       anchor="ls", stroke_width=stroke_width, stroke_fill=stroke)

    alpha = tile.getchannel("A").point(lambda value: int(value * opacity))
    tile.putalpha(alpha)
    canvas.alpha_composite(tile, (int(round(x * scale + left - 1)), int(round(y * scale + top - 1))))


def draw_shape_element(canvas: Image.Image, item: dict, assets: Path, scale: int, opacity: float) -> None:
    kind = item.get("type")
    x = float(item.get("x", 0))
    y = float(item.get("y", 0))
    width = float(item.get("w", 0) or 0)
    height = float(item.get("h", 0) or 0)
    if width <= 0 or height <= 0:
        return

    tile_w = max(1, int(round(width * scale)))
    tile_h = max(1, int(round(height * scale)))
    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)

    if kind == "rect":
        radius = min(float(item.get("radius", 0) or 0), width / 2, height / 2) * scale
        box = (0, 0, tile_w - 1, tile_h - 1)
        fill = parse_color(item.get("fill"))
        stroke = parse_color(item.get("stroke"))
        stroke_width = int(round(float(item.get("strokeWidth", 0) or 0) * scale))
        if radius > 0:
            tile_draw.rounded_rectangle(box, radius=radius, fill=fill, outline=stroke, width=stroke_width or 1)
        else:
            tile_draw.rectangle(box, fill=fill, outline=stroke, width=stroke_width or 1)
    elif kind == "ellipse":
        box = (0, 0, tile_w - 1, tile_h - 1)
        fill = parse_color(item.get("fill"))
        stroke = parse_color(item.get("stroke"))
        stroke_width = int(round(float(item.get("strokeWidth", 0) or 0) * scale))
        tile_draw.ellipse(box, fill=fill, outline=stroke, width=stroke_width or 1)
    elif kind == "line":
        stroke = parse_color(item.get("stroke"), (0, 0, 0, 255))
        stroke_width = max(1, int(round(float(item.get("strokeWidth", 1) or 1) * scale)))
        tile_draw.line((0, 0, tile_w - 1, tile_h - 1), fill=stroke, width=stroke_width)
    elif kind == "arc":
        stroke = parse_color(item.get("stroke"), (0, 0, 0, 255))
        stroke_width = max(1, int(round(float(item.get("strokeWidth", 1) or 1) * scale)))
        start = float(item.get("start", 0) or 0)
        raw_end = item.get("end")
        end = float(360 if raw_end is None else raw_end)
        while end <= start:
            end += 360
        tile_draw.arc((0, 0, tile_w - 1, tile_h - 1), start, end, fill=stroke, width=stroke_width)
    elif kind == "image":
        source = assets.parent / str(item.get("src", ""))
        if source.exists():
            # A QR code must not be smoothed: interpolation blurs the module
            # edges and the code stops decoding. Mark such an element with
            # "resample": "nearest" and it is scaled with hard pixels.
            resample = Image.NEAREST if str(item.get("resample", "")).lower() == "nearest" else Image.LANCZOS
            photo = Image.open(source).convert("RGBA").resize((tile_w, tile_h), resample)
            tile.alpha_composite(photo)

    scale_x = float(item.get("scaleX", 1) or 1)
    scale_y = float(item.get("scaleY", 1) or 1)
    angle = float(item.get("angle", 0) or 0)
    if scale_x != 1 or scale_y != 1:
        tile = tile.resize((max(1, int(tile_w * scale_x)), max(1, int(tile_h * scale_y))), Image.LANCZOS)
    if angle:
        tile = tile.rotate(-angle, resample=Image.BICUBIC, expand=True)

    center_x = x * scale + width * scale / 2
    center_y = y * scale + height * scale / 2
    alpha = tile.getchannel("A").point(lambda value: int(value * opacity))
    tile.putalpha(alpha)
    canvas.alpha_composite(tile, (int(round(center_x - tile.width / 2)), int(round(center_y - tile.height / 2))))


def draw_element(canvas: Image.Image, draw: ImageDraw.ImageDraw, item: dict, assets: Path, scale: int) -> None:
    if item.get("visible") is False:
        return
    opacity = float(item.get("opacity", 1))
    if opacity <= 0:
        return
    if item.get("type") == "text":
        x, y, width, height = text_box(draw, item)
        draw_text_element(canvas, item, x, y, width, height, scale, opacity)
        return
    draw_shape_element(canvas, item, assets, scale, opacity)


def render(source: Path, output: Path, scale: int = 1) -> None:
    project = json.loads(source.read_text(encoding="utf-8"))
    canvas_spec = project.get("canvas", {})
    width = int(canvas_spec.get("width", 1024))
    height = int(canvas_spec.get("height", 1536))
    assets = source.parent / "assets"

    supersample = 3
    canvas = Image.new("RGBA", (width * supersample, height * supersample), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    background = parse_color(canvas_spec.get("background"), (255, 255, 255, 255))
    draw.rectangle((0, 0, canvas.width, canvas.height), fill=background)

    for item in project.get("elements", []):
        try:
            draw_element(canvas, draw, item, assets, supersample)
        except Exception as error:
            print(f"  警告：组件 {item.get('id')} 渲染失败：{error}", file=sys.stderr)

    final = canvas.convert("RGB").resize((width * scale, height * scale), Image.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    final.save(output)
    print(f"预览已渲染：{output}（{final.width}×{final.height}，{len(project.get('elements', []))} 个组件）")


def main() -> None:
    parser = argparse.ArgumentParser(description="Poster Master 无头渲染器")
    parser.add_argument("--source", required=True, help="组件源稿 .poster.json")
    parser.add_argument("--output", required=True, help="输出 PNG")
    parser.add_argument("--scale", type=int, default=1, help="输出倍数（默认 1）")
    args = parser.parse_args()
    source = Path(args.source)
    if not source.exists():
        sys.exit(f"源稿不存在：{source}")
    render(source, Path(args.output), max(1, args.scale))


if __name__ == "__main__":
    main()

