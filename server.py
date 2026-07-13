import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


load_dotenv()

N8N_RESULT_URL = os.getenv("N8N_RESULT_URL", "").strip()
DEFAULT_ANALYSIS_ID = os.getenv(
    "DEFAULT_ANALYSIS_ID",
    "1783849206722_8wgv0un8p1"
).strip()

UPLOAD_GUIDE_URL = os.getenv(
    "UPLOAD_GUIDE_URL",
    "현재 데모에서는 샘플 매장 데이터를 사용합니다. 실제 사용 시 매출 엑셀 업로드 화면을 통해 분석을 시작할 수 있습니다."
).strip()

if not N8N_RESULT_URL:
    raise RuntimeError("N8N_RESULT_URL이 .env 파일에 없습니다.")


mcp = FastMCP(
    name="LocalBizPilot",
    instructions=(
        "LocalBizPilot is an AI digital assistant for small business owners. "
        "The real service flow starts when a store owner uploads a sales Excel file. "
        "For the current PlayMCP demo, use the prepared sample store analysis result "
        "when the user asks for sales analysis, recommended menus, promotion actions, "
        "or poster results. Do not ask ordinary users for an analysis_id. "
        "If the user asks to analyze their own store data, explain that they need to "
        "upload a sales Excel file first."
    ),
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


async def fetch_result(view: str) -> dict[str, Any]:
    payload = {
        "analysis_id": DEFAULT_ANALYSIS_ID,
        "view": view,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                N8N_RESULT_URL,
                json=payload,
                headers={"ngrok-skip-browser-warning": "true"},
            )
            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException as exc:
        raise RuntimeError("LocalBizPilot result lookup timed out.") from exc

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"LocalBizPilot result lookup failed: HTTP {exc.response.status_code}"
        ) from exc

    except ValueError as exc:
        raise RuntimeError("LocalBizPilot result API returned invalid JSON.") from exc

    if not data.get("success"):
        raise RuntimeError("LocalBizPilot result API returned an unsuccessful response.")

    return data.get("result", {})


@mcp.tool(
    name="get_demo_monthly_sales_report",
    title="Demo Monthly Sales Report",
    description=(
        "Use this tool when the user asks for last month's sales analysis, "
        "monthly sales report, store performance, or sales summary. "
        "No input is required. This returns a demo sales report based on a sample "
        "store analysis. Explain that real users can upload their own sales Excel file "
        "to receive a store-specific report."
    ),
    annotations=ToolAnnotations(
        title="Demo Monthly Sales Report",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_demo_monthly_sales_report() -> dict[str, Any]:
    result = await fetch_result("summary")

    return {
        "service_note": (
            "현재는 PlayMCP 테스트를 위해 샘플 매장 데이터를 기준으로 분석 결과를 제공합니다. "
            "실제 사용 시에는 사장님이 매출 엑셀 파일을 업로드하면 해당 매장 기준으로 리포트가 생성됩니다."
        ),
        "store_name": result.get("store_name"),
        "analysis_month": result.get("analysis_month"),
        "next_month": result.get("next_month"),
        "report_preview": result.get("report_preview"),
        "email": result.get("email"),
        "poster_generated": result.get("poster_generated"),
        "updated_at": result.get("updated_at"),
    }


@mcp.tool(
    name="get_demo_menu_and_promotion_actions",
    title="Demo Menu and Promotion Actions",
    description=(
        "Use this tool when the user asks what menu to sell next month, "
        "which menu to promote, what promotion strategy to use, or what actions "
        "the store owner should take. No input is required. This returns demo "
        "recommendations based on sales, time pattern, weather, holiday, and trend analysis."
    ),
    annotations=ToolAnnotations(
        title="Demo Menu and Promotion Actions",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_demo_menu_and_promotion_actions() -> dict[str, Any]:
    result = await fetch_result("actions")

    return {
        "service_note": (
            "현재는 샘플 매장 데이터를 기준으로 추천 메뉴와 홍보 액션을 보여드립니다. "
            "실제 사용 시에는 업로드된 매출 데이터, 요일·시간대 패턴, 날씨, 공휴일, 검색트렌드를 함께 반영합니다."
        ),
        "store_name": result.get("store_name"),
        "analysis_month": result.get("analysis_month"),
        "next_month": result.get("next_month"),
        "recommendation_section": result.get("recommendation_section"),
        "action_section": result.get("action_section"),
    }


@mcp.tool(
    name="get_demo_poster_result",
    title="Demo Poster Result",
    description=(
        "Use this tool when the user asks about promotion posters, poster results, "
        "or whether a poster was generated. No input is required. This returns "
        "demo poster metadata generated from the recommended menu score."
    ),
    annotations=ToolAnnotations(
        title="Demo Poster Result",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_demo_poster_result() -> dict[str, Any]:
    result = await fetch_result("poster")

    return {
        "service_note": (
            "현재는 샘플 매장 분석 결과를 바탕으로 생성된 포스터 결과를 보여드립니다. "
            "실제 사용 시에는 추천 메뉴 점수를 기반으로 매장별 홍보 포스터가 생성됩니다."
        ),
        "store_name": result.get("store_name"),
        "analysis_month": result.get("analysis_month"),
        "next_month": result.get("next_month"),
        "poster": result.get("poster"),
        "email_subject": result.get("email_subject"),
    }


@mcp.tool(
    name="get_sales_file_upload_guide",
    title="Sales File Upload Guide",
    description=(
        "Use this tool when the user asks how to analyze their own store data, "
        "how to upload a sales file, or whether they can use their own Excel file. "
        "No input is required. It explains the real service flow."
    ),
    annotations=ToolAnnotations(
        title="Sales File Upload Guide",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=True,
    ),
)
async def get_sales_file_upload_guide() -> dict[str, Any]:
    return {
        "real_service_flow": [
            "사장님이 월간 매출 엑셀 파일을 업로드합니다.",
            "업로드된 매출 데이터가 PostgreSQL에 저장됩니다.",
            "월간 매출, 카테고리별 매출, 인기·저회전 메뉴, 요일·시간대 패턴을 분석합니다.",
            "날씨, 공휴일, 네이버 검색트렌드 데이터를 함께 반영합니다.",
            "추천 메뉴를 점수화하고, 월간 리포트와 홍보 액션, 포스터 결과를 생성합니다."
        ],
        "demo_note": (
            "현재 PlayMCP 테스트에서는 별도 파일 업로드 없이 샘플 매장 데이터를 기준으로 기능을 체험할 수 있습니다."
        ),
        "upload_guide": UPLOAD_GUIDE_URL,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
