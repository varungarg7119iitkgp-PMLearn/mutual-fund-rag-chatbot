from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import get_settings
from .gemini_client import generate_answer
from .indexer import retrieve_top_k


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    fund_hint: Optional[str] = Field(
        None,
        description="Optional fund name or keyword to bias retrieval.",
    )
    top_k: int = Field(8, ge=1, le=16)


class ChatChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class ChatResponse(BaseModel):
    answer: str
    used_chunks: List[ChatChunk]
    model: str


# ---------------------------------------------------------------------------
# Guardrail: Advice detection
# ---------------------------------------------------------------------------

_ADVICE_PHRASES = [
    "should i buy",
    "should i sell",
    "should i invest",
    "should i hold",
    "is it a good investment",
    "is this a good investment",
    "what should i invest",
    "how much should i invest",
    "how much should i allocate",
    "build my portfolio",
    "construct my portfolio",
    "recommend a portfolio",
    "recommend investments",
    "where should i invest",
    "which fund is best for me",
    "which is better for me",
    "suggest me a fund",
    "suggest a fund",
    "what to buy",
    "what to sell",
]


def _is_advice_like(question: str) -> bool:
    q = question.lower()
    return any(phrase in q for phrase in _ADVICE_PHRASES)


def _make_refusal_answer() -> str:
    return (
        "I'm not able to provide personalised investment advice, recommendations, or "
        "tell you what to buy, sell, or hold. I can, however, share factual details "
        "about any of the 20 supported mutual funds (performance, risk, holdings, costs) "
        "to help you understand them better.\n\n"
        "Last updated from sources: N/A"
    )


# ---------------------------------------------------------------------------
# Guardrail: PII detection
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r"(?<!\d)\d[\d\s\-]{8,}\d(?!\d)")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_AADHAAR_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")


def _contains_pii(text: str) -> bool:
    return bool(
        _PHONE_RE.search(text)
        or _EMAIL_RE.search(text)
        or _PAN_RE.search(text)
        or _AADHAAR_RE.search(text)
    )


def _make_pii_warning() -> str:
    return (
        "For your security, please do not share personal or account information here "
        "(such as phone numbers, email addresses, PAN, Aadhaar, or bank details). "
        "I can only help with general fund details and the 20 supported mutual funds.\n\n"
        "Feel free to ask me about any fund's performance, risk, holdings, or costs!\n\n"
        "Last updated from sources: N/A"
    )


# ---------------------------------------------------------------------------
# Guardrail: Out-of-corpus fund detection
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_fund_universe() -> Tuple[Set[str], Set[str]]:
    """Load fund names and keywords from fund_universe.csv."""
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "config", "fund_universe.csv"
    )
    csv_path = os.path.normpath(csv_path)

    names: Set[str] = set()
    keywords: Set[str] = set()

    if not os.path.exists(csv_path):
        logger.warning("fund_universe.csv not found at %s, skipping corpus check", csv_path)
        return names, keywords

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fund_name = (row.get("Name of Fund") or "").strip().lower()
            if fund_name:
                names.add(fund_name)
            kw_str = row.get("Keywords") or ""
            for kw in kw_str.split(","):
                kw = kw.strip().lower()
                if kw:
                    keywords.add(kw)

    return names, keywords


_FUND_LIKE_RE = re.compile(
    r"\b\w+(?:\s+\w+){0,8}\s+(?:fund|etf|fof|scheme|mutual fund|direct|growth|plan)\b",
    re.IGNORECASE,
)


def _mentions_out_of_corpus_fund(question: str) -> bool:
    """Return True if the question references a specific fund not in our universe."""
    fund_names, fund_keywords = _load_fund_universe()
    if not fund_names:
        return False

    q_lower = question.lower()

    for name in fund_names:
        if name in q_lower:
            return False
    for kw in fund_keywords:
        if kw in q_lower:
            return False

    if _FUND_LIKE_RE.search(question):
        return True

    return False


def _make_out_of_corpus_answer() -> str:
    return (
        "Sorry I can't help you with details on that, I am learning and growing, "
        "maybe on your next interaction I will have answers. "
        "I currently support 20 curated mutual funds across Equity, Debt, Hybrid, "
        "and Commodities categories.\n\n"
        "Last updated from sources: N/A"
    )


# ---------------------------------------------------------------------------
# Guardrail: Rate-limit friendly error
# ---------------------------------------------------------------------------

