"""
llm/anthropic_backend.py
Anthropic Claude backend using LangChain ChatAnthropic.

Secondary fallback for the AppAI Hub LLM router.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnthropicBackend:
    """
    Wraps langchain_anthropic.ChatAnthropic for async text generation.

    Args:
        model:       Anthropic model, e.g. "claude-3-5-sonnet-20241022"
        api_key:     Anthropic API key (can also be set via ANTHROPIC_API_KEY env var)
        temperature: Sampling temperature
        max_tokens:  Maximum completion tokens
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        from langchain_anthropic import ChatAnthropic  # deferred import

        self._llm = ChatAnthropic(
            model=model,
            api_key=api_key or None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info("AnthropicBackend initialised: model=%s", model)

    async def generate(self, messages: list[Any]) -> str:
        """
        Invoke Anthropic Claude with a list of LangChain message objects.

        Returns the response content as a plain string.
        """
        try:
            response = await self._llm.ainvoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            logger.error("AnthropicBackend.generate error: %s", exc, exc_info=True)
            return (
                "Anthropic API request failed. "
                "Please check your API key and network connection."
            )
