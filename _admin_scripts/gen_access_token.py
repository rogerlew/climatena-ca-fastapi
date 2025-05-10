import os
import sys
import dotenv
import requests

from pathlib import Path

dotenv.load_dotenv('../', override=True)
ROOT_JWT = os.getenv("ROOT_JWT")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

if not ROOT_JWT:
    print("ERROR: ROOT_JWT not set in .env", file=sys.stderr)
    sys.exit(1)

print(ROOT_JWT)

# ── Prepare request ──────────────────────────────────────────────────────────
url = f"{API_BASE}/token/create"
headers = {
    "Authorization": f"Bearer {ROOT_JWT}",
    "Content-Type": "application/json",
}
# optional: adjust expires_in (in seconds)
payload = {
    "expires_in": 60 * 60 * 24 * 365 * 5  # 7 days
}

# ── Call the endpoint ────────────────────────────────────────────────────────
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
except requests.RequestException as e:
    print(f"Request failed: {e}", file=sys.stderr)
    if e.response is not None:
        print("Response:", e.response.text, file=sys.stderr)
    sys.exit(1)

data = resp.json()
token = data.get("access_token")
expires = data.get("expires_in")

print("New API token:")
print(token)
print(f"\nExpires in: {expires} seconds")