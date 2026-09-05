"""
Zero-Dependency Deterministic Fallback Engine for J.A.R.V.I.S.
Guarantees immediate offline operation even without a local neural model running.
"""

import datetime
import re
from typing import Any, Dict, List, Optional
from jarvis.config import get_config
from jarvis.llm.base import BaseLLMProvider, LLMResponse


class RuleFallbackProvider(BaseLLMProvider):
    """
    Built-in pattern and intent matcher that routes common system, diagnostic,
    and computer control tasks directly to the tool registry when offline.
    """

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def match_intent(self, user_msg: str) -> Optional[LLMResponse]:
        """
        Fast pattern matcher with strict word-boundary matching.
        """
        if not user_msg:
            return None

        query = user_msg.lower().strip()
        config = get_config()

        # 0. Stop Listening / Pause Intent
        if re.search(r"\b(stop listening|pause listening|mute mic|go to sleep|sleep mode|standby)\b", query):
            return LLMResponse(
                content=f"Paused listening mode. Press 1 and Enter whenever you need me, {config.user_name}."
            )

        # 1. Opening Screenshot
        if re.search(r"\b(open|show|view|display|see)\b.*\bscreenshot\b", query):
            return LLMResponse(
                content="Certainly! Opening screenshot now.",
                tool_calls=[{"name": "open_item", "arguments": {"target": "screenshot"}}],
            )

        # 2. Taking a Screenshot
        if re.search(r"\b(take|capture)\b.*\bscreenshot\b|\bcapture screen\b", query):
            return LLMResponse(
                content="Capturing your screen right away, sir.",
                tool_calls=[{"name": "take_screenshot", "arguments": {}}],
            )

        # 3. Opening Standard Folders
        folders = ["downloads", "pictures", "documents", "desktop", "music", "videos", "workspace"]
        for folder in folders:
            if re.search(rf"\b(open|show|explore)\b.*?\b{folder}\b", query):
                return LLMResponse(
                    content=f"Certainly! Opening your {folder} folder now, {config.user_name}.",
                    tool_calls=[{"name": "open_item", "arguments": {"target": folder}}],
                )

        # 4. Opening Standard Apps
        apps = ["notepad", "calculator", "calc", "vs code", "vscode", "paint", "task manager", "taskmgr", "cmd", "powershell", "spotify"]
        for app in apps:
            if re.search(rf"\b(open|launch|start)\b.*?\b{app}\b", query):
                return LLMResponse(
                    content=f"Certainly! Opening {app} now, {config.user_name}.",
                    tool_calls=[{"name": "open_item", "arguments": {"target": app}}],
                )

        # 5. Opening Websites / Browser
        sites = {
            "instagram": "https://www.instagram.com",
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "github": "https://www.github.com",
            "chatgpt": "https://chatgpt.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "netflix": "https://www.netflix.com",
            "gmail": "https://mail.google.com",
            "linkedin": "https://www.linkedin.com",
            "facebook": "https://www.facebook.com",
            "amazon": "https://www.amazon.com",
        }

        for site_key, site_url in sites.items():
            if re.search(rf"\b(open|launch|browse|go to)\b.*?\b{site_key}\b", query):
                return LLMResponse(
                    content=f"Certainly! Opening {site_key.capitalize()} in your browser now, {config.user_name}.",
                    tool_calls=[{"name": "open_browser", "arguments": {"url": site_url}}],
                )

        # Generic URL detection
        url_match = re.search(r"https?://\S+|www\.\S+|[\w\-]+\.(?:com|org|net|io|edu|gov)\b", query)
        if url_match and re.search(r"\b(open|browse|go to)\b", query):
            url = url_match.group(0)
            return LLMResponse(
                content=f"Certainly! Opening {url} in your browser now.",
                tool_calls=[{"name": "open_browser", "arguments": {"url": url}}],
            )

        # 6. System Info / Hardware (Strict Word Boundaries to avoid 'instagram' containing 'ram')
        if re.search(r"\b(system info|system specs?|hardware specs?|cpu usage|disk space|hardware specifications)\b", query) or re.search(r"\b(check|show|get|what are)\b.*?\b(specs|system specs|ram info|cpu info)\b", query):
            return LLMResponse(
                content="Checking your system hardware and specifications, sir.",
                tool_calls=[{"name": "get_system_info", "arguments": {}}],
            )

        # 7. Diagnostics (e.g. winget, python, git)
        diag_match = re.search(r"\bdiagnose\s+([a-zA-Z0-9_\-\.]+)", query)
        if diag_match:
            cmd_target = diag_match.group(1)
            return LLMResponse(
                content=f"Investigating and diagnosing '{cmd_target}' on your system.",
                tool_calls=[{"name": "diagnose_command", "arguments": {"command_name": cmd_target}}],
            )

        # 8. Directory listing / File listing
        if re.search(r"\b(list files|show files|list directory|dir|ls)\b", query):
            return LLMResponse(
                content="Listing the contents of your active workspace directory.",
                tool_calls=[{"name": "list_directory", "arguments": {}}],
            )

        # 9. Joke
        if re.search(r"\b(tell me a joke|tell a joke|crack a joke|joke)\b", query):
            return LLMResponse(
                content="Here is something to lighten the mood, sir:",
                tool_calls=[{"name": "tell_joke", "arguments": {}}],
            )

        # 10. Time / Date
        if re.search(r"\b(what time is it|current time|what is the time|tell me the time)\b", query):
            now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
            return LLMResponse(content=f"The current time is {now_str}, {config.user_name}.")

        if re.search(r"\b(what is today'?s? date|current date|what date is it|what is the date)\b", query):
            now = datetime.datetime.now()
            return LLMResponse(content=f"Today is {now.strftime('%A, %B %d, %Y')}, {config.user_name}.")

        return None

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "").strip()
                break

        matched = self.match_intent(user_msg)
        if matched:
            return matched

        config = get_config()
        return LLMResponse(
            content=(
                f"I heard you, {config.user_name}. I can open files, folders, websites, apps, screenshots, check system specs, and diagnose issues.\n"
                f"💡 Tip: To enable full open-ended neural reasoning, connect Ollama (ollama.com) with llama3.2."
            )
        )
