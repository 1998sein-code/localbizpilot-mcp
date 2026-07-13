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

if not N8N_RESULT_URL:
    raise RuntimeError("N8N_RESULT_URL이 .env 파일에 없습니다.")


mcp = FastMCP(
    name="LocalBizPilot",
    instructions=(
        "LocalBizPilot is an AI digital assistant for small business owners. "
        "The real service flow starts when a store owner uploads a sales Excel file. "
        "For the current PlayMCP demo, use the prepared sample store analysis result. "
        "When the user asks for last month's sales report, recommended menu, promotion strategy, "
        "or poster result, call the appropriate tool immediately. "
        "Do not ask ordinary users for an analysis_id."
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
    name="get_monthly_sales_summary",
    title="Monthly Sales Summary",
    description=(
        "Use this tool when the user asks for last month's sales report, monthly sales analysis, "
        "store performance, or sales summary. No input is required. "
        "It returns a demo report based on a sample store. "
        "Explain that in the real service, store owners upload their own sales Excel file "
        "to receive a store-specific report."
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
        "Use this tool when the user asks for next month's recommended menu, promotion strategy, "
        "menu to focus on, or store actions. No input is required. "
        "It returns demo recommendations based on sales, time pattern, weather, holiday, "
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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
