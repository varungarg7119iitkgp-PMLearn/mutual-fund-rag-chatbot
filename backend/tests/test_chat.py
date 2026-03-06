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


def test_chat_success_with_mocked_gemini(
    monkeypatch: pytest.MonkeyPatch,
    mock_retrieve_top_k: None,
) -> None:
    """POST /chat returns answer + used_chunks when Gemini succeeds."""

    from app.rag import gemini_client  # type: ignore

    def _fake_generate_answer(
        question: str,
        context_chunks: List[Dict[str, Any]],
        now_timestamp: str,
    ) -> str:
        # Simple deterministic answer with required footer line.
        return (
            "This is a test answer based solely on the provided context.\n\n"
            f"Last updated from sources: {now_timestamp}"
        )

    monkeypatch.setattr(gemini_client, "generate_answer", _fake_generate_answer)

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

    # Check footer line exists.
    assert "Last updated from sources:" in data["answer"]
    # Ensure our fake retrieval was used.
    assert len(data["used_chunks"]) == 1
    assert data["used_chunks"][0]["chunk_id"] == "chunk-1"


def test_chat_refuses_advice_without_calling_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Advice-like questions should be refused before hitting Gemini or retrieval."""

    from app.rag import gemini_client, router as rag_router  # type: ignore

    def _fail_generate_answer(*args: Any, **kwargs: Any) -> str:  # pragma: no cover
        raise AssertionError("generate_answer should not be called for advice-like queries")

    def _fail_retrieve_top_k(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:  # pragma: no cover
        raise AssertionError("retrieve_top_k should not be called for advice-like queries")

    monkeypatch.setattr(gemini_client, "generate_answer", _fail_generate_answer)
    monkeypatch.setattr(rag_router, "retrieve_top_k", _fail_retrieve_top_k)

    payload = {
        "question": "Should I invest in HDFC Silver ETF FoF Direct Growth for 3 years?",
        "fund_hint": "HDFC Silver",
        "top_k": 4,
    }

    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # We expect a refusal style answer and no used_chunks.
    assert "personalised investment advice" in data["answer"]
    assert data["used_chunks"] == []


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

