#!/usr/bin/env python3
"""Poster Master — headless renderer for a component source.

    python render_preview.py --source 城市夜跑-组件源稿.poster.json --output 预览.png
    python render_preview.py --project "<project-dir>" --dpi 300
    python render_preview.py --source x.poster.json --output a3.png --dpi 300 --width 3508

Renders a component source to PNG without a browser, using the same geometry
rules as the editor: x/y is the top-left of the untransformed box, rotation and
scale happen about the element centre, and elements paint in array order.

Four things this renderer gets right, each of which was a real defect before:

* **Anti-aliasing is per element, not per canvas.** Supersampling the whole
  canvas is what makes an A3 file need ~600 MB; here each element is drawn on
  its own tile at 1–3× and composited down. Peak memory is one canvas plus one
  tile.
* **Real font weights.** ``fontWeight`` accepts 100–900 and is applied to
  variable fonts through their weight axis, so 300 and 900 are different faces
  rather than "regular" and "bold".
* **No silent font substitution.** Family names are matched against a candidate
  table plus an optional ``assets/fonts.json`` registry. When nothing matches,
  the render says so instead of swapping in a lookalike and changing every
  measurement.
* **dpi is written, never assumed.** ``--dpi`` writes a ``pHYs`` chunk. Without
  it every reader opens the file at 72 dpi and the physical size is wrong.

Horizontal and vertical rules (``h = 0`` or ``w = 0``) are drawn as real rules;
the old renderer dropped them.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("缺少依赖：Pillow。请先运行 pip install -r requirements.txt")

# (family, nominal weight, path) — first existing path wins.
#
# Weight is resolved by *file*, not only by variation axis: Microsoft YaHei is
# not a variable font, so 300 and 900 are msyhl.ttc and msyhbd.ttc. Treating
# weight as a cosmetic hint is how a "900" headline ends up regular.
FONT_FILES: list[tuple[str, int, str]] = [
    ("Noto Sans SC", 400, "C:/Windows/Fonts/NotoSansSC-VF.ttf"),        # variable 100–900
    ("Noto Serif SC", 400, "C:/Windows/Fonts/NotoSerifSC-VF.ttf"),
    ("Microsoft YaHei", 300, "C:/Windows/Fonts/msyhl.ttc"),
    ("Microsoft YaHei", 400, "C:/Windows/Fonts/msyh.ttc"),
    ("Microsoft YaHei", 700, "C:/Windows/Fonts/msyhbd.ttc"),
    ("DengXian", 300, "C:/Windows/Fonts/Dengl.ttf"),
    ("DengXian", 400, "C:/Windows/Fonts/Deng.ttf"),
    ("DengXian", 700, "C:/Windows/Fonts/Dengb.ttf"),
    ("SimHei", 400, "C:/Windows/Fonts/simhei.ttf"),
    ("SimSun", 400, "C:/Windows/Fonts/simsun.ttc"),
    ("Arial", 400, "C:/Windows/Fonts/arial.ttf"),
    ("Arial", 700, "C:/Windows/Fonts/arialbd.ttf"),
    ("PingFang SC", 400, "/System/Library/Fonts/PingFang.ttc"),
    ("PingFang SC", 700, "/System/Library/Fonts/PingFang.ttc"),
    ("Hiragino Sans GB", 400, "/System/Library/Fonts/Hiragino Sans GB.ttc"),
    ("Songti SC", 400, "/System/Library/Fonts/Songti.ttc"),
    ("Helvetica", 400, "/System/Library/Fonts/Helvetica.ttc"),
    ("Noto Sans SC", 400, "/usr/share/fonts/opentype/noto/NotoSansSC-VF.otf"),
    ("Noto Sans CJK SC", 400, "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ("Noto Sans CJK SC", 700, "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("Source Han Sans SC", 400, "/usr/share/fonts/opentype/adobe/SourceHanSansSC-Regular.otf"),
    ("WenQuanYi Zen Hei", 400, "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    ("DejaVu Sans", 400, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]

MAX_TILE_PIXELS = 40_000_000        # beyond this, stop supersampling a tile
_font_cache: dict[tuple, ImageFont.FreeTypeFont] = {}
_missing_families: set[str] = set()


def normalise(family: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (family or "").lower())


def load_font_registry(project_dir: Path | None) -> dict[str, list[str]]:
    """Optional ``assets/fonts.json``: {family: [path, ...]} or {family: path}."""
    if project_dir is None:
        return {}
    for candidate in (project_dir / "assets" / "fonts.json", project_dir / "fonts.json"):
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  警告：{candidate} 不是合法 JSON，已忽略", file=sys.stderr)
            continue
        registry: dict[str, list[str]] = {}
        for family, value in data.items():
            paths = value if isinstance(value, list) else [value]
            registry[family] = [
                str(item["path"]) if isinstance(item, dict) else str(item) for item in paths
            ]
        return registry
    return {}


def _candidates(family: str, weight: int,
                registry: dict[str, list[str]] | None) -> list[str]:
    """Paths to try, best weight match first, then anything as a fallback."""
    wanted = normalise(family)
    pool: list[tuple[int, int, str]] = []          # (weight distance, family match, path)

    if registry and family in registry:
        for path in registry[family]:
            pool.append((0, 0, path))

    for name, nominal, path in FONT_FILES:
        matched = bool(wanted) and (wanted in normalise(name) or normalise(name) in wanted)
        pool.append((abs(nominal - weight), 0 if matched else 1, path))

    pool.sort(key=lambda entry: (entry[1], entry[0]))
    ordered: list[str] = []
    for _, _, path in pool:
        if path not in ordered:
            ordered.append(path)
    return ordered


def resolve_font(family: str, size: int, weight: int,
                 registry: dict[str, list[str]] | None = None) -> ImageFont.FreeTypeFont:
    key = (family or "", size, weight)
    if key in _font_cache:
        return _font_cache[key]

    font = None
    for path in _candidates(family, weight, registry):
        if not Path(path).exists():
            continue
        try:
            font = ImageFont.truetype(path, max(1, size))
            break
        except OSError:
            continue

    if font is None:
        font = ImageFont.load_default(size=max(1, size))
        if family and family not in _missing_families:
            _missing_families.add(family)
            print(
                f"  警告：字体「{family}」在本机找不到，已退化为内置字体，"
                "文字宽度会与设计不一致；请在 assets/fonts.json 里登记字体文件",
                file=sys.stderr,
            )
    else:
        # A variable font carries the weight itself; a static family already
        # picked the right file above.
        try:
            axes = font.get_variation_axes()
        except (AttributeError, OSError):
            axes = []
        if axes:
            values = []
            for axis in axes:
                axis_name = str(axis.get("name", "")).lower() if isinstance(axis, dict) else ""
                if "weight" in axis_name or axis_name in ("wght",):
                    values.append(float(weight))
                else:
                    default = axis.get("default") if isinstance(axis, dict) else None
                    values.append(float(default if default is not None else 0))
            try:
                font.set_variation_by_axes(values)
            except (OSError, ValueError):
                pass

    _font_cache[key] = font
    return font


def parse_color(value, default=(0, 0, 0, 255)):
    if not value or value == "none":
        return default
    text = str(value).strip()
    if text.startswith("#"):
        text = text[1:]
        if len(text) == 3:
            text = "".join(char * 2 for char in text)
        if len(text) == 6:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        if len(text) == 8:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4, 6))
    if text.startswith("rgb"):
        numbers = [int(part) for part in re.findall(r"\d+", text)[:4]]
        if len(numbers) >= 3:
            return tuple(numbers[:3]) + ((numbers[3],) if len(numbers) > 3 else (255,))
    return default


def weight_of(item: dict) -> int:
    raw = item.get("fontWeight")
    if raw is None:
        return 400
    if isinstance(raw, (int, float)):
        return int(raw)
    text = str(raw).strip().lower()
    named = {"thin": 100, "extralight": 200, "light": 300, "regular": 400,
             "normal": 400, "medium": 500, "semibold": 600, "bold": 700,
             "extrabold": 800, "black": 900}
    if text in named:
        return named[text]
    digits = re.findall(r"\d+", text)
    return int(digits[0]) if digits else 400


def legacy_text(item: dict) -> bool:
    """Old prototype sources anchor text by its centre rather than its top-left."""
    return bool(item.get("psdGroup") and not item.get("group"))


def tile_supersample(width: float, height: float) -> int:
    area = max(1.0, width) * max(1.0, height)
    for factor in (3, 2):
        if area * factor * factor <= MAX_TILE_PIXELS:
            return factor
    return 1


def wrap_line(line: str, font, limit: float) -> list[str]:
    """Greedy wrap. Used only when an element opts in with wrap: true."""
    if limit <= 0 or font.getlength(line) <= limit:
        return [line]
    pieces: list[str] = []
    current = ""
    for char in line:
        candidate = current + char
        if current and font.getlength(candidate) > limit:
            pieces.append(current)
            current = char
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def text_metrics(item: dict, font, scale: float, wrap: bool) -> tuple[list[str], float, float]:
    font_size = float(item.get("fontSize", 24)) * scale
    line_height = font_size * float(item.get("lineHeight", 1.2))
    lines: list[str] = []
    limit = float(item.get("w", 0) or 0) * scale
    for raw in str(item.get("text", "")).split("\n"):
        if wrap and limit > 0:
            lines.extend(wrap_line(raw, font, limit))
        else:
            lines.append(raw)
    width = max((font.getlength(line) for line in lines), default=0.0)
    return lines, width, line_height * max(1, len(lines))


def element_placement(item: dict,  scale: float, measured: tuple[float, float]) -> tuple[float, float, float, float]:
    """Return (left, top, width, height) in canvas pixels of the untransformed box."""
    width, height = measured
    x = float(item.get("x", 0)) * scale
    y = float(item.get("y", 0)) * scale
    if legacy_text(item) and "w" not in item:
        align = item.get("align", "left")
        if align == "center":
            x -= width / 2
        elif align == "right":
            x -= width
        y -= height / 2
        return x, y, width, height
    box_width = float(item.get("w", 0) or 0) * scale
    return x, y, max(box_width, width), height


def draw_text(canvas: Image.Image, item: dict, scale: float, opacity: float,
              registry: dict[str, list[str]]) -> None:
    weight = weight_of(item)
    font_size = float(item.get("fontSize", 24)) * scale
    wrap = bool(item.get("wrap"))
    base_font = resolve_font(item.get("fontFamily", ""), max(1, int(round(font_size))),
                             weight, registry)
    lines, measured_w, measured_h = text_metrics(item, base_font, scale, wrap)
    left, top, box_w, box_h = element_placement(item, scale, (measured_w, measured_h))

    supersample = tile_supersample(box_w or measured_w, measured_h)
    font = resolve_font(item.get("fontFamily", ""),
                        max(1, int(round(font_size * supersample))), weight, registry)
    lines, measured_w, measured_h = text_metrics(item, font, scale * supersample, wrap)

    fill = parse_color(item.get("fill"))
    stroke = parse_color(item.get("stroke"))
    stroke_width = int(round(float(item.get("strokeWidth", 0) or 0) * scale * supersample))
    line_height = float(item.get("fontSize", 24)) * scale * supersample * float(item.get("lineHeight", 1.2))
    align = item.get("align", "left")
    # box_w is in canvas pixels, measured_w is already supersampled — bring both
    # to the same space before comparing, or the centring box gets scaled twice.
    box_w_ss = max(box_w * supersample, measured_w)

    padding = stroke_width + 2
    tile_w = max(1, int(math.ceil(box_w_ss)) + 2 * padding)
    tile_h = max(1, int(math.ceil(line_height * len(lines))) + 2 * padding)
    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)

    for index, line in enumerate(lines):
        advance = font.getlength(line)
        if align == "center":
            draw_x = (box_w_ss - advance) / 2
        elif align == "right":
            draw_x = box_w_ss - advance
        else:
            draw_x = 0.0
        baseline = float(item.get("fontSize", 24)) * scale * supersample * 0.8 + index * line_height
        tile_draw.text((draw_x + padding, baseline + padding), line, font=font, fill=fill,
                       anchor="ls", stroke_width=stroke_width, stroke_fill=stroke)

    if supersample != 1:
        tile = tile.resize(
            (max(1, tile.width // supersample), max(1, tile.height // supersample)),
            Image.LANCZOS,
        )
    paste(canvas, tile, left - padding / supersample, top - padding / supersample, item, opacity)


def draw_shape(canvas: Image.Image, item: dict, assets: Path, scale: float, opacity: float) -> None:
    kind = item.get("type")
    x = float(item.get("x", 0)) * scale
    y = float(item.get("y", 0)) * scale
    width = float(item.get("w", 0) or 0) * scale
    height = float(item.get("h", 0) or 0) * scale
    stroke = parse_color(item.get("stroke"), (0, 0, 0, 255))
    fill = parse_color(item.get("fill"), (0, 0, 0, 0))
    stroke_width = max(0, float(item.get("strokeWidth", 0) or 0) * scale)

    if kind == "line":
        # A rule with h = 0 (or w = 0) is still a rule. The old renderer
        # returned early here and silently dropped every horizontal rule.
        thickness = max(1.0, stroke_width or 1.0)
        if height <= 0:
            height = thickness
        if width <= 0:
            width = thickness
        width = max(width, 1.0)
        height = max(height, 1.0)
        tile = Image.new("RGBA", (max(1, int(round(width))), max(1, int(round(height)))), stroke)
        paste(canvas, tile, x, y, item, opacity)
        return

    if width <= 0 or height <= 0:
        return

    supersample = tile_supersample(width, height) if kind != "image" else 1
    tile_w = max(1, int(round(width * supersample)))
    tile_h = max(1, int(round(height * supersample)))
    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)

    if kind == "rect":
        radius = min(float(item.get("radius", 0) or 0) * scale * supersample,
                     tile_w / 2, tile_h / 2)
        box = (0, 0, tile_w - 1, tile_h - 1)
        stroke_px = int(round(stroke_width * supersample))
        if radius > 0:
            tile_draw.rounded_rectangle(box, radius=radius, fill=fill,
                                        outline=stroke, width=stroke_px or 1)
        else:
            tile_draw.rectangle(box, fill=fill, outline=stroke, width=stroke_px or 1)
    elif kind == "ellipse":
        box = (0, 0, tile_w - 1, tile_h - 1)
        tile_draw.ellipse(box, fill=fill, outline=stroke,
                          width=int(round(stroke_width * supersample)) or 1)
    elif kind == "arc":
        start = float(item.get("start", 0) or 0)
        raw_end = item.get("end")
        end = float(360 if raw_end is None else raw_end)
        while end <= start:
            end += 360
        tile_draw.arc((0, 0, tile_w - 1, tile_h - 1), start, end, fill=stroke,
                      width=max(1, int(round(stroke_width * supersample))))
    elif kind == "image":
        source = Path(item.get("src", ""))
        if not source.is_absolute():
            source = assets.parent / source
        if not source.exists():
            print(f"  警告：图片不存在 {source}", file=sys.stderr)
            return
        if str(item.get("resample", "")).lower() == "nearest":
            # A QR code must land on whole pixels; smoothing breaks the modules.
            resample = Image.NEAREST
        else:
            resample = Image.LANCZOS
        fit = str(item.get("fit") or "fill").lower()
        with Image.open(source) as photo:
            picture = photo.convert("RGBA")
        if fit in ("cover", "contain") and picture.width and picture.height:
            # cover crops, contain letterboxes. Only "fill" stretches, which changes
            # a photographed subject's proportions — a fact, not a style choice.
            ratio = (
                max(tile_w / picture.width, tile_h / picture.height)
                if fit == "cover"
                else min(tile_w / picture.width, tile_h / picture.height)
            )
            scaled = picture.resize(
                (max(1, round(picture.width * ratio)), max(1, round(picture.height * ratio))),
                resample,
            )
            tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
            tile.paste(scaled, ((tile_w - scaled.width) // 2, (tile_h - scaled.height) // 2))
        else:
            tile = picture.resize((tile_w, tile_h), resample)
    else:
        print(f"  警告：未知元素类型 {kind!r}", file=sys.stderr)
        return

    if supersample != 1:
        tile = tile.resize((max(1, int(round(width))), max(1, int(round(height)))), Image.LANCZOS)
    paste(canvas, tile, x, y, item, opacity)


def paste(canvas: Image.Image, tile: Image.Image, x: float, y: float,
          item: dict, opacity: float) -> None:
    scale_x = float(item.get("scaleX", 1) or 1)
    scale_y = float(item.get("scaleY", 1) or 1)
    angle = float(item.get("angle", 0) or 0)
    centre_x = x + tile.width / 2
    centre_y = y + tile.height / 2

    if opacity < 1 or scale_x != 1 or scale_y != 1:
        alpha = tile.getchannel("A").point(lambda value: int(value * opacity))
        tile = tile.copy()
        tile.putalpha(alpha)
    if scale_x != 1 or scale_y != 1:
        tile = tile.resize(
            (max(1, int(round(tile.width * scale_x))), max(1, int(round(tile.height * scale_y)))),
            Image.LANCZOS,
        )
    if angle:
        tile = tile.rotate(-angle, resample=Image.BICUBIC, expand=True)

    canvas.alpha_composite(tile, (int(round(centre_x - tile.width / 2)),
                                  int(round(centre_y - tile.height / 2))))


def render(source: Path, output: Path, scale: float = 1.0, dpi: float | None = None,
           width: int | None = None) -> None:
    project = json.loads(source.read_text(encoding="utf-8"))
    canvas_spec = project.get("canvas", {})
    base_width = int(canvas_spec.get("width", 1024))
    base_height = int(canvas_spec.get("height", 1536))

    if width and width > 0:
        scale = width / base_width
    scale = float(scale) or 1.0

    out_width = max(1, int(round(base_width * scale)))
    out_height = max(1, int(round(base_height * scale)))
    assets = source.parent / "assets"
    registry = load_font_registry(source.parent)

    canvas = Image.new("RGBA", (out_width, out_height),
                       parse_color(canvas_spec.get("background"), (255, 255, 255, 255)))

    failures = 0
    for item in project.get("elements", []):
        if item.get("visible") is False:
            continue
        opacity = float(item.get("opacity", 1) or 0)
        if opacity <= 0:
            continue
        try:
            if item.get("type") == "text":
                draw_text(canvas, item, scale, opacity, registry)
            else:
                draw_shape(canvas, item, assets, scale, opacity)
        except Exception as error:                           # noqa: BLE001
            failures += 1
            print(f"  警告：组件 {item.get('id')} 渲染失败：{error}", file=sys.stderr)

    output.parent.mkdir(parents=True, exist_ok=True)
    final = canvas.convert("RGB")
    save_kwargs = {"dpi": (dpi, dpi)} if dpi else {}
    final.save(output, **save_kwargs)

    dpi_note = f"，{dpi:g} dpi" if dpi else "，未写 dpi（需要印刷请加 --dpi 300）"
    print(
        f"渲染完成：{output}（{final.width}×{final.height}{dpi_note}，"
        f"{len(project.get('elements', []))} 个组件"
        + (f"，{failures} 个失败" if failures else "")
        + "）"
    )
    if failures:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Poster Master 无头渲染器")
    parser.add_argument("--source", help="组件源稿 .poster.json")
    parser.add_argument("--output", help="输出 PNG")
    parser.add_argument("--project", help="项目文件夹（自动找 *.poster.json）")
    parser.add_argument("--scale", type=float, default=1.0, help="输出倍数")
    parser.add_argument("--width", type=int, default=None, help="按目标像素宽自动算倍数")
    parser.add_argument("--dpi", type=float, default=None, help="写入 PNG 的 dpi（印刷用 300）")
    args = parser.parse_args()

    if args.project:
        project = Path(args.project).resolve()
        matches = sorted(project.glob("*.poster.json"))
        if not matches:
            sys.exit(f"{project} 里没有 *.poster.json")
        source = matches[0]
        output = Path(args.output) if args.output else project / "exports" / "预览.png"
    else:
        if not args.source or not args.output:
            sys.exit("用法：python render_preview.py --source <源稿> --output <png> [--dpi 300]")
        source = Path(args.source)
        output = Path(args.output)

    if not source.exists():
        sys.exit(f"源稿不存在：{source}")
    render(source, output, args.scale, args.dpi, args.width)


if __name__ == "__main__":
    main()
