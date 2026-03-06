"""
Phase 7 — Unified data refresh pipeline.

Orchestrates the full scrape → clean → chunk → index rebuild cycle.
Can be run locally or by GitHub Actions on a schedule.

Usage:
    python scripts/refresh_pipeline.py              # full pipeline
    python scripts/refresh_pipeline.py --skip-scrape # skip Phase 1, reprocess existing raw data
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def step_scrape() -> bool:
    """Phase 1: Scrape all 20 funds using Playwright."""
    logger.info("=" * 60)
    logger.info("STEP 1/3 — Scraping fund data (Phase 1)")
    logger.info("=" * 60)
    try:
        from phase1_ingestion.src.playwright_scraper import run_scraping_session
        run_scraping_session()
        logger.info("Scraping completed successfully.")
        return True
    except Exception:
        logger.exception("Scraping failed.")
        return False


def step_process() -> bool:
    """Phase 2: Clean, normalize, and generate RAG chunks."""
    logger.info("=" * 60)
    logger.info("STEP 2/3 — Cleaning & chunking (Phase 2)")
    logger.info("=" * 60)
    try:
        from phase2_processing.src.run_phase2 import main as run_phase2
        run_phase2()
        logger.info("Phase 2 processing completed successfully.")
        return True
    except Exception:
        logger.exception("Phase 2 processing failed.")
        return False


def step_rebuild_index() -> bool:
    """Phase 3: Rebuild the TF-IDF index from Phase 2 chunks."""
    logger.info("=" * 60)
    logger.info("STEP 3/3 — Rebuilding RAG index (Phase 3)")
    logger.info("=" * 60)
    try:
        from app.rag.indexer import build_index
        build_index()
        logger.info("Index rebuild completed successfully.")
        return True
    except Exception:
        logger.exception("Index rebuild failed.")
        return False


def run_pipeline(skip_scrape: bool = False) -> bool:
    """Run the full refresh pipeline. Returns True if all steps succeeded."""
    start = time.time()
    results: dict[str, bool] = {}

    if skip_scrape:
        logger.info("Skipping scrape step (--skip-scrape flag).")
        results["scrape"] = True
    else:
        results["scrape"] = step_scrape()

    if results["scrape"]:
        results["process"] = step_process()
    else:
        logger.warning("Skipping Phase 2 because scraping failed.")
        results["process"] = False

    if results["process"]:
        results["rebuild_index"] = step_rebuild_index()
    else:
        logger.warning("Skipping index rebuild because Phase 2 failed.")
        results["rebuild_index"] = False

    elapsed = time.time() - start

    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    for step_name, success in results.items():
        status = "OK" if success else "FAILED"
        logger.info(f"  {step_name:20s} : {status}")
    logger.info(f"  Total time: {elapsed:.1f}s")

    all_ok = all(results.values())
    if all_ok:
        logger.info("All steps completed successfully.")
    else:
        logger.error("One or more steps failed. Check logs above.")
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full data refresh pipeline.")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip the Phase 1 scraping step (reprocess existing raw data only).",
    )
    args = parser.parse_args()

    success = run_pipeline(skip_scrape=args.skip_scrape)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
