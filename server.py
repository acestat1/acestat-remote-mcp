from fastmcp import FastMCP
import os
import traceback
import requests
from typing import Any

mcp = FastMCP("ACE Statistical MCP")

API_BASE = "https://acestat-logistic-mcp.onrender.com"


@mcp.tool()
def health_check() -> dict:
    """ACE Statistical API의 작동 상태를 확인합니다."""
    try:
        response = requests.get(f"{API_BASE}/", timeout=30)

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type"),
            "text": response.text[:500],
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
def make_logistic_report(
    data: list[dict[str, Any]],
    outcome: str,
    id_column: str | None = None,
) -> dict:
    """
    Claude가 첨부된 Excel 파일의 첫 번째 시트를 읽어 변환한
    JSON 행 데이터를 받아 로지스틱 회귀분석 Word 보고서를 생성합니다.

    data:
        Excel 첫 번째 행을 변수명으로 사용한 행 단위 JSON 배열입니다.
        예: [{"ID": 1, "Age": 52, "Diabetes": 0}, ...]

    outcome:
        이분형 종속변수의 정확한 열 이름입니다.

    id_column:
        분석에서 제외할 ID 열 이름입니다. 없으면 null입니다.
    """
    try:
        if not data:
            return {
                "success": False,
                "step": "validation",
                "error": "분석할 데이터가 없습니다.",
            }

        if not outcome:
            return {
                "success": False,
                "step": "validation",
                "error": "종속변수 outcome이 필요합니다.",
            }

        response = requests.post(
            f"{API_BASE}/report_from_json",
            json={
                "data": data,
                "outcome": outcome,
                "id_column": id_column,
            },
            timeout=180,
        )

        if response.status_code != 200:
            return {
                "success": False,
                "step": "report_from_json",
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "error": response.text[:1000],
            }

        result = response.json()

        if not result.get("success"):
            return {
                "success": False,
                "step": "analysis",
                "result": result,
            }

        return {
            "success": True,
            "message": "로지스틱 회귀분석 Word 보고서가 생성되었습니다.",
            "job_id": result.get("job_id"),
            "outcome": outcome,
            "download_url": result.get("download_url"),
        }

    except Exception as exc:
        return {
            "success": False,
            "step": "exception",
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port,
    )