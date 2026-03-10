# Phase 3 — LLM Integration & RAG Orchestration

## Purpose

Wire up the Gemini LLM with a TF-IDF retrieval index to answer user questions grounded in real fund data (Retrieval-Augmented Generation).

## Actual Code Location

Phase 3 code lives inside the deployed backend:

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry point, registers routers
│   ├── core/
│   │   └── config.py            # Settings (Gemini API key, model name, CORS origins)
│   └── rag/
│       ├── router.py            # POST /chat endpoint — retrieval + Gemini + guardrails
│       ├── gemini_client.py     # Gemini SDK wrapper, prompt template, generation call
│       ├── indexer.py           # TF-IDF index builder and top-k retrieval
│       └── inspect_index.py     # Debug utility for inspecting index contents
├── rag_index/                   # Pre-built TF-IDF index (numpy arrays + metadata JSON)
├── start.py                     # Uvicorn launcher (reads PORT from env)
└── tests/
    └── test_chat.py             # Unit tests for chat endpoint and guardrails
```

## How It Works

1. **Index Building** — `indexer.py` reads Phase 2 chunks, builds a TF-IDF matrix (scikit-learn), and persists it to `rag_index/`.
2. **Retrieval** — On each `/chat` request, the user's question is vectorized and compared against the index to find the top-k most relevant chunks.
3. **Generation** — Retrieved chunks + question are passed to Gemini via `gemini_client.py` with a carefully crafted prompt enforcing tone, citations, and safety rules.
4. **Response** — The answer includes source citations and a "Last updated from sources" footer.

## Key Configuration

| Variable | Where | Purpose |
|----------|-------|---------|
| `GEMINI_API_KEY` | Railway env / `.env` | Google Gemini API authentication |
| `GEMINI_MODEL_NAME` | `config.py` | Model to use (default: `gemini-3-flash-preview`) |
| `CORS_ORIGINS` | Railway env / `.env` | Allowed frontend origins |

## Related Phases

- **Phase 2** (`phase2_processing/`) produces the chunks that this phase indexes.
- **Phase 4** (`phase4/`) defines the guardrail policies enforced in `router.py`.
- **Phase 6** (`phase6_deployment/`) covers how this backend is deployed to Railway.
