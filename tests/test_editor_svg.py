#!/usr/bin/env python3
"""The editor's SVG export must be outlined, not `<text>`.

    python tests/test_editor_svg.py

A delivered SVG that still contains `<text>` depends on the recipient having the same
fonts; when they do not, the substitution changes every glyph width and the layout
breaks. v1.0.0 shipped that way because the browser built the SVG. The export now runs
through ``scripts/export_svg.py``, and this test holds that in place.

It also proves the export uses the *posted* project rather than the file on disk, so
unsaved edits are included.
"""

from __future__ import annotations

import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
SERVER = SKILL / "scripts" / "editor" / "server.js"
EXAMPLE = SKILL / "examples" / "城市夜跑"

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


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


def post(url: str, payload: dict, timeout: float = 300.0) -> tuple[int, dict]:
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
    work = Path(tempfile.mkdtemp())
    project_dir = work / "project"
    shutil.copytree(EXAMPLE, project_dir)
    source = next(project_dir.glob("*.poster.json"))
    project = json.loads(source.read_text(encoding="utf-8"))

    # Change the copy on disk so that "posted project" and "disk file" differ:
    # a text element that exists only in the posted payload must appear in the SVG.
    text_id = next(item["id"] for item in project["elements"] if item.get("type") == "text")
    for item in project["elements"]:
        if item["id"] == text_id:
            item["text"] = "仅存在于内存的改动"
    project["meta"] = project.get("meta") or {}
    project["meta"]["notes"] = "unsaved edit carried through the export"

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        ["node", str(SERVER), "--project", str(project_dir), "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        if not wait_for(base + "/"):
            check(False, "服务没有起来")
            return report()
        check(True, "编辑器服务已启动")

        status, payload = post(
            base + "/api/export/svg",
            {"project": project, "filename": "测试-矢量.svg"},
        )
        check(status == 200, f"导出接口返回 {status}")
        if status != 200:
            print(payload)
            return report()

        svg = payload.get("svg") or ""
        path = project_dir / "exports" / Path(payload.get("file") or "").name

        check(path.exists(), f"文件已写出：{payload.get('file')}")
        check(bool(svg), "响应里带回了 SVG 内容（浏览器才能下载）")
        check("<text" not in svg, f"没有 <text> 元素（实际 {len(re.findall(r'<text', svg))} 个）")
        check("font-family" not in svg, "没有 font-family 依赖")
        check(len(re.findall(r"<path", svg)) > 50, f"文字已转成路径（{len(re.findall(r'<path', svg))} 条）")
        check("仅存在于内存的改动" not in svg,
              "提交的文字已被转成轮廓（原文不再以字符串出现）")
        check(path.stat().st_size > 20_000, f"文件有实际内容（{path.stat().st_size // 1024} KB）")

        # The temporary source used for the run must not be left behind.
        leftovers = list(project_dir.glob(".export-*.poster.json"))
        check(not leftovers, f"没有残留临时源稿（发现 {len(leftovers)} 个）")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(work, ignore_errors=True)

    report()


def report() -> None:
    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
