# Phase 6 — Deployment (Railway + Vercel)

## Purpose

Deploy the backend to Railway and the frontend to Vercel for production access.

## Actual Code / Config Locations

Deployment configuration is spread across the repo root and platform dashboards:

```
(repo root)
├── railway.toml                 # Railway build & start commands
├── requirements.txt             # Python dependencies (used by Railway's Nixpacks builder)
├── runtime.txt                  # Python version pin (3.11.x)
├── backend/
│   └── start.py                 # Uvicorn launcher (reads PORT from Railway env)
└── frontend/
    └── next.config.mjs          # Next.js config (Vercel auto-detects)
```

## Architecture

```
User → Vercel (frontend) → Railway (backend API) → Gemini API
                                    ↓
                              rag_index/ (in-memory TF-IDF)
```

## Platform Details

### Railway (Backend)

| Setting | Value |
|---------|-------|
| Build command | `pip install -r requirements.txt` (auto via Nixpacks) |
| Start command | `python backend/start.py` |
| Environment variables | `GEMINI_API_KEY`, `CORS_ORIGINS` |
| Auto-deploy | Yes — triggers on push to `master` |

### Vercel (Frontend)

| Setting | Value |
|---------|-------|
| Framework | Next.js (auto-detected) |
| Root directory | `frontend/` |
| Environment variables | `NEXT_PUBLIC_BACKEND_URL` |
| Auto-deploy | Yes — triggers on push to `master` |

## Environment Variables Summary

| Variable | Platform | Secret? | Purpose |
|----------|----------|---------|---------|
| `GEMINI_API_KEY` | Railway | Yes | Gemini API access |
| `CORS_ORIGINS` | Railway | No | Allowed frontend URLs |
| `NEXT_PUBLIC_BACKEND_URL` | Vercel | No | Backend API URL for frontend |

## Related Phases

- **Phase 3** (`phase3_llm_rag/`) — The backend code being deployed.
- **Phase 5** (`phase5_frontend/`) — The frontend code being deployed.
- **Phase 7** (`phase7_automation/`) — GitHub Actions auto-commits trigger redeployments.
