"""
Base Tool Definition for J.A.R.V.I.S.
Provides standardized interface, JSON schema generation, and risk classification.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from jarvis.core.permissions import RiskLevel


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool description"
    risk_level: RiskLevel = RiskLevel.LOW

    @abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Executes the tool with the provided arguments.
        Returns a dictionary with at least 'success' (bool) and 'output' or 'error' (str).
        """
        raise NotImplementedError

    def get_schema(self) -> Dict[str, Any]:
        """
        Returns an OpenAI/Ollama compatible function/tool calling schema.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Returns JSON schema for tool parameters.
        Example:
        {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to run"}
            },
            "required": ["command"]
        }
        """
        return {"type": "object", "properties": {}}
