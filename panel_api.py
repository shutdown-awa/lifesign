#!/usr/bin/env python3
"""1Panel API 请求辅助脚本（已实测可用）。

用法:
    ./panel_api.py GET  /api/v2/dashboard/base/os
    ./panel_api.py POST /api/v2/websites/search '{"page":1,"pageSize":50,"name":"","orderBy":"createdAt","order":"descending","websiteGroupId":0}'

自动计算 1Panel-Token (MD5, 兼容模式) 并携带 1Panel-Timestamp。

密钥来源（按优先级）:
    1. 环境变量 ONEPANEL_API_KEY / ONEPANEL_API_URL
    2. 同目录 .env 文件中的同名键（.env 不应提交到 git）

注意: 底层用 ``curl`` 子进程而非 urllib —— 1Panel WAF 对 urllib 的
HTTP 指纹会误拦（返回 "Access Temporarily Unavailable" HTML），
curl 则稳定通过。
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _load_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


_env = _load_dotenv(Path(__file__).resolve().parent / ".env")

API_KEY = os.environ.get("ONEPANEL_API_KEY") or _env.get("ONEPANEL_API_KEY")
BASE = (
    os.environ.get("ONEPANEL_API_URL")
    or _env.get("ONEPANEL_API_URL")
    or "http://127.0.0.1:8001"
)

if not API_KEY:
    sys.exit("错误: 未找到 ONEPANEL_API_KEY，请 export 或写在同目录 .env 中")


def make_token(api_key: str, ts: str) -> str:
    return __import__("hashlib").md5(("1panel" + api_key + ts).encode()).hexdigest()


def request(method: str, path: str, body: dict | None = None) -> dict:
    ts = str(int(time.time()))
    url = BASE + path
    cmd = [
        "curl", "-sS", "--max-time", "15",
        "-X", method,
        "-H", f"1Panel-Token: {make_token(API_KEY, ts)}",
        "-H", f"1Panel-Timestamp: {ts}",
        "-H", "Accept: application/json",
    ]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)]
    cmd.append(url)

    curl = shutil.which("curl")
    if not curl:
        return {"error": "curl 不存在", "status": None}
    try:
        proc = subprocess.run(
            [curl] + cmd[1:], capture_output=True, text=True, timeout=20
        )
        raw = proc.stdout
        try:
            return json.loads(raw)
        except Exception:
            # curl 非零码或非 JSON 输出（WAF HTML 等）
            return {
                "raw": raw[:500],
                "curl_exit": proc.returncode,
                "stderr": proc.stderr[:300],
            }
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "status": None}
    except Exception as e:
        return {"error": str(e), "status": None}


if __name__ == "__main__":
    method = sys.argv[1] if len(sys.argv) > 1 else "GET"
    path = sys.argv[2] if len(sys.argv) > 2 else "/api/v2/dashboard/base/os"
    body = None
    if len(sys.argv) > 3:
        body = json.loads(sys.argv[3])
    print(json.dumps(request(method, path, body), ensure_ascii=False, indent=2))