"""
Tool Registry and Dispatcher for J.A.R.V.I.S.
Handles tool discovery, schema generation for LLMs, and safe execution routing.
"""

from typing import Any, Dict, List, Optional, Type
from jarvis.core.exceptions import PermissionDeniedError, ToolExecutionError
from jarvis.core.logger import logger
from jarvis.core.permissions import RiskLevel, permission_manager
from jarvis.tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers an instance of BaseTool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name} [{tool.risk_level.value}]")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Returns schemas for all registered tools formatted for LLM function calling."""
        return [tool.get_schema() for tool in self._tools.values()]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a registered tool by name with permission checking and error handling.
        """
        tool = self.get_tool(name)
        if not tool:
            error_msg = f"Tool '{name}' is not registered."
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        # Dynamically evaluate risk level if tool has custom assessment (e.g. shell command analyzer)
        risk_level = tool.risk_level
        if name == "run_shell_command" and "command" in arguments:
            risk_level = permission_manager.assess_shell_command_risk(arguments["command"])

        # Check permissions
        details_str = ", ".join(f"{k}={repr(v)}" for k, v in arguments.items())
        is_allowed = permission_manager.check_permission(
            action_name=f"{tool.name}({details_str})",
            risk_level=risk_level,
            details=f"Tool: {tool.name}, Arguments: {arguments}",
        )

        if not is_allowed:
            logger.warn(f"Execution of tool '{name}' was blocked by permission gate.")
            return {
                "success": False,
                "error": f"Permission denied for tool '{name}' (Risk level: {risk_level.value}). Action was cancelled.",
            }

        logger.tool(tool.name, "Executing", details_str)
        try:
            result = tool.execute(**arguments)
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}


# Global singleton instance
tool_registry = ToolRegistry()
