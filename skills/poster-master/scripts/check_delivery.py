#!/usr/bin/env python3
"""Poster Master — automated delivery checks.

    python check_delivery.py --project "<project-dir>" [--expect name=WxH ...] [--json]

For every file in the project's exports folder (and any file named by --expect)
it reports whether the file is actually deliverable:

  * it opens;
  * the pixel size matches the delivery list;
  * the colour mode fits the carrier;
  * a PNG used for print carries its dpi (``pHYs``), because a missing one
    silently means 72 dpi and the wrong physical size;
  * a PSD is a real layered file — parseable by ``psd_tools``, with readable
    layer names, the declared dpi, and a composite that matches the render;
  * an SVG has been outlined, or it is reported as font-dependent;
  * a QR code that is present decodes.

Everything here is a machine check. It never replaces scanning the printed or
displayed poster on a real phone, at the real distance, at the real brightness.

A note on why this file is strict: v1.0.0 shipped a layered PSD whose channel
lengths were two bytes short. Photoshop-replacement readers refused it, yet this
checker reported "PSD readable, 10 layers" and passed it. A check that reports a
broken file as delivered is worse than no check, so the PSD path now delegates
to ``check_psd.py``, which fails on structure rather than on existence.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

OK = "PASS"
WARN = "WARN"
FAIL = "FAIL"

# A QR-shaped detection covering more than this fraction of the frame is not a
# code; it is OpenCV latching onto layout lines. That false positive cost a real
# run ten detection attempts and a full re-layout of the preview width.
QR_BOX_AREA_LIMIT = 0.35


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


class PsdAdapter:
    """Feed check_psd.py's findings into this report, keeping the file name."""

    def __init__(self, path: Path, report: Report) -> None:
        self.path = path
        self.report = report

    def add(self, level: str, message: str) -> None:
        self.report.add(self.path, level, message)


def read_delivery(project: Path) -> dict[str, dict]:
    manifest = project / "delivery.json"
    if not manifest.exists():
        return {}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"delivery.json 解析失败：{error}")
    table: dict[str, dict] = {}
    for entry in data.get("files", []):
        name = entry.get("file")
        if not name:
            continue
        table[name] = entry
        # "exports/海报.png" never matched path.name, so every check for that
        # entry — size, colour, dpi, layer count — was silently skipped and the
        # file passed unexamined. Register the bare name as well, so either
        # spelling drives the checks.
        base = Path(name).name
        if base != name:
            table.setdefault(base, entry)
    return table


def expected_sizes(project: Path, extra: list[str]) -> dict[str, tuple[int, int]]:
    table: dict[str, tuple[int, int]] = {}
    for name, entry in read_delivery(project).items():
        if entry.get("width") and entry.get("height"):
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


# --------------------------------------------------------------------------
# PNG


def read_png_dpi(path: Path) -> float | None:
    """Return the pHYs resolution in dpi, or None when the chunk is absent."""
    import struct

    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            return None
        while True:
            header = handle.read(8)
            if len(header) < 8:
                return None
            length = struct.unpack(">I", header[0:4])[0]
            kind = header[4:8]
            if kind == b"pHYs":
                body = handle.read(length)
                if len(body) >= 9:
                    x, _y, unit = struct.unpack(">IIB", body[0:9])
                    if unit == 1:                     # metres
                        return x * 0.0254
                return None
            if kind == b"IEND":
                return None
            handle.seek(length + 4, 1)


