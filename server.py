from datetime import datetime
import os

from mcp.server.fastmcp import FastMCP

PORT = os.environ.get("PORT", 8000)
mcp = FastMCP("Frontwave", host="0.0.0.0", port=PORT)


@mcp.tool(description="Add 2 numbers")
def add_numbers(a: float, b: float) -> float:
    return a + b


@mcp.tool(description="Returns current time")
def current_time() -> str:
    return datetime.utcnow().isoformat()


@mcp.tool(description="A simple echo tool")
def echo(message: str) -> str:
    return f"Frontwave says: {message}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
