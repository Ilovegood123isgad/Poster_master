#!/usr/bin/env python3
"""Regression test for the delivery gate: bad files must FAIL.

    python tests/test_delivery_gate.py

v1.1.0 shipped a gate that passed four classes of bad file with "0 failures":

  1. a PSD with an inverted layer stack — ``check_delivery`` hard-coded
     ``expect_layers`` and ``compare`` to None, so ``check_psd``'s composite
     comparison and layer-count check never ran;
  2. an indexed (P) print PNG with no pHYs block — the colour-mode branch
     returned early, skipping the dpi and bleed checks below it;
  3. an empty ``exports/`` folder — only a warning, so ``errors`` stayed at 0
     and the tool still printed "自动检查通过";
  4. a PSD checked on a machine without ``psd_tools`` — the structural
     fallback reported no failures, so "无法验证" read as "已验证".

Two quieter ways of failing the same way came out of writing the
``delivery.json`` template, and are covered here too:

  5. an entry written as ``"exports/海报.png"`` instead of ``"海报.png"`` never
     matched ``path.name``, so size, colour, dpi and layer count were all
     silently skipped for that file — the worst kind of gate failure, because
     the output still said it had looked;
  6. a delivery list naming a file that is not in ``exports/`` asserted nothing
     at all, yet reported zero failures.

Each case below asserts the gate FAILS, and asserts *which* finding caught it,
so a future loosening cannot be mistaken for a different check happening to
fire. One case asserts a correct PSD still PASSES — otherwise "everything
fails" would look like a fix.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SKILL = Path(__file__).resolve().parents[1] / "skills" / "poster-master"
SCRIPTS = SKILL / "scripts"
GATE = SCRIPTS / "check_delivery.py"

sys.path.insert(0, str(SCRIPTS))

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
    print(("  PASS  " if condition else "  FAIL  ") + message)


def run_gate(project: Path) -> tuple[int, dict, str]:
    """Run the gate as the user would, and return (exit code, json, raw)."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        [sys.executable, str(GATE), "--project", str(project), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {}
    return completed.returncode, payload, completed.stdout + completed.stderr


def messages(payload: dict) -> str:
    return "\n".join(row.get("message", "") for row in payload.get("results", []))


