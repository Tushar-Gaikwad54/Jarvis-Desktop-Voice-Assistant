"""
Core Orchestration Engine for J.A.R.V.I.S.
Coordinates neural LLM reasoning, intelligent intent classification, tool execution, and verbal synthesis.
"""

import re
from typing import Any, Dict, List, Optional
from jarvis.config import get_config
from jarvis.core.context import SessionContext
from jarvis.core.logger import logger
from jarvis.core.permissions import permission_manager
from jarvis.llm.base import BaseLLMProvider, LLMResponse
from jarvis.llm.factory import LLMFactory
from jarvis.llm.rule_fallback import RuleFallbackProvider
from jarvis.tools.registry import tool_registry


class JarvisEngine:
    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        context: Optional[SessionContext] = None,
    ):
        self.config = get_config()
        self.context = context or SessionContext()
        self.provider = provider or LLMFactory.create_provider()
        self.fallback_provider = RuleFallbackProvider()
        self.tools = tool_registry

    def set_provider(self, provider: BaseLLMProvider) -> None:
        self.provider = provider

    def reload_provider(self, provider_name: str) -> None:
        self.provider = LLMFactory.create_provider(provider_name)

    def _is_reasoning_query(self, query: str) -> bool:
        """
        Determines whether the query is primarily an informational, educational,
        reasoning, coding, or conversational question rather than a direct computer tool action.
        """
        q = query.lower().strip()

        # Explicit computer action triggers
        action_keywords = [
            r"\bopen\b", r"\blaunch\b", r"\bstart\b", r"\bbrowse\b", r"\bgo to\b",
            r"\bscreenshot\b", r"\bcapture screen\b", r"\btake screenshot\b",
            r"\bsystem specs?\b", r"\bhardware specs?\b", r"\bdiagnose\b",
            r"\brun command\b", r"\bexecute command\b", r"\blist files\b", r"\bshow files\b",
            r"\bdir\b", r"\bdelete\b", r"\btell me a joke\b", r"\btell a joke\b"
        ]
        if any(re.search(pat, q) for pat in action_keywords):
            return False

        # Informational / reasoning patterns
        reasoning_patterns = [
            r"^(what|who|why|where|how|when)\b",
            r"^(explain|describe|tell me about|summarize|define|translate|write|generate|compose|solve|help)\b",
            r"\b(meaning of|difference between|how do i|how does|why does|what is)\b",
            r"\b(code|script|function|program|algorithm)\b",
            r"^(hi|hello|hey|good morning|good evening|good afternoon)\b"
        ]
        return any(re.search(pat, q) for pat in reasoning_patterns)

    def process_query(self, user_input: str, max_iterations: int = 3) -> str:
        """
        Processes a user input string through intelligent neural reasoning and action execution:
        User Input -> Neural Cognitive Reasoning -> Tool Execution -> Spoken Conclusion
        """
        if not user_input or not user_input.strip():
            return f"How may I assist you, {self.config.user_name}?"

        clean_input = user_input.strip()

        # 1. Add user message to conversation history
        self.context.add_user_message(clean_input)

        # Determine active provider: use neural model if reachable, else fallback
        active_provider = self.provider
        if not active_provider.is_available():
            logger.warn("[ENGINE] Primary neural provider offline. Using fallback rule matcher.")
            active_provider = self.fallback_provider

        # Classify if tools should be attached
        is_pure_reasoning = self._is_reasoning_query(clean_input)
        tool_schemas = None if is_pure_reasoning else self.tools.get_all_schemas()

        iteration = 0
        final_text = ""

        while iteration < max_iterations:
            iteration += 1

            # 2. Get pruned context window
            messages = self.context.get_messages_for_llm(max_recent_messages=6)

            # 3. Call active provider for cognitive reasoning and tool selection
            try:
                response: LLMResponse = active_provider.chat(messages=messages, tools=tool_schemas)
            except Exception as e:
                logger.error(f"[ENGINE] Primary LLM failed ({e}). Attempting fallback engine...")
                try:
                    response = self.fallback_provider.chat(messages=messages, tools=self.tools.get_all_schemas())
                except Exception as fallback_err:
                    return f"An error occurred while consulting my cognitive core: {fallback_err}"

            # 4. If no tool calls, return text reasoning directly
            if not response.tool_calls:
                final_text = response.content
                self.context.add_assistant_message(final_text)
                break

            # 5. Record assistant decision with tool calls in history
            self.context.add_assistant_message(
                content=response.content or "Executing requested actions...",
                tool_calls=response.tool_calls,
            )

            if response.content:
                logger.info(response.content)

            # 6. Execute selected tools
            tool_outputs = []
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                args = tool_call.get("arguments", {})

                logger.info(f"[ACTION] Invoking tool '{tool_name}' with args: {args}")
                tool_result = self.tools.execute_tool(tool_name, args)
                tool_output_str = str(tool_result.get("output", tool_result.get("error", "Action completed.")))

                self.context.add_tool_message(
                    content=tool_output_str,
                    tool_call_id=tool_name,
                )
                tool_outputs.append(tool_output_str)

            # 7. Format clean conversational acknowledgement
            executed_tools = [tc.get("name") for tc in response.tool_calls]

            # Browser actions
            if "open_browser" in executed_tools:
                url_arg = response.tool_calls[0].get("arguments", {}).get("url", "")
                final_text = response.content or f"Certainly! Opening {url_arg} in your browser now, {self.config.user_name}."
                break

            # Application & File opening
            if "open_item" in executed_tools:
                target_arg = response.tool_calls[0].get("arguments", {}).get("target", "")
                final_text = response.content or f"Certainly! Opening {target_arg} now, {self.config.user_name}."
                break

            # Screen Capture
            if "take_screenshot" in executed_tools:
                final_text = response.content or f"Capturing your screen right away, {self.config.user_name}."
                break

            # Jokes
            if "tell_joke" in executed_tools:
                final_text = tool_outputs[0] if tool_outputs else "Why do programmers prefer dark mode? Because light attracts bugs!"
                break

            # If response had commentary and was not an info dump tool
            if response.content and not any(t in ["get_system_info", "diagnose_command", "list_directory"] for t in executed_tools):
                final_text = response.content
                break

            combined_output = "\n\n".join(tool_outputs)
            final_text = combined_output if not response.content else f"{response.content}\n\n{combined_output}"
            break

        return final_text
