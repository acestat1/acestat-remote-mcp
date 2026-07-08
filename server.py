from fastmcp import FastMCP
import os
import re
import traceback
import requests
from io import BytesIO

mcp = FastMCP("ACE Statistical MCP")

API_BASE = "https://acestat-logistic-mcp.onrender.com"


def convert_google_sheet_url(file_url: str) -> str:
    match = re.search(r"/spreadsheets/d/([^/]+)", file_url)
    if match:
        sheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    return file_url


@mcp.tool()
def health_check() -> dict:
    try:
        r = requests.get(f"{API_BASE}/", timeout=30)
        return {
            "success": True,
            "status_code": r.status_code,
            "content_type": r.headers.get("content-type"),
            "text": r.text[:500],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
def make_logistic_report(
    file_url: str,
    outcome: str,
    id_column: str | None = None
) -> dict:
    """
    Google Sheets 공유 링크 또는 직접 다운로드 가능한 xlsx URL을 받아
    로지스틱 회귀분석 Word 보고서를 생성합니다.
    """
    try:
        download_url = convert_google_sheet_url(file_url)

        file_response = requests.get(
            download_url,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=60,
        )

        if file_response.status_code != 200:
            return {
                "success": False,
                "step": "download_excel",
                "download_url": download_url,
                "status_code": file_response.status_code,
                "content_type": file_response.headers.get("content-type"),
                "error": file_response.text[:500],
            }

        content_type = file_response.headers.get("content-type", "")

        if "html" in content_type.lower():
            return {
                "success": False,
                "step": "download_excel",
                "download_url": download_url,
                "content_type": content_type,
                "error": "엑셀 파일이 아니라 HTML 페이지가 다운로드되었습니다. Google Sheets 공유 설정을 '링크가 있는 모든 사용자 보기 가능'으로 바꿔주세요.",
            }

        excel_file = BytesIO(file_response.content)

        upload_response = requests.post(
            f"{API_BASE}/upload",
            files={
                "file": (
                    "uploaded_data.xlsx",
                    excel_file,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            timeout=120,
        )

        if upload_response.status_code != 200:
            return {
                "success": False,
                "step": "upload",
                "status_code": upload_response.status_code,
                "content_type": upload_response.headers.get("content-type"),
                "error": upload_response.text[:500],
            }

        upload_result = upload_response.json()
        job_id = upload_result.get("job_id")

        if not job_id:
            return {
                "success": False,
                "step": "get_job_id",
                "upload_result": upload_result,
            }

        logistic_response = requests.post(
            f"{API_BASE}/logistic",
            json={
                "job_id": job_id,
                "outcome": outcome,
                "id_column": id_column,
            },
            timeout=120,
        )

        if logistic_response.status_code != 200:
            return {
                "success": False,
                "step": "logistic",
                "status_code": logistic_response.status_code,
                "content_type": logistic_response.headers.get("content-type"),
                "error": logistic_response.text[:500],
            }

        logistic_result = logistic_response.json()

        if not logistic_result.get("success"):
            return {
                "success": False,
                "step": "logistic_result",
                "result": logistic_result,
            }

        return {
            "success": True,
            "message": "로지스틱 회귀분석 Word 보고서가 생성되었습니다.",
            "job_id": job_id,
            "outcome": outcome,
            "download_url": f"{API_BASE}/download/{job_id}",
        }

    except Exception as e:
        return {
            "success": False,
            "step": "exception",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port,
    )