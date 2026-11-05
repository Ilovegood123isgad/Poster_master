#!/usr/bin/env python3
"""Poster Master — background removal with an edge-quality report.

    python cutout.py --input 人物.jpg --output 人物-抠图.png [--preview 边缘预览.png]

This is a first pass, not a final cutout. The report tells you what to look at:
the hair outline, the gaps between strands, the clothing edge, the white halo on
transparent edges, and whether the subject's proportions changed.

A cutout that fails here is not fixed by adding smoke or cropping tighter.
Either re-run with a better original, refine by hand, or keep the original scene
and art-direct it as an editorial photograph.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少依赖：Pillow。请先运行 pip install -r requirements.txt")


def report_alpha(alpha: Image.Image) -> list[str]:
    bbox = alpha.getbbox()
    width, height = alpha.size
    if bbox is None:
        return ["抠图结果为空：没有检测到前景。"]
    left, top, right, bottom = bbox
    coverage = (right - left) * (bottom - top) / float(width * height)
    notes = [
        f"前景外接框：({left}, {top}) - ({right}, {bottom})",
        f"前景占画面比例：{coverage * 100:.1f}%",
    ]
    if coverage > 0.97:
        notes.append("前景几乎铺满画面，背景可能没有被真正分离，请人工核对边缘。")
    if coverage < 0.02:
        notes.append("前景极小，可能识别到了错误区域，请人工核对。")
    histogram = alpha.histogram()
    soft = sum(histogram[8:248])
    total = max(1, sum(histogram))
    notes.append(f"半透明像素占比：{soft / total * 100:.1f}%（过高通常意味着发丝或半透明区域被削平）")
    return notes


def make_preview(image: Image.Image, output: Path) -> None:
    checker = Image.new("RGB", image.size, "white")
    pixels = checker.load()
    for y in range(0, image.height, 16):
        for x in range(0, image.width, 16):
            if (x // 16 + y // 16) % 2 == 0:
                for dy in range(min(16, image.height - y)):
                    for dx in range(min(16, image.width - x)):
                        pixels[x + dx, y + dy] = (210, 210, 210)
    checker.paste(image, (0, 0), image)
    output.parent.mkdir(parents=True, exist_ok=True)
    checker.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Poster Master 抠图工具")
    parser.add_argument("--input", required=True, help="原图")
    parser.add_argument("--output", required=True, help="透明 PNG 输出")
    parser.add_argument("--preview", help="棋盘格边缘预览图输出路径")
    args = parser.parse_args()

    try:
        from rembg import remove
    except ImportError:
        sys.exit("缺少依赖：rembg。请先运行 pip install -r requirements.txt")

    source = Path(args.input)
    if not source.exists():
        sys.exit(f"原图不存在：{source}")

    with Image.open(source) as image:
        original = image.convert("RGBA")
        try:
            result = remove(original, alpha_matting=False, post_process_mask=True)
        except TypeError:
            result = remove(original)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output)

    alpha = result.getchannel("A") if result.mode == "RGBA" else Image.new("L", result.size, 255)
    print(f"抠图已写出：{output}")
    for note in report_alpha(alpha):
        print("  · " + note)
    print("  · 请人工核对：发丝外轮廓、发丝空隙、肩部与衣物边缘、手臂轮廓、透明边缘白边、人物比例。")
    if args.preview:
        make_preview(result, Path(args.preview))
        print(f"边缘预览已保存：{args.preview}")


if __name__ == "__main__":
    main()

