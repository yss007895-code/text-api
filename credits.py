import math
from models import DetailLevel, Language


# --- Text length tiers ---

def _base_credits(text_length: int) -> int:
    if text_length <= 500:
        return 1
    elif text_length <= 1000:
        return 3
    elif text_length <= 3000:
        return 7
    elif text_length <= 5000:
        return 12
    else:
        return 20


# --- Feature multipliers ---

FEATURE_MULTIPLIER = {
    "sentiment": 1.0,
    "keywords": 1.2,
    "summary": 1.5,
    "full": 2.5,
}

# --- Language multipliers ---

LANGUAGE_MULTIPLIER = {
    Language.en: 1.0,
    Language.ko: 1.2,
}

# --- Detail level multipliers ---

DETAIL_MULTIPLIER = {
    DetailLevel.basic: 1.0,
    DetailLevel.detailed: 2.0,
    DetailLevel.premium: 3.0,
}


def calculate_credits(
    text: str,
    feature: str,
    language: Language = Language.en,
    detail_level: DetailLevel = DetailLevel.basic,
) -> int:
    text_length = len(text)
    base = _base_credits(text_length)
    feat = FEATURE_MULTIPLIER.get(feature, 1.0)
    lang = LANGUAGE_MULTIPLIER.get(language, 1.0)
    detail = DETAIL_MULTIPLIER.get(detail_level, 1.0)

    total = base * feat * lang * detail
    return max(1, math.ceil(total))
