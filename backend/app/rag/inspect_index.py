from __future__ import annotations

"""
Small CLI helper to inspect the Phase 3 local TF index.

Usage (from backend/):

    python -m app.rag.inspect_index --question "overview of HDFC Silver ETF FoF Direct Growth" --fund "HDFC Silver" --top-k 5
"""

import argparse
from typing import List, Dict, Any

from loguru import logger

from .indexer import retrieve_top_k


def format_chunk(c: Dict[str, Any], rank: int) -> str:
    meta = c.get("metadata") or {}
    fund_name = meta.get("identity_name") or meta.get("fund_name") or "Unknown fund"
    score = float(c.get("score", 0.0))
    text = c.get("text", "")
    text_preview = text if len(text) <= 240 else text[:237] + "..."
    source_urls: List[str] = meta.get("source_urls") or meta.get("source_url") or []
    if isinstance(source_urls, str):
        source_urls = [source_urls]
    sources_str = ", ".join(source_urls)

    lines = [
        f"#{rank}  chunk_id={c['chunk_id']}  score={score:.4f}",
        f"    fund_name: {fund_name}",
        f"    preview:   {text_preview}",
    ]
    if sources_str:
        lines.append(f"    sources:   {sources_str}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect nearest-neighbour chunks from the local TF index."
    )
    parser.add_argument(
        "--question",
        "-q",
        required=True,
        help="Natural-language question or query string.",
    )
    parser.add_argument(
        "--fund",
        "-f",
        default=None,
        help="Optional fund name/keyword to filter chunks (e.g. 'HDFC Silver').",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=8,
        help="Number of nearest chunks to display.",
    )

    args = parser.parse_args()
    question: str = args.question
    fund_filter: str | None = args.fund
    top_k: int = args.top_k

    logger.info(f"Query: {question!r}")
    if fund_filter:
        logger.info(f"Fund filter: {fund_filter!r}")

    results = retrieve_top_k(
        question=question,
        top_k=top_k,
        fund_name_filter=fund_filter,
    )

    if not results:
        print("No chunks retrieved. Ensure the index is built and query is valid.")
        return

    print(f"\nTop {len(results)} chunks:\n")
    for i, chunk in enumerate(results, start=1):
        print(format_chunk(chunk, rank=i))
        print()


if __name__ == "__main__":
    main()

