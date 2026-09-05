"""
Unit tests for J.A.R.V.I.S. Core Engine and Diagnostics
"""

from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from jarvis.core.engine import JarvisEngine
from jarvis.llm.rule_fallback import RuleFallbackProvider
from jarvis.tools.builtins.diagnostics import DiagnoseCommandTool


class TestJarvisEngineAndDiagnostics(unittest.TestCase):
    def setUp(self):
        self.engine = JarvisEngine(provider=RuleFallbackProvider())

    def test_engine_system_info_query(self):
        response = self.engine.process_query("What are my system specs?")
        self.assertIn("Operating System", response)
        self.assertIn("CPU Cores", response)

    def test_engine_time_query(self):
        response = self.engine.process_query("What time is it?")
        self.assertIn("The current time is", response)

    def test_engine_diagnostics_query(self):
        response = self.engine.process_query("diagnose python")
        self.assertIn("Diagnostic Report for: 'python'", response)

    def test_engine_open_screenshot_query(self):
        response = self.engine.process_query("open screenshot")
        self.assertIn("Opening screenshot", response)

    def test_engine_open_folder_query(self):
        response = self.engine.process_query("open downloads folder")
        self.assertIn("Opening your downloads folder", response)

    def test_diagnose_tool_execution(self):
        tool = DiagnoseCommandTool()
        res = tool.execute("powershell")
        self.assertTrue(res["success"])
        self.assertTrue(res["is_available"])
        self.assertIn("Diagnostic Report", res["output"])


if __name__ == "__main__":
    unittest.main()
