import os
import time
import re
from typing import Dict, Any
import requests
from flask import Flask, request, jsonify, Response, redirect

app = Flask(__name__)

TTL = int(os.getenv("CACHE_TTL", "300"))  # seconds
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5.0"))
USER_AGENT = os.getenv("USER_AGENT", "roblox-headshot-proxy-py/1.0")

_session = requests.Session()
_session.headers.update({"Accept": "application/json", "User-Agent": USER_AGENT})

_cache: Dict[str, Dict[str, Any]] = {}  # userId -> { "data": item, "exp": epoch }


def _digits(s: str) -> bool:
    return bool(re.fullmatch(r"\d+", s))


def _fetch_headshot(user_id: str) -> Dict[str, Any]:
    now = time.time()
    hit = _cache.get(user_id)
    if hit and now < hit["exp"]:
        return hit["data"]

    upstream = (
        "https://thumbnails.roblox.com/v1/users/avatar-headshot"
        f"?userIds={user_id}&size=420x420&format=Png&isCircular=false"
    )

    r = _session.get(upstream, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    j = r.json()
    item = (j.get("data") or [None])[0]
    if not item:
        raise RuntimeError("no data")

    _cache[user_id] = {"data": item, "exp": now + TTL}
    return item


@app.get("/v1/headshot")
def headshot_json():
    user_id = str(request.args.get("userId", "")).strip()
    if not _digits(user_id):
        return jsonify({"error": "invalid userId"}), 400
    try:
        item = _fetch_headshot(user_id)
        return jsonify(
            {
                "targetId": item.get("targetId"),
                "state": item.get("state"),
                "imageUrl": item.get("imageUrl"),
                "version": item.get("version"),
                "raw": item,
            }
        )
    except requests.RequestException as e:
        return jsonify({"error": f"upstream {getattr(e.response,'status_code',None)}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.get("/v1/headshot/url")
def headshot_url():
    user_id = str(request.args.get("userId", "")).strip()
    if not _digits(user_id):
        return Response("", status=400, mimetype="text/plain")
    try:
        item = _fetch_headshot(user_id)
        url = item.get("imageUrl") or ""
        return Response(url, mimetype="text/plain")
    except Exception:
        return Response("", status=502, mimetype="text/plain")


@app.get("/v1/headshot/redirect")
def headshot_redirect():
    user_id = str(request.args.get("userId", "")).strip()
    if not _digits(user_id):
        return Response("invalid userId", status=400)
    try:
        item = _fetch_headshot(user_id)
        url = item.get("imageUrl")
        if url:
            return redirect(url, code=302)
        return Response("not ready", status=202)
    except Exception:
        return Response("upstream error", status=502)


@app.get("/health")
def health():
    return jsonify({"ok": True, "uptime": time.time() - ps_start})


ps_start = time.time()
