from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.sentiment import analyze_sentiment, stock_sentiment_analysis, sentiment_demo

router = APIRouter()


class SentimentBatchRequest(BaseModel):
    texts: list[str]
    labels: list[str] | None = None
    weights: list[float] | None = None


class StockSentimentRequest(BaseModel):
    symbol: str
    news_texts: list[str]
    social_texts: list[str] | None = None


@router.post("/analyze")
async def analyze_endpoint(req: SentimentBatchRequest):
    """Analyze sentiment for a batch of texts."""
    return analyze_sentiment(req.texts, req.labels, req.weights)


@router.post("/stock")
async def stock_sentiment_endpoint(req: StockSentimentRequest):
    """Analyze sentiment for a specific stock."""
    return stock_sentiment_analysis(req.symbol, req.news_texts, req.social_texts)


@router.get("/demo")
async def demo_endpoint():
    """Get demo sentiment analysis with sample TSE news."""
    return sentiment_demo()
