from datetime import datetime
import os

from fastapi import FastAPI, Request, HTTPException
from starlette.responses import RedirectResponse

from authlib.integrations.starlette_client import OAuth
from itsdangerous import URLSafeSerializer

from mcp.server.fastmcp import FastMCP

# -------------------------
# ENV
# -------------------------

PORT = int(os.environ.get("PORT", 8000))

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
SECRET_KEY = os.environ["SECRET_KEY"]

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

# -------------------------
# APP + MCP
# -------------------------

app = FastAPI()
mcp = FastMCP("Frontwave", host="0.0.0.0", port=PORT)

serializer = URLSafeSerializer(SECRET_KEY, salt="session")

# -------------------------
# GOOGLE OAUTH SETUP
# -------------------------

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


def get_user_from_request(request: Request):
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        return serializer.loads(token)
    except Exception:
        return None


def require_user(request: Request):
    user = get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


# -------------------------
# OAUTH ROUTES
# -------------------------


@app.get("/")
def home():
    return {"message": "Frontwave MCP Auth Server"}


@app.get("/login")
async def login(request: Request):
    redirect_uri = f"{BASE_URL}/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/callback")
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    if not userinfo:
        raise HTTPException(status_code=400, detail="No user info")

    session_token = serializer.dumps(
        {
            "email": userinfo["email"],
            "name": userinfo["name"],
            "sub": userinfo["sub"],
        }
    )

    response = RedirectResponse(url="/")
    response.set_cookie("session", session_token, httponly=True)

    return response


# -------------------------
# MCP TOOLS (PROTECTED)
# -------------------------


@mcp.tool(description="Add 2 numbers")
def add_numbers(a: float, b: float, request: Request) -> float:
    require_user(request)
    return a + b


@mcp.tool(description="Returns current time")
def current_time(request: Request) -> str:
    require_user(request)
    return datetime.utcnow().isoformat()


@mcp.tool(description="Echo tool")
def echo(message: str, request: Request) -> str:
    require_user(request)
    return f"Frontwave says: {message}"


# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
