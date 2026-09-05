"""
Session Context and State Manager for J.A.R.V.I.S.
Manages multi-turn conversation history, persona prompting, workspace state, and tool outputs.
Optimized for rapid LLM inference and minimal context latency.
"""

from dataclasses import dataclass, field
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from jarvis.config import get_config


@dataclass
class Message:
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


class SessionContext:
    def __init__(self, workspace_dir: Optional[str] = None):
        config = get_config()
        self.workspace_dir = Path(workspace_dir or config.workspace_dir).resolve()
        self.messages: List[Message] = []
        self.scratchpad: Dict[str, Any] = {}
        self.system_prompt: str = self._build_default_system_prompt()
        self._init_history()

    def _build_default_system_prompt(self) -> str:
        config = get_config()
        return (
            f"You are {config.name} (Just A Rather Very Intelligent System), the loyal, brilliant, polite, and sophisticated "
            f"personal AI computer assistant and coding agent for {config.user_name}.\n\n"
            f"Key Persona & Behavioral Guidelines:\n"
            f"1. Tone: Eloquent, respectful, attentive, confident, and articulate (like Tony Stark's AI assistant J.A.R.V.I.S.).\n"
            f"2. Natural Voice Communication: Your responses will be spoken aloud to {config.user_name}. "
            f"Be concise, swift, and decisive (1 to 3 sentences for spoken answers unless detailed technical explanation is specifically requested). "
            f"Avoid markdown symbols, unnecessary formatting, or giant lists in speech.\n"
            f"3. Active Computer Control: Only invoke tools when {config.user_name} explicitly requests a computer action (such as opening an application, opening a website or URL in the browser, taking a screenshot, checking hardware specs, or running a shell command). Acknowledge actions with a polite remark.\n"
            f"4. Conversational Intelligence & Reasoning: For general knowledge, explanations, coding questions, science, advice, or chat, reason thoughtfully and answer directly using your own knowledge without invoking tools.\n"
            f"5. Current Working Directory: {self.workspace_dir}."
        )

    def _init_history(self) -> None:
        self.messages.clear()
        self.messages.append(Message(role="system", content=self.system_prompt))

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))

    def add_tool_message(self, content: str, tool_call_id: Optional[str] = None) -> None:
        self.messages.append(Message(role="tool", content=content, tool_call_id=tool_call_id))

    def clear(self) -> None:
        self._init_history()
        self.scratchpad.clear()

    def get_messages_for_llm(self, max_recent_messages: int = 8) -> List[Dict[str, Any]]:
        """
        Returns a pruned, token-efficient list of messages for fast LLM inference.
        Preserves the system prompt and the most recent conversation turns,
        capping large tool payloads to prevent prompt bloating.
        """
        if not self.messages:
            return [{"role": "system", "content": self.system_prompt}]

        system_msg = self.messages[0]
        recent = self.messages[1:]
        if len(recent) > max_recent_messages:
            recent = recent[-max_recent_messages:]

        result = [{"role": system_msg.role, "content": system_msg.content}]
        for msg in recent:
            content = msg.content or ""
            # Cap very large tool output in conversation history to 400 chars for rapid inference
            if msg.role == "tool" and len(content) > 400:
                content = content[:400] + "... [truncated]"

            entry = {"role": msg.role, "content": content}
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            result.append(entry)

        return result
