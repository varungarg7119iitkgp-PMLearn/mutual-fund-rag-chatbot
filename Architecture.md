## Mutual Fund RAG Chatbot — Phase-wise Architecture

### 1. Document Purpose

This document describes the **phase-wise architecture** for the Mutual Fund RAG Chatbot. It translates the product requirements in `Requirements.md`, the visual design in `ui-references/UI_UX_Specs.md`, and the data guides in `config/` into a clear implementation roadmap.

- It does **not** define low-level implementation details or deployment configuration.
- Each phase is **reviewable and testable in isolation** before moving to the next.
- All phases must remain consistent with `Requirements.md`, which is the **master source of truth**.

---

### 2. High-Level System Overview

At maturity, the system will consist of the following logical components:

- **Fund Configuration Layer**
  - Configuration for the curated fund universe (`config/fund_universe.csv`).
  - Scraping and data-field requirements (`config/scraping_reference_guide.md`).

- **Data Ingestion & Scraping Layer**
  - Scrapers that read `fund_universe.csv` and extract required fields from Groww/AMC/SEBI pages.
  - Structured outputs representing each fund (conceptually as nested objects/JSON).

- **Data Processing & RAG Preparation Layer**
  - Cleaning, validation, normalization, and enrichment of scraped data.
  - Generation of RAG-ready chunks (text + metadata) from structured objects.
  - Storage in a persistent database and vector index.

- **LLM & RAG Orchestration Layer**
  - Retrieval logic that selects relevant chunks for a given query.
  - Prompt construction and interaction with the LLM (Gemini).
  - Application of formatting rules (citations, timestamps, concise answers).

- **Guardrail & Policy Layer**
  - Enforcement of "facts-only, no advice" rules.
  - Filtering for PII and out-of-scope content.
  - Response-shaping policies for refusals and safe alternatives.

- **Application Backend Layer**
  - API endpoints for chat, fund metadata, news, trending analytics, and health checks.
  - Internal endpoints for re-scraping and diagnostics.
  - Lives under `backend/` (current FastAPI skeleton).

- **Frontend / UI Layer**
  - Web client implementing the WealthAI UI (`ui-references/UI_UX_Specs.md`).
  - Chat interface, ticker, Market Pulse panel, fund quick-view cards, and onboarding.

- **Deployment & Operations Layer**
  - Backend deployed on **Railway** (Python/Nixpacks, auto-deploy on push to `master`).
  - Frontend deployed on **Vercel** (Next.js, auto-deploy on push to `master`).
  - Scheduled scraping and re-indexing (Phase 7).
  - Logging, analytics, and monitoring (Phase 8).

The following sections decompose this into **phases** that will be executed and reviewed sequentially.

---

### 3. Phase 0 — Foundations & Configuration (Completed Conceptually)

**Objective**: Establish a shared configuration and requirements foundation before any significant coding.

- **Key Artifacts**:
  - `Requirements.md` — master product requirements, including:
    - Fund universe definition.
    - Data requirements and guardrails.
    - High-level UI/UX expectations and references.
  - `config/fund_universe.csv` — authoritative list of the 20 funds, their categories, Groww URLs, and query keywords.
  - `config/scraping_reference_guide.md` — canonical field list and conceptual structured representation for scraping.
  - `ui-references/` — visual and interaction references, plus `UI_UX_Specs.md` for WealthAI UI.
  - `backend/` skeleton — minimal app entry point and dependency manifest.

- **Success Criteria**:
  - All future phases can reference these files without ambiguity.
  - Any changes to scope (funds, fields, UI patterns) are first reflected in these documents.

---

### 4. Phase 1 — Initial Data Ingestion & Scraping for 20 Funds

**Objective**: For each fund in `config/fund_universe.csv`, reliably scrape and persist the fields defined in `config/scraping_reference_guide.md`, producing comprehensive structured data and initial chunks.

#### 4.1 Scope

- Read the curated list of 20 funds from `config/fund_universe.csv`.
- For each fund:
  - Visit the configured Groww (and/or AMC/SEBI) URL.
  - Extract all fields listed in the scraping guide:
    - Identity, Performance, Risk, Portfolio, Operations, People, Market Intelligence/News.
  - Handle "In the News / Updates" with **headline, date, publisher, summary snippet, URL**.
