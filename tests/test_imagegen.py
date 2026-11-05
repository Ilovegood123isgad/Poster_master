#!/usr/bin/env python3
"""Image-generation path: config, dry run, real call against a local stub.

    python tests/test_imagegen.py

No external network and no real key. A local HTTP server stands in for the
provider so the whole path is exercised: config resolution, key masking, the
request that would be sent, saving the image, and the sidecar record.

This is the test that makes "bring your own key" safe to ship: it proves the
scripts work, that the key never appears in the output, and that a bad key
produces a readable error instead of a traceback.
"""

from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from PIL import Image

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
SCRIPTS = SKILL / "scripts"
SETUP = SCRIPTS / "setup_imagegen.py"
GENERATE = SCRIPTS / "generate_artwork.py"

results: list[tuple[bool, str]] = []


def check(condition: bool, message: str) -> None:
    results.append((bool(condition), message))
    print(("  PASS  " if condition else "  FAIL  ") + message)


def png_b64() -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (255, 107, 44)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


GOOD_KEY = "sk-test-1234567890abcdef"


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *_args):        # keep the test output clean
        return

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            if self.headers.get("Authorization") != "Bearer " + GOOD_KEY:
                self._send(401, {"error": {"message": "invalid api key"}})
                return
            self._send(200, {"data": [{"id": "test-image-1"}, {"id": "test-image-2"}]})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.headers.get("Authorization") != "Bearer " + GOOD_KEY:
            self._send(401, {"error": {"message": "invalid api key"}})
            return
        if not payload.get("prompt"):
            self._send(400, {"error": {"message": "prompt required"}})
            return
        self._send(200, {"id": "gen-stub-1", "data": [{"b64_json": png_b64()}]})


def run(script: Path, argv: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *argv],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )


def main() -> None:
    home = Path(tempfile.mkdtemp())
    env = {**os.environ, "POSTER_MASTER_HOME": str(home), "PYTHONIOENCODING": "utf-8"}
    for name in ("POSTER_IMAGEGEN_API_KEY", "POSTER_IMAGEGEN_BASE_URL", "POSTER_IMAGEGEN_MODEL"):
        env.pop(name, None)

    # 1. nothing configured -> readable guidance, not a traceback
    completed = run(SETUP, ["--status"], env)
    check(completed.returncode == 1 and "setup_imagegen.py" in completed.stdout,
          "未配置时给出可执行指引")
    check("Traceback" not in completed.stderr, "未配置时没有抛栈")

    server = HTTPServer(("127.0.0.1", 0), Stub)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}/v1"

    try:
        # 2. config from environment
        env.update({
            "POSTER_IMAGEGEN_API_KEY": GOOD_KEY,
            "POSTER_IMAGEGEN_BASE_URL": base,
            "POSTER_IMAGEGEN_MODEL": "test-image-1",
        })
        completed = run(SETUP, ["--status"], env)
        check(completed.returncode == 0, "--status 在已配置时返回 0")
        check(GOOD_KEY not in completed.stdout, "状态输出里没有完整密钥")
        check("sk-t" in completed.stdout and "*" in completed.stdout, "密钥以掩码形式显示")

        # 3. connectivity test (no cost)
        completed = run(SETUP, ["--test"], env)
        check(completed.returncode == 0 and "接口可用" in completed.stdout,
              "--test 能测通（GET /models）")
        check("test-image-1" in completed.stdout, "--test 会列出可用图像模型")

        # 4. dry run: shows the request, leaks nothing, writes nothing
        output = home / "assets" / "主视觉.png"
        completed = run(GENERATE, [
            "--prompt", "深空中的悬浮岛，扁平矢量，薄荷绿与深青",
            "--size", "1536x1024", "--output", str(output), "--dry-run",
        ], env)
        check(completed.returncode == 0, "--dry-run 返回 0")
        check("images/generations" in completed.stdout, "--dry-run 打印了真实端点")
        check("深空中的悬浮岛" in completed.stdout, "--dry-run 打印了提示词")
        check(GOOD_KEY not in completed.stdout, "--dry-run 不打印密钥")
        check(not output.exists(), "--dry-run 不写文件")

        # 5. real call against the stub
        completed = run(GENERATE, [
            "--prompt", "深空中的悬浮岛，扁平矢量", "--size", "1024x1024",
            "--output", str(output),
        ], env)
        check(completed.returncode == 0, "生成调用成功")
        check(output.exists(), "图片已写出")
        if output.exists():
            check(Image.open(output).size == (4, 4), "写出的是服务端返回的图")
        sidecar = output.with_suffix(output.suffix + ".json")
        check(sidecar.exists(), "生成了 sidecar 记录")
        if sidecar.exists():
            record = json.loads(sidecar.read_text(encoding="utf-8"))
            check(record.get("model") == "test-image-1", "记录里有模型名")
            check("深空中的悬浮岛" in record.get("prompt", ""), "记录里有提示词")
            check(bool(record.get("date")), "记录里有日期")
            check(GOOD_KEY not in json.dumps(record), "记录里没有密钥")
        check("素材台账" in completed.stdout, "提示把记录填进素材台账")

        # 6. wrong key -> readable failure
        bad = {**env, "POSTER_IMAGEGEN_API_KEY": "sk-wrong-key-000000"}
        completed = run(GENERATE, [
            "--prompt", "x", "--output", str(home / "bad.png"),
        ], bad)
        check(completed.returncode == 1, "错误密钥返回非 0")
        check("密钥无效" in completed.stdout, "错误信息说明了原因")
        check("Traceback" not in completed.stderr, "错误密钥不抛栈")

        # 7. config file round-trip, and it never lives inside a project
        saved = run(SETUP, ["--status"], {**env, "POSTER_MASTER_HOME": str(home)})
        check(saved.returncode == 0, "配置可重复读取")
        check(not (home / "assets" / "imagegen.json").exists(), "配置不写进项目 assets")
    finally:
        server.shutdown()

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    print(f"结论：{len(results) - len(failed)} 项通过，{len(failed)} 项失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
