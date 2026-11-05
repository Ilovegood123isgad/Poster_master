#!/usr/bin/env python3
"""Create the GitHub Release for the current version and attach the archive.

    python tools/make_release.py [--dry-run]

Why this exists: the documentation links straight at
``releases/download/v<version>/poster-master-skill-v<version>.zip``. A pushed tag
alone does not create that URL — the release and its asset do. So the release is
part of publishing, not an optional extra.

The token comes from the same credential helper git already uses; it is read into
memory, used for two API calls, and never printed or written to disk.

The release body is taken from the ``## v<version>`` section of CHANGELOG.md, so
there is one place to edit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "poster-master"
OWNER = "Ilovegood123isgad"
NAME = "Poster_master"
API = "https://api.github.com"
UPLOADS = "https://uploads.github.com"


def skill_version() -> str:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"([^"]+)"', text, re.M)
    if not match:
        sys.exit("读不到 SKILL.md 里的 metadata.version")
    return match.group(1)


def release_body(version: str) -> str:
    changelog = REPO / "CHANGELOG.md"
    if not changelog.exists():
        return f"poster-master v{version}"
    text = changelog.read_text(encoding="utf-8")
    pattern = re.compile(rf"^## v{re.escape(version)}\b.*?(?=^## v|\Z)", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return f"poster-master v{version}"
    body = match.group(0).strip()
    body = re.sub(rf"^## v{re.escape(version)}[^\n]*\n", "", body)
    return body.strip()


def git_token() -> str:
    """Read the token git already uses for github.com, without echoing it."""
    payload = "protocol=https\nhost=github.com\n\n"
    completed = subprocess.run(
        ["git", "credential", "fill"],
        input=payload, capture_output=True, text=True, cwd=str(REPO),
    )
    if completed.returncode != 0:
        sys.exit("拿不到 git 凭据：先确认 git push 可用（git credential fill 失败）")
    for line in completed.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    sys.exit("凭据里没有 password 字段，无法调用 GitHub API")


def api(method: str, url: str, token: str, payload: dict | None = None,
        raw: bytes | None = None, content_type: str = "application/json") -> tuple[int, dict]:
    data = raw if raw is not None else (
        json.dumps(payload).encode("utf-8") if payload is not None else None
    )
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", "Bearer " + token)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("Content-Type", content_type)
    if raw is not None:
        request.add_header("Content-Length", str(len(raw)))
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:500]
        return error.code, {"error": detail}


def main() -> None:
    parser = argparse.ArgumentParser(description="为当前版本创建 GitHub Release 并附上压缩包")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要发布的内容")
    parser.add_argument("--update-body", action="store_true",
                        help="只把已有 Release 的说明同步成 CHANGELOG 的最新内容（改错别字、日期用）")
    args = parser.parse_args()

    version = skill_version()
    tag = f"v{version}"
    archive = REPO / "dist" / f"poster-master-skill-v{version}.zip"
    body = release_body(version)

    print(f"仓库：{OWNER}/{NAME}")
    print(f"标签：{tag}")
    print(f"附件：{archive.name}（{archive.stat().st_size // 1024 if archive.exists() else 0} KB）")
    print(f"说明：{len(body)} 字符，取自 CHANGELOG.md")
    if not archive.exists():
        sys.exit(f"找不到压缩包：{archive}（先跑 tools/package_skill.py）")

    if args.dry_run:
        print("\n--- 将要创建的 Release 说明 ---")
        print(body)
        return

    token = git_token()

    if args.update_body:
        status, release = api("GET", f"{API}/repos/{OWNER}/{NAME}/releases/tags/{tag}", token)
        if status != 200:
            sys.exit(f"读不到 Release {tag}：{status} {release.get('error') or release}")
        release_id = release.get("id")
        status, updated = api(
            "PATCH", f"{API}/repos/{OWNER}/{NAME}/releases/{release_id}", token,
            {"body": body, "name": f"poster-master {tag}"},
        )
        if status == 200:
            print(f"Release 说明已更新：{updated.get('html_url')}（{len(body)} 字符）")
        else:
            sys.exit(f"更新失败：{status} {updated.get('error') or updated}")
        return

    status, release = api(
        "POST", f"{API}/repos/{OWNER}/{NAME}/releases", token,
        {"tag_name": tag, "name": f"poster-master {tag}", "body": body,
         "draft": False, "prerelease": False},
    )
    if status == 422:
        # Already exists: reuse it rather than failing the publish.
        status, release = api("GET", f"{API}/repos/{OWNER}/{NAME}/releases/tags/{tag}", token)
        if status != 200:
            sys.exit(f"Release 已存在但读取失败：{status} {release}")
        print(f"Release {tag} 已存在，复用：{release.get('html_url')}")
    elif status == 201:
        print(f"Release 已创建：{release.get('html_url')}")
    else:
        sys.exit(f"创建 Release 失败：{status} {release.get('error') or release}")

    upload_url = release.get("upload_url") or ""
    if not upload_url:
        sys.exit("Release 返回里没有 upload_url")
    base_upload = upload_url.split("{", 1)[0]
    asset_url = f"{base_upload}?name={archive.name}"
    status, asset = api("POST", asset_url, token, raw=archive.read_bytes(),
                        content_type="application/zip")
    if status in (201, 200):
        print(f"附件已上传：{asset.get('browser_download_url')}")
    else:
        print(f"附件上传失败：{status} {asset.get('error')}")
        print("可以手动在 Release 页面拖入 dist/" + archive.name)

    print(f"\n下载地址（文档里引用的就是它）：")
    print(f"https://github.com/{OWNER}/{NAME}/releases/download/{tag}/{archive.name}")


if __name__ == "__main__":
    main()
