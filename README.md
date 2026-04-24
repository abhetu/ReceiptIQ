# Receipt Reconciliation Agent

AI-powered tool that matches receipts to bank transactions for small businesses.
Upload your receipts (PDF/images) + bank CSV → get a reconciled expense report.

## Architecture

```
Frontend (React + Tailwind)
    ↓ REST API
Backend (Python FastAPI)
    ├── Receipt Parser → Claude API (vision/text extraction)
    ├── CSV Parser → Pandas (pure logic)
    ├── Reconciliation Engine → Custom fuzzy matching algorithm (YOUR CODE)
    ├── AI Explainer → Claude API (explains flagged matches)
    └── Report Generator → SQLAlchemy aggregations
Database (SQLite dev / PostgreSQL prod)
```

### Where AI is used (and why only there)
- **Receipt parsing**: Extracting structured data from unstructured images/PDFs requires language understanding
- **Match explanations**: Generating human-readable explanations for uncertain matches
- **Everything else is deterministic code** — reconciliation algorithm, CSV parsing, report generation

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## How It Works

### Reconciliation Algorithm
The core matching logic (see `services/reconciliation.py`) scores each receipt-transaction pair on 3 dimensions:

| Dimension | Weight | Logic |
|-----------|--------|-------|
| Amount | 50 pts | Exact match ±2% tolerance |
| Date | 30 pts | Same day (30), ±1 day (21), ±2 days (10) |
| Vendor | 20 pts | Fuzzy string similarity via RapidFuzz |

- Score ≥ 65: Confirmed match
- Score 45-64: Flagged for human review
- Score < 45: No match

### Hallucination Prevention
- Claude is given strict output format (JSON only)
- Amount validation: if extracted amount deviates >90% from matched transaction, flagged
- Confidence scoring: Claude reports its own confidence; LOW confidence items get human review
- Fallback: if JSON parse fails, receipt is marked LOW confidence, not silently discarded

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python FastAPI (async)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **File parsing**: PyMuPDF + Pillow + Pandas
- **Fuzzy matching**: RapidFuzz

## Deploy
```bash
# Backend on Railway
railway login
railway init
railway up

# Frontend on Vercel
vercel --prod
```
