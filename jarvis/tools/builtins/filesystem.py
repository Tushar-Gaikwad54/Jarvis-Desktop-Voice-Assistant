"""
Filesystem Tools for J.A.R.V.I.S.
Allows safe reading, writing, listing, and searching of files on the system.
"""

import os
from pathlib import Path
from typing import Any, Dict
from jarvis.config import get_config
from jarvis.core.permissions import RiskLevel
from jarvis.tools.base import BaseTool


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads the text content of a file at the specified path."
    risk_level = RiskLevel.LOW

    def execute(self, file_path: str, max_lines: int = 500) -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists():
            return {"success": False, "error": f"File does not exist: {path}"}
        if not path.is_file():
            return {"success": False, "error": f"Path is not a file: {path}"}

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            selected_lines = lines[:max_lines]
            content = "".join(selected_lines)

            if total_lines > max_lines:
                content += f"\n... [Truncated {total_lines - max_lines} remaining lines]"

            return {
                "success": True,
                "file_path": str(path),
                "total_lines": total_lines,
                "content": content,
                "output": content,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute or relative path to the file to read."},
                "max_lines": {"type": "integer", "description": "Maximum lines to return. Defaults to 500."},
            },
            "required": ["file_path"],
        }


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Writes or overwrites text content to a specified file."
    risk_level = RiskLevel.MEDIUM

    def execute(self, file_path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        path = Path(file_path).resolve()
        try:
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "file_path": str(path),
                "bytes_written": len(content.encode("utf-8")),
                "output": f"Successfully wrote {len(content.encode('utf-8'))} bytes to {path}",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {str(e)}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the destination file."},
                "content": {"type": "string", "description": "The exact text content to write."},
                "create_dirs": {"type": "boolean", "description": "Whether to create parent folders if missing."},
            },
            "required": ["file_path", "content"],
        }


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "Lists files and subdirectories within a target directory."
    risk_level = RiskLevel.LOW

    def execute(self, dir_path: str = None, depth: int = 1) -> Dict[str, Any]:
        config = get_config()
        target = Path(dir_path or config.workspace_dir).resolve()

        if not target.exists():
            return {"success": False, "error": f"Directory does not exist: {target}"}
        if not target.is_dir():
            return {"success": False, "error": f"Path is not a directory: {target}"}

        try:
            entries = []
            for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                entry_type = "DIR" if item.is_dir() else "FILE"
                size_str = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
                entries.append(f"[{entry_type}] {item.name}{size_str}")

            output = f"Contents of {target}:\n" + "\n".join(entries) if entries else f"Directory {target} is empty."
            return {
                "success": True,
                "dir_path": str(target),
                "total_items": len(entries),
                "items": entries,
                "output": output,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list directory: {str(e)}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "Directory path to list. Defaults to workspace."},
                "depth": {"type": "integer", "description": "Listing depth. Defaults to 1."},
            },
        }
