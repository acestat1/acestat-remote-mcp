from fastmcp import FastMCP
import os
import requests

mcp = FastMCP(
    "ACE Statistical MCP",
    stateless_http=True
)

API_BASE = "https://acestat-logistic-mcp.onrender.com/"


@mcp.tool()
def health_check() -> dict:
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
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp/",
        allowed_hosts=[
            "acestat-remote-mcp.onrender.com",
            "127.0.0.1",
            "localhost"
        ],
        allowed_origins=[
            "https://claude.ai",
            "https://acestat-remote-mcp.onrender.com"
        ]
    )