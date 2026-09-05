"""
Unit tests for J.A.R.V.I.S. Tools and Registry
"""

import os
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from jarvis.tools.builtins.filesystem import ListDirectoryTool, ReadFileTool, WriteFileTool
from jarvis.tools.builtins.shell import RunShellCommandTool
from jarvis.tools.builtins.sys_info import GetSystemInfoTool
from jarvis.tools.registry import tool_registry


class TestJarvisTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("./test_sandbox").resolve()
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_file = self.test_dir / "sample.txt"
        self.test_file.write_text("Hello from J.A.R.V.I.S. test!", encoding="utf-8")

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()

    def test_tool_registry_discovery(self):
        tools = tool_registry.list_tools()
        self.assertGreaterEqual(len(tools), 5)
        self.assertIsNotNone(tool_registry.get_tool("get_system_info"))
        self.assertIsNotNone(tool_registry.get_tool("read_file"))
        self.assertIsNotNone(tool_registry.get_tool("write_file"))
        self.assertIsNotNone(tool_registry.get_tool("run_shell_command"))

    def test_read_file_tool(self):
        tool = ReadFileTool()
        result = tool.execute(file_path=str(self.test_file))
        self.assertTrue(result["success"])
        self.assertIn("Hello from J.A.R.V.I.S. test!", result["content"])

    def test_write_file_tool(self):
        tool = WriteFileTool()
        new_file = self.test_dir / "created.txt"
        result = tool.execute(file_path=str(new_file), content="Test content creation")
        self.assertTrue(result["success"])
        self.assertTrue(new_file.exists())
        self.assertEqual(new_file.read_text(encoding="utf-8"), "Test content creation")
        new_file.unlink()

    def test_list_directory_tool(self):
        tool = ListDirectoryTool()
        result = tool.execute(dir_path=str(self.test_dir))
        self.assertTrue(result["success"])
        self.assertIn("sample.txt", result["output"])

    def test_get_system_info_tool(self):
        tool = GetSystemInfoTool()
        result = tool.execute()
        self.assertTrue(result["success"])
        self.assertIn("cpu_cores", result["data"])
        self.assertIn("os", result["data"])

    def test_open_item_tool_registration(self):
        self.assertIsNotNone(tool_registry.get_tool("open_item"))

    def test_shell_command_tool(self):
        tool = RunShellCommandTool()
        result = tool.execute(command="Write-Output 'Jarvis Shell Test'")
        self.assertTrue(result["success"])
        self.assertEqual(result["stdout"], "Jarvis Shell Test")


if __name__ == "__main__":
    unittest.main()
