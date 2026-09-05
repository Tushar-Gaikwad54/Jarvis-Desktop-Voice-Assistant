"""
Desktop and Media Automation Tools for J.A.R.V.I.S.
Preserves and modernizes screenshot, file/app opening, browser, and utility capabilities.
"""

import datetime
import os
from pathlib import Path
import random
import subprocess
import webbrowser
from typing import Any, Dict, Optional
from jarvis.config import get_config
from jarvis.core.permissions import RiskLevel
from jarvis.tools.base import BaseTool


class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Captures a full screenshot of the screen and saves it as an image file."
    risk_level = RiskLevel.LOW

    def execute(self, custom_name: str = None) -> Dict[str, Any]:
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png" if not custom_name else custom_name
            if not filename.endswith(".png"):
                filename += ".png"

            pics_dir = Path(os.path.expanduser("~\\Pictures"))
            pics_dir.mkdir(parents=True, exist_ok=True)
            save_path = pics_dir / filename

            img = pyautogui.screenshot()
            img.save(str(save_path))

            # Store the latest screenshot path in a marker file
            latest_marker = pics_dir / "latest_screenshot.txt"
            latest_marker.write_text(str(save_path), encoding="utf-8")

            return {
                "success": True,
                "file_path": str(save_path),
                "output": f"Screenshot saved successfully at: {save_path}",
            }
        except ImportError:
            return {"success": False, "error": "PyAutoGUI is not installed. Install with 'pip install PyAutoGUI'."}
        except Exception as e:
            return {"success": False, "error": f"Failed to take screenshot: {str(e)}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "custom_name": {"type": "string", "description": "Optional custom filename for the screenshot."}
            },
        }


