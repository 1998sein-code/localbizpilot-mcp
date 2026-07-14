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
    "현재 PlayMCP 데모에서는 샘플 매장 데이터로 기능을 체험할 수 있습니다. 실제 서비스에서는 사장님이 매출 엑셀 파일을 업로드하면 해당 매장 기준으로 분석이 시작됩니다."
).strip()


mcp = FastMCP(
    name="LocalBizPilot",
    instructions=(
        "LocalBizPilot is an AI digital assistant for small business owners. "
        "The real service flow starts when a store owner uploads a sales Excel file. "
        "For the current PlayMCP demo, use the prepared sample store analysis result. "
        "When the user asks for last month's sales report, recommended menu, promotion strategy, "
        "or poster result, call the appropriate tool immediately. "
        "If the user asks how to use their own sales data, explain the sales file upload flow."
    ),
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


DEMO_RESULTS: dict[str, dict[str, Any]] = {
    "summary": {
        "store_name": "카페 아들러",
        "analysis_month": "2026-05",
        "next_month": "2026-06",
        "report_preview": (
            "5월 한 달간 총 매출은 약 388만 원, 주문 건수는 241건입니다. "
            "제과/빵과 커피가 전체 매출의 핵심 카테고리로 나타났으며, "
            "아메리카노, 로쉐쿠키, 버터떡, 아들러커피가 주요 인기 메뉴로 확인되었습니다. "
            "금요일 점심 시간대와 주말 오후 시간대에 매출이 집중되는 패턴이 나타났습니다. "
            "실제 사용 시에는 사장님이 업로드한 매출 엑셀 데이터를 기준으로 월간 매출, "
            "카테고리별 매출, 인기·저회전 메뉴, 요일·시간대별 판매 패턴을 분석합니다."
        ),
        "email": {
            "to": "demo@example.com",
            "subject": "카페 아들러 2026년 5월 매출 리포트"
        },
        "poster_generated": True,
        "updated_at": "demo"
    },
    "actions": {
        "store_name": "카페 아들러",
        "analysis_month": "2026-05",
        "next_month": "2026-06",
        "recommendation_section": (
            "다음 달 집중 메뉴로는 아메리카노와 제과/빵류를 추천합니다. "
            "최근 판매량, 분석월 판매 성장률, 날씨 적합도, 네이버 검색트렌드, "
            "공휴일·이벤트 적합도를 종합해 홍보 우선 메뉴를 도출합니다. "
            "특히 커피와 디저트 조합은 객단가를 높이는 세트 구성으로 활용하기 좋습니다."
        ),
        "action_section": (
            "금요일 점심 시간대와 주말 오후 피크타임에 인기 메뉴를 전면 배치하고, "
            "SNS에는 계절 메뉴와 세트 구성을 강조하는 홍보 문구를 활용하는 것이 좋습니다. "
            "공휴일이나 이벤트일에는 선물용 세트, 예약 안내, 한정 메뉴 메시지를 함께 제안합니다. "
            "저회전 메뉴는 재고 부담을 줄이기 위해 판매 지속 여부를 점검하거나 세트 구성으로 재배치하는 전략이 적합합니다."
        )
    },
    "poster": {
        "store_name": "카페 아들러",
        "analysis_month": "2026-05",
        "next_month": "2026-06",
        "poster": {
            "generated": True,
            "file_name": "demo_poster.png",
            "mime_type": "image/png",
            "file_size": "demo"
        },
        "email_subject": "카페 아들러 2026년 5월 매출 리포트"
    }
}


async def fetch_result(view: str) -> dict[str, Any]:
    fallback = DEMO_RESULTS.get(view, {})

    if not N8N_RESULT_URL:
        return fallback

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

        if data.get("success") and isinstance(data.get("result"), dict):
            return data.get("result", {})

        return fallback

    except Exception:
        return fallback


@mcp.tool(
    name="get_monthly_sales_summary",
    title="Monthly Sales Summary",
    description=(
        "소상공인을 위한 매출 분석 & 포스터 생성: "
        "Use this tool when the user asks for last month's sales report, monthly sales analysis, "
        "store performance, or sales summary. No input is required. "
        "It returns a demo monthly report based on a sample store. "
        "Explain that real users can upload their own sales Excel file to receive a store-specific report."
    ),
    annotations=ToolAnnotations(
        title="Monthly Sales Summary",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_monthly_sales_summary() -> dict[str, Any]:
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
    name="recommend_store_actions",
    title="Recommended Store Actions",
    description=(
        "소상공인을 위한 매출 분석 & 포스터 생성: "
        "Use this tool when the user asks for next month's recommended menu, promotion strategy, "
        "menu to focus on, or store actions. No input is required. "
        "It returns demo recommendations based on sales, day and time pattern, weather, holiday, "
        "and search trend analysis."
    ),
    annotations=ToolAnnotations(
        title="Recommended Store Actions",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def recommend_store_actions() -> dict[str, Any]:
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
    name="get_poster_assets",
    title="Poster Asset Metadata",
    description=(
        "소상공인을 위한 매출 분석 & 포스터 생성: "
        "Use this tool when the user asks for promotion poster results, poster generation, "
        "or whether a poster was created. No input is required. "
        "It returns demo poster metadata generated from the recommended menu score."
    ),
    annotations=ToolAnnotations(
        title="Poster Asset Metadata",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_poster_assets() -> dict[str, Any]:
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
        "소상공인을 위한 매출 분석 & 포스터 생성: "
        "Use this tool when the user asks how to analyze their own store data, "
        "how to upload a sales Excel file, or how the real service starts. "
        "No input is required. It explains the upload-based service flow."
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
        "service_summary": (
            "이 서비스는 실제로 사장님이 매출 엑셀 파일을 업로드하면 해당 매장 데이터를 분석하는 구조입니다. "
            "현재 PlayMCP 데모에서는 별도 파일 업로드 없이 샘플 매장 데이터로 기능을 체험할 수 있습니다."
        ),
        "real_service_flow": [
            "사장님이 월간 매출 엑셀 파일을 업로드합니다.",
            "업로드된 매출 데이터가 PostgreSQL에 저장됩니다.",
            "월간 매출, 카테고리별 매출, 인기 메뉴와 저회전 메뉴를 분석합니다.",
            "요일·시간대별 판매 패턴을 분석해 피크 타임과 주요 판매 메뉴를 도출합니다.",
            "날씨, 공휴일, 검색트렌드 데이터를 함께 반영합니다.",
            "추천 메뉴를 점수화하고 월간 리포트, 홍보 액션, 포스터 결과를 생성합니다."
        ],
        "demo_note": (
            "지금은 심사자가 바로 기능을 확인할 수 있도록 샘플 매장 분석 결과를 기본으로 제공합니다."
        ),
        "upload_guide": UPLOAD_GUIDE_URL,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
