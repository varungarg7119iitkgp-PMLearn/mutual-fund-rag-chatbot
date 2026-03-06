# Mutual Fund Chatbot Project

Backend: Python (FastAPI) with Playwright-based scraping and Gemini-powered RAG.  
Frontend: Next.js (TypeScript + Tailwind) implementing the WealthAI UI.

## Backend quickstart

```bash
cd backend
pip install -r requirements.txt
# Install Playwright browsers once:
python -m playwright install

uvicorn app.main:app --reload
```

Once the backend skeleton is running, we will:

- Implement Playwright scrapers for the target mutual fund sites.
- Add data structuring + chunking for RAG.
- Integrate Gemini for answer generation with guard rails.
- Expose chat and admin endpoints for the frontend UI.

## Frontend (Phase 5) quickstart

The frontend lives under `frontend/` and uses Next.js (App Router) with Tailwind CSS.

```bash
cd frontend
npm install

# Ensure the backend is running locally on http://127.0.0.1:8000
# or set NEXT_PUBLIC_BACKEND_URL in a .env.local file.

npm run dev
```

Then open `http://localhost:3000` in your browser to explore the WealthAI UI:

- Left sidebar: categories & popular queries.
- Top header: marquee-style ticker strip and search bar.
- Center: chat panel with Welcome state, conversation timeline, typing indicator, and disclaimer.
- Right: Market Pulse panel (initially using mock trending data, wired later to backend analytics).

### Phase 3 — RAG + Gemini backend

- Phase 1 raw snapshots live under `phase1_ingestion/output/raw/`.
- Phase 2 cleaned snapshots and RAG chunks live under:
  - `phase2_processing/output/clean/`
  - `phase2_processing/output/chunks/`
- Phase 3 adds:
  - A small RAG index in `backend/rag_index/` built from Phase 2 chunks using Gemini embeddings.
  - A Gemini client wrapper (`app/rag/gemini_client.py`) for embeddings and answer generation.
  - An offline index builder (`app/rag/indexer.py`) to embed all chunks and save them locally.
  - A chat API endpoint (`POST /chat`) wired via `app/rag/router.py`.

To build the index (after Phase 2 is complete and `.env` is configured with your Gemini keys), run an ad‑hoc script or Python shell that calls:

```python
from app.rag.indexer import build_index
build_index()
```

Then start the backend as usual and send chat requests to `POST /chat`.

