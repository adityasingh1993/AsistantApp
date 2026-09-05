"""
llm/router.py
LLM Router — selects the correct backend from config and builds system prompts.

System prompt strategy:
  - app_user / support_agent  →  strict no-code-exposure prompt
  - developer / super_admin   →  full technical prompt, code allowed
"""

import os
import logging
from pathlib import Path
from typing import Optional

import yaml
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from auth.rbac import RolePermissions

logger = logging.getLogger(__name__)

# ── System prompt templates ──────────────────────────────────────────────────

_SYSTEM_PROMPT_USER = """You are {app_name} Assistant, an intelligent in-app AI helper.
Your job is to guide users step-by-step through the application's features.

RULES — follow these strictly:
1. NEVER reveal, quote, paraphrase, or describe internal source code, proprietary
   algorithms, or implementation details to the user.  If asked, politely decline
   and offer to help them achieve their goal through the UI instead.
2. Base your answers on the provided knowledge-base context and conversation history.
3. When describing UI steps, use numbered lists so the overlay system can parse them.
4. Keep responses concise and friendly.
5. Current screen: {screen}. Tailor your guidance to this screen when possible.

Knowledge base context:
{kb_context}
"""

_SYSTEM_PROMPT_DEVELOPER = """You are {app_name} Assistant in DEVELOPER mode.
You have full access to technical information including source code details.

Your job is to help developers understand, debug, and extend the application.

Guidelines:
1. Provide detailed technical answers, including source code references when relevant.
2. Base your answers on the provided knowledge-base context and conversation history.
3. Be precise with file paths, class names, and function signatures.
4. Current screen / context: {screen}.

Knowledge base context:
{kb_context}
"""


class LLMRouter:
    """
    Reads appai.config.yaml and routes LLM calls to the appropriate backend.

    The config ``llm.provider`` field controls which backend is instantiated:
      - "ollama"    → OllamaBackend  (default)
      - "openai"    → OpenAIBackend
      - "anthropic" → AnthropicBackend

    Args:
        config_path: Path to appai.config.yaml.  Defaults to the file
                     sitting next to this module in ../config/.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Resolve relative to this file's location
            config_path = str(
                Path(__file__).parent.parent / "config" / "appai.config.yaml"
            )
        self._config = self._load_config(config_path)
        self._backend = None  # lazy initialisation

    # ── config ───────────────────────────────────────────────────────────────

    @staticmethod
    def _load_config(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        logger.info("LLMRouter: config loaded from %s", path)
        return cfg

    @property
    def llm_config(self) -> dict:
        return self._config.get("llm", {})

    # ── backend factory ──────────────────────────────────────────────────────

    def get_backend(self):
        """
        Return the configured LLM backend instance (created once on first call).

        Provider priority:
          config llm.provider → environment overrides (APPAI_LLM_PROVIDER)
        """
        if self._backend is not None:
            return self._backend

        provider = os.environ.get("APPAI_LLM_PROVIDER", self.llm_config.get("provider", "ollama"))
        model = self.llm_config.get("model", "qwen2.5:7b")
        temperature = float(self.llm_config.get("temperature", 0.2))
        max_tokens = int(self.llm_config.get("max_tokens", 1024))

        if provider == "ollama":
            from llm.ollama_backend import OllamaBackend
            self._backend = OllamaBackend(
                model=model,
                base_url=self.llm_config.get("base_url", "http://localhost:11434"),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        elif provider == "openai":
            from llm.openai_backend import OpenAIBackend
            self._backend = OpenAIBackend(
                model=model,
                api_key=os.environ.get("OPENAI_API_KEY", ""),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        elif provider == "anthropic":
            from llm.anthropic_backend import AnthropicBackend
            self._backend = AnthropicBackend(
                model=model,
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        elif provider == "llama_cpp":
            from llm.llama_cpp_backend import LlamaCppBackend
            # Read the llama_cpp sub-config block (all keys optional)
            lc_cfg = self.llm_config.get("llama_cpp", {})
            mode = lc_cfg.get("mode", "server")
            self._backend = LlamaCppBackend(
                mode=mode,
                # Server mode options
                server_url=lc_cfg.get("server_url", "http://localhost:8080"),
                # Embedded mode options
                model_path=lc_cfg.get("model_path"),
                n_ctx=int(lc_cfg.get("n_ctx", 4096)),
                n_threads=int(lc_cfg.get("n_threads", 8)),
                n_gpu_layers=int(lc_cfg.get("n_gpu_layers", 0)),
                chat_format=lc_cfg.get("chat_format", "chatml"),
                # Shared
                temperature=temperature,
                max_tokens=max_tokens,
            )

        else:
            raise ValueError(
                f"Unknown LLM provider: {provider!r}. "
                "Valid options: ollama | openai | anthropic | llama_cpp"
            )

        logger.info("LLMRouter: backend set to %s (mode=%s)", provider,
                    self.llm_config.get("llama_cpp", {}).get("mode", "-") if provider == "llama_cpp" else "-")
        return self._backend

    # ── generation ───────────────────────────────────────────────────────────

    async def generate(
        self,
        messages: list[dict],
        role: str,
        app_name: str = "AppAI",
        app_context: Optional[dict] = None,
        kb_context: str = "",
    ) -> str:
        """
        Build the full message list (system prompt + history + user query)
        and call the backend.

        Args:
            messages:    Conversation history list of {role, content} dicts.
                         The LAST item should be the new user query.
            role:        Platform role string (e.g. "app_user", "developer").
            app_name:    Human-readable app name for the system prompt.
            app_context: Current UI context dict (screen, idle_ms, errors).
            kb_context:  Pre-retrieved knowledge base text chunks.

        Returns:
            LLM response as a plain string.
        """
        if app_context is None:
            app_context = {}

        prompt_role = RolePermissions.get_system_prompt_role(role)
        screen = app_context.get("screen", "Unknown")

        # Select system prompt template based on role
        if prompt_role == "developer":
            system_text = _SYSTEM_PROMPT_DEVELOPER.format(
                app_name=app_name, screen=screen, kb_context=kb_context or "(none)"
            )
        else:
            system_text = _SYSTEM_PROMPT_USER.format(
                app_name=app_name, screen=screen, kb_context=kb_context or "(none)"
            )

        # Build LangChain message list
        lc_messages = [SystemMessage(content=system_text)]
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            # Ignore unknown roles silently

        backend = self.get_backend()
        response = await backend.generate(lc_messages)
        return response
