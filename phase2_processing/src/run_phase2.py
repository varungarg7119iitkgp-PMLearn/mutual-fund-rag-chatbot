"""
CLI entrypoint for Phase 2 processing.

Usage (from project root, after Phase 1 has been run):

    python -m phase2_processing.src.run_phase2

This will:
- Load raw snapshots from `phase1_ingestion/output/raw/`.
- Apply normalization rules (category, risk label, NAV date).
- Write cleaned snapshots to `phase2_processing/output/clean/`.
- Generate RAG chunks and write them to `phase2_processing/output/chunks/` as JSONL.
"""

from __future__ import annotations

from pathlib import Path
import json

from loguru import logger

from .loader import load_all_snapshots
from .normalization import normalize_snapshot
from .chunker import build_all_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = PROJECT_ROOT / "phase2_processing" / "output" / "clean"
CHUNKS_DIR = PROJECT_ROOT / "phase2_processing" / "output" / "chunks"


def ensure_output_dirs() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_output_dirs()
    snapshots = load_all_snapshots()

    for key, snapshot in snapshots.items():
        logger.info(f"Normalizing snapshot for {snapshot.identity.name}")
        normalized = normalize_snapshot(snapshot)

        # Write cleaned snapshot
        clean_path = CLEAN_DIR / f"{key}.json"
        with clean_path.open("w", encoding="utf-8") as f:
            json.dump(normalized.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Wrote cleaned snapshot: {clean_path}")

        # Build and write chunks as JSONL
        chunks = build_all_chunks(normalized)
        chunks_path = CHUNKS_DIR / f"{key}_chunks.jsonl"
        with chunks_path.open("w", encoding="utf-8") as f:
            for chunk in chunks:
                json.dump(chunk.to_dict(), f, ensure_ascii=False)
                f.write("\n")
        logger.info(f"Wrote {len(chunks)} chunks: {chunks_path}")

    logger.info("Phase 2 processing completed.")


if __name__ == "__main__":
    main()

