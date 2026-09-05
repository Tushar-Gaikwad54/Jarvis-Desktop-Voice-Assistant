"""
Native Local Ollama Provider for J.A.R.V.I.S.
Works offline using local models (Llama 3, Mistral, Qwen 2.5 Coder, Phi-3, etc.).
"""

import json
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request
from jarvis.config import get_config
from jarvis.core.exceptions import LLMProviderError
from jarvis.core.logger import logger
from jarvis.llm.base import BaseLLMProvider, LLMResponse


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        config = get_config()
        self.base_url = (base_url or config.llm.ollama_url).rstrip("/")
        self.model = model or config.llm.model
        self.timeout = config.llm.timeout_seconds

    def is_available(self) -> bool:
        """Checks if local Ollama server is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_installed_models(self) -> List[str]:
        """Returns names of all locally installed models in Ollama."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        return self._send_request(f"{self.base_url}/api/generate", payload)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        config = get_config()
        options: Dict[str, Any] = {
            "temperature": config.llm.temperature,
            "num_predict": min(config.llm.max_tokens or 256, 300),
            "num_ctx": 2048,
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if tools:
            payload["tools"] = tools

        return self._send_request(f"{self.base_url}/api/chat", payload)

    def _send_request(self, endpoint: str, payload: Dict[str, Any]) -> LLMResponse:
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))

            if "message" in raw:
                # Chat endpoint response
                msg = raw["message"]
                content = msg.get("content", "")
                raw_tool_calls = msg.get("tool_calls")
                tool_calls = None
                if raw_tool_calls:
                    tool_calls = []
                    for tc in raw_tool_calls:
                        func = tc.get("function", {})
                        tool_calls.append({
                            "name": func.get("name"),
                            "arguments": func.get("arguments", {}),
                        })

                return LLMResponse(
                    content=content,
                    tool_calls=tool_calls,
                    finish_reason=raw.get("done_reason", "stop"),
                    raw_response=raw,
                )
            else:
                # Generate endpoint response
                return LLMResponse(
                    content=raw.get("response", ""),
                    finish_reason="stop",
                    raw_response=raw,
                )

        except urllib.error.URLError as e:
            raise LLMProviderError("Ollama", f"Cannot connect to Ollama at {self.base_url}. Is Ollama running? ({e})")
        except Exception as e:
            raise LLMProviderError("Ollama", f"Request failed: {str(e)}")
