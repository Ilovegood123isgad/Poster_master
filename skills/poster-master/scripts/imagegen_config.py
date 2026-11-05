#!/usr/bin/env python3
"""Configuration for the optional image-generation provider.

Poster Master never ships an API key and never calls a network service unless
you configure one. This module owns the three settings that turn generation on:

    base_url   an OpenAI-compatible endpoint, e.g. https://api.openai.com/v1
               or a relay that speaks the same /images/generations shape
    api_key    your key — stored on your machine, never written into a project
    model      the image model name that endpoint accepts

Resolution order, first hit wins:

    1. command-line flags               (--model ...)
    2. environment variables            POSTER_IMAGEGEN_API_KEY
                                        POSTER_IMAGEGEN_BASE_URL
                                        POSTER_IMAGEGEN_MODEL
    3. the config file                  ~/.poster-master/imagegen.json

Environment variables win over the file so a user can override per shell
without editing anything. Nothing is written into the poster project folder, so
a project stays shareable.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("POSTER_MASTER_HOME") or (Path.home() / ".poster-master"))
CONFIG_FILE = CONFIG_DIR / "imagegen.json"

ENV_KEYS = {
    "api_key": "POSTER_IMAGEGEN_API_KEY",
    "base_url": "POSTER_IMAGEGEN_BASE_URL",
    "model": "POSTER_IMAGEGEN_MODEL",
}

DEFAULT_BASE_URL = "https://api.openai.com/v1"


class ConfigError(RuntimeError):
    """Raised when generation was asked for but is not configured."""


def mask(secret: str) -> str:
    """Show enough to recognise a key, never enough to use it."""
    if not secret:
        return "（未设置）"
    if len(secret) <= 8:
        return "*" * len(secret)
    return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]


def load_file() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{CONFIG_FILE} 不是合法 JSON：{error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"{CONFIG_FILE} 的内容必须是一个 JSON 对象")
    return data


def save_file(values: dict) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {key: value for key, value in values.items() if value}
    CONFIG_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        # Best effort: a key file should not be world-readable.
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return CONFIG_FILE


def resolve(overrides: dict | None = None) -> dict:
    """Return {base_url, api_key, model, source} or raise ConfigError."""
    overrides = {key: value for key, value in (overrides or {}).items() if value}
    file_values = load_file()

    resolved: dict[str, str] = {}
    sources: dict[str, str] = {}
    for key, env_name in ENV_KEYS.items():
        if overrides.get(key):
            resolved[key] = str(overrides[key])
            sources[key] = "命令行参数"
        elif os.environ.get(env_name):
            resolved[key] = os.environ[env_name]
            sources[key] = f"环境变量 {env_name}"
        elif file_values.get(key):
            resolved[key] = str(file_values[key])
            sources[key] = str(CONFIG_FILE)

    missing = [key for key in ("api_key", "model") if not resolved.get(key)]
    if missing:
        names = {"api_key": "API Key", "model": "模型名"}
        raise ConfigError(
            "还没有配置生图模型：缺少 " + "、".join(names[key] for key in missing) + "。\n"
            "运行这条命令按提示填写（只需要做一次）：\n"
            "    python scripts/setup_imagegen.py"
        )

    resolved.setdefault("base_url", DEFAULT_BASE_URL)
    sources.setdefault("base_url", "默认值 " + DEFAULT_BASE_URL)
    return {**resolved, "source": sources}


def endpoint(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def describe(config: dict) -> str:
    return (
        f"  接口地址 base_url : {config['base_url']}   （来源：{config['source']['base_url']}）\n"
        f"  模型     model    : {config['model']}   （来源：{config['source']['model']}）\n"
        f"  密钥     api_key  : {mask(config['api_key'])}   （来源：{config['source']['api_key']}）"
    )
