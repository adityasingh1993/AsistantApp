"""
llm/ollama_backend.py
Ollama LLM backend using LangChain ChatOllama.

This is the primary LLM backend for AppAI Hub (Qwen 2.5 7B by default).
Falls back gracefully with a human-readable error if Ollama is unreachable.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OllamaBackend:
    """
    Wraps langchain_ollama.ChatOllama for async text generation.

    Args:
        model:       Ollama model tag, e.g. "qwen2.5:7b"
        base_url:    Ollama API base URL, e.g. "http://localhost:11434"
        temperature: Sampling temperature (0.0 – 1.0)
        max_tokens:  Maximum tokens in the completion
    """

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        from langchain_ollama import ChatOllama  # deferred import for startup speed

        self.model = model
        self._llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            num_predict=max_tokens,
        )
        logger.info("OllamaBackend initialised: model=%s base_url=%s", model, base_url)

    async def generate(self, messages: list[Any]) -> str:
        """
        Invoke the Ollama model with a list of LangChain message objects.

        Args:
            messages: list of HumanMessage / SystemMessage / AIMessage instances

        Returns:
            The model's reply as a plain string.

        Raises:
            Returns an error string on connection failure instead of raising,
            so the WebSocket handler can surface a friendly message to the user.
        """
        try:
            response = await self._llm.ainvoke(messages)
            # ChatOllama returns an AIMessage; extract its text content.
            return response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            logger.error("OllamaBackend.generate error: %s", exc, exc_info=True)
            return (
                "I'm having trouble connecting to the local AI model right now. "
                "Please ensure Ollama is running and try again."
            )
