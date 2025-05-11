import uuid
import csv
import subprocess
import pathlib
from typing import List, Literal
import os
from os.path import join as _join

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from starlette.responses import FileResponse
import asyncio
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import time
import uuid
from typing import Optional

import jwt
import dotenv

import logging
log = logging.getLogger("perf")   

dotenv.load_dotenv(override=True)

# ── CONFIG ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 60 * 60 * 24 * 365 * 10  # 10 years
ROOT_TOKEN = os.getenv("ROOT_JWT")        # generate once, store safely

# default parameters
DEFAULT_NORMAL = "Normal_1991_2020.nrm"
DEFAULT_MODE: Literal["Y","S","M","YSM"] = "M"

BASE_DIRS = {
    "bc": r"C:\\ClimateBC_v7.50",
    "na": r"C:\\ClimateNA_v7.50",
}
EXE_NAMES = {
    "bc": "ClimateBC_v7.50.exe",
    "na": "ClimateNA_v7.50.exe",
}

# ── MODELS ───────────────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class CreateTokenRequest(BaseModel):
    expires_in: Optional[int] = ACCESS_TOKEN_EXPIRE

class RevokeTokenRequest(BaseModel):
    jti: str

# ── SETUP ────────────────────────────────────────────────────────────────────
app = FastAPI()
security = HTTPBearer()   # parses Authorization: Bearer <token>

# in‐memory revoked‐JTIs (persist to file/Redis if you like)
REVOKED: set[str] = set()

@app.get("/health")
async def health():
    return {"status": "ok"}
    
# ── HELPERS ──────────────────────────────────────────────────────────────────
def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    jti = payload.get("jti")
    if not jti or jti in REVOKED:
        raise HTTPException(401, "Token revoked")
    return payload


def require_root(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    if token != ROOT_TOKEN:
        raise HTTPException(403, "Root token required")

    return {"sub":"root","role":"root"}

def create_token_payload(expires_in: int, role: str = "api") -> dict:
    now = int(time.time())
    jti = uuid.uuid4().hex
    return {
        "sub": "api_token",
        "role": role,
        "iat": now,
        "exp": now + expires_in,
        "jti": jti,
    }

# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.post("/token/create", response_model=TokenResponse)
def create_token(req: CreateTokenRequest, _: dict = Depends(require_root)):
    """Root only: mint a new API token."""
    payload = create_token_payload(req.expires_in, role="api")
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "access_token": token,
        "expires_in": req.expires_in,
    }

@app.post("/token/revoke")
def revoke_token(req: RevokeTokenRequest, _: dict = Depends(require_root)):
    """Root only: add a jti to the local blacklist."""
    REVOKED.add(req.jti)
    return {"revoked": req.jti}

class Location(BaseModel):
    id1: str
    id2: str
    lat: float
    long: float
    elev: float


class Query(BaseModel):
    locations: List[Location]
    # optional override of normal and mode
    normal: str = DEFAULT_NORMAL
    mode: Literal["Y","S","M","YSM"] = DEFAULT_MODE


def require_token(
    creds: HTTPAuthorizationCredentials = Depends(security)
):
    payload = decode_jwt(creds.credentials)
    return payload

@app.post(
    "/{variant}/query",
    summary="Run a ClimateBC/NA query (requires a valid API token)",
)
async def run_climatena(
    variant: Literal["bc", "na"],
    q: Query,
    token_payload: dict = Depends(require_token),  # ← protect here
):
    # look up the paths for this variant
    try:
        base_dir = BASE_DIRS[variant]
        exe_name = EXE_NAMES[variant]
    except KeyError:
        raise HTTPException(404, detail=f"Unknown variant '{variant}'")

    query_root = _join(base_dir, "api", "queries")

    # 1) make a UUID’d work folder
#    run_id = str(uuid.uuid4())
    run_id = uuid.uuid4().hex
    work_dir = _join(query_root, run_id)
    os.makedirs(work_dir)


    assert os.path.exists(work_dir)

    t0 = time.perf_counter()                 # ── probe 0

    inp = _join(work_dir, "input.csv")
    i = 0
    with open(inp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id1","id2","lat","long","elev"])
        for loc in q.locations:
            w.writerow([loc.id1, loc.id2, loc.lat, loc.long, loc.elev])
            i += 1

    out = _join(work_dir, "out.csv")

    inp = os.path.relpath(inp, base_dir)
    out = os.path.relpath(out, base_dir)

    cmd = [
        _join(base_dir, exe_name),
        f"/{q.mode}",
        f"/{q.normal}",
        f"/{inp}",
        f"/{out}",
        "/V",       
    ]
    
    timeout = 10.0 + len(q.locations) * 0.1

    # ── run ClimateNA -----------------------------------------------------------
    t1 = time.perf_counter()                 # before launch

    # ─── override env so ClimateNA uses our fast temp folder ─────────────────
    env = os.environ.copy()
    fast_temp = r"C:\ClimateNA_v7.50\api\temp"
    env["TEMP"]          = fast_temp
    env["TMP"]           = fast_temp
    env["LOCALAPPDATA"]  = fast_temp
    os.environ["SESSIONNAME"] = "Console"  # Mimic console environment
    # ─────────────────────────────────────────────────────────────────────────────
    result = subprocess.run(
        cmd,
        cwd=str(base_dir),
        env=env,                          # <-- use our env
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    t2 = time.perf_counter()                 # after ClimateNA exits
    result.check_returncode()
    # ---------------------------------------------------------------------------

    # ── read the CSV (for FileResponse with stat_result we touch the file anyway)
    csv_path = _join(base_dir, out)
    _     = os.stat(csv_path)                # warm cache
    t3 = time.perf_counter()                 # after stat

    log.info("perf  create_csv  %.3f s", t2 - t1)   # EXE runtime
    log.info("perf  stat_csv    %.3f s", t3 - t2)   # filesystem / AV hit
    log.info("perf  total route %.3f s", t3 - t0)

    # 5) return the CSV for download
    return FileResponse(
        path=_join(base_dir, out),
        filename=f"{run_id}_out.csv",
        media_type="text/csv",
        stat_result=os.stat(_join(base_dir, out)),  # forces blocking sendfile()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
