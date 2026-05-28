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
    required_scopes=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
    ],
)

mcp = FastMCP("Frontwave", auth=auth)


async def get_google_user() -> dict:
    token = get_access_token()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        resp.raise_for_status()

    return resp.json()


@mcp.tool(description="Add 2 numbers")
async def add_numbers(a: float, b: float) -> float:
    user = await get_google_user()
    return a + b


@mcp.tool(description="Returns current time")
async def current_time() -> str:
    user = await get_google_user()
    return datetime.utcnow().isoformat()


@mcp.tool(description="A simple echo tool")
async def echo(message: str) -> str:
    user = await get_google_user()
    return f"Frontwave says: {message}"

@mcp.tool(description="Get the authenticated Google user identity")
async def who_am_i() -> dict:
    user = await get_google_user()
    payload = {
        "user": user
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://frontwave.biz:30003/health",
            json=payload
        )
        resp.raise_for_status()
        return resp.json()

@mcp.tool(description="Get branch code and name")
async def get_branch() -> dict:
    user = await get_google_user()
    payload = {
        "user": user
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://frontwave.biz:30003/get-branch",
            json=payload
        )
        resp.raise_for_status()
        return resp.json()

@mcp.tool(description="List inventory")
async def list_inventory() -> dict:
    user = await get_google_user()
    payload = {
        "user": user
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://frontwave.biz:30003/list-inventory",
            json=payload
        )
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=PORT))
