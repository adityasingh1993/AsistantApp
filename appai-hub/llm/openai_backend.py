"""
llm/openai_backend.py
OpenAI LLM backend using LangChain ChatOpenAI.

Used as a fallback when Ollama is unavailable or for higher-accuracy tasks.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OpenAIBackend:
    """
    Wraps langchain_openai.ChatOpenAI for async text generation.

    Args:
        model:       OpenAI model name, e.g. "gpt-4o"
        api_key:     OpenAI API key (can also be set via OPENAI_API_KEY env var)
        temperature: Sampling temperature
        max_tokens:  Maximum completion tokens
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        from langchain_openai import ChatOpenAI  # deferred import

        self._llm = ChatOpenAI(
            model=model,
            api_key=api_key or None,  # None → reads OPENAI_API_KEY env var
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info("OpenAIBackend initialised: model=%s", model)

    async def generate(self, messages: list[Any]) -> str:
        """
        Invoke OpenAI with a list of LangChain message objects.

        Returns the response content as a plain string.
        """
        try:
            response = await self._llm.ainvoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            logger.error("OpenAIBackend.generate error: %s", exc, exc_info=True)
            return (
                "OpenAI API request failed. "
                "Please check your API key and network connection."
            )
