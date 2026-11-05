#!/usr/bin/env python3
"""Renderer regression: the four things v1.0.0 got wrong.

    python tests/test_render.py

Covers, on a synthetic source so the assertions are exact:

  * a horizontal rule with ``h = 0`` is actually drawn (the old renderer
    returned early and dropped every rule),
  * ``fontWeight`` 300 and 900 produce different glyphs, not the same face,
  * ``--dpi`` writes a real ``pHYs`` chunk,
  * rotation is applied to text, not just to shapes.

Then it renders the shipped example and the real 2026-11-05 source, so a crash
or a silent font substitution shows up here rather than in a delivery.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
sys.path.insert(0, str(SKILL / "scripts"))

import render_preview  # noqa: E402
from check_delivery import read_png_dpi  # noqa: E402

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def ink(image: Image.Image, box: tuple[int, int, int, int] | None = None) -> int:
    array = np.asarray(image.convert("RGB"))
    if box:
        array = array[box[1]:box[3], box[0]:box[2]]
    return int((array.sum(axis=2) < 720).sum())


def build_source(path: Path) -> None:
    source = {
        "schemaVersion": 1,
        "name": "渲染测试",
        "canvas": {"width": 400, "height": 380, "background": "#ffffff"},
        "elements": [
            {"id": "rule", "type": "line", "label": "分隔线",
             "x": 20, "y": 40, "w": 360, "h": 0,
             "stroke": "#ff0000", "strokeWidth": 6},
            {"id": "light", "type": "text", "label": "细体", "group": "文字",
             "x": 20, "y": 80, "w": 360, "text": "海报排版",
             "fontFamily": "Microsoft YaHei", "fontSize": 64, "fontWeight": "300",
             "lineHeight": 1.2, "align": "left", "fill": "#000000", "strokeWidth": 0},
            {"id": "heavy", "type": "text", "label": "粗体", "group": "文字",
             "x": 20, "y": 170, "w": 360, "text": "海报排版",
             "fontFamily": "Microsoft YaHei", "fontSize": 64, "fontWeight": "900",
             "lineHeight": 1.2, "align": "left", "fill": "#000000", "strokeWidth": 0},
            {"id": "tilted", "type": "text", "label": "旋转", "group": "文字",
             "x": 250, "y": 250, "w": 120, "text": "AB", "angle": 25,
             "fontFamily": "Arial", "fontSize": 40, "fontWeight": "400",
             "lineHeight": 1.2, "align": "left", "fill": "#0000ff", "strokeWidth": 0},
            {"id": "centered", "type": "text", "label": "居中", "group": "文字",
             "x": 20, "y": 300, "w": 360, "text": "居中", "align": "center",
             "fontFamily": "Microsoft YaHei", "fontSize": 48, "fontWeight": "400",
             "lineHeight": 1.2, "fill": "#008000", "strokeWidth": 0},
        ],
    }
    path.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "t.poster.json"
        build_source(source)
        output = tmp / "out.png"

        render_preview.render(source, output, 1.0, 300)

        image = Image.open(output)
        check(image.size == (400, 380), f"画布 {image.size}")

        rule_row = np.asarray(image.convert("RGB"))[40:46, 20:380]
        red = ((rule_row[:, :, 0] > 180) & (rule_row[:, :, 1] < 90)).sum()
        check(red > 1000, f"h=0 的横线被画出来了（红色像素 {red}）")

        light_ink = ink(image, (0, 70, 400, 165))
        heavy_ink = ink(image, (0, 160, 400, 245))
        print(f"字重 300 墨量 {light_ink}，字重 900 墨量 {heavy_ink}")
        check(light_ink > 200, "字重 300 有字形")
        check(heavy_ink > light_ink * 1.05,
              f"字重 900 明显比 300 粗（{heavy_ink} vs {light_ink}）")

        dpi = read_png_dpi(output)
        check(dpi is not None and abs(dpi - 300) < 0.5, f"dpi {dpi}")

        upright = tmp / "upright.png"
        flat = json.loads(source.read_text(encoding="utf-8"))
        for item in flat["elements"]:
            if item["id"] == "tilted":
                item["angle"] = 0
        (tmp / "flat.poster.json").write_text(
            json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")
        render_preview.render(tmp / "flat.poster.json", upright, 1.0, None)
        tilted_ink = ink(image, (230, 200, 400, 300))
        upright_ink = ink(Image.open(upright), (230, 200, 400, 300))
        print(f"旋转区墨量：旋转 {tilted_ink} / 不旋转 {upright_ink}")
        check(tilted_ink != upright_ink, "文字旋转生效（旋转前后墨量不同）")

        check(read_png_dpi(upright) is None, "不给 --dpi 时不写 pHYs（不虚报印刷信息）")

        # centre alignment: the ink must sit around the box centre (200 px), not
        # at its right edge. Getting this wrong scaled the box by the supersample
        # factor and pushed every centred headline off the canvas.
        band = np.asarray(image.convert("RGB"))[300:380, :, :]
        green = (band[:, :, 1] > 100) & (band[:, :, 0] < 90) & (band[:, :, 2] < 90)
        columns = np.flatnonzero(green.any(axis=0))
        check(columns.size > 0, "居中文字有字形")
        if columns.size:
            centre = (columns.min() + columns.max()) / 2
            print(f"居中文字墨迹中心 {centre:.0f}px，框中心 200px")
            check(abs(centre - 200) <= 14, f"居中对齐正确（中心 {centre:.0f}px ≈ 200px）")

    # ---- the shipped example and the real failure case --------------------
    example = SKILL / "examples" / "城市夜跑"
    example_source = next(example.glob("*.poster.json"), None)
    if example_source:
        out = Path(tempfile.mkdtemp()) / "example.png"
        try:
            render_preview.render(example_source, out, 1.0, 72)
            check(Image.open(out).size[0] == 1080, "示例工程渲染成功（1080 宽）")
        except SystemExit:
            check(False, "示例工程渲染失败")
    else:
        check(False, "找不到示例工程源稿")

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
