#!/usr/bin/env python3
"""Guided one-time setup for the image-generation provider.

    python setup_imagegen.py                # ask for what is missing, then test
    python setup_imagegen.py --status       # show the current configuration
    python setup_imagegen.py --test         # test the endpoint and the key
    python setup_imagegen.py --clear        # forget the stored settings

Nothing here ships a key, and no key is ever printed back in full or written
into a poster project. The file it creates is

    ~/.poster-master/imagegen.json

Three questions are asked, in this order, because each one decides the next:

1. **接口地址 (base_url)** — the endpoint that speaks the OpenAI
   ``/images/generations`` shape. For the official API that is
   ``https://api.openai.com/v1``. For a relay (中转站) it is the relay's base,
   usually ending in ``/v1`` — ask the provider, it is not guessable.
2. **API Key** — pasted at a hidden prompt so it stays out of your shell
   history and out of the screen.
3. **模型名 (model)** — must be an image model that endpoint actually serves.
   ``--list-models`` prints the ones the endpoint advertises.

The connectivity test calls ``GET {base_url}/models``, which costs nothing. It
does not spend tokens; use ``--test-generate`` to also render one 1024×1024
image when you are ready to pay for a real round trip.
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import imagegen_config as cfg  # noqa: E402


def request_json(url: str, api_key: str, payload: dict | None = None,
                 timeout: float = 60.0) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def explain(error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        detail = ""
        try:
            detail = error.read().decode("utf-8", "replace")[:300]
        except Exception:                                   # noqa: BLE001
            pass
        if error.code in (401, 403):
            return f"HTTP {error.code}：密钥无效或没有该模型的权限。{detail}"
        if error.code == 404:
            return (
                f"HTTP 404：接口地址或路径不对。base_url 应指到 /v1 这一层，"
                f"不是 /v1/images/generations。{detail}"
            )
        if error.code == 429:
            return f"HTTP 429：额度或频率受限。{detail}"
        return f"HTTP {error.code}：{detail}"
    if isinstance(error, urllib.error.URLError):
        return f"连不上：{error.reason}。检查网络、代理，或 base_url 是否写错。"
    return f"{type(error).__name__}：{error}"


def list_models(config: dict) -> list[str]:
    data = request_json(cfg.endpoint(config["base_url"], "models"), config["api_key"])
    rows = data.get("data") or data.get("models") or []
    names = []
    for row in rows:
        name = row.get("id") or row.get("name") if isinstance(row, dict) else str(row)
        if name:
            names.append(name)
    return names


def test_connection(config: dict, generate: bool) -> bool:
    print("正在测试连通性（GET /models，不消耗额度）…")
    try:
        names = list_models(config)
    except Exception as error:                              # noqa: BLE001
        print("  ✗ " + explain(error))
        print("\n可以先用 --skip-test 保存配置，之后再修。")
        return False

    print(f"  ✓ 接口可用，返回 {len(names)} 个模型")
    if names:
        images = [name for name in names if any(
            token in name.lower() for token in ("image", "dall", "flux", "seedream", "sd", "wanx")
        )]
        shown = images or names[:12]
        print("  可用的图像模型（建议从这里选）：" + ", ".join(shown[:12]))
        if config["model"] not in names and images:
            print(f"  ! 你填的「{config['model']}」不在返回列表里；"
                  f"若它是别名可忽略，否则改成上面某一个")

    if generate:
        print("\n正在生成一张 1024×1024 测试图（会产生费用）…")
        payload = {
            "model": config["model"],
            "prompt": "a single flat orange circle centered on a white background, minimal vector",
            "size": "1024x1024",
            "n": 1,
            "response_format": "b64_json",
        }
        try:
            data = request_json(
                cfg.endpoint(config["base_url"], "images/generations"),
                config["api_key"], payload, timeout=300,
            )
        except Exception as error:                          # noqa: BLE001
            print("  ✗ " + explain(error))
            return False
        items = data.get("data") or []
        if not items:
            print("  ✗ 返回里没有 data 字段：" + json.dumps(data, ensure_ascii=False)[:200])
            return False
        keys = ", ".join(sorted(items[0].keys()))
        print(f"  ✓ 生成成功，返回字段 {keys}")
    return True


def ask(prompt: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        if secret:
            value = getpass.getpass(prompt + suffix + "：")
        else:
            value = input(prompt + suffix + "：").strip()
        if value:
            return value
        if default:
            return default
        print("  这一项必须填写。")


def interactive() -> int:
    current = {}
    try:
        current = cfg.load_file()
    except cfg.ConfigError as error:
        print(f"! 现有配置读不出来：{error}（继续会覆盖它）")

    print("Poster Master · 生图模型配置")
    print("=" * 56)
    print("这个技能不自带任何生图密钥。用自己的账号填一次，之后所有项目都能用。")
    print("配置只存在你自己的电脑上（~/.poster-master/imagegen.json），不进项目文件夹。")
    print()

    base_url = ask("① 接口地址 base_url（OpenAI 兼容，通常以 /v1 结尾）",
                   current.get("base_url") or cfg.DEFAULT_BASE_URL)
    api_key = ask("② API Key（输入时不显示）", secret=True)
    model = ask("③ 模型名（该接口支持的图像模型）",
                current.get("model") or "")

    values = {"base_url": base_url, "api_key": api_key, "model": model}
    try:
        config = cfg.resolve(values)
    except cfg.ConfigError as error:
        print(error)
        return 1

    print()
    print("即将保存：")
    print(cfg.describe(config))
    path = cfg.save_file(values)
    print(f"\n已写入 {path}")

    print()
    if not test_connection(config, generate=False):
        print("\n配置已保存，但接口没通过测试。改完再跑：python setup_imagegen.py --test")
        return 1
    print("\n配置可用。下一步：")
    print('  python scripts/generate_artwork.py --prompt "一座悬浮在深空中的小岛，扁平矢量" \\')
    print('      --size 1536x1024 --output assets/主视觉.png')
    return 0


def show_status() -> int:
    try:
        config = cfg.resolve()
    except cfg.ConfigError as error:
        print(error)
        print(f"\n配置文件：{cfg.CONFIG_FILE}（{'存在' if cfg.CONFIG_FILE.exists() else '不存在'}）")
        return 1
    print("当前生图配置：")
    print(cfg.describe(config))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="配置 Poster Master 的生图模型")
    parser.add_argument("--status", action="store_true", help="只显示当前配置")
    parser.add_argument("--test", action="store_true", help="测试接口与密钥，不消耗额度")
    parser.add_argument("--test-generate", action="store_true",
                        help="再生成一张测试图（会产生费用）")
    parser.add_argument("--list-models", action="store_true", help="列出接口返回的模型")
    parser.add_argument("--clear", action="store_true", help="删除已保存的配置")
    parser.add_argument("--skip-test", action="store_true", help="保存后不测连通性")
    args = parser.parse_args()

    if args.clear:
        if cfg.CONFIG_FILE.exists():
            cfg.CONFIG_FILE.unlink()
            print(f"已删除 {cfg.CONFIG_FILE}")
        else:
            print("没有保存过配置")
        return 0

    if args.status:
        return show_status()

    if args.list_models or args.test or args.test_generate:
        try:
            config = cfg.resolve()
        except cfg.ConfigError as error:
            print(error)
            return 1
        print(cfg.describe(config))
        print()
        if args.list_models:
            try:
                for name in list_models(config):
                    print("  " + name)
            except Exception as error:                      # noqa: BLE001
                print("  ✗ " + explain(error))
                return 1
            return 0
        return 0 if test_connection(config, generate=args.test_generate) else 1

    return interactive()


if __name__ == "__main__":
    sys.exit(main())