def check_png(path: Path, expected: tuple[int, int] | None, entry: dict, report: Report) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            size = image.size
            mode = image.mode
    except Exception as error:                               # noqa: BLE001
        report.add(path, FAIL, f"打不开：{error}")
        return

    if expected and size != expected:
        report.add(path, FAIL, f"尺寸 {size[0]}×{size[1]}，期望 {expected[0]}×{expected[1]}")
        return

    wanted_colour = str(entry.get("colour") or "").upper()
    if wanted_colour == "CMYK":
        report.add(path, FAIL, f"交付清单要求 CMYK，但 PNG 只能是 {mode}（RGB 需转 CMYK 或用 PDF/TIFF）")
        return
    if mode not in ("RGB", "RGBA"):
        # Do not return here. v1.1.0 returned after this warning, which skipped
        # the dpi and bleed checks below — so an indexed (P) print PNG with no
        # pHYs block passed with "0 failures". The colour mode is a hint; the
        # dpi is what makes the file physically the wrong size.
        report.add(
            path,
            WARN,
            f"色彩模式 {mode}（屏幕交付建议 RGB/RGBA）——继续核对 dpi 与出血",
        )
    else:
        report.add(path, OK, f"尺寸 {size[0]}×{size[1]}，模式 {mode}")

    declared_dpi = entry.get("dpi")
    actual_dpi = read_png_dpi(path)
    if declared_dpi:
        declared = float(declared_dpi)
        if actual_dpi is None:
            if declared > 72.5:
                report.add(
                    path,
                    FAIL,
                    f"声明 {declared:g} dpi，但 PNG 没有 pHYs 块"
                    "→ 所有软件都按 72 dpi 打开，成品物理尺寸会错",
                )
            else:
                report.add(path, OK, f"屏幕件（{declared:g} dpi），无 pHYs 属正常")
        elif abs(actual_dpi - declared) > 0.6:
            report.add(path, FAIL, f"pHYs {actual_dpi:.0f} dpi，清单声明 {declared:g}")
        else:
            report.add(path, OK, f"dpi {actual_dpi:.0f}（pHYs 已写入）")
    elif actual_dpi is None and max(size) > 2000:
        report.add(
            path,
            WARN,
            "没有 pHYs 也没有清单 dpi：若用于印刷请在 delivery.json 里写明 dpi",
        )
    elif actual_dpi is not None:
        report.add(path, OK, f"dpi {actual_dpi:.0f}（pHYs 已写入）")

    if entry.get("bleed_px"):
        bleed = int(entry["bleed_px"])
        trim = (int(entry.get("trim_width") or 0), int(entry.get("trim_height") or 0))
        if trim[0] and trim[1]:
            want = (trim[0] + 2 * bleed, trim[1] + 2 * bleed)
            if size != want:
                report.add(
                    path, FAIL,
                    f"含出血尺寸应为 {want[0]}×{want[1]}（成品 {trim[0]}×{trim[1]} + 出血 {bleed}px×2），"
                    f"实际 {size[0]}×{size[1]}",
                )
            else:
                report.add(path, OK, f"出血核对通过（成品 {trim[0]}×{trim[1]} + {bleed}px×2）")
    elif str(entry.get("use") or "").find("印刷") >= 0:
        report.add(path, WARN, "印刷件未声明出血尺寸（delivery.json 可加 bleed_px / trim_width / trim_height）")


# --------------------------------------------------------------------------
# SVG


def check_svg(path: Path, expected: tuple[int, int] | None, report: Report) -> None:
    import re

    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.lstrip().startswith("<svg"):
        report.add(path, FAIL, "不是有效的 SVG 文件")
        return
    match = re.search(r"<svg[^>]*\bwidth\s*=\s*[\"']?([\d.]+)", text)
    height_match = re.search(r"<svg[^>]*\bheight\s*=\s*[\"']?([\d.]+)", text)
    if not match or not height_match:
        report.add(path, WARN, "未读到 width/height，无法核对尺寸")
    else:
        size = (int(float(match.group(1))), int(float(height_match.group(1))))
        if expected and size != expected:
            report.add(path, FAIL, f"尺寸 {size[0]}×{size[1]}，期望 {expected[0]}×{expected[1]}")
        else:
            embedded = text.count("data:image")
            report.add(path, OK, f"尺寸 {size[0]}×{size[1]}，内嵌位图 {embedded} 处")

    text_elements = len(re.findall(r"<text\b", text))
    if text_elements:
        report.add(
            path,
            WARN,
            f"含 {text_elements} 个 <text> 元素：接收方缺字体会错版。"
            "交付级 SVG 应把文字转成路径（参考 scripts/export_svg.py）",
        )
    else:
        report.add(path, OK, "文字未以 <text> 依赖字体（已转曲或纯图形）")


