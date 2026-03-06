from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.rag.router import router as chat_router


app = FastAPI(title="Mutual Fund Chatbot Backend")

# Allow local frontend origins during development (Next.js dev ports).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/scrape/test")
async def scrape_test() -> JSONResponse:
    # Placeholder: will use Playwright to scrape a sample page
    return JSONResponse(
        {"message": "Scraping endpoint stub. Playwright integration pending."}
    )

