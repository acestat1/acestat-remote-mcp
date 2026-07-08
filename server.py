from fastmcp import FastMCP
import os
import requests
from io import BytesIO

mcp = FastMCP("ACE Statistical MCP")

API_BASE = "https://acestat-logistic-mcp.onrender.com"


@mcp.tool()
def health_check() -> dict:
    """
    ACE Statistical API 연결 상태를 확인합니다.
    """
    r = requests.get(f"{API_BASE}/")

    return {
        "success": True,
        "status_code": r.status_code,
        "content_type": r.headers.get("content-type"),
        "text": r.text
    }


@mcp.tool()
def make_logistic_report(
    file_url: str,
    outcome: str,
    id_column: str | None = None
) -> dict:
    """
    엑셀 파일 URL을 받아 로지스틱 회귀분석 Word 보고서를 생성합니다.
    """

    # 1. Claude/ChatGPT가 전달한 파일 URL에서 엑셀 다운로드
    file_response = requests.get(file_url)

    if file_response.status_code != 200:
        return {
            "success": False,
            "step": "download_excel",
            "status_code": file_response.status_code,
            "error": file_response.text[:500]
        }

    excel_file = BytesIO(file_response.content)

    # 2. 기존 API 서버에 엑셀 업로드
    upload_response = requests.post(
        f"{API_BASE}/upload",
        files={
            "file": (
                "uploaded_data.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        }
    )

    if upload_response.status_code != 200:
        return {
            "success": False,
            "step": "upload",
            "status_code": upload_response.status_code,
            "error": upload_response.text[:500]
        }

    upload_result = upload_response.json()
    job_id = upload_result.get("job_id")

    if not job_id:
        return {
            "success": False,
            "step": "get_job_id",
            "upload_result": upload_result
        }

    # 3. 로지스틱 분석 실행
    logistic_response = requests.post(
        f"{API_BASE}/logistic",
        json={
            "job_id": job_id,
            "outcome": outcome,
            "id_column": id_column
        }
    )

    if logistic_response.status_code != 200:
        return {
            "success": False,
            "step": "logistic",
            "status_code": logistic_response.status_code,
            "error": logistic_response.text[:500]
        }

    logistic_result = logistic_response.json()

    if not logistic_result.get("success"):
        return {
            "success": False,
            "step": "logistic_result",
            "result": logistic_result
        }

    # 4. 다운로드 URL 반환
    download_url = f"{API_BASE}/download/{job_id}"

    return {
        "success": True,
        "message": "로지스틱 회귀분석 Word 보고서가 생성되었습니다.",
        "job_id": job_id,
        "outcome": outcome,
        "download_url": download_url
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port
    )