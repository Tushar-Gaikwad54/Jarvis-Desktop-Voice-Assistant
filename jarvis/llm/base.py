"""
Abstract Base LLM Provider Interface for J.A.R.V.I.S.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Checks whether the LLM service/model is online and reachable."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generates a text completion for a prompt."""
        raise NotImplementedError

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generates a chat completion with optional tool definitions."""
        raise NotImplementedError
