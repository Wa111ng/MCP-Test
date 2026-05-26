from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

mcp = FastMCP(name="Google Secure MCP")

@mcp.tool()
async def who_am_i() -> dict:
    token = get_access_token()

    return {
        "user_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name"),
    }


@mcp.tool()
def add(a: float, b: float) -> float:
    return a + b
