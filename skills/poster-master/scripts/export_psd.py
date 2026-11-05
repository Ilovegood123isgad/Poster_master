#!/usr/bin/env python3
"""Write a Photoshop-compatible RGB PSD with one raster layer per named group.

The manifest lists the layers in composition order (background first):

    {
      "width": 1024,
      "height": 1536,
      "output": "/path/to/output.psd",
      "layers": [{"name": "背景", "path": "00.png", "visible": true}]
    }

Layer paths may be absolute or relative to the manifest directory. Layer images
must match the canvas size exactly. This is used by the Poster Master editor's
PSD export; it can also be run directly against a hand-written manifest.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment problem, not a logic problem
    sys.exit("缺少依赖：Pillow。请先运行 pip install -r requirements.txt")


def be16(value: int) -> bytes:
    return struct.pack(">H", value)


def be16s(value: int) -> bytes:
    return struct.pack(">h", value)


def be32(value: int) -> bytes:
    return struct.pack(">I", value)


def pascal_name(name: str) -> bytes:
    encoded = name.encode("latin-1", "replace")[:255]
    output = bytes([len(encoded)]) + encoded
    return output + (b"\0" * ((4 - len(output) % 4) % 4))


def layer_pixels(image: Image.Image) -> list[bytes]:
    rgba = image.convert("RGBA")
    return [rgba.getchannel(channel).tobytes() for channel in "RGBA"]


def compose(layers: list[Image.Image], width: int, height: int) -> Image.Image:
    composite = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for layer in layers:
        composite.alpha_composite(layer)
    return composite


def build_psd(manifest: dict, base_path: Path) -> bytes:
    width = int(manifest.get("width") or 0)
    height = int(manifest.get("height") or 0)
    loaded: list[tuple[str, Image.Image]] = []
    for item in manifest["layers"]:
        if not item.get("visible", True):
            continue
        source_path = Path(item["path"])
        if not source_path.is_absolute():
            source_path = base_path / source_path
        image = Image.open(source_path).convert("RGBA")
        loaded.append((str(item["name"]), image))

    if not loaded:
        raise ValueError("没有可写入的图层")

    if width <= 0 or height <= 0:
        # A manifest that does not state a canvas size takes the size of the
        # first layer, so a caller that only knows the layers still works.
        width, height = loaded[0][1].size

    for name, image in loaded:
        if image.size != (width, height):
            raise ValueError(f"图层尺寸不匹配：{name}（{image.size}，应为 {(width, height)}）")

    # PSD stores layer records from top to bottom; the manifest is bottom to top.
    top_to_bottom = list(reversed(loaded))
    records: list[bytes] = []
    channel_data: list[bytes] = []
    raw_length = 2 + width * height
    for name, image in top_to_bottom:
        record = struct.pack(">iiii", 0, 0, height, width)
        record += be16(4)
        for channel_id in (0, 1, 2, -1):
            record += be16s(channel_id) + be32(raw_length)
        record += b"8BIMnorm" + bytes([255, 0, 0, 0])
        extra = be32(0) + be32(0) + pascal_name(name)
        record += be32(len(extra)) + extra
        records.append(record)
        for plane in layer_pixels(image):
            channel_data.append(be16(0) + plane)

    layer_info = be16s(len(top_to_bottom)) + b"".join(records) + b"".join(channel_data)
    layer_mask = be32(len(layer_info)) + layer_info + be32(0)
    composite = compose([image for _, image in loaded], width, height)
    flat_data = be16(0) + b"".join(layer_pixels(composite))
    header = b"8BPS" + be16(1) + (b"\0" * 6) + be16(4) + be32(height) + be32(width) + be16(8) + be16(3)
    return header + be32(0) + be32(0) + be32(len(layer_mask)) + layer_mask + flat_data


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("用法：python export_psd.py <manifest.json>")
    manifest_path = Path(sys.argv[1]).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = Path(manifest["output"])
    if not output.is_absolute():
        output = manifest_path.parent / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build_psd(manifest, manifest_path.parent))
    print(f"PSD 已写出：{output}")


if __name__ == "__main__":
    main()