def solid(size: tuple[int, int], colour: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", size, colour)


def rect(size: tuple[int, int], box: tuple[int, int, int, int],
         colour: tuple[int, int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    image.paste(colour, box)
    return image


def make_layered_project(root: Path, *, invert: bool) -> Path:
    """Write a 4-layer PSD plus a reference render, and return the project dir."""
    width = height = 64
    size = (width, height)
    project = root / ("inverted" if invert else "correct")
    exports = project / "exports"
    exports.mkdir(parents=True)

    # bottom -> top
    solid(size, RED).save(project / "00.png")
    rect(size, (8, 8, 24, 24), GREEN).save(project / "01.png")
    rect(size, (32, 8, 56, 20), BLUE).save(project / "02.png")
    rect(size, (32, 32, 56, 44), WHITE).save(project / "03.png")

    manifest = {
        "width": width,
        "height": height,
        "dpi": 300,
        "layers": [
            {"name": "背景", "path": "00.png"},
            {"name": "主视觉", "path": "01.png"},
            {"name": "主标题", "path": "02.png"},
            {"name": "副标题", "path": "03.png"},
        ],
    }

    # The reference is always the composite of the *correct* stack, so the
    # inverted build is compared against what the artwork is supposed to be.
    reference = PSDImage.open(_write_psd(project, manifest, root / "ref.psd"))
    composite = reference.composite(force=True)
    composite.convert("RGB").save(project / "reference.png")

    target = copy.deepcopy(manifest)
    if invert:
        target["layers"] = list(reversed(target["layers"]))
    _write_psd(project, target, exports / "poster.psd")

    (project / "delivery.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "file": "poster.psd",
                        "width": width,
                        "height": height,
                        "dpi": 300,
                        "expect_layers": 4,
                        "reference": "reference.png",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return project


def _write_psd(project: Path, manifest: dict, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(manifest)
    payload["output"] = str(output)
    output.write_bytes(export_psd.build_psd(payload, project))
    return output


def case_inverted_psd(tmp: Path) -> None:
    print("\n[1] 图层顺序颠倒的 PSD 必须被合成比对拦下")
    project = make_layered_project(tmp, invert=True)
    code, payload, raw = run_gate(project)
    check(code != 0 and payload.get("ok") is False, f"exit={code}，ok={payload.get('ok')}（应为失败）")
    check("合成结果与参考图不一致" in messages(payload),
          "失败原因是合成比对（不是别的检查碰巧触发）")
    if "合成结果与参考图不一致" not in messages(payload):
        print(raw)


def case_indexed_png(tmp: Path) -> None:
    print("\n[2] P 模式印刷 PNG（无 pHYs）必须因为 dpi 失败")
    project = tmp / "indexed-png"
    exports = project / "exports"
    exports.mkdir(parents=True)
    Image.new("RGB", (120, 90), (200, 200, 200)).convert("P").save(exports / "a.png")
    (project / "delivery.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "file": "a.png",
                        "width": 120,
                        "height": 90,
                        "dpi": 300,
                        "colour": "RGB",
                        "use": "印刷",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    code, payload, raw = run_gate(project)
    check(code != 0 and payload.get("ok") is False, f"exit={code}，ok={payload.get('ok')}（应为失败）")
    check("pHYs" in messages(payload), "失败原因是缺失 pHYs（dpi 检查没有被色彩模式分支跳过）")
    if "pHYs" not in messages(payload):
        print(raw)


def case_empty_exports(tmp: Path) -> None:
    print("\n[3] 空 exports/ 必须失败")
    project = tmp / "empty-exports"
    (project / "exports").mkdir(parents=True)
    code, payload, raw = run_gate(project)
    check(code != 0 and payload.get("ok") is False, f"exit={code}，ok={payload.get('ok')}（应为失败）")
    check("没有找到待检查的导出文件" in messages(payload), "失败原因是导出目录为空")
    if "没有找到待检查的导出文件" not in messages(payload):
        print(raw)


def case_without_psd_tools(tmp: Path) -> None:
    print("\n[4] 没有 psd_tools 时，PSD 必须判为未验证并失败")
    import check_psd

    project = tmp / "no-psd-tools"
    project.mkdir(parents=True)
    solid((64, 64), RED).save(project / "00.png")
    psd_path = _write_psd(
        project,
        {"width": 64, "height": 64, "dpi": 300,
         "layers": [{"name": "背景", "path": "00.png"}]},
        project / "solo.psd",
    )

    original = check_psd.HAVE_PSD_TOOLS
    check_psd.HAVE_PSD_TOOLS = False
    try:
        report = check_psd.Report()
        check_psd.check(psd_path, None, None, None, None, report)
    finally:
        check_psd.HAVE_PSD_TOOLS = original

    check(report.failures() > 0, f"失败项 {report.failures()} 个（应为 >0）")
    detail = "\n".join(message for _, message in report.rows)
    check("未安装 psd_tools" in detail, "结论写明「未安装 psd_tools，PSD 未验证」")


def case_prefixed_file_entry(tmp: Path) -> None:
    print("\n[6] 清单里 file 写成 exports/xxx.png 也必须生效")
    project = tmp / "prefixed-entry"
    exports = project / "exports"
    exports.mkdir(parents=True)
    Image.new("RGB", (80, 80), (180, 180, 180)).save(exports / "a.png")
    # CMYK on a PNG can only ever fail. If the entry is silently dropped, the
    # run reports success instead — which is the regression this guards.
    (project / "delivery.json").write_text(
        json.dumps(
            {"files": [{"file": "exports/a.png", "width": 80, "height": 80,
                        "colour": "CMYK", "dpi": 300}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    code, payload, raw = run_gate(project)
    check(code != 0 and payload.get("ok") is False, f"exit={code}，ok={payload.get('ok')}（应为失败）")
    check("CMYK" in messages(payload), "清单条目没有被路径前缀静默丢弃")
    if "CMYK" not in messages(payload):
        print(raw)


def case_declared_but_absent(tmp: Path) -> None:
    print("\n[7] 清单声明了 exports 里没有的文件必须失败")
    project = tmp / "declared-absent"
    exports = project / "exports"
    exports.mkdir(parents=True)
    Image.new("RGB", (60, 60), (200, 200, 200)).save(exports / "real.png")
    (project / "delivery.json").write_text(
        json.dumps(
            {"files": [{"file": "ghost.png", "width": 60, "height": 60}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    code, payload, raw = run_gate(project)
    check(code != 0 and payload.get("ok") is False, f"exit={code}，ok={payload.get('ok')}（应为失败）")
    check("找不到" in messages(payload), "失败原因是清单与实物不一致")
    if "找不到" not in messages(payload):
        print(raw)


def case_correct_psd_passes(tmp: Path) -> None:
    print("\n[8] 正确的 PSD 必须仍然通过（防止「一律失败」式假修）")
    project = make_layered_project(tmp, invert=False)
    code, payload, raw = run_gate(project)
    check(code == 0 and payload.get("ok") is True, f"exit={code}，ok={payload.get('ok')}（应为通过）")
    check("合成结果与参考一致" in messages(payload), "合成比对确实执行并通过")
    if code != 0:
        print(raw)


def main() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        case_inverted_psd(tmp)
        case_indexed_png(tmp)
        case_empty_exports(tmp)
        case_without_psd_tools(tmp)
        case_prefixed_file_entry(tmp)
        case_declared_but_absent(tmp)
        case_correct_psd_passes(tmp)

    failed = [message for ok, message in results if not ok]
    print("-" * 68)
    if failed:
        print(f"结论：{len(failed)} 项失败（交付门禁又放行了坏文件）")
        sys.exit(1)
    print(f"结论：{len(results)} 项全部通过")


if __name__ == "__main__":
    main()
