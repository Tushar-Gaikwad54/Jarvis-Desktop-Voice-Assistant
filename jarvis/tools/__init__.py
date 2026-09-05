"""
Builtin Tools Initializer for J.A.R.V.I.S.
"""

from jarvis.tools.base import BaseTool
from jarvis.tools.builtins.desktop import OpenBrowserTool, OpenItemTool, TakeScreenshotTool, TellJokeTool
from jarvis.tools.builtins.diagnostics import DiagnoseCommandTool
from jarvis.tools.builtins.filesystem import ListDirectoryTool, ReadFileTool, WriteFileTool
from jarvis.tools.builtins.shell import RunShellCommandTool
from jarvis.tools.builtins.sys_info import GetSystemInfoTool
from jarvis.tools.registry import tool_registry


def register_all_builtins() -> None:
    """Registers all standard builtin tools into the tool_registry."""
    tools = [
        RunShellCommandTool(),
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        GetSystemInfoTool(),
        DiagnoseCommandTool(),
        TakeScreenshotTool(),
        OpenItemTool(),
        OpenBrowserTool(),
        TellJokeTool(),
    ]
    for t in tools:
        tool_registry.register(t)


# Auto-register upon import
register_all_builtins()
