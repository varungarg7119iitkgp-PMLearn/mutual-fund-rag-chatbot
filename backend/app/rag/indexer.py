from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json
import math

import numpy as np
from loguru import logger


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHUNKS_DIR = PROJECT_ROOT / "phase2_processing" / "output" / "chunks"
INDEX_DIR = PROJECT_ROOT / "backend" / "rag_index"
INDEX_MATRIX_PATH = INDEX_DIR / "tf_matrix.npy"
INDEX_METADATA_PATH = INDEX_DIR / "metadata.json"
INDEX_VOCAB_PATH = INDEX_DIR / "vocab.json"


@dataclass
class IndexedChunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any]


def load_all_chunks() -> List[IndexedChunk]:
    """Load all chunk JSONL files produced by Phase 2."""
    if not CHUNKS_DIR.exists():
        raise FileNotFoundError(
            f"Chunks directory not found at {CHUNKS_DIR}. "
            "Run Phase 2 processing before building the index."
        )

    chunks: List[IndexedChunk] = []
    for path in sorted(CHUNKS_DIR.glob("*.jsonl")):
        logger.info(f"Loading chunks from {path.name}")
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                chunks.append(
                    IndexedChunk(
                        chunk_id=data["chunk_id"],
                        text=data["text"],
                        metadata=data.get("metadata", {}),
                    )
                )
    logger.info(f"Loaded {len(chunks)} chunks from {CHUNKS_DIR}")
    return chunks


def _tokenize(text: str) -> List[str]:
    """Very simple whitespace + lowercase tokenizer."""
    return [tok for tok in text.lower().split() if tok]


def build_index() -> None:
    """
    Build a simple TF-based vector index for all chunks (no external ML deps).

    This is an offline step that should be run whenever Phase 2 outputs change.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    chunks = load_all_chunks()
    texts = [c.text for c in chunks]

    # Build vocabulary
    vocab: Dict[str, int] = {}
    tokenized_docs: List[List[str]] = []
    for text in texts:
        tokens = _tokenize(text)
        tokenized_docs.append(tokens)
        for tok in tokens:
            if tok not in vocab:
                vocab[tok] = len(vocab)

    logger.info(f"Vocabulary size: {len(vocab)}")

    # Build term-frequency matrix
    num_docs = len(texts)
    num_terms = len(vocab)
    matrix = np.zeros((num_docs, num_terms), dtype="float32")

    df = np.zeros(num_terms, dtype="float32")

    for i, tokens in enumerate(tokenized_docs):
        counts: Dict[int, int] = {}
        for tok in tokens:
            j = vocab[tok]
            counts[j] = counts.get(j, 0) + 1
        for j, cnt in counts.items():
            matrix[i, j] = cnt
        for j in counts.keys():
            df[j] += 1.0

    # Convert to tf-idf-like weights (optional but improves retrieval)
    idf = np.ones(num_terms, dtype="float32")
    for j in range(num_terms):
        if df[j] > 0:
            idf[j] = math.log((1.0 + num_docs) / (1.0 + df[j])) + 1.0
    matrix *= idf

    # L2-normalize rows
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8
    matrix = matrix / norms

    logger.info(f"TF matrix shape: {matrix.shape}")

    # Save matrix and metadata
    np.save(INDEX_MATRIX_PATH, matrix.astype("float32"))

    meta_records: List[Dict[str, Any]] = []
    for c in chunks:
        meta_records.append(
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "metadata": c.metadata,
            }
        )
    with INDEX_METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(meta_records, f, ensure_ascii=False, indent=2)

    with INDEX_VOCAB_PATH.open("w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved local TF index to {INDEX_DIR}")


def _load_index() -> Tuple[np.ndarray, List[Dict[str, Any]], Dict[str, int]]:
    if (
        not INDEX_MATRIX_PATH.exists()
        or not INDEX_METADATA_PATH.exists()
        or not INDEX_VOCAB_PATH.exists()
    ):
        raise FileNotFoundError(
            f"Index files not found in {INDEX_DIR}. "
            "Run the index builder (Phase 3 indexing step) first."
        )

    matrix = np.load(INDEX_MATRIX_PATH)
    with INDEX_METADATA_PATH.open(encoding="utf-8") as f:
        metadata: List[Dict[str, Any]] = json.load(f)
    with INDEX_VOCAB_PATH.open(encoding="utf-8") as f:
        vocab: Dict[str, int] = json.load(f)

    if matrix.shape[0] != len(metadata):
        raise RuntimeError(
            f"Matrix row count ({matrix.shape[0]}) does not match metadata records ({len(metadata)})."
        )
    return matrix, metadata, vocab


def retrieve_top_k(
    question: str,
    top_k: int = 8,
    fund_name_filter: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k most similar chunks for a query string using cosine similarity
    over a simple TF/IDF-like vector space model.
    """
    matrix, metadata, vocab = _load_index()

    # Build query vector
    q_vec = np.zeros(matrix.shape[1], dtype="float32")
    counts: Dict[int, int] = {}
    for tok in _tokenize(question):
        if tok in vocab:
            j = vocab[tok]
            counts[j] = counts.get(j, 0) + 1
    for j, cnt in counts.items():
        q_vec[j] = cnt

    # Normalize query
    q_norm = np.linalg.norm(q_vec) + 1e-8
    q_vec = q_vec / q_norm

    # Cosine similarity
    sims = matrix @ q_vec

    # Optional fund filter
    indices = list(range(len(metadata)))
    if fund_name_filter:
        needle = fund_name_filter.lower()
        filtered_indices = []
        for i, rec in enumerate(metadata):
            fund_name = (
                (rec.get("metadata") or {}).get("fund_name")
                or (rec.get("metadata") or {}).get("identity_name")
                or ""
            )
            if needle in fund_name.lower():
                filtered_indices.append(i)
        if filtered_indices:
            indices = filtered_indices

    # Rank by similarity
    ranked = sorted(indices, key=lambda i: float(sims[i]), reverse=True)[:top_k]
    results: List[Dict[str, Any]] = []
    for i in ranked:
        rec = metadata[i]
        rec_copy = {
            "chunk_id": rec["chunk_id"],
            "text": rec["text"],
            "metadata": rec.get("metadata", {}),
            "score": float(sims[i]),
        }
        results.append(rec_copy)
    return results


