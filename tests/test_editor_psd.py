#!/usr/bin/env python3
"""End-to-end test of the editor's PSD export path.

    python tests/test_editor_psd.py

Starts the real server, posts a real layer tree, then validates the file that
comes out. This is the chain that was broken in v1.0.0 and that no unit test
would have caught:

  app.js builds a tree -> server writes PNGs -> server finds Python ->
  export_psd.py writes the PSD -> check_psd.py proves it parses.

It also covers the two behaviours the user asked for: arbitrary layer count and
real layer groups.
"""

from __future__ import annotations

import base64
import io
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
SERVER = SKILL / "scripts" / "editor" / "server.js"
CHECK = SKILL / "scripts" / "check_psd.py"
EXAMPLE = SKILL / "examples" / "城市夜跑"

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def wait_for(url: str, timeout: float = 40.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.4)
    return False


def post(url: str, payload: dict, timeout: float = 600.0) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8") or "{}")


def main() -> None:
    if not EXAMPLE.is_dir():
        sys.exit(f"找不到示例项目：{EXAMPLE}")

    work = Path(tempfile.mkdtemp())
    project = work / "project"
    shutil.copytree(EXAMPLE, project)

    source_path = next(project.glob("*.poster.json"))
    canvas = json.loads(source_path.read_text(encoding="utf-8"))["canvas"]
    width, height = int(canvas["width"]), int(canvas["height"])
    print(f"项目画布 {width}×{height}")

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        ["node", str(SERVER), "--project", str(project), "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        if not wait_for(base + "/"):
            output = process.stdout.read() if process.stdout else ""
            check(False, f"服务没有起来：{output[-400:]}")
            return report()
        check(True, f"编辑器服务已启动于 {base}")

        background = Image.new("RGBA", (width, height), (12, 15, 30, 255))
        block = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        block.paste((255, 107, 44, 255), (80, 200, 600, 420))

        tree = [
            {"name": "背景", "data": data_url(background)},
            {
                "name": "文字组",
                "children": [
                    {"name": "主标题", "data": data_url(block)},
                    {"name": "副标题", "data": data_url(block)},
                ],
            },
        ]

        status, payload = post(
            base + "/api/export/psd",
            {"tree": tree, "dpi": 300, "filename": "集成测试-分层.psd"},
        )
        check(status == 200, f"导出接口返回 {status} {payload.get('file') or payload.get('error', '')}")
        if status != 200:
            return report()

        psd_path = project / "exports" / "集成测试-分层.psd"
        check(psd_path.exists(), "PSD 文件已写出")
        if not psd_path.exists():
            return report()
        print(f"文件大小 {psd_path.stat().st_size / 1024:.0f} KB")

        completed = subprocess.run(
            [sys.executable, str(CHECK), str(psd_path),
             "--expect-dpi", "300", "--expect-size", f"{width}x{height}",
             "--expect-layers", "3"],
            capture_output=True, text=True, encoding="utf-8",
        )
        print(completed.stdout.strip())
        check(completed.returncode == 0, "check_psd 校验通过（含图层组与中文层名）")
        check("图层组 1 个" in completed.stdout, "图层组被写成真正的 PSD 文件夹")

        # legacy shape still accepted
        status, payload = post(
            base + "/api/export/psd",
            {"layers": [{"name": "单层", "data": data_url(background)}],
             "filename": "旧接口.psd"},
        )
        check(status == 200, "旧的 layers 数组仍被接受（向后兼容）")

        # a group nested too deep is refused rather than silently flattened
        deep = {"name": "L1", "children": [{"name": "L2", "children": [
            {"name": "L3", "children": [{"name": "L4", "children": [
                {"name": "L5", "children": [{"name": "L6", "children": [
                    {"name": "L7", "data": data_url(background)}]}]}]}]}]}]}
        status, payload = post(
            base + "/api/export/psd", {"tree": [deep], "filename": "过深.psd"})
        check(status == 400 and "嵌套" in str(payload.get("error", "")),
              f"嵌套过深被拒绝（{status}）")

    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    report()


def report() -> None:
    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
