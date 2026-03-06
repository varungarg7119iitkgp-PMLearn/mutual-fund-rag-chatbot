from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv

# Load .env from the current working directory (backend/) or its parents.
# This is robust with uvicorn's reload behaviour.
load_dotenv(override=False)


@dataclass
class Settings:
    gemini_api_key: str
    gemini_model_name: str
    gemini_embedding_model: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Read settings from environment variables (including backend/.env).

    This avoids pydantic-settings complexity and works reliably with uvicorn reload.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Ensure it is present in backend/.env or your environment."
        )

    # Default to the legacy 'gemini-pro' name used by google-generativeai 0.8.x.
    # Can be overridden in .env if needed.
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    # For the current google-generativeai client, use the legacy embeddings model name.
    # See: https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/embed_content.md
    embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")

    return Settings(
        gemini_api_key=api_key,
        gemini_model_name=model_name,
        gemini_embedding_model=embedding_model,
    )