# --------------------------------------------------------------------------
# PSD


def check_psd(
    path: Path,
    expected: tuple[int, int] | None,
    entry: dict,
    report: Report,
    project: Path | None = None,
) -> None:
    try:
        import check_psd
    except ImportError as error:
        report.add(path, FAIL, f"无法加载 check_psd.py，PSD 未验证：{error}")
        return

    adapter = PsdAdapter(path, report)
    wanted_dpi = entry.get("dpi")

    # v1.1.0 passed None for both expect_layers and compare, so check_psd's
    # composite comparison and layer-count check never ran — a PSD with an
    # inverted layer stack scored "0 failures". Both now come from the
    # delivery list.
    expect_layers: int | None = None
    raw_layers = entry.get("expect_layers")
    if raw_layers is not None:
        try:
            expect_layers = int(raw_layers)
        except (TypeError, ValueError):
            report.add(path, FAIL, f"delivery.json 的 expect_layers 不是整数：{raw_layers!r}")

    reference: Path | None = None
    raw_reference = entry.get("reference")
    if raw_reference:
        candidate = Path(raw_reference)
        if not candidate.is_absolute():
            candidate = (project or path.parent) / candidate
        if candidate.exists():
            reference = candidate
        else:
            report.add(path, FAIL, f"delivery.json 声明的参考图不存在：{raw_reference}")
    else:
        # No reference render means the composite cannot be compared, so layer
        # order is simply unverified. Say that instead of implying it passed.
        report.add(
            path,
            WARN,
            "delivery.json 未给 PSD 声明 reference 参考图：图层顺序与合成结果未验证"
            "（填 \"reference\": \"exports/预览.png\" 可让门禁真正比对）",
        )

    check_psd.check(
        path,
        float(wanted_dpi) if wanted_dpi else None,
        expected,
        expect_layers,
        reference,
        adapter,
    )


# --------------------------------------------------------------------------
# QR


def qr_candidate(array, scale: int) -> tuple[str, bool]:
    import cv2

    detector = cv2.QRCodeDetector()
    frame = array if scale == 1 else cv2.resize(
        array, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
    )
    try:
        payload, points, _ = detector.detectAndDecode(frame)
    except cv2.error:
        return "", False
    if payload:
        return payload, True
    if points is None:
        return "", False

    x, y, width, height = cv2.boundingRect(points.reshape(-1, 2))
    area_ratio = (width * height) / float(frame.shape[0] * frame.shape[1])
    if area_ratio > QR_BOX_AREA_LIMIT:
        # Not a code: a detection box covering a third of the frame is the
        # detector latching onto layout structure.
        return "", False

    pad = int(0.3 * max(width, height))
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1 = min(frame.shape[1], x + width + pad)
    y1 = min(frame.shape[0], y + height + pad)
    try:
        payload, _, _ = detector.detectAndDecode(frame[y0:y1, x0:x1])
    except cv2.error:
        payload = ""
    return payload, bool(payload)


