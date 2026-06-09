"""Shared LLM factory for all agents.

Supports two modes:
1. Ollama (local) — respects LLM_PROVIDER=ollama even for tool calling
2. OpenRouter — for tasks requiring tool calling (LLM_PROVIDER=openrouter or unset)

Call `get_llm(tools=True)` when the LLM needs tool/function calling.
"""

import os
import logging

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)


def get_llm(tools: bool = False) -> ChatOpenAI | ChatOllama:
    """Return an LLM instance.

    Args:
        tools: Set to True when the LLM needs tool calling support.
              Behaviour depends on LLM_PROVIDER env var:
              - "ollama" → uses local Ollama (supports tool calling natively on recent models)
              - "openrouter" or unset → uses OpenRouter
    """

    provider = os.getenv("LLM_PROVIDER", "openrouter").lower().strip()

    # --- OpenRouter path ---
    if provider == "openrouter":
        model = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            logger.info("Using OpenRouter: model=%s", model)
            return ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
            )
        logger.warning("OPENROUTER_API_KEY not set, falling back to Ollama")

    # --- Ollama (local) ---
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    logger.info("Using Ollama: model=%s base_url=%s", model, base_url)
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
    )
