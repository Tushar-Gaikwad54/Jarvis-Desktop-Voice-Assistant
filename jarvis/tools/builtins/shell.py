"""
Safe Shell and PowerShell Execution Tool for J.A.R.V.I.S.
"""

import os
from pathlib import Path
import subprocess
from typing import Any, Dict
from jarvis.config import get_config
from jarvis.core.permissions import RiskLevel
from jarvis.tools.base import BaseTool


class RunShellCommandTool(BaseTool):
    name = "run_shell_command"
    description = (
        "Executes a command in PowerShell or CMD on the host system. "
        "Use this to inspect system state, run scripts, run builds, check versions, or test diagnostics."
    )
    risk_level = RiskLevel.HIGH  # Evaluated dynamically per command

    def execute(self, command: str, working_dir: str = None, timeout: int = None) -> Dict[str, Any]:
        config = get_config()
        cwd = working_dir or config.workspace_dir
        timeout_sec = timeout or config.security.command_timeout_seconds

        try:
            creationflags = 0x08000000 if os.name == "nt" else 0
            process = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                cwd=cwd,
                capture_output=True,
                text=True,
                creationflags=creationflags,
                timeout=timeout_sec,
                encoding="utf-8",
                errors="replace",
            )

            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            exit_code = process.returncode

            # Output truncation if too large
            max_len = 8000
            if len(stdout) > max_len:
                stdout = stdout[:max_len] + f"\n... [Output truncated ({len(stdout)} total characters)]"

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "output": stdout if stdout else (stderr if stderr else f"Command completed with exit code {exit_code}"),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Command timed out after {timeout_sec} seconds.",
                "output": f"Command timed out after {timeout_sec} seconds.",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e),
                "output": f"Execution error: {str(e)}",
            }

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The exact shell command to execute in PowerShell.",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional working directory path. Defaults to active workspace.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Optional timeout in seconds.",
                },
            },
            "required": ["command"],
        }
