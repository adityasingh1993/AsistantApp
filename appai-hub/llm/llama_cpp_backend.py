"""
llm/llama_cpp_backend.py
llama.cpp backend for AppAI Hub.

Supports two modes controlled by ``llama_cpp.mode`` in appai.config.yaml:

  server   — Connects to a running ``llama-server`` process via its
              OpenAI-compatible REST API (recommended for production).
              The server can be on the same machine or a remote GPU box.

  embedded — Loads a .gguf model file directly in-process via the
             ``llama-cpp-python`` package (good for single-user dev).
             Inference runs in a thread-pool executor so it does not
             block the FastAPI event loop.

Server mode setup
-----------------
Download a pre-built llama-server binary from:
  https://github.com/ggerganov/llama.cpp/releases

Then run (example with Qwen 2.5 7B Q4):
  llama-server -m qwen2.5-7b-instruct-q4_k_m.gguf --port 8080 --ctx-size 4096

Or build from source:
  git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp
  cmake -B build && cmake --build build --config Release -j
  .\\build\\bin\\Release\\llama-server.exe -m path\\to\\model.gguf --port 8080

Embedded mode setup
-------------------
pip install llama-cpp-python

  # CPU only (default):
  pip install llama-cpp-python

  # With CUDA GPU acceleration:
  CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall

Download .gguf models from HuggingFace, e.g.:
  https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

Config example (appai.config.yaml)
-----------------------------------
# Server mode (recommended):
llm:
  provider: llama_cpp
  llama_cpp:
    mode: server
    server_url: http://localhost:8080
  temperature: 0.2
  max_tokens: 1024

# Embedded mode:
llm:
  provider: llama_cpp
  llama_cpp:
    mode: embedded
    model_path: C:/models/qwen2.5-7b-instruct-q4_k_m.gguf
    n_ctx: 4096
    n_threads: 8
    n_gpu_layers: 0      # set >0 to offload layers to GPU
    chat_format: chatml  # chatml | llama-2 | mistral-instruct | gemma
  temperature: 0.2
  max_tokens: 1024
"""

import asyncio
import logging
from typing import Optional

import httpx
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

logger = logging.getLogger(__name__)


def _lc_to_dict(messages: list[BaseMessage]) -> list[dict]:
    """Convert a list of LangChain message objects to plain dicts."""
    result = []
    for m in messages:
        if isinstance(m, SystemMessage):
            result.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            result.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            result.append({"role": "assistant", "content": m.content})
        # Unknown message types are silently skipped
    return result


# ── Server mode ───────────────────────────────────────────────────────────────

class _LlamaCppServerBackend:
    """
    Calls a running ``llama-server`` process via the OpenAI-compatible
    ``/v1/chat/completions`` endpoint using an async httpx client.

    No Python packages beyond httpx are required (already a Hub dependency).
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8080",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: float = 120.0,
    ):
        self.server_url = server_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        logger.info(
            "LlamaCppServerBackend: server_url=%s  temperature=%.2f  max_tokens=%d",
            self.server_url, self.temperature, self.max_tokens,
        )

    async def generate(self, messages: list[BaseMessage]) -> str:
        """Send chat messages to llama-server and return the reply text."""
        payload = {
            "messages": _lc_to_dict(messages),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.server_url}/v1/chat/completions",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

        except httpx.ConnectError:
            err = (
                f"Cannot connect to llama-server at {self.server_url}. "
                "Make sure llama-server is running. "
                "Start it with: llama-server -m your_model.gguf --port 8080"
            )
            logger.error(err)
            raise RuntimeError(err)

        except httpx.HTTPStatusError as exc:
            logger.error("llama-server HTTP error: %s", exc.response.text)
            raise


# ── Embedded mode ─────────────────────────────────────────────────────────────

class _LlamaCppEmbeddedBackend:
    """
    Loads a .gguf model directly in-process via ``llama-cpp-python``.

    Inference is dispatched to a thread-pool executor so it never blocks
    the FastAPI async event loop.

    Install:
        pip install llama-cpp-python
        # With CUDA:
        CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall
    """

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: int = 8,
        n_gpu_layers: int = 0,
        chat_format: str = "chatml",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        self.temperature = temperature
        self.max_tokens = max_tokens

        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Run: pip install llama-cpp-python\n"
                "For GPU support: "
                "CMAKE_ARGS=\"-DGGML_CUDA=on\" pip install llama-cpp-python --force-reinstall"
            ) from exc

        logger.info(
            "LlamaCppEmbeddedBackend: loading model %s  n_ctx=%d  n_threads=%d  n_gpu_layers=%d",
            model_path, n_ctx, n_threads, n_gpu_layers,
        )
        self._llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            chat_format=chat_format,
            verbose=False,
        )
        logger.info("LlamaCppEmbeddedBackend: model loaded successfully")

    def _sync_generate(self, messages_dict: list[dict]) -> str:
        """Synchronous inference call — run this in a thread executor."""
        response = self._llm.create_chat_completion(
            messages=messages_dict,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response["choices"][0]["message"]["content"]

    async def generate(self, messages: list[BaseMessage]) -> str:
        """Dispatch synchronous llama.cpp inference to a thread-pool executor."""
        messages_dict = _lc_to_dict(messages)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._sync_generate, messages_dict)
            return result
        except Exception as exc:
            logger.error("LlamaCppEmbeddedBackend inference error: %s", exc)
            raise


# ── Public factory ─────────────────────────────────────────────────────────────

class LlamaCppBackend:
    """
    Public facade that delegates to either the server or embedded backend
    based on the ``mode`` config key.

    Args:
        mode:        ``"server"`` (default) or ``"embedded"``
        server_url:  llama-server base URL (server mode only)
        model_path:  Path to .gguf model file (embedded mode only)
        n_ctx:       Context window size (embedded mode only)
        n_threads:   CPU threads to use (embedded mode only)
        n_gpu_layers: GPU layers to offload; 0 = CPU only (embedded mode only)
        chat_format: Model chat template name (embedded mode only)
        temperature: Sampling temperature
        max_tokens:  Max tokens to generate
    """

    def __init__(
        self,
        mode: str = "server",
        server_url: str = "http://localhost:8080",
        model_path: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: int = 8,
        n_gpu_layers: int = 0,
        chat_format: str = "chatml",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        self.mode = mode

        if mode == "server":
            self._impl = _LlamaCppServerBackend(
                server_url=server_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif mode == "embedded":
            if not model_path:
                raise ValueError(
                    "llama_cpp embedded mode requires 'model_path' in config. "
                    "Set llm.llama_cpp.model_path to your .gguf file path."
                )
            self._impl = _LlamaCppEmbeddedBackend(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                chat_format=chat_format,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(
                f"Unknown llama_cpp mode: {mode!r}. Use 'server' or 'embedded'."
            )

        logger.info("LlamaCppBackend: mode=%s initialised", mode)

    async def generate(self, messages: list[BaseMessage]) -> str:
        """Route generation to the active backend implementation."""
        return await self._impl.generate(messages)
