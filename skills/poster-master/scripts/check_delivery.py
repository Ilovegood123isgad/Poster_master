#!/usr/bin/env python3
"""Poster Master — automated delivery checks.

    python check_delivery.py --project "<project-dir>" [--expect name=WxH ...] [--json]

For every file in the project's exports folder (and any file named by --expect)
it reports:

  * the file opens;
  * the pixel size, and whether it matches the expected size;
  * the colour mode (RGB / RGBA / CMYK / L);
  * for PNG and PSD, that the file is structurally sound;
  * for PNG, whether a QR code is present and what it decodes to.

A QR check is a machine check. It does not replace scanning the printed or
displayed poster on a real phone at the real viewing distance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少依赖：Pillow。请先运行 pip install -r requirements.txt")

OK = "PASS"
WARN = "WARN"
FAIL = "FAIL"


class Report:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.errors = 0
        self.warnings = 0

    def add(self, path: Path, status: str, message: str) -> None:
        self.rows.append({"file": str(path), "status": status, "message": message})
        if status == FAIL:
            self.errors += 1
        elif status == WARN:
            self.warnings += 1

    @property
    def passed(self) -> bool:
        return self.errors == 0


def expected_sizes(project: Path, extra: list[str]) -> dict[str, tuple[int, int]]:
    table: dict[str, tuple[int, int]] = {}
    manifest = project / "delivery.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"delivery.json 解析失败：{error}")
        for entry in data.get("files", []):
            name = entry.get("file")
            if name and entry.get("width") and entry.get("height"):
                table[name] = (int(entry["width"]), int(entry["height"]))
    for item in extra:
        if "=" not in item:
            raise SystemExit(f"--expect 格式无效：{item}（应为 文件名=宽x高）")
        name, size = item.split("=", 1)
        parts = size.lower().split("x")
        if len(parts) != 2 or not all(part.strip().isdigit() for part in parts):
            raise SystemExit(f"--expect 尺寸无效：{size}（应为 宽x高）")
        table[name.strip()] = (int(parts[0]), int(parts[1]))
    return table


def check_png(path: Path, expected: tuple[int, int] | None, report: Report) -> None:
    with Image.open(path) as image:
        image.load()
        size = image.size
        mode = image.mode
    if expected and size != expected:
        report.add(path, FAIL, f"尺寸 {size[0]}×{size[1]}，期望 {expected[0]}×{expected[1]}")
        return
    if mode not in ("RGB", "RGBA"):
        report.add(path, WARN, f"色彩模式为 {mode}（屏幕交付建议 RGB/RGBA，印刷交付按印厂要求转 CMYK）")
        return
    report.add(path, OK, f"尺寸 {size[0]}×{size[1]}，模式 {mode}")


def check_svg(path: Path, expected: tuple[int, int] | None, report: Report) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.lstrip().startswith("<svg"):
        report.add(path, FAIL, "不是有效的 SVG 文件")
        return
    import re

    match = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', text)
    if not match:
        report.add(path, WARN, "未读到 width/height，无法核对尺寸")
        return
    size = (int(match.group(1)), int(match.group(2)))
    if expected and size != expected:
        report.add(path, FAIL, f"尺寸 {size[0]}×{size[1]}，期望 {expected[0]}×{expected[1]}")
        return
    embedded = text.count('href="data:image')
    report.add(path, OK, f"尺寸 {size[0]}×{size[1]}，内嵌位图 {embedded} 处")


def check_psd(path: Path, report: Report) -> None:
    with Image.open(path) as image:
        image.load()
        frames = getattr(image, "n_frames", 1)
        # n_frames is a count on a PSD, not a list.
        layers = int(frames) if isinstance(frames, int) else len(frames)
        size = image.size
    report.add(path, OK, f"PSD 可读取，{size[0]}×{size[1]}，图层 {layers}")


def check_other(path: Path, report: Report) -> None:
    report.add(path, WARN, "未知格式，未做自动检查，请人工核对")


def decode_qr(array) -> tuple[str, bool]:
    """Try hard to read a QR code out of a poster image.

    Returns (payload, detected). ``detected`` means a QR-shaped graphic was
    found; ``payload`` stays empty when the code is found but cannot be read.
    Small codes inside a big poster often need an upscale before OpenCV can
    lock onto them, so the whole frame is tried at three scales and the
    detected region is retried on its own.
    """
    import cv2

    detector = cv2.QRCodeDetector()
    detected = False
    for scale in (1, 2, 3):
        if scale == 1:
            frame = array
        else:
            frame = cv2.resize(array, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        try:
            payload, points, _ = detector.detectAndDecode(frame)
        except cv2.error:
            payload, points = "", None
        if payload:
            return payload, True
        if points is None:
            continue
        detected = True
        x, y, width, height = cv2.boundingRect(points.reshape(-1, 2))
        pad = int(0.3 * max(width, height))
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(frame.shape[1], x + width + pad)
        y1 = min(frame.shape[0], y + height + pad)
        try:
            payload, _, _ = detector.detectAndDecode(frame[y0:y1, x0:x1])
        except cv2.error:
            payload = ""
        if payload:
            return payload, True
    return "", detected


def check_qr(path: Path, report: Report) -> None:
    try:
        import cv2
        import numpy as np
    except ImportError:
        report.add(path, WARN, "未安装 OpenCV，跳过二维码检查")
        return
    try:
        with Image.open(path) as image:
            array = np.array(image.convert("RGB"))
    except Exception as error:  # pragma: no cover - unreadable file already reported
        report.add(path, WARN, f"二维码检查跳过：{error}")
        return
    payload, detected = decode_qr(array)
    if payload:
        report.add(path, OK, f"二维码可解码：{payload}")
    elif detected:
        report.add(path, FAIL, "检测到二维码图形，但无法解码")
    else:
        report.add(path, WARN, "未检测到二维码；若成品应含二维码，请人工核对")


def main() -> None:
    parser = argparse.ArgumentParser(description="Poster Master 交付检查")
    parser.add_argument("--project", required=True, help="项目文件夹")
    parser.add_argument("--expect", action="append", default=[], metavar="文件名=宽x高", help="期望尺寸，可重复")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        sys.exit(f"项目文件夹不存在：{project}")

    report = Report()
    expected = expected_sizes(project, args.expect)

    exports = project / "exports"
    candidates: list[Path] = []
    if exports.is_dir():
        candidates.extend(sorted(p for p in exports.iterdir() if p.is_file() and not p.name.startswith("._")))
    for name in expected:
        candidate = project / name
        if candidate.exists() and candidate not in candidates:
            candidates.append(candidate)

    if not candidates:
        report.add(exports, WARN, "没有找到待检查的导出文件")

    for path in candidates:
        suffix = path.suffix.lower()
        size = expected.get(path.name)
        if suffix == ".png":
            check_png(path, size, report)
            check_qr(path, report)
        elif suffix == ".jpg" or suffix == ".jpeg":
            with Image.open(path) as image:
                size_read = image.size
            if size and size_read != size:
                report.add(path, FAIL, f"尺寸 {size_read[0]}×{size_read[1]}，期望 {size[0]}×{size[1]}")
            else:
                report.add(path, OK, f"尺寸 {size_read[0]}×{size_read[1]}（JPEG 无透明通道）")
        elif suffix == ".svg":
            check_svg(path, size, report)
        elif suffix == ".psd":
            check_psd(path, report)
        else:
            check_other(path, report)

    if args.json:
        print(json.dumps({"ok": report.passed, "errors": report.errors, "warnings": report.warnings, "results": report.rows}, ensure_ascii=False, indent=2))
    else:
        print("交付检查：" + str(project))
        print("-" * 72)
        for row in report.rows:
            print(f"[{row['status']}] {Path(row['file']).name}  {row['message']}")
        print("-" * 72)
        print(f"结论：{report.errors} 项失败，{report.warnings} 项提示。")
        if report.passed:
            print("自动检查通过。仍需人工确认：实际距离可读性、文案事实、二维码真机扫描、字体与图片授权。")

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()

