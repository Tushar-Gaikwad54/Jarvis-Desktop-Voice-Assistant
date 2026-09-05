"""
Ollama Service & Background Daemon Manager for J.A.R.V.I.S.
Automatically detects, launches, and monitors the local Ollama LLM server.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

from jarvis.config import get_config
from jarvis.core.logger import logger


class OllamaService:
    def __init__(self):
        self.config = get_config()
        self.base_url = self.config.llm.ollama_url.rstrip("/")
        self._process: Optional[subprocess.Popen] = None

    def find_ollama_binary(self) -> Optional[str]:
        """Locates the Ollama executable on the system."""
        # 1. Check PATH
        path_binary = shutil.which("ollama")
        if path_binary and os.path.isfile(path_binary):
            return path_binary

        # 2. Common Windows paths
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
            r"C:\Program Files\Ollama\ollama.exe",
            r"C:\Program Files (x86)\Ollama\ollama.exe",
        ]

        for cand in candidates:
            if os.path.isfile(cand):
                return cand

        return None

    def is_running(self) -> bool:
        """Checks if the local Ollama API is responding."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_installed_models(self) -> List[str]:
        """Returns the list of installed Ollama models."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Checks if the specified model is installed locally in Ollama."""
        target_model = (model_name or self.config.llm.model).lower()
        installed = [m.lower() for m in self.get_installed_models()]
        return any(
            target_model == m or target_model == m.split(":")[0] or target_model in m
            for m in installed
        )

    def start_service(
        self,
        timeout_seconds: int = 12,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Starts Ollama in the background silently if not already running.
        Returns (success: bool, message: str).
        """
        if self.is_running():
            logger.info("Ollama is already running and operational.")
            if progress_callback:
                progress_callback("Ollama server is active and responsive.", 100)
            return True, "Ollama is already running."

        binary = self.find_ollama_binary()
        if not binary:
            logger.warning("Ollama executable was not found on the system.")
            return False, "Ollama executable not found. Please install Ollama from https://ollama.com."

        logger.info(f"Launching Ollama background daemon from: {binary}")
        if progress_callback:
            progress_callback("Initializing Ollama background server daemon...", 30)

        # On Windows, use PowerShell Start-Process with Hidden window or subprocess detached
        try:
            if sys.platform == "win32":
                ps_cmd = f"Start-Process -FilePath '{binary}' -ArgumentList 'serve' -WindowStyle Hidden"
                subprocess.Popen(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                self._process = subprocess.Popen(
                    [binary, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
        except Exception as e:
            logger.error(f"Failed to launch Ollama process: {e}")
            return False, f"Failed to start Ollama: {e}"

        # Poll until API is responsive
        start_time = time.time()
        poll_interval = 0.4
        while time.time() - start_time < timeout_seconds:
            elapsed = time.time() - start_time
            progress = min(90, int(30 + (elapsed / timeout_seconds) * 60))
            if progress_callback:
                progress_callback(f"Connecting to Ollama core ({elapsed:.1f}s)...", progress)

            if self.is_running():
                logger.info(f"Ollama server connected in {elapsed:.2f}s.")
                if progress_callback:
                    progress_callback("Ollama neural engine is online.", 100)
                return True, "Ollama server started successfully."
            time.sleep(poll_interval)

        if self.is_running():
            return True, "Ollama server started successfully."

        return False, f"Ollama started but failed to respond within {timeout_seconds} seconds."

    def ensure_running(
        self,
        timeout_seconds: int = 12,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Tuple[bool, str]:
        """Convenience method to check and launch Ollama if needed."""
        if self.is_running():
            return True, "Ollama is online."
        return self.start_service(timeout_seconds=timeout_seconds, progress_callback=progress_callback)


# Global singleton instance
ollama_service = OllamaService()