def _is_rate_limit_error(exc: Exception) -> bool:
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for the Mutual Fund RAG bot.

    Guardrail pipeline (in order):
    1. PII detection — refuse and warn.
    2. Advice detection — refuse without calling Gemini.
    3. Out-of-corpus fund detection — refuse with safety phrase.
    4. Retrieval + Gemini generation with rate-limit handling.
    """
    settings = get_settings()

    # Guardrail 1: PII detection.
    if _contains_pii(req.question):
        logger.info("chat_request.pii_detected", extra={"question_length": len(req.question)})
        return ChatResponse(
            answer=_make_pii_warning(), used_chunks=[], model=settings.gemini_model_name
        )

    # Guardrail 2: Advice detection.
    if _is_advice_like(req.question):
        logger.info("chat_request.advice_refusal", extra={"question": req.question})
        return ChatResponse(
            answer=_make_refusal_answer(), used_chunks=[], model=settings.gemini_model_name
        )

    # Guardrail 3: Out-of-corpus fund detection.
    if _mentions_out_of_corpus_fund(req.question):
        logger.info("chat_request.out_of_corpus", extra={"question": req.question})
        return ChatResponse(
            answer=_make_out_of_corpus_answer(), used_chunks=[], model=settings.gemini_model_name
        )

    # Retrieve candidate chunks from the local TF index.
    try:
        retrieved = retrieve_top_k(
            question=req.question,
            top_k=req.top_k,
            fund_name_filter=req.fund_hint,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG index not built yet. "
                "Run the Phase 3 indexing step to generate embeddings for Phase 2 chunks."
            ),
        ) from exc

    if not retrieved:
        raise HTTPException(
            status_code=404,
            detail="No relevant context found for this question.",
        )

    # Derive a "last updated" timestamp from the latest last_scraped_at across chunks.
    last_updated_values: List[str] = []
    for r in retrieved:
        meta = r.get("metadata") or {}
        ts = meta.get("last_scraped_at")
        if isinstance(ts, str):
            last_updated_values.append(ts)
    if last_updated_values:
        now_ts = max(last_updated_values)
    else:
        now_ts = datetime.utcnow().isoformat() + "Z"

    logger.info(
        "chat_request.retrieval",
        extra={
            "question": req.question,
            "fund_hint": req.fund_hint,
            "top_k": req.top_k,
            "used_chunk_ids": [c.get("chunk_id") for c in retrieved],
        },
    )

    # Generate answer with Gemini.
    try:
        answer_text = generate_answer(
            question=req.question,
            context_chunks=retrieved,
            now_timestamp=now_ts,
        )
    except Exception as exc:
        if _is_rate_limit_error(exc):
            logger.warning("chat_request.rate_limited", extra={"error": str(exc)})
            raise HTTPException(
                status_code=429,
                detail="I'm receiving too many requests right now. Please try again in a minute.",
            ) from exc
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer with Gemini: {exc}",
        ) from exc

    used_chunks = [
        ChatChunk(
            chunk_id=c["chunk_id"],
            text=c["text"],
            metadata=c.get("metadata", {}),
            score=float(c.get("score", 0.0)),
        )
        for c in retrieved
    ]

    logger.info(
        "chat_response.generated",
        extra={
            "question": req.question,
            "model": settings.gemini_model_name,
            "answer_preview": answer_text[:400],
            "used_chunk_ids": [c.chunk_id for c in used_chunks],
        },
    )

    return ChatResponse(
        answer=answer_text,
        used_chunks=used_chunks,
        model=settings.gemini_model_name,
    )


@router.get("/debug/retrieval", response_model=List[ChatChunk])
async def debug_retrieval(
    question: str,
    fund_hint: Optional[str] = None,
    top_k: int = 8,
) -> List[ChatChunk]:
    """
    Debug endpoint to inspect retrieval only (no Gemini call).
    """
    try:
        retrieved = retrieve_top_k(
            question=question,
            top_k=top_k,
            fund_name_filter=fund_hint,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG index not built yet. "
                "Run the Phase 3 indexing step to generate embeddings for Phase 2 chunks."
            ),
        ) from exc

    return [
        ChatChunk(
            chunk_id=c["chunk_id"],
            text=c["text"],
            metadata=c.get("metadata", {}),
            score=float(c.get("score", 0.0)),
        )
        for c in retrieved
    ]
