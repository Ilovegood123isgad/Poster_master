#!/usr/bin/env python3
"""Write a Photoshop-compatible layered PSD — arbitrary layer count, real groups.

    python export_psd.py <manifest.json>
    python export_psd.py --project "<project-dir>"     # reads ./psd-manifest.json

Manifest, layers listed **bottom to top** (the order they are painted):

    {
      "width": 3508,
      "height": 4961,
      "dpi": 300,
      "output": "海报-分层.psd",
      "compression": "rle",
      "layers": [
        {"name": "背景", "path": "00.png"},
        {"name": "主视觉", "path": "01.png", "opacity": 0.9},
        {"name": "文字", "children": [
            {"name": "主标题", "path": "02.png"},
            {"name": "副标题", "path": "03.png"}
        ]}
      ]
    }

A node with ``children`` becomes a real Photoshop layer group (``lsct`` folders).
A node with ``path`` becomes one raster layer. There is no fixed layer limit:
one layer per element, per group, or a mix of both all work.

Why every field here exists:

* **Channel length includes the 2-byte compression word.** Getting this wrong by
  two bytes makes the file unreadable by every strict parser (psd_tools rejects
  it outright) and makes Photoshop show a scrambled stack. This was a real
  shipped defect — see ``references/psd-layer-spec.md``.
* **RLE (PackBits) is the default.** Uncompressed channels on an A3 canvas cost
  ~70 MB per layer; ten layers is 730 MB, which nobody can hand over.
* **Unicode names go in a `luni` block.** The legacy Pascal name field is
  MacRoman; without `luni` every Chinese layer name becomes "?".
* **A ResolutionInfo resource carries the dpi.** Without it every file reports
  72 dpi and an A3 at 3508 px looks like a 1.2 m poster.

Verified with ``scripts/check_psd.py``, which reads the file back through
``psd_tools`` and compares the composite against the source layers.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("缺少依赖：Pillow、numpy。请先运行 pip install -r requirements.txt")

# Records are written bottom-to-top, which is the order Photoshop and psd_tools
# both use. Flip this only if a real Photoshop test proves otherwise.
RECORD_ORDER = "bottom_up"

COMPRESSION_RLE = 1
COMPRESSION_RAW = 0


# --------------------------------------------------------------------------
# integers


def be16(value: int) -> bytes:
    return struct.pack(">H", value)


def be16s(value: int) -> bytes:
    return struct.pack(">h", value)


def be32(value: int) -> bytes:
    return struct.pack(">I", value)


def fixed16_16(value: float) -> bytes:
    return struct.pack(">I", int(round(value * 65536.0)) & 0xFFFFFFFF)


# --------------------------------------------------------------------------
# PackBits (RLE)
#
# A row is encoded as a sequence of packets:
#   n in 0..127   -> the next n+1 bytes are literal
#   n in -1..-127 -> the next byte repeats 1-n times
#
# Rows in a poster are mostly flat colour, so the run-aware path does the work.
# Busy rows (photographs) fall back to literal-only packets: still valid
# PackBits, no size win, but it keeps the encoder fast on a 3508 px canvas.


MAX_PACKET = 128
_RUN_AWARE_LIMIT = 96


def _repeat_packets(length: int, value: int) -> bytearray:
    out = bytearray()
    while length > 0:
        take = min(length, MAX_PACKET)
        out.append((1 - take) & 0xFF)
        out.append(value)
        length -= take
    return out


def _literal_packets(data: bytes) -> bytearray:
    out = bytearray()
    for start in range(0, len(data), MAX_PACKET):
        chunk = data[start:start + MAX_PACKET]
        out.append(len(chunk) - 1)
        out += chunk
    return out


def packbits_row(row: np.ndarray) -> bytes:
    length = row.size
    if length == 0:
        return b""

    if row.min() == row.max():
        return bytes(_repeat_packets(length, int(row[0])))

    changes = np.flatnonzero(np.diff(row) != 0) + 1
    if changes.size + 1 > _RUN_AWARE_LIMIT:
        return bytes(_literal_packets(row.tobytes()))

    bounds = np.concatenate(([0], changes, [length]))
    run_lengths = np.diff(bounds)
    run_values = row[bounds[:-1]].tolist()
    run_starts = bounds[:-1].tolist()
    raw = row.tobytes()

    out = bytearray()
    pending_start = 0
    pending_len = 0

    def flush() -> None:
        nonlocal pending_start, pending_len
        if pending_len:
            out.extend(_literal_packets(raw[pending_start:pending_start + pending_len]))
        pending_start = 0
        pending_len = 0

    for start, run, value in zip(run_starts, run_lengths.tolist(), run_values):
        if run >= 3:
            flush()
            out.extend(_repeat_packets(run, value))
        else:
            if pending_len == 0:
                pending_start = start
            pending_len += run
    flush()
    return bytes(out)


def encode_channel(plane: np.ndarray, compression: int) -> bytes:
    """Return one channel blob: compression word, optional row table, data."""
    height, width = plane.shape
    if compression == COMPRESSION_RAW:
        return be16(COMPRESSION_RAW) + plane.tobytes()

    packed = [packbits_row(plane[y]) for y in range(height)]
    table = b"".join(be16(len(item)) for item in packed)
    return be16(COMPRESSION_RLE) + table + b"".join(packed)


# --------------------------------------------------------------------------
# layer record pieces


def pascal_string(name: str) -> bytes:
    """Legacy name field: MacRoman-ish, padded so 1 + len is a multiple of 4."""
    encoded = name.encode("mac_roman", "replace")[:255]
    field = bytes([len(encoded)]) + encoded
    return field + b"\0" * ((4 - len(field) % 4) % 4)


def unicode_name(name: str) -> bytes:
    """`luni` block — the one Photoshop actually displays for CJK names."""
    encoded = name.encode("utf-16-be")
    body = be32(len(encoded) // 2) + encoded
    return b"8BIMluni" + be32(len(body)) + body


def section_divider(kind: int) -> bytes:
    """`lsct` block: 1 = open folder, 2 = closed folder, 3 = bounding divider."""
    return b"8BIMlsct" + be32(4) + be32(kind)


def resolution_resource(dpi: float) -> bytes:
    """Image resource 1005 — without it every reader reports 72 dpi."""
    body = (
        fixed16_16(dpi) + be16(1) + be16(1)      # horizontal res, ppi, inches
        + fixed16_16(dpi) + be16(1) + be16(1)    # vertical res, ppi, inches
    )
    return b"8BIM" + be16(1005) + b"\0\0" + be32(len(body)) + body


def make_record(
    *,
    name: str,
    width: int,
    height: int,
    channels: list[tuple[int, int]],
    visible: bool,
    opacity: int,
    blocks: list[bytes],
    empty_channels: bool,
) -> bytes:
    """Build one layer record.

    ``channels`` carries (id, declared length) pairs. The declared length MUST
    include the 2-byte compression word that precedes each channel's data.
    """
    record = struct.pack(">iiii", 0, 0, height if not empty_channels else 0,
                         width if not empty_channels else 0)
    record += be16(len(channels))
    for channel_id, declared in channels:
        record += be16s(channel_id) + be32(declared)

    flags = 0 if visible else 2          # bit 1 = hidden
    record += b"8BIM" + b"norm" + bytes([opacity, 0, flags, 0])

    extra = be32(0) + be32(0)            # mask data, blending ranges
    extra += pascal_string(name)
    extra += b"".join(blocks)

    record += be32(len(extra)) + extra
    return record


# --------------------------------------------------------------------------
# tree


def normalise(node: dict) -> dict:
    children = node.get("children")
    if children is not None:
        return {
            "kind": "group",
            "name": str(node.get("name") or "组"),
            "visible": bool(node.get("visible", True)),
            "opacity": int(round(float(node.get("opacity", 1) or 1) * 255)),
            "children": [normalise(child) for child in children],
        }
    if "path" not in node:
        raise ValueError(f"图层既没有 path 也没有 children：{node!r}")
    return {
        "kind": "layer",
        "name": str(node.get("name") or "图层"),
        "path": str(node["path"]),
        "visible": bool(node.get("visible", True)),
        "opacity": int(round(float(node.get("opacity", 1) or 1) * 255)),
    }


def load_node_image(node: dict, base: Path, size: tuple[int, int]) -> np.ndarray:
    path = Path(node["path"])
    if not path.is_absolute():
        path = base / path
    if not path.exists():
        raise ValueError(f"图层文件不存在：{path}")
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        if rgba.size != size:
            raise ValueError(
                f"图层尺寸不匹配：{node['name']} {rgba.size}，画布应为 {size}"
            )
        return np.asarray(rgba)


# --------------------------------------------------------------------------
# writer


def build_psd(manifest: dict, base: Path) -> bytes:
    width = int(manifest["width"])
    height = int(manifest["height"])
    if width <= 0 or height <= 0:
        raise ValueError("manifest 必须给出正的 width / height")
    dpi = float(manifest.get("dpi") or 72)
    compression = (
        COMPRESSION_RAW
        if str(manifest.get("compression", "rle")).lower() == "raw"
        else COMPRESSION_RLE
    )

    roots = [normalise(node) for node in manifest["layers"]]
    if not roots:
        raise ValueError("manifest.layers 为空")

    size = (width, height)
    composite = np.zeros((height, width, 4), dtype=np.uint8)

    records: list[bytes] = []
    blobs: list[bytes] = []
    layer_total = 0

    def emit_real_layer(node: dict) -> None:
        nonlocal layer_total, composite
        rgba = load_node_image(node, base, size)
        if node["visible"]:
            # composite bottom-to-top, matching the paint order
            top = rgba.astype(np.uint16)
            dst = composite.astype(np.uint16)
            alpha = top[:, :, 3:4]
            inverse = 255 - alpha
            for channel in range(3):
                dst[:, :, channel:channel + 1] = (
                    top[:, :, channel:channel + 1] * alpha
                    + dst[:, :, channel:channel + 1] * inverse
                ) // 255
            dst[:, :, 3:4] = alpha + (dst[:, :, 3:4] * inverse) // 255
            composite = dst.astype(np.uint8)

        channel_info: list[tuple[int, int]] = []
        channel_blobs: list[bytes] = []
        for channel_id, plane_index in ((0, 0), (1, 1), (2, 2), (-1, 3)):
            blob = encode_channel(np.ascontiguousarray(rgba[:, :, plane_index]), compression)
            channel_info.append((channel_id, len(blob)))
            channel_blobs.append(blob)

        records.append(
            make_record(
                name=node["name"],
                width=width,
                height=height,
                channels=channel_info,
                visible=node["visible"],
                opacity=node["opacity"],
                blocks=[unicode_name(node["name"])],
                empty_channels=False,
            )
        )
        blobs.extend(channel_blobs)
        layer_total += 1

    def emit_group(node: dict) -> None:
        nonlocal layer_total
        # Bounding divider sits below the children; the folder header above them.
        records.append(
            make_record(
                name="</Layer group>",
                width=0,
                height=0,
                channels=[(cid, 2) for cid in (-1, 0, 1, 2)],
                visible=True,
                opacity=255,
                blocks=[section_divider(3), unicode_name("</Layer group>")],
                empty_channels=True,
            )
        )
        blobs.extend(be16(COMPRESSION_RAW) for _ in range(4))
        layer_total += 1

        for child in node["children"]:
            if child["kind"] == "group":
                emit_group(child)
            else:
                emit_real_layer(child)

        records.append(
            make_record(
                name=node["name"],
                width=0,
                height=0,
                channels=[(cid, 2) for cid in (-1, 0, 1, 2)],
                visible=node["visible"],
                opacity=node["opacity"],
                blocks=[section_divider(1), unicode_name(node["name"])],
                empty_channels=True,
            )
        )
        blobs.extend(be16(COMPRESSION_RAW) for _ in range(4))
        layer_total += 1

    for node in roots:
        if node["kind"] == "group":
            emit_group(node)
        else:
            emit_real_layer(node)

    if layer_total == 0:
        raise ValueError("没有可写入的图层")

    order = list(range(len(records)))
    if RECORD_ORDER == "top_down":
        order.reverse()

    ordered_records = [records[i] for i in order]

    if compression == COMPRESSION_RLE:
        plane_bytes = 2 * height
        merged_rows = []
        for channel in range(4):
            plane = np.ascontiguousarray(composite[:, :, channel])
            merged_rows.extend(packbits_row(plane[y]) for y in range(height))
        merged_table = b"".join(be16(len(item)) for item in merged_rows)
        merged_data = be16(COMPRESSION_RLE) + merged_table + b"".join(merged_rows)
    else:
        merged_data = be16(COMPRESSION_RAW) + composite.tobytes()

    # Layer count is negative: the merged image's first alpha channel carries
    # the composite transparency, which is what we wrote.
    layer_info = be16s(-layer_total) + b"".join(ordered_records) + b"".join(blobs)
    layer_mask = be32(len(layer_info)) + layer_info + be32(0)

    resources = resolution_resource(dpi)

    header = (
        b"8BPS" + be16(1) + b"\0" * 6
        + be16(4) + be32(height) + be32(width) + be16(8) + be16(3)
    )
    return (
        header
        + be32(0)                                  # colour mode data
        + be32(len(resources)) + resources
        + be32(len(layer_mask)) + layer_mask
        + merged_data
    )


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(
            "用法：python export_psd.py <manifest.json>\n"
            "      python export_psd.py --project <项目文件夹>\n\n"
            "manifest 示例：\n"
            '  {"width": 3508, "height": 4961, "dpi": 300, "compression": "rle",\n'
            '   "output": "海报-分层.psd",\n'
            '   "layers": [{"name": "背景", "path": "000-背景.png"},\n'
            '              {"name": "文字", "children": [\n'
            '                 {"name": "主标题", "path": "001.png"}]}]}\n\n'
            "图层按从下到上排列；带 children 的节点会写成真正的 PSD 图层组。\n"
            "层数没有固定上限。详见 references/psd-layer-spec.md。"
        )
        return

    if args[0] == "--project":
        if len(args) < 2:
            sys.exit("--project 需要一个项目文件夹")
        project = Path(args[1]).resolve()
        candidates = list(project.glob("*psd-manifest.json")) + [project / "psd-manifest.json"]
        manifest_path = next((path for path in candidates if path.exists()), None)
        if manifest_path is None:
            sys.exit(f"在 {project} 里找不到 psd-manifest.json")
    else:
        manifest_path = Path(args[0]).resolve()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = Path(manifest["output"])
    if not output.is_absolute():
        output = manifest_path.parent / output
    output.parent.mkdir(parents=True, exist_ok=True)

    data = build_psd(manifest, manifest_path.parent)
    output.write_bytes(data)
    print(
        f"PSD 已写出：{output}"
        f"（{len(data) / 1048576:.1f} MB，图层记录 {manifest_summary(manifest)}）"
    )


def manifest_summary(manifest: dict) -> str:
    def count(nodes: list[dict]) -> tuple[int, int]:
        layers = groups = 0
        for node in nodes:
            if node.get("children") is not None:
                groups += 1
                child_layers, child_groups = count(node["children"])
                layers += child_layers
                groups += child_groups
            else:
                layers += 1
        return layers, groups

    layers, groups = count(manifest.get("layers", []))
    return f"{layers} 个图层 + {groups} 个组"


if __name__ == "__main__":
    main()
