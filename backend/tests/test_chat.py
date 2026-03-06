from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture
def mock_retrieve_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide a deterministic retrieve_top_k for tests."""

    def _fake_retrieve_top_k(
        question: str,
        top_k: int = 8,
        fund_name_filter: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "chunk_id": "chunk-1",
                "text": "HDFC Silver ETF FoF Direct Growth is a Commodity mutual fund scheme.",
                "metadata": {
                    "identity_name": "HDFC Silver ETF FoF Direct Growth",
                    "last_scraped_at": "2026-03-04T10:00:00Z",
                    "source_urls": [
                        "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth"
                    ],
                },
                "score": 0.9,
            }
        ]

    from app.rag import router as rag_router  # type: ignore

    monkeypatch.setattr(rag_router, "retrieve_top_k", _fake_retrieve_top_k)


def _patch_gemini_and_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch both Gemini and retrieval to fail if called (for guardrail tests)."""
    from app.rag import router as rag_router  # type: ignore

    def _fail_generate_answer(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("generate_answer should not be called")

    def _fail_retrieve_top_k(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        raise AssertionError("retrieve_top_k should not be called")

    monkeypatch.setattr(rag_router, "generate_answer", _fail_generate_answer)
    monkeypatch.setattr(rag_router, "retrieve_top_k", _fail_retrieve_top_k)


# ---- Normal chat ----

def test_chat_success_with_mocked_gemini(
    monkeypatch: pytest.MonkeyPatch,
    mock_retrieve_top_k: None,
) -> None:
    """POST /chat returns answer + used_chunks when Gemini succeeds."""

    from app.rag import router as rag_router  # type: ignore

    def _fake_generate_answer(
        question: str,
        context_chunks: List[Dict[str, Any]],
        now_timestamp: str,
    ) -> str:
        return (
            "This is a test answer based solely on the provided context.\n\n"
            f"Last updated from sources: {now_timestamp}"
        )

    monkeypatch.setattr(rag_router, "generate_answer", _fake_generate_answer)

    payload = {
        "question": "Give me an overview of HDFC Silver ETF FoF Direct Growth.",
        "fund_hint": "HDFC Silver",
        "top_k": 4,
    }

    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "answer" in data
    assert "used_chunks" in data
    assert "model" in data
    assert "Last updated from sources:" in data["answer"]
    assert len(data["used_chunks"]) == 1
    assert data["used_chunks"][0]["chunk_id"] == "chunk-1"


# ---- Advice guardrail ----

def test_chat_refuses_advice_without_calling_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Advice-like questions should be refused before hitting Gemini or retrieval."""
    _patch_gemini_and_retrieval(monkeypatch)

    advice_queries = [
        "Should I invest in HDFC Silver ETF FoF Direct Growth for 3 years?",
        "Which fund is best for me?",
        "Where should i invest my money?",
        "Suggest me a fund for retirement",
    ]
    for question in advice_queries:
        resp = client.post("/chat", json={"question": question})
        assert resp.status_code == 200, f"Failed for: {question}"
        data = resp.json()
        assert "personalised investment advice" in data["answer"], f"Missing refusal for: {question}"
        assert data["used_chunks"] == []


# ---- PII guardrail ----

def test_chat_warns_on_pii_phone(monkeypatch: pytest.MonkeyPatch) -> None:
    """Phone numbers should trigger a PII warning."""
    _patch_gemini_and_retrieval(monkeypatch)

    resp = client.post("/chat", json={"question": "My number is 9876543210, tell me about HDFC Silver"})
    assert resp.status_code == 200
    data = resp.json()
    assert "do not share personal" in data["answer"]
    assert data["used_chunks"] == []


def test_chat_warns_on_pii_email(monkeypatch: pytest.MonkeyPatch) -> None:
    """Email addresses should trigger a PII warning."""
    _patch_gemini_and_retrieval(monkeypatch)

    resp = client.post("/chat", json={"question": "Send details to user@example.com please"})
    assert resp.status_code == 200
    data = resp.json()
    assert "do not share personal" in data["answer"]
    assert data["used_chunks"] == []


def test_chat_warns_on_pii_pan(monkeypatch: pytest.MonkeyPatch) -> None:
    """PAN numbers should trigger a PII warning."""
    _patch_gemini_and_retrieval(monkeypatch)

    resp = client.post("/chat", json={"question": "My PAN is ABCDE1234F can you check"})
    assert resp.status_code == 200
    data = resp.json()
    assert "do not share personal" in data["answer"]
    assert data["used_chunks"] == []


def test_chat_warns_on_pii_aadhaar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aadhaar numbers should trigger a PII warning."""
    _patch_gemini_and_retrieval(monkeypatch)

    resp = client.post("/chat", json={"question": "My aadhaar is 1234 5678 9012 please help"})
    assert resp.status_code == 200
    data = resp.json()
    assert "do not share personal" in data["answer"]
    assert data["used_chunks"] == []


# ---- Out-of-corpus guardrail ----

def test_chat_refuses_out_of_corpus_fund(monkeypatch: pytest.MonkeyPatch) -> None:
    """Questions about funds not in the 20-fund universe should be refused."""
    _patch_gemini_and_retrieval(monkeypatch)

    out_of_corpus_queries = [
        "Tell me about Parag Parikh Flexi Cap Fund Direct Growth",
        "What are the returns for Mirae Asset Large Cap Fund?",
        "Show me details of Tata Digital India Fund Direct Plan",
    ]
    for question in out_of_corpus_queries:
        resp = client.post("/chat", json={"question": question})
        assert resp.status_code == 200, f"Failed for: {question}"
        data = resp.json()
        assert "learning and growing" in data["answer"], f"Missing safety phrase for: {question}"
        assert data["used_chunks"] == []


def test_chat_allows_in_corpus_fund(
    monkeypatch: pytest.MonkeyPatch,
    mock_retrieve_top_k: None,
) -> None:
    """Questions about our 20 supported funds should proceed normally."""

    from app.rag import router as rag_router  # type: ignore

    def _fake_generate_answer(
        question: str,
        context_chunks: List[Dict[str, Any]],
        now_timestamp: str,
    ) -> str:
        return f"Test answer.\n\nLast updated from sources: {now_timestamp}"

    monkeypatch.setattr(rag_router, "generate_answer", _fake_generate_answer)

    resp = client.post("/chat", json={"question": "What is the NAV of HDFC Silver ETF FoF Direct Growth?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "learning and growing" not in data["answer"]
    assert len(data["used_chunks"]) > 0


# ---- Debug retrieval endpoint ----

def test_debug_retrieval_endpoint_uses_indexer(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /chat/debug/retrieval should return chunks from retrieve_top_k."""

    from app.rag import router as rag_router  # type: ignore

    def _fake_retrieve_top_k(
        question: str,
        top_k: int = 8,
        fund_name_filter: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "chunk_id": "debug-1",
                "text": "Debug chunk text",
                "metadata": {"identity_name": "Debug Fund", "score_hint": 0.99},
                "score": 0.99,
            }
        ]

    monkeypatch.setattr(rag_router, "retrieve_top_k", _fake_retrieve_top_k)

    params = {
        "question": "Test retrieval",
        "fund_hint": "Debug",
        "top_k": 1,
    }
    resp = client.get("/chat/debug/retrieval", params=params)
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["chunk_id"] == "debug-1"
    assert data[0]["text"] == "Debug chunk text"
