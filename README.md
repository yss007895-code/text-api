# Text Analysis AI API

AI-powered text analysis API with credit-based billing.
Claude API를 활용한 텍스트 분석 API — 크레딧 기반 과금 시스템.

## Features

| Endpoint | Description | Multiplier |
|----------|-------------|------------|
| `POST /analyze/sentiment` | Sentiment analysis (positive/negative/neutral + score) | 1x |
| `POST /analyze/keywords` | Keyword & topic extraction | 1.2x |
| `POST /analyze/summary` | Text summarization | 1.5x |
| `POST /analyze/full` | All three combined (bundle) | 2.5x |

## Credit System

### Text Length Tiers

| Characters | Base Credits |
|-----------|-------------|
| 1–500 | 1 |
| 501–1,000 | 3 |
| 1,001–3,000 | 7 |
| 3,001–5,000 | 12 |
| 5,001+ | 20 |

### Multipliers

- **Language**: English 1x / Korean 1.2x
- **Detail Level**: basic 1x / detailed 2x / premium 3x
- **Formula**: `base × feature × language × detail`

### Credit Packages

| Package | Price | Per Credit |
|---------|-------|-----------|
| 100 credits | $5 | $0.05 |
| 500 credits | $20 | $0.04 |
| 2,000 credits | $60 | $0.03 |
| 10,000 credits | $200 | $0.02 |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yss007895-code/text-api.git
cd text-api

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY

# 4. Run server
uvicorn main:app --reload

# 5. Open docs
# http://127.0.0.1:8000/docs
```

## API Usage

### 1. Register (get API key)

```bash
curl -X POST http://127.0.0.1:8000/register
```

```json
{
  "api_key": "ta_abc123...",
  "credits": 10,
  "message": "API key created. You have 10 free credits to start."
}
```

### 2. Analyze Text

```bash
curl -X POST http://127.0.0.1:8000/analyze/sentiment \
  -H "x-api-key: ta_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I love this product!",
    "language": "en",
    "detail_level": "basic"
  }'
```

```json
{
  "success": true,
  "credits_used": 1,
  "credits_remaining": 9,
  "data": {
    "label": "positive",
    "score": 0.95,
    "explanation": "The text expresses strong positive sentiment."
  }
}
```

### 3. Check Balance

```bash
curl http://127.0.0.1:8000/credits -H "x-api-key: ta_abc123..."
```

### 4. Preview Cost

```bash
curl -X POST http://127.0.0.1:8000/preview-cost?feature=summary \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here...", "language": "ko", "detail_level": "detailed"}'
```

## Tech Stack

- **API**: FastAPI (Python)
- **AI**: Claude API (Anthropic)
- **DB**: SQLite (async)
- **Payments**: Lemonsqueezy (webhook)

## Project Structure

```
text-api/
├── main.py           # FastAPI app & routes
├── auth.py           # API key auth & credit management
├── credits.py        # Credit calculation logic
├── analyzer.py       # Claude API integration
├── database.py       # SQLite setup & models
├── webhook.py        # Lemonsqueezy payment webhook
├── models.py         # Pydantic request/response models
├── requirements.txt  # Dependencies
└── .env.example      # Environment variables template
```

## License

MIT
