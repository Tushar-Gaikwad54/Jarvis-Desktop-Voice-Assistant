"""
OpenAI-Compatible Local Endpoint Provider for J.A.R.V.I.S.
Works with LM Studio, LocalAI, Jan, text-generation-webui, and vLLM.
"""

import json
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request
from jarvis.config import get_config
from jarvis.core.exceptions import LLMProviderError
from jarvis.llm.base import BaseLLMProvider, LLMResponse


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = None, api_key: str = None):
        config = get_config()
        self.base_url = (base_url or config.llm.openai_compat_url).rstrip("/")
        self.model = model or config.llm.model
        self.api_key = api_key or config.llm.openai_compat_api_key
        self.timeout = config.llm.timeout_seconds

    def is_available(self) -> bool:
        """Checks if local server is running by pinging /models."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))

            choices = raw.get("choices", [])
            if not choices:
                return LLMResponse(content="No response received from local server.", raw_response=raw)

            msg = choices[0].get("message", {})
            content = msg.get("content") or ""
            raw_tool_calls = msg.get("tool_calls")
            tool_calls = None

            if raw_tool_calls:
                tool_calls = []
                for tc in raw_tool_calls:
                    func = tc.get("function", {})
                    fn_name = func.get("name")
                    fn_args = func.get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except Exception:
                            fn_args = {"raw": fn_args}
                    tool_calls.append({"name": fn_name, "arguments": fn_args})

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=choices[0].get("finish_reason", "stop"),
                raw_response=raw,
            )

        except urllib.error.URLError as e:
            raise LLMProviderError("OpenAI-Compatible", f"Cannot connect to {self.base_url}: {e}")
        except Exception as e:
            raise LLMProviderError("OpenAI-Compatible", f"Request failed: {str(e)}")