- Output per-fund data in a **nested, self-contained structure** (conceptually aligned with the JSON example in `scraping_reference_guide.md`).

#### 4.2 Data Flow (Conceptual)

1. **Configuration Load**:
   - Ingestion process reads `config/fund_universe.csv` and validates that 20 entries exist and map cleanly to categories.
2. **Scrape & Extract**:
   - Scraper functions iterate over each fund row.
   - For each configured URL, DOM selectors or structured parsing extract the required fields, guided by `scraping_reference_guide.md`.
3. **Structured Representation**:
   - Raw scraped values are assembled into a normalized in-memory object for that fund:
     - Identity, metrics, risk, portfolio, operations, people, news_context, last_scraped_at.
4. **Persistence (Raw Layer)**:
   - Structured objects are written to a raw data store or snapshot (e.g., JSON files or database tables).

#### 4.3 Outputs & Deliverables

- A **repeatable ingestion pipeline** that, when run, produces:
  - One structured data object per fund, covering all required fields where available.
  - Clear logging for any missing fields or parsing issues.
- A documented mapping between:
  - Fields in `scraping_reference_guide.md` and their locations on the Groww/AMC pages.
- No LLM or RAG functionality yet; focus is on **data completeness and correctness**.

#### 4.4 Review & Sign-off Criteria

- For a sample of funds in each category, scraped fields are manually compared to the live web pages and match exactly (within reasonable tolerances for frequently changing values like NAV).
- Any fields that are consistently unavailable are documented (with rationale) and reflected back into `scraping_reference_guide.md` / `Requirements.md` if needed.

---

### 5. Phase 2 — Data Cleaning, Normalization & Chunk Preparation

**Objective**: Transform raw scraped data into a clean, consistent, and RAG-ready dataset with well-defined chunks and metadata.

#### 5.1 Scope

- Define and implement:
  - **Validation rules** (e.g., numeric ranges, required fields, date formats).
  - **Normalization rules** (e.g., standard currency representation, consistent risk labels).
  - **Derived fields** where appropriate (e.g., normalized category labels, computed deltas vs category average -- still factual).
- Convert each structured fund object into:
  - A set of **RAG chunks** (text + metadata) aligned with `Requirements.md` (e.g., overview, performance, risk, fees, news).
  - A compact, queryable structured representation suitable for the backend API.

#### 5.2 Data Flow (Conceptual)

1. **Load Raw Objects**:
   - Read structured outputs from Phase 1.
2. **Validation & Cleaning**:
   - Check required fields and types.
   - Standardize units, labels, and date formats.
   - Log and mark incomplete entries for review.
3. **Normalization & Enrichment**:
   - Normalize category names, riskometer levels, and plan types.
   - Attach configuration metadata (fund keywords/aliases from `fund_universe.csv`).
4. **Chunk Generation**:
   - For each fund, generate semantically coherent text chunks:
     - Overview.
     - Performance (with benchmark and category context).
     - Risk & risk metrics.
     - Fees and investment minimums.
     - Portfolio composition and holdings.
     - News context (including short snippets).
   - Attach rich metadata tags as defined in `Requirements.md` (fund_id, category, data_type, last_updated_at, source URLs).
5. **Persistence (Processed Layer)**:
   - Store:
     - Clean, normalized fund records.
     - Corresponding chunks ready for embedding/vectorization.

#### 5.3 Outputs & Deliverables

- A **cleaned dataset** for all 20 funds with:
  - Validation reports.
  - Well-defined chunk structures and metadata.
- Documentation describing:
  - Validation rules.
  - Normalization logic.
  - Chunking strategy and how each chunk maps back to original structured data.

---

### 6. Phase 3 — LLM Integration & RAG Orchestration (Gemini)

**Objective**: Integrate an LLM (Gemini) with the processed dataset to answer user queries using RAG, while strictly adhering to grounding and formatting rules.

#### 6.1 Scope

- Implement:
  - Embedding and indexing of chunks generated in Phase 2.
  - Retrieval logic that:
    - Maps user queries to relevant funds (using keywords and aliases).
    - Selects the most relevant chunks across data types (performance, risk, news, etc.).
  - Prompt orchestration with Gemini that:
    - Supplies retrieved chunks and metadata.
    - Enforces concise answers, required citations, and timestamp lines.
