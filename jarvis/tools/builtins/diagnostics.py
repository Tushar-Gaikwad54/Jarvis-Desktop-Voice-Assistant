"""
Diagnostic and Troubleshooting Tools for J.A.R.V.I.S.
Diagnoses missing CLI tools, PATH misconfigurations, Windows AppExecutionAliases (e.g. winget), and environment issues.
"""

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List
from jarvis.core.permissions import RiskLevel
from jarvis.tools.base import BaseTool


class DiagnoseCommandTool(BaseTool):
    name = "diagnose_command"
    description = (
        "Diagnoses software installation issues on Windows when the user specifically asks to fix or diagnose a broken command line tool (e.g. winget, git, python, npm, docker). "
        "Do NOT call this tool for general explanations, science questions, concepts, or normal conversations."
    )
    risk_level = RiskLevel.LOW

    def execute(self, command_name: str) -> Dict[str, Any]:
        target = command_name.strip().lower()
        findings: List[str] = []
        fix_suggestions: List[str] = []
        is_available = False

        # 1. Check direct which/where
        creationflags = 0x08000000 if os.name == "nt" else 0
        which_path = shutil.which(target)
        if which_path:
            is_available = True
            findings.append(f"[OK] Found in PATH: {which_path}")
            # Try running --version or -v
            try:
                ver_res = subprocess.run(
                    [which_path, "--version"],
                    capture_output=True,
                    text=True,
                    creationflags=creationflags,
                    timeout=5,
                )
                if ver_res.returncode == 0:
                    findings.append(f"     Version output: {ver_res.stdout.strip()}")
            except Exception:
                pass
        else:
            findings.append(f"[FAIL] '{target}' is NOT directly available in the active PATH.")

        # 2. Specific Winget Diagnosis
        if "winget" in target:
            app_data = os.environ.get("LOCALAPPDATA", "")
            windows_apps = Path(app_data) / "Microsoft" / "WindowsApps"
            winget_alias = windows_apps / "winget.exe"

            if winget_alias.exists():
                findings.append(f"[INFO] Found winget App Execution Alias at: {winget_alias}")
                if str(windows_apps).lower() not in os.environ.get("PATH", "").lower():
                    findings.append(f"[WARN] '{windows_apps}' is missing from the environment PATH variable.")
                    fix_suggestions.append(f"Add '{windows_apps}' to your User or System PATH environment variable.")
                else:
                    findings.append("[INFO] The WindowsApps directory IS in your PATH. The alias may be disabled in Windows Settings.")
                    fix_suggestions.append("Check Windows Settings -> Apps -> Advanced app settings -> App execution aliases, and ensure 'App Installer (winget.exe)' is toggled ON.")
            else:
                findings.append(f"[FAIL] Winget alias does NOT exist at {winget_alias}.")

            # Query AppInstaller AppX package
            try:
                ps_res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-AppxPackage -Name *DesktopAppInstaller* | Select-Object -ExpandProperty PackageFullName"],
                    capture_output=True,
                    text=True,
                    creationflags=creationflags,
                    timeout=5,
                )
                pkg_name = ps_res.stdout.strip()
                if pkg_name:
                    findings.append(f"[PKG] Microsoft App Installer package is installed: {pkg_name}")
                else:
                    findings.append("[FAIL] Microsoft DesktopAppInstaller package is not installed on this system.")
                    fix_suggestions.append("Install 'App Installer' from the Microsoft Store or download the .msixbundle from github.com/microsoft/winget-cli/releases.")
            except Exception as e:
                findings.append(f"Could not query AppX packages: {e}")

        # 3. Specific Python / Pip Diagnosis
        elif "python" in target or "pip" in target:
            py_path = shutil.which("python")
            if py_path:
                findings.append(f"[OK] Python executable: {py_path}")
            else:
                findings.append("[FAIL] Python is not in PATH.")
                fix_suggestions.append("Download Python from python.org and ensure 'Add Python to PATH' is checked during installation.")

        # 4. General PATH analysis
        path_dirs = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
        findings.append(f"[PATH] PATH contains {len(path_dirs)} search directories.")

        # Summary output
        output_sections = [
            f"--- Diagnostic Report for: '{command_name}' ---",
            "Findings:",
            *[f"  {f}" for f in findings],
        ]

        if fix_suggestions:
            output_sections.append("\nRecommended Fixes:")
            output_sections.extend([f"  {i+1}. {s}" for i, s in enumerate(fix_suggestions)])

        return {
            "success": True,
            "command": command_name,
            "is_available": is_available,
            "findings": findings,
            "recommendations": fix_suggestions,
            "output": "\n".join(output_sections),
        }

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command_name": {
                    "type": "string",
                    "description": "The exact CLI software name that is broken or missing (e.g. 'winget', 'git', 'python', 'docker').",
                }
            },
            "required": ["command_name"],
        }
