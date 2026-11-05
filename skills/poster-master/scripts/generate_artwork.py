#!/usr/bin/env python3
"""Generate one artwork asset with your own image model.

    python generate_artwork.py --prompt "深空中的悬浮岛，扁平矢量，薄荷绿与深青" \\
        --size 1536x1024 --output assets/主视觉.png
    python generate_artwork.py --prompt-file prompt.txt --output assets/主视觉.png --dry-run

Requires a configured provider: run ``setup_imagegen.py`` once.

What this script deliberately does **not** do:

* it does not ship, ask for, or print a key;
* it does not generate logos, brand marks, packaging text, or a real person's
  likeness — those are facts, not atmosphere (see
  ``references/asset-processing.md``);
* it does not pretend a result is final: every output gets a sidecar record
  with the model, the prompt, the size, and the date, so the asset ledger can
  cite it.

``--dry-run`` prints the exact request without sending it, which is how you
check a prompt and a size before spending anything.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import imagegen_config as cfg  # noqa: E402


def build_payload(args) -> dict:
    payload: dict = {
        "model": args.model,
        "prompt": args.prompt,
        "n": 1,
        "size": args.size,
        "response_format": "b64_json",
    }
    if args.quality:
        payload["quality"] = args.quality
    if args.negative:
        # Not part of the OpenAI schema, but most relays accept it; harmless if ignored.
        payload["negative_prompt"] = args.negative
    return payload


def call(config: dict, payload: dict, timeout: float) -> dict:
    url = cfg.endpoint(config["base_url"], "images/generations")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + config["api_key"],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def save_image(item: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if item.get("b64_json"):
        output.write_bytes(base64.b64decode(item["b64_json"]))
        return
    if item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=180) as response:
            output.write_bytes(response.read())
        return
    raise SystemExit("返回里既没有 b64_json 也没有 url：" + json.dumps(item)[:200])


def main() -> int:
    parser = argparse.ArgumentParser(description="用你自己的生图模型生成一张素材")
    parser.add_argument("--prompt", help="提示词")
    parser.add_argument("--prompt-file", help="从文件读提示词（长提示词用这个）")
    parser.add_argument("--negative", help="反向提示词（部分中转站支持）")
    parser.add_argument("--size", default="1024x1024",
                        help="像素尺寸，例如 1536x1024；必须是模型支持的尺寸")
    parser.add_argument("--quality", help="quality 参数，例如 high / medium（可选）")
    parser.add_argument("--output", help="输出图片路径，建议放在项目 assets/ 下")
    parser.add_argument("--model", help="覆盖配置里的模型名")
    parser.add_argument("--base-url", help="覆盖配置里的接口地址")
    parser.add_argument("--api-key", help="覆盖配置里的密钥（不推荐：会留在命令历史里）")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--dry-run", action="store_true", help="只打印请求，不真的调用")
    args = parser.parse_args()

    if args.prompt_file:
        args.prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not args.prompt:
        parser.error("需要 --prompt 或 --prompt-file")

    try:
        config = cfg.resolve({"model": args.model, "base_url": args.base_url,
                              "api_key": args.api_key})
    except cfg.ConfigError as error:
        print(error)
        return 1

    args.model = config["model"]
    payload = build_payload(args)

    print("生图配置：")
    print(cfg.describe(config))
    print(f"  尺寸 size     : {args.size}")
    print()

    if args.dry_run:
        print("--dry-run：将要发送的请求如下（未实际调用）")
        print(f"POST {cfg.endpoint(config['base_url'], 'images/generations')}")
        safe = {key: ("<你的密钥，已隐去>" if key == "api_key" else value)
                for key, value in payload.items()}
        print(json.dumps(safe, ensure_ascii=False, indent=2))
        return 0

    if not args.output:
        parser.error("需要 --output")

    print("正在生成…")
    try:
        data = call(config, payload, args.timeout)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        hint = {
            401: "密钥无效或没有该模型权限。",
            403: "密钥没有该模型的权限。",
            404: "接口地址不对：base_url 应指到 /v1 这一层。",
            429: "额度或频率受限。",
        }.get(error.code, "")
        print(f"生成失败：HTTP {error.code} {hint}\n{detail}")
        return 1
    except urllib.error.URLError as error:
        print(f"连不上：{error.reason}。检查网络或 base_url。")
        return 1

    items = data.get("data") or []
    if not items:
        print("返回里没有 data：" + json.dumps(data, ensure_ascii=False)[:400])
        return 1

    output = Path(args.output)
    save_image(items[0], output)

    record = {
        "file": str(output),
        "tool": "generate_artwork.py",
        "base_url": config["base_url"],
        "model": args.model,
        "prompt": args.prompt,
        "negative_prompt": args.negative or "",
        "size": args.size,
        "quality": args.quality or "",
        "date": date.today().isoformat(),
        "response_id": data.get("id") or "",
        "reviewer": "",
        "licence": "由用户自有账号生成；商用与再分发条款以该服务商为准",
    }
    sidecar = output.with_suffix(output.suffix + ".json")
    sidecar.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"已保存：{output}")
    print(f"生成记录：{sidecar.name}")
    print()
    print("粘进「素材台账.md」的生成素材记录表：")
    print(f"| {output.name} | {args.model} | {args.prompt[:40]}… | {record['date']} | （待审） | v1 |")
    print()
    print("下一步（不要跳过）：")
    print("  1. 打开图看构图、留白、安全区；主体不要压到画面边缘。")
    print("  2. 确认没有生成 logo、品牌字、包装文字或真人面孔。")
    print("  3. 把这一行记录填进素材台账，审核人签字后才可进交付稿。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