- Define and document **prompt templates**:
  - Base prompt for factual Q&A.
  - Specialized prompts for news/contextual "why" questions.
  - Prompts that combine multiple funds while still avoiding advice.

#### 6.2 Data Flow (Conceptual)

1. **User Query (Backend)**:
   - Backend chat endpoint receives natural-language query plus session context.
2. **Fund & Intent Resolution**:
   - Identify referenced funds using names and keywords from `fund_universe.csv`.
   - Classify query intent (e.g., performance, risk, news, portfolio exposure).
3. **Chunk Retrieval**:
   - Query vector index and/or metadata filters to select top-N chunks.
4. **Prompt Construction**:
   - Assemble a prompt including:
     - User query.
     - Selected chunks (as context).
     - System instructions covering:
       - Facts-only policy.
       - Citation requirement.
       - Answer length and formatting.
       - Timestamp behavior.
5. **LLM Call & Post-processing**:
   - Send prompt to Gemini; receive candidate answer.
   - Enforce formatting:
     - Ensure citations are present and link to known URLs.
     - Append "Last updated from sources: [Date/Time]" based on chunk metadata.
   - Return structured response to the frontend (text, citations, timestamps, structured snippets for UI widgets).

#### 6.3 Outputs & Deliverables

- A working **RAG backend** that:
  - Answers questions about the 20 funds using only grounded data.
  - Surfaces news snippets when users ask "why" or "what happened" type questions.
- A documented set of **prompt templates** and their intended behaviors, ready to be refined in later phases.

#### 6.4 Implementation Notes (Current Version)

- The initial implementation of Phase 3 uses:
  - A **local TF/IDF-style index** over Phase 2 chunks, persisted under `backend/rag_index/` (`tf_matrix.npy`, `metadata.json`, `vocab.json`).
  - Retrieval logic implemented in `backend/app/rag/indexer.py` (`retrieve_top_k`) to select relevant chunks for a given query (with optional fund-name filter).
  - The **Google GenAI SDK** (`google-genai`) and the **`gemini-3-flash-preview`** model for answer generation, via a thin wrapper in `backend/app/rag/gemini_client.py`.
- The main chat API is exposed via FastAPI in `backend/app/rag/router.py`:
  - `POST /chat` -- performs retrieval, applies guardrails, calls Gemini, and returns `{ answer, used_chunks, model }`.
  - `GET /chat/debug/retrieval` -- returns only the top-k retrieved chunks for inspection (no Gemini call).
- These choices are implementation details of the current version; the architecture remains compatible with swapping in an external vector database or a different Gemini model in future phases without changing higher-level flows.

---

### 7. Phase 4 — Guardrails & Policy Enforcement

**Objective**: Enforce safety, scope, and compliance constraints end-to-end, ensuring the system behaves as a facts-only informational assistant.

#### 7.1 Scope

- Implement guardrail logic that:
  - Detects and safely responds to:
    - Personalized advice questions (buy/sell/allocate).
    - Out-of-scope instruments or unsupported funds.
    - Requests for forecasts or projections.
  - Filters or flags PII and discourages its submission.
  - Enforces content safety and regulatory tone.
- Integrate guardrails:
  - At **input level** (pre-processing user queries).
  - At **output level** (post-processing LLM responses).

#### 7.2 Data Flow (Conceptual)

1. **Input Filtering**:
   - Before retrieval:
     - Check for PII patterns.
     - Classify query as in-scope vs. out-of-scope.
2. **Guardrail Decision**:
   - If out-of-scope:
     - Bypass standard RAG flow.
     - Use predefined refusal templates (e.g., advice prohibition, off-universe fund, speculative projection).
   - If in-scope:
     - Proceed to RAG flow with added constraints in the prompt.
3. **Output Validation**:
   - Inspect LLM response:
     - Ensure no advice language or projections.
     - Ensure citations are present.
     - Ensure disclaimers and timestamps remain intact.

#### 7.3 Outputs & Deliverables

- A consistent **guardrails policy layer** that:
  - Produces predictable, compliant refusal messages.
  - Keeps all responses within the scope defined in `Requirements.md`.
- Tests and scenarios demonstrating behavior for:
  - Advice-seeking queries.
  - PII attempts.
  - Off-universe fund names.
  - Speculative what-if questions.

#### 7.4 Implementation Notes (Current Version)

