import os
import json
from anthropic import AsyncAnthropic
from models import (
    DetailLevel,
    Language,
    SentimentResult,
    SummaryResult,
    KeywordsResult,
    FullAnalysisResult,
)

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-20250514"


def _detail_instruction(detail_level: DetailLevel) -> str:
    if detail_level == DetailLevel.basic:
        return "Provide a brief, concise analysis."
    elif detail_level == DetailLevel.detailed:
        return "Provide a detailed analysis with reasoning."
    else:
        return "Provide an in-depth premium analysis with examples and nuanced reasoning."


def _lang_instruction(language: Language) -> str:
    if language == Language.ko:
        return "Respond in Korean (한국어로 응답하세요)."
    return "Respond in English."


async def analyze_sentiment(
    text: str,
    language: Language = Language.en,
    detail_level: DetailLevel = DetailLevel.basic,
) -> SentimentResult:
    prompt = f"""{_lang_instruction(language)}
{_detail_instruction(detail_level)}

Analyze the sentiment of the following text. Return ONLY valid JSON with these fields:
- "label": one of "positive", "negative", or "neutral"
- "score": a float between 0.0 and 1.0 indicating confidence
- "explanation": a brief explanation of the sentiment

Text:
\"\"\"
{text}
\"\"\"

Return ONLY the JSON object, no markdown or extra text."""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(message.content[0].text)
    return SentimentResult(**data)


async def analyze_summary(
    text: str,
    language: Language = Language.en,
    detail_level: DetailLevel = DetailLevel.basic,
) -> SummaryResult:
    prompt = f"""{_lang_instruction(language)}
{_detail_instruction(detail_level)}

Summarize the following text concisely. Return ONLY valid JSON with these fields:
- "summary": the summarized text

Text:
\"\"\"
{text}
\"\"\"

Return ONLY the JSON object, no markdown or extra text."""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(message.content[0].text)
    return SummaryResult(
        summary=data["summary"],
        original_length=len(text),
        summary_length=len(data["summary"]),
    )


async def analyze_keywords(
    text: str,
    language: Language = Language.en,
    detail_level: DetailLevel = DetailLevel.basic,
) -> KeywordsResult:
    prompt = f"""{_lang_instruction(language)}
{_detail_instruction(detail_level)}

Extract keywords and topics from the following text. Return ONLY valid JSON with these fields:
- "keywords": a list of important keywords (5-15 items)
- "topics": a list of main topics/themes (2-5 items)

Text:
\"\"\"
{text}
\"\"\"

Return ONLY the JSON object, no markdown or extra text."""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(message.content[0].text)
    return KeywordsResult(**data)


async def analyze_full(
    text: str,
    language: Language = Language.en,
    detail_level: DetailLevel = DetailLevel.basic,
) -> FullAnalysisResult:
    prompt = f"""{_lang_instruction(language)}
{_detail_instruction(detail_level)}

Perform a full analysis of the following text. Return ONLY valid JSON with these fields:
- "sentiment": {{"label": "positive"|"negative"|"neutral", "score": 0.0-1.0, "explanation": "..."}}
- "summary": {{"summary": "..."}}
- "keywords": {{"keywords": ["..."], "topics": ["..."]}}

Text:
\"\"\"
{text}
\"\"\"

Return ONLY the JSON object, no markdown or extra text."""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(message.content[0].text)

    sentiment = SentimentResult(**data["sentiment"])
    summary = SummaryResult(
        summary=data["summary"]["summary"],
        original_length=len(text),
        summary_length=len(data["summary"]["summary"]),
    )
    keywords = KeywordsResult(**data["keywords"])

    return FullAnalysisResult(
        sentiment=sentiment, summary=summary, keywords=keywords
    )
