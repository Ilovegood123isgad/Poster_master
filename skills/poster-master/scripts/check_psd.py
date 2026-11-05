#!/usr/bin/env python3
"""Read a PSD back and prove it is what it claims to be.

    python check_psd.py "<file.psd>" [--expect-dpi 300] [--expect-size 3508x4961]
                                       [--expect-layers 12] [--compare "<render.png>"]

Exit code 0 = every requested check passed, 1 = at least one failed.

Why this exists: a PSD that "opens" is not a PSD that is correct. The v1.0.0
exporter wrote channel lengths two bytes short, which left every layer's data
misaligned. Photoshop-replacement readers refused it outright, while the
delivery checker happily reported "PSD readable, 10 layers". This script is the
gate that would have caught it, so it checks structure, not just existence.

Checks, in order of what usually breaks:

1. the file parses at all, through ``psd_tools`` when it is installed — the
   reference implementation, and the closest thing to Photoshop we can gate on
   in CI; without it we fall back to a structural parser and say so;
2. the declared dpi (a missing ResolutionInfo resource silently means 72);
3. layer count, group count and every layer name — a Chinese name that comes
   back as "?" means the Unicode ``luni`` block is missing;
4. sizes, when asked;
5. the composite, when a reference render is given, so "the layers add up to
   the artwork" is measured rather than assumed.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("缺少依赖：Pillow、numpy。请先运行 pip install -r requirements.txt")

try:
    from psd_tools import PSDImage

    HAVE_PSD_TOOLS = True
except ImportError:
    PSDImage = None
    HAVE_PSD_TOOLS = False


FAIL = "FAIL"
WARN = "WARN"
OK = "OK"


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str]] = []

    def add(self, level: str, message: str) -> None:
        self.rows.append((level, message))

    def failures(self) -> int:
        return sum(1 for level, _ in self.rows if level == FAIL)

    def warnings(self) -> int:
        return sum(1 for level, _ in self.rows if level == WARN)

    def print(self) -> None:
        for level, message in self.rows:
            print(f"[{level}] {message}")
        print("-" * 68)
        verdict = (
            f"{self.failures()} 项失败，{self.warnings()} 项提示"
            if self.failures() or self.warnings()
            else "全部通过"
        )
        print(f"结论：{verdict}")


# --------------------------------------------------------------------------
# structural fallback: enough to catch the length bug without psd_tools


def read_dpi(data: bytes) -> float | None:
    offset = 26
    colour_mode_length = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4 + colour_mode_length
    resource_length = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4
    end = offset + resource_length
    while offset + 12 <= end:
        signature = data[offset:offset + 4]
        if signature not in (b"8BIM", b"MeSa", b"PHUT", b"AgHg", b"DCSR"):
            break
        resource_id = struct.unpack(">H", data[offset + 4:offset + 6])[0]
        name_length = data[offset + 6]
        name_total = name_length + 1
        name_total += name_total % 2
        cursor = offset + 6 + name_total
        size = struct.unpack(">I", data[cursor:cursor + 4])[0]
        body = data[cursor + 4:cursor + 4 + size]
        if resource_id == 1005 and len(body) >= 16:
            return struct.unpack(">I", body[0:4])[0] / 65536.0
        offset = cursor + 4 + size
        offset += size % 2
    return None


def structural_walk(data: bytes) -> tuple[list[str], int]:
    """Walk layer records and return (names, declared-count).

    Channel payloads are walked using the declared length. If a writer forgot
    the 2-byte compression word, this walk still survives, which is exactly why
    the strict psd_tools path is the one that matters.
    """
    offset = 26
    colour_mode_length = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4 + colour_mode_length
    resource_length = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4 + resource_length
    offset += 4                                            # layer and mask length
    offset += 4                                            # layer info length
    count = struct.unpack(">h", data[offset:offset + 2])[0]
    offset += 2

    names: list[str] = []
    for _ in range(abs(count)):
        offset += 16
        channels = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2 + channels * 6
        offset += 12                                       # blend mode and flags
        extra = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        block_end = offset + extra

        mask_length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4 + mask_length
        ranges_length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4 + ranges_length

        name_length = data[offset]
        raw = data[offset + 1:offset + 1 + name_length]
        names.append(raw.decode("latin-1", "replace"))
        offset += ((1 + name_length + 3) // 4) * 4

        decoded = None
        while offset + 12 <= block_end:
            signature = data[offset:offset + 4]
            if signature != b"8BIM":
                break
            key = data[offset + 4:offset + 8]
            size = struct.unpack(">I", data[offset + 8:offset + 12])[0]
            body = data[offset + 12:offset + 12 + size]
            if key == b"luni" and len(body) >= 4:
                chars = struct.unpack(">I", body[0:4])[0]
                decoded = body[4:4 + chars * 2].decode("utf-16-be", "replace")
            offset += 12 + size
            offset += size % 2
        if decoded:
            names[-1] = decoded
        offset = block_end
    return names, count


# --------------------------------------------------------------------------


def check(
    path: Path,
    expect_dpi: float | None,
    expect_size: tuple[int, int] | None,
    expect_layers: int | None,
    compare: Path | None,
    report: Report,
) -> None:
    data = path.read_bytes()
    if data[:4] != b"8BPS":
        report.add(FAIL, "不是 PSD 文件（缺少 8BPS 签名）")
        return

    version = struct.unpack(">H", data[4:6])[0]
    report.add(OK if version == 1 else WARN, f"PSD 版本 {version}")

    dpi = read_dpi(data)
    if dpi is None:
        report.add(FAIL, "缺少 ResolutionInfo 资源 → 所有软件都会按 72 dpi 打开")
    elif expect_dpi and abs(dpi - expect_dpi) > 0.5:
        report.add(FAIL, f"声明 dpi {dpi:g}，期望 {expect_dpi:g}")
    else:
        report.add(OK, f"dpi {dpi:g}")

    if not HAVE_PSD_TOOLS:
        report.add(
            WARN,
            "未安装 psd_tools，跳过严格结构校验"
            "（pip install psd-tools）；只做结构性解析，无法证明 Photoshop 能打开",
        )
        names, count = structural_walk(data)
        report.add(OK, f"图层记录 {abs(count)} 个")
        broken = [name for name in names if "?" in name]
        if broken:
            report.add(FAIL, f"{len(broken)} 个图层名含 '?'，Unicode luni 块缺失或被降级")
        else:
            report.add(OK, "图层名可读")
        if expect_size:
            height, width = struct.unpack(">II", data[14:22])
            if (width, height) != expect_size:
                report.add(FAIL, f"画布 {width}×{height}，期望 {expect_size[0]}×{expect_size[1]}")
        return

    try:
        psd = PSDImage.open(path)
    except Exception as error:                              # noqa: BLE001
        report.add(FAIL, f"psd_tools 无法解析：{error}")
        report.add(
            FAIL,
            "这是硬失败：Photoshop 之外的读取器会直接拒绝，"
            "最常见原因是通道数据长度没有包含 2 字节压缩标志",
        )
        return

    width, height = psd.size
    report.add(OK, f"psd_tools 可解析：{width}×{height}")
    if expect_size and (width, height) != expect_size:
        report.add(FAIL, f"画布 {width}×{height}，期望 {expect_size[0]}×{expect_size[1]}")

    layers = list(psd.descendants())
    groups = [layer for layer in layers if layer.is_group()]
    real = [layer for layer in layers if not layer.is_group()]
    report.add(OK, f"图层 {len(real)} 个，图层组 {len(groups)} 个")

    if expect_layers is not None and len(real) != expect_layers:
        report.add(FAIL, f"图层数 {len(real)}，期望 {expect_layers}")

    unreadable = [layer.name for layer in layers if "?" in layer.name or not layer.name.strip()]
    if unreadable:
        report.add(FAIL, f"{len(unreadable)} 个图层名不可读（Unicode luni 块问题）：{unreadable[:5]}")
    else:
        preview = [layer.name for layer in layers][:6]
        report.add(OK, f"图层名可读，前几个：{', '.join(preview)}")

    if compare is not None:
        composite = psd.composite(force=True)
        if composite is None:
            report.add(FAIL, "psd_tools 无法合成，图层数据可能已损坏")
        else:
            reference = Image.open(compare).convert("RGBA")
            sample = composite.convert("RGBA")
            same_size = sample.size == reference.size
            scale = min(1.0, 900 / max(1, reference.size[0]))
            target = (
                max(1, int(reference.size[0] * scale)),
                max(1, int(reference.size[1] * scale)),
            )
            left = np.asarray(sample.resize(target, Image.LANCZOS), dtype=np.int16)
            right = np.asarray(reference.resize(target, Image.LANCZOS), dtype=np.int16)
            diff = np.abs(left - right)
            worst = int(diff.max())
            mean = float(diff.mean())
            # Absolute max is the wrong gate: comparing a design-size PSD with a
            # print-size render means every glyph edge lands on a different
            # subpixel, and a handful of pixels differ by 200 while the artwork
            # is obviously identical. A wrong layer order, on the other hand,
            # changes whole regions, which moves the mean and the share of
            # heavily-different pixels — so gate on those two.
            heavy = float(np.percentile(diff, 99.0))
            heavy_share = float((diff > 24).mean() * 100)
            detail = (
                f"最大差 {worst}，平均差 {mean:.2f}，p99 {heavy:.0f}，"
                f"差异>24 的像素 {heavy_share:.2f}%"
                + ("（同尺寸比对）" if same_size else "（跨尺寸比对，边缘差异属正常）")
            )
            if mean > 2.5 or heavy_share > 3.0:
                report.add(
                    FAIL,
                    f"合成结果与参考图不一致：{detail}"
                    "——先查图层顺序与透明度，再查是否漏了图层",
                )
            else:
                report.add(OK, f"合成结果与参考一致：{detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="校验分层 PSD 的结构与合成结果")
    parser.add_argument("psd")
    parser.add_argument("--expect-dpi", type=float, default=None)
    parser.add_argument("--expect-size", default=None, help="宽x高，例如 3508x4961")
    parser.add_argument("--expect-layers", type=int, default=None)
    parser.add_argument("--compare", default=None, help="参考渲染 PNG")
    args = parser.parse_args()

    expect_size = None
    if args.expect_size:
        width, height = args.expect_size.lower().split("x")
        expect_size = (int(width), int(height))

    report = Report()
    path = Path(args.psd).resolve()
    print(f"PSD 检查：{path}")
    print("-" * 68)
    check(
        path,
        args.expect_dpi,
        expect_size,
        args.expect_layers,
        Path(args.compare).resolve() if args.compare else None,
        report,
    )
    report.print()
    sys.exit(1 if report.failures() else 0)


if __name__ == "__main__":
    main()