- The Phase 4 behavior and guardrail policies are defined in:
  - `phase4/Behavior_Specs.md` -- chatbot role, persona, RAG-first operating logic, and prompt orchestration.
  - `phase4/Guardrails.md` -- strict no-advice wall, PII and privacy rules, performance/claims limits, source integrity, and response formatting contract.
- Backend enforcement in `POST /chat` (`backend/app/rag/router.py`) applies a three-stage guardrail pipeline before reaching retrieval or Gemini:
  1. **PII detection** -- regex patterns for phone numbers, emails, PAN, and Aadhaar. If detected, a warning is returned without echoing the PII or calling Gemini.
  2. **Advice detection** -- phrase matching for buy/sell/hold/allocate/recommend patterns. Returns a standard refusal answer.
  3. **Out-of-corpus fund detection** -- loads fund names and keywords from `config/fund_universe.csv` and checks if the query references a fund not in the 20-fund universe. Returns the safety phrase from `Behavior_Specs.md`.
- Rate-limit errors from Gemini (HTTP 429 / `RESOURCE_EXHAUSTED`) are caught and surfaced as a 429 to the frontend with a friendly message.
- A separate debug endpoint (`GET /chat/debug/retrieval`) allows safe inspection of retrieval behavior independently of LLM generation.
- Unit tests under `backend/tests/test_chat.py` (9 tests) cover:
  - Normal chat with mocked Gemini and retrieval.
  - Advice-like query refusal (multiple phrases).
  - PII detection for phone, email, PAN, and Aadhaar.
  - Out-of-corpus fund refusal and in-corpus fund pass-through.
  - Debug retrieval endpoint wiring.

---

### 8. Phase 5 — Frontend & WealthAI UI Implementation

**Objective**: Implement the web UI described in `ui-references/UI_UX_Specs.md` and connect it to the backend chat and data APIs.

#### 8.1 Scope

- Build:
  - The Dark Wealth Manager layout:
    - Sidebar (categories, popular queries).
    - Header with marquee ticker and search.
    - Central chat panel (welcome state, conversation, input).
    - Right-side Market Pulse and fund quick-view panels.
  - Core interactions:
    - Asking questions, viewing responses with citations and timestamps.
    - Clicking ticker items or trending funds to seed queries and open quick-view cards.
    - Displaying "Verified" icons and Gemini-branded avatar accents.
  - Micro-interactions:
    - Typing indicators.
    - Streaming answers.
    - Refusal states with attention border.
    - Loading shimmer for ticker and Market Pulse.

#### 8.2 Integration Points

- Chat API:
  - Send user queries and display structured responses (answer + citations + timestamp).
- Fund metadata API:
  - Populate ticker, search, fund quick-view cards.
- Trending/analytics API:
  - Drive Market Pulse panel (top queried funds).

#### 8.3 Mobile-Responsive UI

The desktop "Bloomberg-style" three-column layout is preserved at `lg`/`xl` breakpoints. On smaller screens, the layout transforms into a mobile-optimized experience:

- **Mobile Header** (`AppShell.tsx`): A compact header (visible below `lg`) with a centered "WealthAI" logo, a Menu icon (left) to open the Sidebar Drawer, and a TrendingUp icon (right) to open the Market Pulse Drawer.
- **Sliding Drawers**: The left sidebar and right Market Pulse panel convert to overlay drawers on mobile, with `bg-black/60` backdrop and `slide-in-left` / `slide-in-right` animations (defined in `tailwind.config.js`).
- **Mobile Ticker** (`HeaderBar.tsx` -- `MobileTicker` component): A condensed, always-visible ticker strip below the mobile header with `text-[10px]` and faster animation.
- **Chat Panel** (`ChatPanel.tsx`):
  - Full-width layout on mobile (no `max-w-3xl` constraint).
  - Welcome suggestion chips stack vertically (`flex-col`) for thumb-friendly tapping.
  - Message bubbles use wider max-widths on mobile for readability.
  - `h-[100dvh]` on the main container prevents the mobile browser address bar from obscuring the input field.
- **Send Button**: Uses `type="button"` with an explicit `onClick` handler (in addition to Enter-to-send) to ensure both tap and keyboard submission work reliably.

#### 8.4 Outputs & Deliverables

- A production-quality web interface:
  - Matching layout, color, and interaction patterns in `UI_UX_Specs.md`.
  - Fully wired to backend endpoints.
  - Responsive across desktop, tablet, and mobile form factors.

