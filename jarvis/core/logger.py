"""
Structured Logging and Audit System for J.A.R.V.I.S.
Provides clean terminal output with color-coding, Windows cp1252 safety, and persistent audit logs.
"""

import datetime
import logging
import os
from pathlib import Path
import sys
from typing import Optional

# Reconfigure stdout/stderr for Unicode safety on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def safe_print(text: str) -> None:
    """Safely prints text handling legacy terminal encodings without crashing."""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            encoding = getattr(sys.stdout, "encoding", "ascii") or "ascii"
            encoded = text.encode(encoding, errors="replace").decode(encoding)
            print(encoded)
        except Exception:
            print(text.encode("ascii", errors="replace").decode("ascii"))


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground colors
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"


class JarvisLogger:
    def __init__(self, name: str = "JARVIS", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session log file
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"jarvis_{today}.log"
        
        # Setup file logger
        self._file_logger = logging.getLogger(f"jarvis_file_{name}")
        self._file_logger.setLevel(logging.DEBUG)
        if not self._file_logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self._file_logger.addHandler(handler)

    def info(self, msg: str) -> None:
        self._file_logger.info(msg)
        safe_print(f"{Colors.CYAN}[INFO]{Colors.RESET} {msg}")

    def success(self, msg: str) -> None:
        self._file_logger.info(f"SUCCESS: {msg}")
        safe_print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {msg}")

    def warn(self, msg: str) -> None:
        self._file_logger.warning(msg)
        safe_print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {msg}")

    def error(self, msg: str) -> None:
        self._file_logger.error(msg)
        safe_print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")

    def tool(self, tool_name: str, action: str, details: Optional[str] = None) -> None:
        log_msg = f"TOOL [{tool_name}] -> {action}" + (f" ({details})" if details else "")
        self._file_logger.info(log_msg)
        safe_print(f"{Colors.MAGENTA}[TOOL]{Colors.RESET} {Colors.BOLD}{tool_name}{Colors.RESET}: {action}")
        if details:
            safe_print(f"   {Colors.GRAY}{details}{Colors.RESET}")

    def audit(self, action_type: str, details: str, risk_level: str, approved: bool) -> None:
        status = "APPROVED" if approved else "DENIED"
        log_msg = f"AUDIT [{risk_level}] [{status}] {action_type}: {details}"
        self._file_logger.info(log_msg)

    def agent(self, msg: str) -> None:
        safe_print(f"{Colors.CYAN}{Colors.BOLD}J.A.R.V.I.S.:{Colors.RESET} {msg}")

    def debug(self, msg: str) -> None:
        self._file_logger.debug(msg)


# Global singleton instance
logger = JarvisLogger()
