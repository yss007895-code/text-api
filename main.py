from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse

from database import init_db, get_db
from auth import create_user, verify_api_key, deduct_credits, log_usage
from credits import calculate_credits
from analyzer import analyze_sentiment, analyze_summary, analyze_keywords, analyze_full
from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    CreditBalanceResponse,
    UsageResponse,
    UsageLog,
    ApiKeyResponse,
    ErrorResponse,
)
from webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Text Analysis AI API",
    description="AI-powered text analysis API with credit-based billing. "
    "Supports sentiment analysis, summarization, and keyword extraction.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)


# --- API Key Registration ---


@app.post("/register", response_model=ApiKeyResponse)
async def register():
    """Register a new API key with 10 free credits."""
    user = await create_user(initial_credits=10)
    return ApiKeyResponse(
        api_key=user["api_key"],
        credits=user["credits"],
        message="API key created. You have 10 free credits to start.",
    )


# --- Credit Balance ---


@app.get("/credits", response_model=CreditBalanceResponse)
async def get_credits(user: dict = Depends(verify_api_key)):
    return CreditBalanceResponse(api_key=user["api_key"], credits=user["credits"])


# --- Usage History ---


@app.get("/usage", response_model=UsageResponse)
async def get_usage(limit: int = 50, user: dict = Depends(verify_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT endpoint, credits_used, text_length, timestamp
               FROM usage_logs WHERE user_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (user["id"], limit),
        )
        rows = await cursor.fetchall()
        total_cursor = await db.execute(
            "SELECT COALESCE(SUM(credits_used), 0) as total FROM usage_logs WHERE user_id = ?",
            (user["id"],),
        )
        total_row = await total_cursor.fetchone()

        logs = [
            UsageLog(
                endpoint=row["endpoint"],
                credits_used=row["credits_used"],
                text_length=row["text_length"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
        return UsageResponse(total_used=total_row["total"], logs=logs)
    finally:
        await db.close()


# --- Credit Cost Preview ---


@app.post("/preview-cost")
async def preview_cost(request: AnalyzeRequest, feature: str = "sentiment"):
    """Preview how many credits an analysis would cost without running it."""
    cost = calculate_credits(request.text, feature, request.language, request.detail_level)
    return {
        "feature": feature,
        "text_length": len(request.text),
        "language": request.language,
        "detail_level": request.detail_level,
        "estimated_credits": cost,
    }


# --- Analysis Endpoints ---


async def _run_analysis(user: dict, request: AnalyzeRequest, feature: str, analyzer_fn):
    cost = calculate_credits(request.text, feature, request.language, request.detail_level)

    remaining = await deduct_credits(user["api_key"], cost)

    try:
        result = await analyzer_fn(request.text, request.language, request.detail_level)
    except Exception as e:
        # Refund on AI failure
        from auth import add_credits
        await add_credits(user["api_key"], cost)
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error=f"AI analysis failed: {str(e)}", credits_remaining=remaining + cost
            ).model_dump(),
        )

    await log_usage(
        user_id=user["id"],
        endpoint=f"/analyze/{feature}",
        credits_used=cost,
        text_length=len(request.text),
        detail_level=request.detail_level.value,
        language=request.language.value,
    )

    return AnalyzeResponse(
        credits_used=cost,
        credits_remaining=remaining,
        data=result,
    )


@app.post("/analyze/sentiment", response_model=AnalyzeResponse)
async def sentiment(request: AnalyzeRequest, user: dict = Depends(verify_api_key)):
    """Analyze text sentiment (positive/negative/neutral with confidence score)."""
    return await _run_analysis(user, request, "sentiment", analyze_sentiment)


@app.post("/analyze/summary", response_model=AnalyzeResponse)
async def summary(request: AnalyzeRequest, user: dict = Depends(verify_api_key)):
    """Generate a concise summary of the text."""
    return await _run_analysis(user, request, "summary", analyze_summary)


@app.post("/analyze/keywords", response_model=AnalyzeResponse)
async def keywords(request: AnalyzeRequest, user: dict = Depends(verify_api_key)):
    """Extract keywords and topics from the text."""
    return await _run_analysis(user, request, "keywords", analyze_keywords)


@app.post("/analyze/full", response_model=AnalyzeResponse)
async def full_analysis(request: AnalyzeRequest, user: dict = Depends(verify_api_key)):
    """Full analysis: sentiment + summary + keywords (bundled discount)."""
    return await _run_analysis(user, request, "full", analyze_full)