---

### 9. Phase 6 — Deployment

**Objective**: Deploy the backend on Railway and the frontend on Vercel, connected via environment variables.

#### 9.1 Backend — Railway

- **Platform**: Railway (https://railway.app)
- **Configuration**: `railway.toml` at repo root defines the build and start commands.
  - Nixpacks auto-detects Python from `requirements.txt` (root-level file delegates to `backend/requirements.txt`).
  - Start command: `cd backend && python start.py` (reads `PORT` from environment, defaults to 8000)
  - Health check endpoint: `GET /health`
- **Environment Variables** (set in Railway dashboard):
  | Variable | Value |
  |---|---|
  | `GEMINI_API_KEY` | Your real Gemini API key |
  | `GEMINI_MODEL_NAME` | `gemini-3-flash-preview` |
  | `GEMINI_EMBEDDING_MODEL` | `models/embedding-001` |
  | `CORS_ORIGINS` | Your Vercel frontend URL (e.g., `https://your-app.vercel.app`) |
- **Runtime**: Python 3.11 (specified in `runtime.txt`)
- **Port**: Railway injects `PORT` env var automatically; uvicorn binds to it.

#### 9.2 Frontend — Vercel

- **Platform**: Vercel (https://vercel.com)
- **Framework**: Auto-detected as Next.js.
- **Root Directory**: Set to `frontend/` in Vercel project settings.
- **Environment Variables** (set in Vercel dashboard):
  | Variable | Value |
  |---|---|
  | `NEXT_PUBLIC_BACKEND_URL` | Railway backend URL (e.g., `https://your-app.up.railway.app`) |
- **Build**: Vercel runs `npm run build` automatically; no custom config needed.
- **Output**: Server-side rendered (SSR) Next.js app -- identical to local dev UI.

#### 9.3 Security

- `.gitignore` ensures `.env` files with real API keys are never committed.
- `.env.example` files in both `backend/` and `frontend/` document required variables with placeholder values.
- CORS is configurable via `CORS_ORIGINS` env var (defaults to `*` for development; set to the Vercel URL in production).

#### 9.4 Git & CI

- GitHub repository: Private, connected to both Railway and Vercel.
- On every push to `master`, both platforms auto-deploy.

---

### 10. Phase 7 — Scheduling, Refresh, and Automation

**Objective**: Keep data fresh and automate recurring processes using a scheduler (e.g., GitHub Actions plus platform scheduling).

#### 10.1 Scope

- Define and implement:
  - Scheduled scraping jobs that:
    - Re-run Phase 1 ingestion at configured intervals (e.g., daily).
    - Trigger Phase 2 cleaning and re-chunking.
    - Refresh embeddings and indexes used by RAG.
  - Automated checks:
    - Scrape success/failure notifications.
    - Data freshness dashboards or summaries.
- Integrate with:
  - Git repository workflows (e.g., GitHub Actions) to:
    - Run tests.
    - Optionally trigger re-deployment or re-indexing steps as needed.

#### 10.2 Outputs & Deliverables

- A **documented refresh schedule** and automation logic ensuring:
  - NAVs, returns, and news are regularly refreshed.
  - The chatbot's "Last updated from sources" timestamps reflect recent data.

---

### 11. Phase 8 — Observability, Analytics, and Iteration

**Objective**: Add observability and analytics to continuously monitor data quality, system health, and user interaction patterns.

#### 11.1 Scope

- Metrics:
  - Scrape job results per fund and overall.
  - Query volumes and latency.
  - Guardrail/refusal rates.
  - Trending funds and category mix.
- Tools:
  - Logs and dashboards to:
    - Inspect sample RAG answers with their underlying chunks.
    - Verify adherence to constraints over time.

#### 11.2 Outputs & Deliverables

- A feedback loop to:
  - Identify gaps in scraped fields or UI affordances.
  - Prioritize future enhancements (e.g., more funds, new metrics, UX refinements).

---

### 12. Phase Execution Strategy

- Phases will be executed **sequentially**, with:
  - Design and implementation.
  - Local testing and validation.
  - Review and sign-off from you before moving to the next phase.
- Any structural or scope changes discovered in later phases must:
  - Be reflected first in `Requirements.md` and relevant files under `config/` and `ui-references/`.
  - Then be propagated into the corresponding phase implementation.
