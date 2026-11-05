#!/usr/bin/env python3
"""Round-trip test for the PSD exporter: write it, then prove it reads back.

    python tests/test_psd_roundtrip.py

Writes a small PSD through scripts/export_psd.py, then asserts with psd_tools
(the reference implementation) that

  * the file parses,
  * Chinese layer names survive (luni block),
  * layer groups are real groups,
  * the dpi resource is present,
  * the layer stack composites to the intended artwork — this is the check that
    catches an inverted record order, which a "it opens fine" test never would.
"""

from __future__ import annotations

import json
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
sys.path.insert(0, str(SKILL / "scripts"))

import export_psd  # noqa: E402

try:
    from psd_tools import PSDImage
except ImportError:
    sys.exit("需要 psd_tools：pip install psd-tools")

WHITE = (255, 255, 255, 255)
RED = (220, 40, 40, 255)
GREEN = (40, 200, 90, 255)
BLUE = (40, 90, 220, 255)

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))


def solid(size: tuple[int, int], colour: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, colour)


def rect(size: tuple[int, int], box: tuple[int, int, int, int],
         colour: tuple[int, int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    image.paste(colour, box)
    return image


def main() -> None:
    width = height = 64
    size = (width, height)

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)

        # bottom -> top: 背景(RED) / 主视觉(GREEN 方块) / [组 文字] 主标题(BLUE) 副标题(WHITE)
        solid(size, RED).save(tmp / "00.png")
        rect(size, (8, 8, 24, 24), GREEN).save(tmp / "01.png")
        rect(size, (32, 8, 56, 20), BLUE).save(tmp / "02.png")
        rect(size, (32, 32, 56, 44), WHITE).save(tmp / "03.png")

        manifest = {
            "width": width,
            "height": height,
            "dpi": 300,
            "output": str(tmp / "out.psd"),
            "layers": [
                {"name": "背景", "path": "00.png"},
                {"name": "主视觉", "path": "01.png"},
                {
                    "name": "文字组",
                    "children": [
                        {"name": "主标题", "path": "02.png"},
                        {"name": "副标题", "path": "03.png"},
                    ],
                },
            ],
        }
        (tmp / "psd-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        psd_path = tmp / "out.psd"
        psd_path.write_bytes(export_psd.build_psd(manifest, tmp))
        print(f"写出 {psd_path.stat().st_size} 字节")

        # ---- structural read-back through psd_tools -------------------------
        try:
            psd = PSDImage.open(psd_path)
            check(True, "psd_tools 能打开文件")
        except Exception as error:                          # noqa: BLE001
            check(False, f"psd_tools 打开失败：{error}")
            report()
            return

        check(psd.size == size, f"画布 {psd.size}，期望 {size}")

        resolution_values = [int(block) for block in psd.image_resources]
        check(1005 in resolution_values,
              f"图像资源里有 ResolutionInfo(1005)，实际 {resolution_values}")
        dpi_value = None
        try:
            from psd_tools.constants import Resource
            raw = psd.image_resources.get_data(Resource.RESOLUTION_INFO)
            print("ResolutionInfo 原始类型：", type(raw), repr(raw)[:200])
            if isinstance(raw, (bytes, bytearray)) and len(raw) >= 16:
                dpi_value = struct.unpack(">I", raw[0:4])[0] / 65536.0
            elif raw is not None and hasattr(raw, "hres"):
                dpi_value = float(raw.hres)
        except Exception as error:                          # noqa: BLE001
            print("读取 ResolutionInfo 失败：", error)
        if dpi_value is None:
            from check_psd import read_dpi
            dpi_value = read_dpi(psd_path.read_bytes())
            print("改用结构解析得到 dpi：", dpi_value)
        check(dpi_value is not None and abs(dpi_value - 300) < 0.5,
              f"分辨率 {dpi_value}，期望 300 dpi")

        layers = list(psd.descendants())
        names = [layer.name for layer in layers]
        print("读回的图层/组顺序：", names)

        check(names.count("文字组") == 1, "存在名为「文字组」的图层组")
        check(names.count("背景") == 1, "中文图层名「背景」可读（luni 生效）")
        check(names.count("主视觉") == 1, "中文图层名「主视觉」可读")
        check(all("?" not in name for name in names), "没有任何图层名被降级成 '?'")

        groups = [layer for layer in layers if layer.is_group()]
        check(len(groups) == 1, f"图层组数量 {len(groups)}，期望 1")
        if groups:
            children = [child.name for child in groups[0]]
            check(children == ["主标题", "副标题"],
                  f"组内子图层（底→顶）{children}，期望 ['主标题', '副标题']")

        real = [layer for layer in layers if not layer.is_group()]
        check(len(real) == 4, f"栅格图层数量 {len(real)}，期望 4")

        # ---- the decisive check: does the stack composite correctly? --------
        composite = psd.composite(force=True)
        if composite is None:
            check(False, "psd_tools 无法合成")
        else:
            rgba = np.asarray(composite.convert("RGBA"))
            centre = rgba[16, 16, :3]
            corner = rgba[2, 2, :3]
            title = rgba[14, 44, :3]
            print("合成采样  中心", centre, "角落", corner, "标题区", title)
            check(tuple(centre) == GREEN[:3],
                  f"中心应为绿色（主视觉在最上层），实际 {tuple(centre)}")
            check(tuple(corner) == RED[:3],
                  f"角落应为红色（背景在最下层），实际 {tuple(corner)}")
            check(tuple(title) == BLUE[:3],
                  f"标题区应为蓝色（组的子层压在主视觉上），实际 {tuple(title)}")

    report()


def report() -> None:
    failed = [message for ok, message in results if not ok]
    for ok, message in results:
        print(("  PASS  " if ok else "  FAIL  ") + message)
    print("-" * 68)
    if failed:
        print(f"结论：{len(failed)} 项失败")
        sys.exit(1)
    print(f"结论：{len(results)} 项全部通过")


if __name__ == "__main__":
    main()
