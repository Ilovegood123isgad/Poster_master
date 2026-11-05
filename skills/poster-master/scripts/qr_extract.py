#!/usr/bin/env python3
"""Poster Master — QR extraction, verification, and clean regeneration.

Three modes:

    # 1. Find and decode a QR code inside a screenshot, save the cropped region
    python qr_extract.py --input 截图.png --output 输出目录.png --expect "https://example.com/join"

    # 2. Verify that a QR image decodes to the expected link
    python qr_extract.py --input 二维码.png --expect "https://example.com/join"

    # 3. Regenerate a clean QR from a confirmed link
    python qr_extract.py --generate "https://example.com/join" --output 二维码.png

The decoded string must be compared with the link the client stated, character by
character. "It opens" is not confirmation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    sys.exit("缺少依赖：opencv-python 与 numpy。请先运行 pip install -r requirements.txt")

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少依赖：Pillow。请先运行 pip install -r requirements.txt")

QUIET_ZONE_RATIO = 0.12


def detect_qr(array: np.ndarray):
    detector = cv2.QRCodeDetector()
    payload, points, _ = detector.detectAndDecode(array)
    if points is None:
        found = detector.detectMulti(array)
        if found and found[0] is not None:
            points = found[0]
            payloads = found[1]
            return (payloads[0] if payloads else ""), points
        return "", None
    return payload, points


def crop_region(image: Image.Image, points: np.ndarray) -> Image.Image:
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    margin = int(round(max(right - left, bottom - top) * QUIET_ZONE_RATIO))
    box = (
        max(0, int(left) - margin),
        max(0, int(top) - margin),
        min(image.width, int(right) + margin),
        min(image.height, int(bottom) + margin),
    )
    return image.crop(box)


def generate(url: str, output: Path, size: int) -> None:
    encoder = cv2.QRCodeEncoder.create()
    matrix = encoder.encode(url)
    array = np.array(matrix)
    if array.max() <= 1:
        array = array * 255
    array = np.clip(array, 0, 255).astype(np.uint8)
    modules = array.shape[0]
    quiet = 4  # the quiet zone the spec asks for, counted in modules
    span = modules + 2 * quiet
    # Every module must land on a whole pixel. A code stretched to an
    # arbitrary size gets uneven modules, and an uneven code is the usual
    # reason a "generated" QR stops decoding once it is scaled into a poster.
    module_px = max(1, size // span)
    edge = module_px * span
    code = Image.fromarray(array, mode="L").convert("RGB")
    code = code.resize((modules * module_px, modules * module_px), Image.NEAREST)
    canvas = Image.new("RGB", (edge, edge), "white")
    canvas.paste(code, (quiet * module_px, quiet * module_px))
    if edge != size:
        padded = Image.new("RGB", (size, size), "white")
        padded.paste(canvas, ((size - edge) // 2, (size - edge) // 2))
        canvas = padded
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(
        f"二维码已生成：{output}（{canvas.width}×{canvas.height}，内容 {url}，"
        f"{modules}×{modules} 模块，每模块 {module_px}px）"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Poster Master 二维码工具")
    parser.add_argument("--input", help="待检查的图片")
    parser.add_argument("--output", help="裁切图输出文件（模式 1）或生成文件（模式 3）")
    parser.add_argument("--expect", help="客户确认的链接，用于逐字符比对")
    parser.add_argument("--generate", help="从链接生成新的干净二维码")
    parser.add_argument("--size", type=int, default=1024, help="生成尺寸（默认 1024）")
    args = parser.parse_args()

    if args.generate:
        if not args.output:
            sys.exit("模式 3 需要 --output")
        generate(args.generate, Path(args.output), args.size)
        return

    if not args.input:
        sys.exit("需要 --input 或 --generate")

    source = Path(args.input)
    if not source.exists():
        sys.exit(f"文件不存在：{source}")

    with Image.open(source) as image:
        array = np.array(image.convert("RGB"))
        payload, points = detect_qr(array)
        if points is None:
            print("未检测到二维码。请确认图片未被裁掉静区、没有聊天界面遮挡，并尝试更清晰的原图。")
            sys.exit(2)
        print(f"检测到二维码，解码结果：{payload or '（无法解码）'}")
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            crop_region(image, points).save(output)
            print(f"区域裁切已保存：{output}")
        if args.expect:
            if payload == args.expect:
                print("比对结果：与客户确认的链接完全一致。")
            else:
                print("比对结果：不一致！")
                print(f"  期望：{args.expect}")
                print(f"  实际：{payload}")
                sys.exit(1)
        if not payload:
            sys.exit(3)


if __name__ == "__main__":
    main()

