#!/usr/bin/env python3
"""`fit` on an image: fill stretches, cover crops, contain letterboxes.

    python tests/test_image_fit.py

A photograph stretched to the box changes the subject's proportions — that is a
factual error, not a styling preference. `fill` still exists (some assets really are
meant to fill), but `cover` and `contain` must actually differ from it in all three
renderers.

The fixture makes the difference measurable: a 200×100 image, red for the left 150 px and
blue for the right 50 px, placed in a 100×100 box.

  fill     squeezes 200 px into 100 → the red/blue boundary lands at x = 75
  cover    scale 1.0 then centre-crop the middle 100 px (source 50…150) → all red
  contain  scale 0.5, letterboxed → boundary still at x = 75, background above and below

The first attempt used a split at the exact centre, where fill and cover happen to look
identical — a fixture that cannot fail is not a test.
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

import export_svg  # noqa: E402
import render_preview  # noqa: E402

results: list[tuple[bool, str]] = []

BACKGROUND = (255, 255, 255, 255)


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def build_fixture(folder: Path) -> Image.Image:
    picture = Image.new("RGB", (200, 100), (255, 0, 0))
    picture.paste((0, 0, 255), (150, 0, 200, 100))
    picture.save(folder / "assets" / "split.png")
    return picture


def render(folder: Path, fit: str) -> np.ndarray:
    source = {
        "schemaVersion": 1,
        "name": "fit 测试",
        "canvas": {"width": 100, "height": 100, "background": "#ffffff"},
        "elements": [
            {"id": "photo", "type": "image", "label": "测试图", "group": "图片",
             "x": 0, "y": 0, "w": 100, "h": 100,
             "src": "assets/split.png", "fit": fit},
        ],
    }
    path = folder / f"{fit}.poster.json"
    path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
    output = folder / f"{fit}.png"
    render_preview.render(path, output, 1.0, None)
    return np.asarray(Image.open(output).convert("RGB"))


def is_red(pixel) -> bool:
    return pixel[0] > 180 and pixel[1] < 90 and pixel[2] < 90


def is_blue(pixel) -> bool:
    return pixel[2] > 180 and pixel[0] < 90 and pixel[1] < 90


def is_background(pixel) -> bool:
    return all(channel > 240 for channel in pixel)


def main() -> None:
    with tempfile.TemporaryDirectory() as raw:
        folder = Path(raw)
        (folder / "assets").mkdir()
        build_fixture(folder)

        filled = render(folder, "fill")
        checker("fill", lambda: (
            check(is_red(filled[50, 10]), "fill：左侧是红色"),
            check(is_blue(filled[50, 90]), "fill：右侧是蓝色（分界被压到 x=75）"),
        ))

        covered = render(folder, "cover")
        checker("cover", lambda: (
            check(is_red(covered[50, 10]), "cover：左侧是红色"),
            check(is_red(covered[50, 90]), "cover：右侧也是红色（裁掉了蓝色部分，没有拉伸）"),
        ))

        contained = render(folder, "contain")
        checker("contain", lambda: (
            check(is_background(contained[10, 50]), "contain：上方留白"),
            check(is_background(contained[90, 50]), "contain：下方留白"),
            check(is_red(contained[50, 10]), "contain：中部左侧红色"),
            check(is_blue(contained[50, 90]), "contain：中部右侧蓝色（等比缩小，未变形）"),
        ))

        # The three fits must not all produce the same image.
        check(not np.array_equal(filled, covered), "fill 与 cover 结果不同")
        check(not np.array_equal(filled, contained), "fill 与 contain 结果不同")

        # SVG must express the same semantics rather than always stretching.
        for fit, expected in (("fill", "none"), ("cover", "xMidYMid slice"), ("contain", "xMidYMid meet")):
            source = json.loads((folder / f"{fit}.poster.json").read_text(encoding="utf-8"))
            svg = export_svg.build_svg(source, folder / "assets")
            check(f'preserveAspectRatio="{expected}"' in svg,
                  f"SVG 的 {fit} 使用 preserveAspectRatio={expected}")

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


def checker(_label: str, run) -> None:
    run()


if __name__ == "__main__":
    main()
