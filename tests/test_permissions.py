"""
Unit tests for J.A.R.V.I.S. Permission and Safety System
"""

from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from jarvis.core.permissions import PermissionManager, RiskLevel


class TestJarvisPermissions(unittest.TestCase):
    def setUp(self):
        self.pm = PermissionManager(prompt_callback=lambda action, risk: True)

    def test_safe_command_assessment(self):
        self.assertEqual(self.pm.assess_shell_command_risk("dir"), RiskLevel.LOW)
        self.assertEqual(self.pm.assess_shell_command_risk("git status"), RiskLevel.LOW)
        self.assertEqual(self.pm.assess_shell_command_risk("python --version"), RiskLevel.LOW)

    def test_medium_command_assessment(self):
        self.assertEqual(self.pm.assess_shell_command_risk("pip install rich"), RiskLevel.MEDIUM)
        self.assertEqual(self.pm.assess_shell_command_risk("git commit -m 'test'"), RiskLevel.MEDIUM)

    def test_dangerous_command_assessment(self):
        self.assertEqual(self.pm.assess_shell_command_risk("del /f /q C:\\somefile"), RiskLevel.CRITICAL)
        self.assertEqual(self.pm.assess_shell_command_risk("shutdown /s /f /t 0"), RiskLevel.CRITICAL)
        self.assertEqual(self.pm.assess_shell_command_risk("reg delete HKLM\\Software"), RiskLevel.CRITICAL)

    def test_permission_denial(self):
        denying_pm = PermissionManager(prompt_callback=lambda action, risk: False)
        # Low risk is auto-approved by default
        self.assertTrue(denying_pm.check_permission("read_file", RiskLevel.LOW))
        # High risk requires callback which returns False
        self.assertFalse(denying_pm.check_permission("delete_all", RiskLevel.HIGH))


if __name__ == "__main__":
    unittest.main()
