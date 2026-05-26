from datetime import datetime
import os

from fastapi import FastAPI, Request, HTTPException
from starlette.responses import RedirectResponse

from authlib.integrations.starlette_client import OAuth
from itsdangerous import URLSafeSerializer

from mcp.server.fastmcp import FastMCP

# -------------------------
# CONFIG
# -------------------------

PORT = int(os.getenv("PORT", 8000))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY]):
    raise RuntimeError("Missing env vars")

app = FastAPI()
mcp = FastMCP("Frontwave")

serializer = URLSafeSerializer(SECRET_KEY, salt="session")

oauth = OAuth()

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# -------------------------
# AUTH HELPERS
# -------------------------

def get_user_from_cookie(cookie: str):
    try:
        return serializer.loads(cookie)
    except Exception:
        return None


def require_token(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    user = get_user_from_cookie(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    return user

# -------------------------
# ROUTES
# -------------------------

@app.get("/")
def home():
    return {"message": "Frontwave MCP Auth Server"}


@app.get("/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(
        request,
        f"{BASE_URL}/callback"
    )


@app.get("/callback")
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    if not userinfo:
        raise HTTPException(status_code=400, detail="No user info")

    session = serializer.dumps({
        "email": userinfo["email"],
        "name": userinfo["name"],
        "sub": userinfo["sub"],
    })

    resp = RedirectResponse("/")
    resp.set_cookie("session", session, httponly=True)
    return resp

# -------------------------
# MCP TOOLS (FIXED)
# -------------------------

@mcp.tool(description="Add 2 numbers")
def add_numbers(
    a: float,
    b: float,
    auth_token: str
) -> float:
    require_token(auth_token)
    return a + b


@mcp.tool(description="Returns current time")
def current_time(auth_token: str) -> str:
    require_token(auth_token)
    return datetime.utcnow().isoformat()


@mcp.tool(description="Echo tool")
def echo(message: str, auth_token: str) -> str:
    require_token(auth_token)
    return f"Frontwave says: {message}"

# -------------------------
# RUN MCP INSIDE FASTAPI
# -------------------------

app.mount("/mcp", mcp.streamable_http_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
