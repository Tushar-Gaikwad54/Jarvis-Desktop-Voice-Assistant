"""
Permission and Safety Gate System for J.A.R.V.I.S.
Classifies tool operations into risk tiers and prompts user confirmation for dangerous actions.
"""

from enum import Enum
import re
from typing import Callable, Optional
from jarvis.config import get_config
from jarvis.core.logger import Colors, logger, safe_print


class RiskLevel(Enum):
    LOW = "LOW"            # Read-only operations, system queries, info checks
    MEDIUM = "MEDIUM"      # Non-destructive writes inside workspace, safe builds
    HIGH = "HIGH"          # Arbitrary shell execution, file deletion, overwriting files
    CRITICAL = "CRITICAL"  # System shutdown, registry/environment modifications, formatting


class PermissionManager:
    # High-risk patterns in shell commands
    DANGEROUS_SHELL_PATTERNS = [
        r"\brmdir\s+/[sS]",
        r"\bdel\s+/[fFqQsS]",
        r"\bformat\s+[a-zA-Z]:",
        r"\bshutdown\b",
        r"\brestart-computer\b",
        r"\bstop-computer\b",
        r"\breg\s+delete\b",
        r"\bSet-ExecutionPolicy\b",
        r"\bRemove-Item\s+.*-Recurse\b",
        r"\bdiskpart\b",
        r"\bnet\s+user\b",
    ]

    def __init__(self, prompt_callback: Optional[Callable[[str, RiskLevel], bool]] = None):
        self.config = get_config()
        self.prompt_callback = prompt_callback or self._default_console_prompt

    def assess_shell_command_risk(self, command: str) -> RiskLevel:
        """Assesses the risk level of a raw shell command string."""
        cmd_lower = command.lower()
        
        # Check for critical patterns
        for pattern in self.DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, cmd_lower, re.IGNORECASE):
                return RiskLevel.CRITICAL

        # Common dangerous commands
        if any(keyword in cmd_lower for keyword in ["rmdir", "del /", "remove-item", "drop table", "mkfs"]):
            return RiskLevel.HIGH
        
        # Standard build/run/test commands
        if any(keyword in cmd_lower for keyword in ["pip install", "npm install", "git commit", "mkdir", "echo"]):
            return RiskLevel.MEDIUM

        # Read-only / inspection commands
        if any(keyword in cmd_lower for keyword in ["dir", "ls", "pwd", "git status", "git log", "python --version", "where", "Get-"]):
            return RiskLevel.LOW

        return RiskLevel.MEDIUM

    def check_permission(self, action_name: str, risk_level: RiskLevel, details: str = "") -> bool:
        """
        Evaluates whether an action is allowed to proceed based on security configuration and user prompt.
        """
        sec_cfg = self.config.security

        # 1. Low risk auto-approval
        if risk_level == RiskLevel.LOW and sec_cfg.auto_approve_low_risk:
            logger.audit(action_name, details, risk_level.value, approved=True)
            return True

        # 2. Medium risk auto-approval
        if risk_level == RiskLevel.MEDIUM and sec_cfg.auto_approve_medium_risk:
            logger.audit(action_name, details, risk_level.value, approved=True)
            return True

        # 3. Requires prompt/confirmation
        safe_print(f"\n{Colors.YELLOW}[SECURITY PROMPT] J.A.R.V.I.S. requests permission to perform action:{Colors.RESET}")
        safe_print(f"   {Colors.BOLD}Action:{Colors.RESET} {action_name}")
        safe_print(f"   {Colors.BOLD}Risk Level:{Colors.RESET} [{risk_level.value}]")
        if details:
            safe_print(f"   {Colors.BOLD}Details:{Colors.RESET} {details}")

        approved = self.prompt_callback(action_name, risk_level)
        logger.audit(action_name, details, risk_level.value, approved=approved)
        return approved

    def _default_console_prompt(self, action_name: str, risk_level: RiskLevel) -> bool:
        """Prompts the user interactively on the console."""
        try:
            choice = input(f"   {Colors.CYAN}Authorize this action? (y/n / [d]ry-run): {Colors.RESET}").strip().lower()
            return choice in ["y", "yes"]
        except (KeyboardInterrupt, EOFError):
            safe_print("\nAction cancelled.")
            return False


# Global singleton instance
permission_manager = PermissionManager()
