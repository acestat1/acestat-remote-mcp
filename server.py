from fastmcp import FastMCP
import os
import requests

mcp = FastMCP("ACE Statistical MCP")

API_BASE = "https://acestat-logistic-mcp.onrender.com/"


@mcp.tool()
def health_check() -> dict:
    """
    ACE Statistical MCP 서버와 기존 분석 API 연결 상태를 확인합니다.
    """
    r = requests.get(API_BASE)

    return {
        "success": True,
        "status_code": r.status_code,
        "content_type": r.headers.get("content-type"),
        "text": r.text
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port
    )