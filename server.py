import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


load_dotenv()

N8N_RESULT_URL = os.getenv("N8N_RESULT_URL", "").strip()

if not N8N_RESULT_URL:
    raise RuntimeError("N8N_RESULT_URL이 .env 파일에 없습니다.")


mcp = FastMCP(
    name="LocalBizPilot",
    instructions=(
        "LocalBizPilot(로컬비즈파일럿) helps small cafe owners review "
        "monthly sales analysis results, recommended store actions, and "
        "poster asset metadata using a previously generated analysis_id."
    ),
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


async def fetch_result(analysis_id: str, view: str) -> dict[str, Any]:
    if not analysis_id or not analysis_id.strip():
        raise ValueError("analysis_id is required.")

    payload = {
        "analysis_id": analysis_id.strip(),
        "view": view,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(N8N_RESULT_URL, json=payload)
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
        "Gets a compact monthly sales summary from LocalBizPilot(로컬비즈파일럿) "
        "using a previously generated analysis_id. Returns store name, "
        "analysis month, next month, a short report preview, email metadata, "
        "and poster availability."
    ),
    annotations=ToolAnnotations(
        title="Monthly Sales Summary",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_monthly_sales_summary(analysis_id: str) -> dict[str, Any]:
    result = await fetch_result(analysis_id, "summary")

    return {
        "analysis_id": result.get("analysis_id"),
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
        "Gets recommended menu and promotion actions from LocalBizPilot(로컬비즈파일럿) "
        "using a previously generated analysis_id. Returns compact recommendation "
        "and action sections for the next month."
    ),
    annotations=ToolAnnotations(
        title="Recommended Store Actions",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def recommend_store_actions(analysis_id: str) -> dict[str, Any]:
    result = await fetch_result(analysis_id, "actions")

    return {
        "analysis_id": result.get("analysis_id"),
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
        "Gets poster asset metadata from LocalBizPilot(로컬비즈파일럿) "
        "using a previously generated analysis_id. Returns whether a poster "
        "was generated and basic file metadata."
    ),
    annotations=ToolAnnotations(
        title="Poster Asset Metadata",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)
async def get_poster_assets(analysis_id: str) -> dict[str, Any]:
    result = await fetch_result(analysis_id, "poster")

    return {
        "analysis_id": result.get("analysis_id"),
        "store_name": result.get("store_name"),
        "analysis_month": result.get("analysis_month"),
        "next_month": result.get("next_month"),
        "poster": result.get("poster"),
        "email_subject": result.get("email_subject"),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
