#!/usr/bin/env python3
"""Run every regression test for the poster-master skill.

    python tests/run_all.py

Each test is independent and exits non-zero on failure. This runner exists because
the previous version was released without any executable check at all, and every
defect it shipped — an inverted layer stack, a two-byte channel length, a centring
box scaled twice, a PSD the delivery check passed — would have been caught by one.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

TESTS = [
    "test_psd_roundtrip.py",
    "test_editor_psd.py",
    "test_render.py",
    "test_svg_export.py",
    "test_imagegen.py",
    "test_editor_ui.py",
]

HERE = Path(__file__).resolve().parent


def main() -> None:
    results: list[tuple[str, bool, float]] = []
    for name in TESTS:
        script = HERE / name
        if not script.exists():
            results.append((name, False, 0.0))
            print(f"\n=== {name} === 缺失")
            continue
        print(f"\n=== {name} ===")
        started = time.time()
        completed = subprocess.run([sys.executable, str(script)], capture_output=False)
        results.append((name, completed.returncode == 0, time.time() - started))

    print("\n" + "=" * 68)
    for name, ok, elapsed in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({elapsed:.1f}s)")
    failures = [name for name, ok, _ in results if not ok]
    print("=" * 68)
    if failures:
        print(f"结论：{len(failures)} 个测试文件失败")
        sys.exit(1)
    print(f"结论：{len(results)} 个测试文件全部通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
