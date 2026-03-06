from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

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


def _is_advice_like(question: str) -> bool:
    q = question.lower()
    advice_phrases = [
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
    ]
    return any(phrase in q for phrase in advice_phrases)


def _make_refusal_answer() -> str:
    return (
        "I’m not able to provide personalised investment advice, recommendations, or "
        "tell you what to buy, sell, or hold. I can, however, share factual details "
        "about any of the 20 supported mutual funds (performance, risk, holdings, costs) "
        "to help you understand them better.\n\n"
        "Last updated from sources: N/A"
    )


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for the Mutual Fund RAG bot.

    - Retrieves top-k relevant chunks.
    - Calls Gemini to generate a grounded, citation-rich answer.
    - Applies guardrails to avoid personalised investment advice.
    """
    settings = get_settings()

    # Guardrail: pre-emptively refuse explicit advice questions.
    if _is_advice_like(req.question):
        logger.info(
            "chat_request.advice_refusal",
            extra={
                "question": req.question,
            },
        )
        refusal = _make_refusal_answer()
        return ChatResponse(answer=refusal, used_chunks=[], model=settings.gemini_model_name)

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

    # Derive a "last updated" timestamp using the latest last_scraped_at across chunks.
    last_updated_values: List[str] = []
    for r in retrieved:
        meta = r.get("metadata") or {}
        ts = meta.get("last_scraped_at")
        if isinstance(ts, str):
            last_updated_values.append(ts)
    if last_updated_values:
        # Use max lexical ordering; ISO timestamps sort correctly.
        now_ts = max(last_updated_values)
    else:
        now_ts = datetime.utcnow().isoformat() + "Z"

    # Log retrieval snapshot for observability.
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
    except Exception as exc:  # pragma: no cover - network/credentials error path
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

    - Returns the top-k retrieved chunks for a question.
    - Intended for admin/debug and future UI tooling.
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

