# roblox-headshot-proxy-py

Minimal Python proxy for Roblox thumbnails API. Returns the `imageUrl` for a user's avatar headshot.

## Endpoints
- `GET /v1/headshot?userId=<number>` → JSON `{ targetId, state, imageUrl, version, raw }`
- `GET /v1/headshot/url?userId=<number>` → `text/plain` image URL (empty string on error)
- `GET /health` → `{ ok: true }`

## Deploy on Render
1) Push to GitHub  
2) Create Web Service → Runtime: **Python**  
3) Build Command: `pip install -r requirements.txt`  
4) Start Command: `gunicorn app:app`  
5) (Optional) Env var `CACHE_TTL=300`
