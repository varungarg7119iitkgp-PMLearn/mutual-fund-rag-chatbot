# Phase 5 — Frontend UI Implementation

## Purpose

Build a world-class, mobile-responsive chat interface with dark theme, live ticker, trending funds sidebar, and an intuitive conversational UX.

## Actual Code Location

All Phase 5 code lives in the deployed frontend:

```
frontend/
├── app/
│   ├── layout.tsx               # Root layout (fonts, metadata, global styles)
│   ├── page.tsx                 # Entry page — renders AppShell
│   └── globals.css              # Tailwind base styles + custom animations
├── components/
│   ├── AppShell.tsx             # Root UI shell — desktop/mobile layout orchestration
│   ├── HeaderBar.tsx            # Top bar with marquee ticker + search (desktop & mobile variants)
│   ├── ChatPanel.tsx            # Central chat interface — messages, input, send logic
│   ├── LeftSidebar.tsx          # Fund list sidebar (desktop permanent, mobile sliding drawer)
│   ├── RightSidebar.tsx         # Trending funds + details sidebar (desktop/mobile drawer)
│   └── WelcomeScreen.tsx        # Initial state with suggestion chips
├── tailwind.config.js           # Custom animations (slide-in-left, slide-in-right)
├── next.config.mjs              # Next.js configuration
└── package.json                 # Dependencies (Next.js, React, Tailwind, Lucide icons)
```

## Key Features

- **Dark theme** — Consistent dark palette across all components.
- **Mobile-responsive** — Sliding drawers for sidebars, optimized mobile header/ticker, full-width chat, `h-[100dvh]` for proper mobile viewport.
- **Live ticker** — Scrolling marquee showing fund NAV data.
- **Welcome screen** — Suggestion chips for common questions when chat is empty.
- **Rate-limit handling** — Friendly "tired" message when Gemini quota is exhausted.
- **Loading states** — Animated typing indicator during Gemini response.

## Key Configuration

| Variable | Where | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Vercel env / `.env` | Backend API base URL |

## Related Phases

- **Phase 3** (`phase3_llm_rag/`) — The backend API that this frontend calls.
- **Phase 6** (`phase6_deployment/`) — Deployment to Vercel.

## Design References

UI/UX specifications and mockups are in `ui-references/UI_UX_Specs.md`.