class OpenItemTool(BaseTool):
    name = "open_item"
    description = (
        "Opens any target file, screenshot, folder (Downloads, Pictures, Documents, Desktop, etc.), "
        "or Windows desktop application (Notepad, Calculator, VS Code, Paint, Task Manager, etc.)."
    )
    risk_level = RiskLevel.LOW

    KNOWN_FOLDERS = {
        "downloads": "~\\Downloads",
        "download": "~\\Downloads",
        "pictures": "~\\Pictures",
        "picture": "~\\Pictures",
        "documents": "~\\Documents",
        "document": "~\\Documents",
        "desktop": "~\\Desktop",
        "music": "~\\Music",
        "videos": "~\\Videos",
        "video": "~\\Videos",
    }

    KNOWN_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "vs code": "code",
        "vscode": "code",
        "code": "code",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "spotify": "spotify.exe",
    }

    def _launch_path_on_windows(self, target_path: Path) -> bool:
        """Launches a file or folder on Windows without popping up terminal consoles."""
        try:
            os.startfile(str(target_path))
            return True
        except Exception:
            try:
                creationflags = 0x08000000 if os.name == "nt" else 0
                subprocess.Popen(f'cmd.exe /c start "" "{str(target_path)}"', shell=True, creationflags=creationflags)
                return True
            except Exception:
                return False

    def execute(self, target: str) -> Dict[str, Any]:
        clean_target = target.strip().lower()
        config = get_config()
        creationflags = 0x08000000 if os.name == "nt" else 0

        # 1. Opening Screenshot
        if "screenshot" in clean_target:
            pics_dir = Path(os.path.expanduser("~\\Pictures"))
            target_path = None

            # Check latest marker file first
            latest_marker = pics_dir / "latest_screenshot.txt"
            if latest_marker.exists():
                try:
                    saved_path = Path(latest_marker.read_text(encoding="utf-8").strip())
                    if saved_path.exists():
                        target_path = saved_path
                except Exception:
                    pass

            # If marker file not found or invalid, find most recently created screenshot
            if not target_path and pics_dir.exists():
                screenshots = list(pics_dir.glob("screenshot*.png"))
                if screenshots:
                    target_path = max(screenshots, key=lambda p: p.stat().st_mtime)

            if target_path and target_path.exists():
                success = self._launch_path_on_windows(target_path)
                if success:
                    return {
                        "success": True,
                        "path": str(target_path),
                        "output": f"Screenshot opened: {target_path.name}",
                    }
                else:
                    return {"success": False, "error": f"Failed to display screenshot {target_path}"}
            else:
                return {"success": False, "error": "No screenshot found in Pictures folder. Take a screenshot first."}

        # 2. Opening Standard Folder
        folder_match = clean_target.replace("folder", "").replace("directory", "").strip()
        if folder_match in self.KNOWN_FOLDERS:
            folder_path = Path(os.path.expanduser(self.KNOWN_FOLDERS[folder_match])).resolve()
            if folder_path.exists():
                try:
                    os.startfile(str(folder_path))
                    return {"success": True, "path": str(folder_path), "output": f"Opened {folder_match} folder."}
                except Exception:
                    try:
                        subprocess.Popen(f'explorer.exe "{str(folder_path)}"', shell=True, creationflags=creationflags)
                        return {"success": True, "path": str(folder_path), "output": f"Opened {folder_match} folder."}
                    except Exception as e:
                        return {"success": False, "error": f"Failed to open folder: {e}"}

        # 3. Opening Workspace / Current Folder
        if clean_target in ["workspace", "current folder", "project folder"]:
            ws_path = Path(config.workspace_dir).resolve()
            try:
                os.startfile(str(ws_path))
                return {"success": True, "path": str(ws_path), "output": f"Opened workspace folder: {ws_path}"}
            except Exception:
                try:
                    subprocess.Popen(f'explorer.exe "{str(ws_path)}"', shell=True, creationflags=creationflags)
                    return {"success": True, "path": str(ws_path), "output": f"Opened workspace folder: {ws_path}"}
                except Exception as e:
                    return {"success": False, "error": f"Failed to open workspace: {e}"}

        # 4. Opening Standard Desktop Application
        app_key = clean_target.replace("app", "").replace("application", "").strip()
        if app_key in self.KNOWN_APPS:
            app_cmd = self.KNOWN_APPS[app_key]
            try:
                subprocess.Popen(f'cmd.exe /c start "" "{app_cmd}"', shell=True, creationflags=creationflags)
                return {"success": True, "app": app_key, "output": f"Launched application: {app_key}"}
            except Exception as e:
                return {"success": False, "error": f"Failed to launch {app_key}: {e}"}

        # 5. Opening arbitrary file or path
        candidate_path = Path(target).resolve()
        if not candidate_path.exists():
            candidate_path = Path(config.workspace_dir) / target

        if candidate_path.exists():
            success = self._launch_path_on_windows(candidate_path)
            if success:
                return {"success": True, "path": str(candidate_path), "output": f"Opened {candidate_path.name}"}
            else:
                return {"success": False, "error": f"Failed to open {candidate_path}"}

        # Try generic shell launch
        try:
            subprocess.Popen(f'cmd.exe /c start "" "{target}"', shell=True, creationflags=creationflags)
            return {"success": True, "target": target, "output": f"Launched {target}"}
        except Exception as e:
            return {"success": False, "error": f"Could not find or open target '{target}': {e}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "The item to open: 'screenshot', a folder name ('downloads', 'pictures', 'documents', 'desktop'), an app name ('notepad', 'calculator', 'vs code'), or a file path.",
                }
            },
            "required": ["target"],
        }


class OpenBrowserTool(BaseTool):
    name = "open_browser"
    description = "Opens a web page or URL in the default web browser."
    risk_level = RiskLevel.LOW

    def execute(self, url: str) -> Dict[str, Any]:
        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                target_url = "https://" + url
            else:
                target_url = url

            webbrowser.open(target_url)
            return {"success": True, "url": target_url, "output": f"Opened browser to {target_url}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to open browser: {str(e)}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL or website domain to open."}
            },
            "required": ["url"],
        }


class TellJokeTool(BaseTool):
    name = "tell_joke"
    description = "Returns a random programming or tech joke."
    risk_level = RiskLevel.LOW

    def execute(self) -> Dict[str, Any]:
        try:
            import pyjokes
            joke = pyjokes.get_joke()
        except ImportError:
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
                "Why do Python programmers have low vision? Because they don't C#!",
            ]
            joke = random.choice(jokes)

        return {"success": True, "joke": joke, "output": joke}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}
