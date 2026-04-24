# Receipt Reconciliation Agent

AI-assisted receipt reconciliation system for small businesses.  
Upload receipts and bank transactions, run deterministic matching, and review uncertain items in a clean dashboard workflow.

## What I Built
- A FastAPI + SQLAlchemy backend for receipt ingestion, bank CSV ingestion, reconciliation, and dashboard/report APIs.
- An AI-assisted parsing layer powered by OpenAI GPT-5 for unstructured receipt extraction.
- A deterministic reconciliation engine (custom scoring code) with explainable outputs:
  - `matched`
  - `flagged` (human review)
  - `unmatched`
- Dashboard-friendly responses with score breakdowns, reason labels, and confidence buckets.

## AI vs Deterministic Logic

### Where GPT-5 is used
- Parsing raw receipt files (PDF/image) into strict structured fields.
- Generating natural-language explanations for uncertain matches.

### Where AI is NOT used
- Matching decisions.
- Reconciliation scoring.
- Thresholding and final status classification.

All final matching decisions are deterministic custom code.

## Reconciliation Scoring Algorithm

Each receipt is scored against candidate bank transactions:

| Dimension | Weight | Behavior |
|---|---:|---|
| Amount | 50 | Exact/near amount match gets highest weight |
| Date | 30 | Same day highest; 1-2 day delay partially scored |
| Vendor fuzzy match | 20 | RapidFuzz similarity of normalized vendor text |

Status thresholds:
- Score `>= 65` -> `MATCHED`
- Score `45-64` -> `FLAGGED` (needs human review)
- Score `< 45` -> `UNMATCHED`

Confidence labels:
- `HIGH`: score `>= 80`
- `MEDIUM`: score `65-79`
- `LOW`: score `45-64`

For flagged items, top 3 candidate matches are returned for reviewer context.

## Hallucination Prevention
- Strict JSON extraction prompt with fixed schema:
  - `vendor`, `amount`, `date`, `category`, `confidence`, `notes`
- Safe/fallback JSON parsing when model output contains wrappers or extra text.
- Confidence labels retained in parsed output.
- Human review required for uncertain (`FLAGGED`) matches.
- Deterministic matching engine is the source of truth for outcomes.

## API Highlights
- `POST /receipts/upload`
- `POST /transactions/upload`
- `POST /reconcile`
- `GET /dashboard`
- `GET /report`

`/reconcile` returns:
- `summary`
- `matched`
- `flagged`
- `unmatched_receipts`
- `unmatched_transactions`

`/dashboard` returns:
- totals (receipts, transactions, matched, flagged, unmatched)
- total spend
- spend by category
- recent receipts and transactions

## Setup

### Backend
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY in .env
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Optional frontend env:
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

## Demo Flow
1. Upload receipt files (`/receipts/upload`).
2. Upload bank CSV (`/transactions/upload`).
3. Run reconciliation (`/reconcile`).
4. Review flagged matches and confirm/reject.
5. View high-level metrics from `/dashboard` and spend summary from `/report`.
