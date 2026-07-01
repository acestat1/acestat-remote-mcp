from fastmcp import FastMCP
import requests
import os

mcp = FastMCP("ACE Logistic Remote MCP")

API_BASE = "https://acestat-logistic-mcp.onrender.com"


@mcp.tool()
def health_check() -> dict:
    """
    ACE Statistical API 서버가 정상 작동하는지 확인합니다.
    """
    r = requests.get(f"{API_BASE}/")
    return r.json()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )