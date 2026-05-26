import asyncio
from datetime import datetime
import os
import httpx
from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.dependencies import get_access_token
from functools import lru_cache

PORT = int(os.environ.get("PORT", 8000))

auth = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url=os.environ["BASE_URL"],
)

mcp = FastMCP("Frontwave", auth=auth)


async def get_google_user() -> dict:
    """Fetch Google user info and return stable user identity."""
    token = get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        resp.raise_for_status()
        data = resp.json()
    return {
        "sub": data["sub"],           # stable unique Google user ID
        "email": data.get("email"),   # for logging/display only
        "name": data.get("name"),
    }


@mcp.tool(description="Add 2 numbers")
async def add_numbers(a: float, b: float) -> float:
    user = await get_google_user()
    print(f"[add_numbers] user={user['sub']} ({user['email']})")
    return a + b


@mcp.tool(description="Returns current time")
async def current_time() -> str:
    user = await get_google_user()
    print(f"[current_time] user={user['sub']} ({user['email']})")
    return datetime.utcnow().isoformat()


@mcp.tool(description="A simple echo tool")
async def echo(message: str) -> str:
    user = await get_google_user()
    print(f"[echo] user={user['sub']} ({user['email']})")
    return f"Frontwave says: {message}"


if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=PORT))
