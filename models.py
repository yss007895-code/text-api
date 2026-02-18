from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


# --- Enums ---

class DetailLevel(str, Enum):
    basic = "basic"
    detailed = "detailed"
    premium = "premium"


class Language(str, Enum):
    en = "en"
    ko = "ko"


# --- Request Models ---

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    language: Language = Language.en
    detail_level: DetailLevel = DetailLevel.basic


# --- Response Models ---

class SentimentResult(BaseModel):
    label: str  # positive / negative / neutral
    score: float  # 0.0 ~ 1.0
    explanation: str


class SummaryResult(BaseModel):
    summary: str
    original_length: int
    summary_length: int


class KeywordsResult(BaseModel):
    keywords: list[str]
    topics: list[str]


class FullAnalysisResult(BaseModel):
    sentiment: SentimentResult
    summary: SummaryResult
    keywords: KeywordsResult


class AnalyzeResponse(BaseModel):
    success: bool = True
    credits_used: int
    credits_remaining: int
    data: SentimentResult | SummaryResult | KeywordsResult | FullAnalysisResult


class CreditBalanceResponse(BaseModel):
    api_key: str
    credits: int


class UsageLog(BaseModel):
    endpoint: str
    credits_used: int
    text_length: int
    timestamp: str


class UsageResponse(BaseModel):
    total_used: int
    logs: list[UsageLog]


class ApiKeyResponse(BaseModel):
    api_key: str
    credits: int
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    credits_remaining: Optional[int] = None
