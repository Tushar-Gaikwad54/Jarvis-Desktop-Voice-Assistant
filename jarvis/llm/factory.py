"""
LLM Factory and Auto-Detector for J.A.R.V.I.S.
"""

from typing import Optional
from jarvis.config import get_config
from jarvis.core.logger import logger
from jarvis.llm.base import BaseLLMProvider
from jarvis.llm.ollama_provider import OllamaProvider
from jarvis.llm.openai_compat import OpenAICompatibleProvider
from jarvis.llm.rule_fallback import RuleFallbackProvider


class LLMFactory:
    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
        config = get_config()
        name = (provider_name or config.llm.provider).lower()

        if name == "ollama":
            prov = OllamaProvider()
            if prov.is_available():
                logger.info(f"Connected to local Ollama server (Model: {prov.model})")
                return prov
            else:
                logger.warn("Ollama server not reachable at configured URL. Falling back to Rule Engine.")
                return RuleFallbackProvider()

        elif name in ["openai_compatible", "lm_studio", "localai", "vllm"]:
            prov = OpenAICompatibleProvider()
            if prov.is_available():
                logger.info(f"Connected to local OpenAI-compatible endpoint ({prov.base_url})")
                return prov
            else:
                logger.warn(f"Local server not reachable at {prov.base_url}. Falling back to Rule Engine.")
                return RuleFallbackProvider()

        elif name == "fallback":
            return RuleFallbackProvider()

        else:
            logger.warn(f"Unknown LLM provider '{name}'. Defaulting to fallback rule engine.")
            return RuleFallbackProvider()

    @staticmethod
    def auto_detect() -> BaseLLMProvider:
        """Attempts to auto-detect any active local LLM backend before defaulting to fallback."""
        # Check Ollama
        ollama = OllamaProvider()
        if ollama.is_available():
            logger.info("Auto-detected active local Ollama service!")
            return ollama

        # Check LM Studio / Local endpoint
        lm_studio = OpenAICompatibleProvider()
        if lm_studio.is_available():
            logger.info("Auto-detected active local LM Studio / OpenAI-compatible endpoint!")
            return lm_studio

        # Default
        return RuleFallbackProvider()
