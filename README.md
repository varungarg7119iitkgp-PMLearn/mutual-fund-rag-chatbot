# Mutual Fund RAG Chatbot — WealthAI

A production-grade, Retrieval-Augmented Generation chatbot for 20 curated mutual funds across Equity, Debt, Hybrid, and Commodities categories. Built with a FastAPI backend (Gemini LLM) and a Next.js frontend, deployed on Railway and Vercel.

**Live**: [Frontend (Vercel)](https://mutual-fund-rag-chatbot-psi.vercel.app)

---

## Architecture & Phases

The project follows a strict phase-wise development approach. Full details are in [`Architecture.md`](Architecture.md) and product requirements in [`Requirements.md`](Requirements.md).

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Foundations & Configuration | Complete |
| 1 | Data Ingestion & Scraping (20 funds) | Complete |
| 2 | Data Cleaning, Normalization & RAG Chunks | Complete |
| 3 | LLM Integration & RAG Orchestration (Gemini) | Complete |
| 4 | Guardrails & Policy Enforcement | Complete |
| 5 | Frontend UI (Desktop + Mobile Responsive) | Complete |
| 6 | Deployment (Railway + Vercel) | Complete |
| 7 | Scheduling, Refresh & Automation | Planned |
| 8 | Observability, Analytics & Iteration | Planned |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| LLM | Google Gemini (`gemini-3-flash-preview`) via `google-genai` SDK |
| Retrieval | Local TF-IDF index over Phase 2 RAG chunks (`numpy`) |
| Scraping | Playwright (headless Chromium) |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide React |
| Backend Hosting | Railway (Nixpacks) |
| Frontend Hosting | Vercel |
| Repository | GitHub (private, auto-deploy on push to `master`) |

---

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m playwright install

# Create .env from the example and add your Gemini API key
cp .env.example .env

uvicorn app.main:app --reload
```

The backend runs on `http://127.0.0.1:8000`. Key endpoints:

- `GET /health` — health check
- `POST /chat` — RAG-powered Q&A (accepts `{ "question": "...", "fund_hint": "..." }`)
- `GET /chat/debug/retrieval` — inspect retrieved chunks without calling Gemini

### Frontend

```bash
cd frontend
npm install

# Create .env.local pointing to the backend
echo "NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000" > .env.local

npm run dev
```

Open `http://localhost:3000` to use the WealthAI UI.

---

## Deployment

### Backend — Railway

- Configured via [`railway.toml`](railway.toml) at repo root.
- Nixpacks detects Python from the root `requirements.txt` (delegates to `backend/requirements.txt`).
- Start command: `cd backend && python start.py` (reads `PORT` from environment).
- Environment variables set in Railway dashboard: `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `GEMINI_EMBEDDING_MODEL`, `CORS_ORIGINS`.

### Frontend — Vercel

- Root directory set to `frontend/` in Vercel project settings.
- Auto-detected as Next.js; runs `npm run build` automatically.
- Environment variable: `NEXT_PUBLIC_BACKEND_URL` pointing to the Railway backend URL.

Both platforms auto-deploy on every push to `master`.

---

## Key Features

- **Facts-only RAG responses** — grounded exclusively in scraped fund data with mandatory citations and timestamps.
- **Guardrails** — advice-seeking, PII, speculative, and out-of-scope queries are refused before reaching the LLM.
- **Desktop UI** — dark "Bloomberg-style" three-column layout: sidebar, chat panel, Market Pulse card, marquee ticker.
- **Mobile-responsive UI** — sliding drawers for sidebar/market pulse, mobile header, condensed ticker, full-width chat, vertically stacked suggestion chips.
- **20 curated funds** across Equity, Debt, Hybrid, and Commodities categories.

---

## Project Structure

```
├── Architecture.md          # Phase-wise architecture document
├── Requirements.md          # Master product requirements
├── railway.toml             # Railway deployment config
├── requirements.txt         # Root deps (delegates to backend)
├── runtime.txt              # Python version for Railway
├── config/
│   ├── fund_universe.csv    # 20 curated funds
│   └── scraping_reference_guide.md
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── core/config.py   # Settings
│   │   └── rag/
│   │       ├── router.py    # /chat endpoint
│   │       ├── gemini_client.py
│   │       └── indexer.py   # TF-IDF retrieval
│   ├── rag_index/           # Pre-built index files
│   ├── start.py             # Uvicorn launcher for Railway
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # AppShell, ChatPanel, HeaderBar, etc.
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env.example
├── phase1_ingestion/        # Scraping pipeline & raw output
├── phase2_processing/       # Cleaning, normalization & chunks
├── phase4/                  # Guardrails & behavior specs
└── ui-references/           # Visual references & UI/UX specs
```

---

## Guardrails & Safety

Detailed specifications in [`phase4/Guardrails.md`](phase4/Guardrails.md) and [`phase4/Behavior_Specs.md`](phase4/Behavior_Specs.md).

- **No investment advice** — buy/sell/hold/allocate queries are refused at the backend before reaching Gemini.
- **No PII** — phone numbers, emails, PAN/Aadhaar patterns are detected and the user is warned.
- **No projections** — future value calculations and SIP simulators are declined.
- **Source integrity** — only Groww, AMC factsheets, and SEBI pages are cited.
- **Mandatory citations & timestamps** — every response includes at least one source URL and a "Last updated from sources" footer.