def check_qr(path: Path, report: Report) -> None:
    try:
        import cv2  # noqa: F401
        import numpy as np
    except ImportError:
        report.add(path, WARN, "未安装 OpenCV，跳过二维码检查")
        return
    try:
        with Image.open(path) as image:
            array = np.array(image.convert("RGB"))
    except Exception as error:                               # noqa: BLE001
        report.add(path, WARN, f"二维码检查跳过：{error}")
        return

    for scale in (1, 2, 3):
        try:
            payload, ok = qr_candidate(array, scale)
        except Exception:                                    # noqa: BLE001
            continue
        if ok:
            report.add(path, OK, f"二维码可解码：{payload}")
            return
    report.add(path, WARN, "未检测到二维码；若成品应含二维码，请人工核对")


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Poster Master 交付检查")
    parser.add_argument("--project", required=True, help="项目文件夹")
    parser.add_argument("--expect", action="append", default=[], metavar="文件名=宽x高",
                        help="期望尺寸，可重复")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        sys.exit(f"项目文件夹不存在：{project}")

    report = Report()
    delivery = read_delivery(project)
    expected = expected_sizes(project, args.expect)

    exports = project / "exports"
    candidates: list[Path] = []
    if exports.is_dir():
        candidates.extend(
            sorted(p for p in exports.iterdir() if p.is_file() and not p.name.startswith("._"))
        )
    for name in expected:
        candidate = project / name
        if candidate.exists() and candidate not in candidates:
            candidates.append(candidate)

    if not candidates:
        # An empty exports folder is not "nothing to worry about": it means the
        # delivery cannot be proven at all. v1.1.0 reported a warning here and
        # then still printed "自动检查通过".
        report.add(
            exports,
            FAIL,
            "没有找到待检查的导出文件：交付前 exports/ 必须至少有一个成品，否则无法证明可交付",
        )

    # A delivery list that names files nobody exported must not pass: those
    # entries were never checked, so "0 failures" would be a statement about an
    # empty set of assertions rather than about the artwork.
    present = {p.name for p in candidates}
    missing = sorted({Path(name).name for name in delivery if Path(name).name not in present})
    if missing:
        more = "…" if len(missing) > 5 else ""
        report.add(
            project / "delivery.json",
            FAIL,
            f"清单声明了 {len(missing)} 个文件但 exports/ 里找不到："
            f"{'、'.join(missing[:5])}{more}"
            "——文件名或路径不一致，这些条目根本没有被检查",
        )

    for path in candidates:
        suffix = path.suffix.lower()
        size = expected.get(path.name)
        entry = delivery.get(path.name, {})
        try:
            if suffix == ".png":
                check_png(path, size, entry, report)
                check_qr(path, report)
            elif suffix in (".jpg", ".jpeg"):
                with Image.open(path) as image:
                    image.load()
                    read_size = image.size
                    mode = image.mode
                if size and read_size != size:
                    report.add(path, FAIL, f"尺寸 {read_size[0]}×{read_size[1]}，期望 {size[0]}×{size[1]}")
                else:
                    report.add(path, OK, f"尺寸 {read_size[0]}×{read_size[1]}，模式 {mode}（JPEG 无透明通道）")
                check_qr(path, report)
            elif suffix == ".svg":
                check_svg(path, size, report)
            elif suffix == ".psd":
                check_psd(path, size, entry, report, project)
            else:
                report.add(path, WARN, "未知格式，未做自动检查，请人工核对")
        except Exception as error:                           # noqa: BLE001
            report.add(path, FAIL, f"检查时出错（文件可能损坏）：{error}")

    if args.json:
        print(json.dumps(
            {"ok": report.passed, "errors": report.errors,
             "warnings": report.warnings, "results": report.rows},
            ensure_ascii=False, indent=2,
        ))
    else:
        print("交付检查：" + str(project))
        print("-" * 72)
        for row in report.rows:
            print(f"[{row['status']}] {Path(row['file']).name}  {row['message']}")
        print("-" * 72)
        print(f"结论：{report.errors} 项失败，{report.warnings} 项提示。")
        if report.errors:
            print("自动检查未通过：先修失败项，再谈交付。")
        elif report.warnings:
            print(
                f"自动检查没有失败项，但有 {report.warnings} 项提示尚未解决——"
                "那是「未验证」，不是「通过」。"
            )
        else:
            print(
                "自动检查全部通过。仍需人工确认：实际距离可读性、文案事实、"
                "二维码真机扫描、字体与图片授权。"
            )

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
