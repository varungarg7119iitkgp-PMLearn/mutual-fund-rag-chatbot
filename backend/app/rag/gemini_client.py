from __future__ import annotations

from typing import List, Dict, Any
import time

from google import genai
from google.genai import types as genai_types
from loguru import logger

from app.core.config import get_settings


settings = get_settings()
client = genai.Client(api_key=settings.gemini_api_key)


def generate_answer(
    question: str,
    context_chunks: List[Dict[str, Any]],
    now_timestamp: str,
) -> str:
    """
    Call Gemini (via google-genai) to generate a grounded answer based on retrieved chunks.

    - `context_chunks` are the top-N RAG chunks (each with `text` and `metadata`).
    - `now_timestamp` is the timestamp string we want to show in the footer line.
    """
    # Build a compact context section from chunks.
    context_parts: List[str] = []
    for chunk in context_chunks:
        meta = chunk.get("metadata") or {}
        sources = meta.get("source_urls") or []
        source_str = ", ".join(sorted(set(sources))) if sources else ""
        context_parts.append(
            f"[{chunk.get('data_type', 'context')}] {chunk.get('text')}\nSources: {source_str}"
        )
    context_block = "\n\n".join(context_parts)

    system_instructions = (
        "You are WealthAI, a calm, professional AI Wealth Concierge for a curated "
        "universe of 20 mutual funds. You must answer only using the factual data "
        "in the context below. Do not guess or use outside knowledge for any "
        "fund-specific metrics.\n\n"
        "Guardrails:\n"
        "- Do NOT provide personalised investment advice, buy/sell/hold opinions, "
        "or allocation recommendations under any circumstance.\n"
        "- If the user asks what to buy/sell/hold, or how much to invest, politely "
        "refuse and offer to share factual details instead.\n"
        "- If the question is about a fund or product outside the 20 supported "
        "mutual funds or the context does not contain the requested metric, use "
        'this safety phrase: \"Sorry I can help you with details on that, I am '
        'learning and growing, maybe on your next interaction i will have answers.\" '
        "and do not invent an answer.\n\n"
        "Style:\n"
        "- Speak like a seasoned private banker: composed, respectful, and clear.\n"
        "- Begin every answer with a short, warm greeting that implicitly acknowledges "
        "the question (for example, \"Happy to walk you through this,\" or a light "
        "wordplay related to clarity, numbers, or markets) while staying professional.\n"
        "- You may briefly explain concepts or use simple analogies, but keep the "
        "focus on factual data from the context.\n"
    )

    prompt = (
        f"{system_instructions}\n"
        "Context (scraped, cleaned data):\n"
        f"{context_block}\n\n"
        f"User question:\n{question}\n\n"
        "Instructions for your answer:\n"
        "- Start with a brief, friendly greeting that feels tailored to someone "
        "reviewing mutual funds.\n"
        "- Use at most 3 sentences in clear, professional English.\n"
        "- Prefer short paragraphs; you may use a short bulleted list if it improves readability.\n"
        "- Clearly surface the key metrics the user cares about (for example NAV, risk level, or returns) if present.\n"
        "- Include at least one explicit clickable source URL from the context in the body of your answer.\n"
        "- If a requested metric is missing in the context, say you do not have that detail yet and do NOT guess.\n"
        f"- End your answer with a new line exactly like:\nLast updated from sources: {now_timestamp}"
    )

    logger.info(
        "gemini_request.generate_answer",
        extra={
            "question": question,
            "now_timestamp": now_timestamp,
            "context_chunk_ids": [c.get("chunk_id") for c in context_chunks],
            "prompt_preview": prompt[:800],
        },
    )
    contents = [
        genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=prompt)],
        )
    ]

    # Simple retry loop to smooth over transient 5xx "high demand" errors from Gemini.
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=contents,
            )
            # google-genai returns a response with .text for concatenated text.
            raw_text = getattr(response, "text", "") or ""
            break
        except Exception as exc:  # pragma: no cover - network/5xx errors
            last_exc = exc
            logger.warning(
                "Gemini call failed on attempt %d/3: %r", attempt + 1, exc
            )
            # Backoff: 0.5s, 1s, 2s
            sleep_s = 0.5 * (2**attempt)
            time.sleep(sleep_s)
    else:
        # All retries failed; re-raise the last exception for FastAPI to surface.
        assert last_exc is not None
        raise last_exc

    # Fix common mojibake for the rupee symbol that can appear when
    # combining scraped content and model output.
    cleaned = raw_text.replace("â¹", "₹")
    return cleaned

