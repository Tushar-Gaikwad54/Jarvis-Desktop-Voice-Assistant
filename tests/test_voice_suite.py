"""
Comprehensive unit test suite for voice sanitization, gender selection, and interrupt controls.
"""

import unittest
from jarvis.interface.voice import clean_text_for_speech, voice_bridge
from jarvis.interface.gui.app import JarvisAPI
from jarvis.core.engine import JarvisEngine


class TestVoiceSanitizer(unittest.TestCase):
    def test_code_block_stripping(self):
        text = "Here is the code:\n```python\nprint('Hello world')\n```\nHope that helps!"
        cleaned = clean_text_for_speech(text)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("print('Hello world')", cleaned)
        self.assertIn("displayed the code", cleaned)

    def test_literal_escapes(self):
        text = r"First line\nSecond line\n\nThird line."
        cleaned = clean_text_for_speech(text)
        self.assertNotIn(r"\n", cleaned)
        self.assertIn("First line. Second line. Third line.", cleaned)

    def test_path_and_slash_cleaning(self):
        text = r"Please check C:\Users\Admin\Documents\project / file.txt"
        cleaned = clean_text_for_speech(text)
        self.assertNotIn("\\", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertIn("Users", cleaned)
        self.assertIn("Documents", cleaned)

    def test_markdown_and_links(self):
        text = "### Overview\n- Check [Google](https://google.com)\n- **Bold item** and *italic item*"
        cleaned = clean_text_for_speech(text)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertIn("Google", cleaned)
        self.assertIn("Bold item", cleaned)

    def test_emojis_and_special_symbols(self):
        text = "Status: Online! 🚀 All systems nominal ⚡ 🕒 ~~strikethrough~~"
        cleaned = clean_text_for_speech(text)
        self.assertNotIn("🚀", cleaned)
        self.assertNotIn("⚡", cleaned)
        self.assertNotIn("🕒", cleaned)
        self.assertNotIn("~~", cleaned)
        self.assertIn("Status: Online! All systems nominal", cleaned)


class TestVoiceBridgeControls(unittest.TestCase):
    def setUp(self):
        self.bridge = voice_bridge

    def test_gender_selection(self):
        self.bridge.set_gender("female")
        self.assertEqual(self.bridge.gender, "female")
        self.bridge.set_gender("male")
        self.assertEqual(self.bridge.gender, "male")

    def test_interrupt_when_idle(self):
        # Stopping when not speaking should be safe and idempotent
        self.bridge.stop()
        self.assertFalse(self.bridge.is_speaking())


class TestJarvisGUIAPI(unittest.TestCase):
    def setUp(self):
        self.api = JarvisAPI(engine=JarvisEngine())

    def test_toggle_voice_gender(self):
        res1 = self.api.set_voice_gender("male")
        self.assertEqual(res1["gender"], "male")
        self.assertEqual(res1["persona"], "J.A.R.V.I.S.")

        res2 = self.api.toggle_voice_gender()
        self.assertEqual(res2["gender"], "female")
        self.assertEqual(res2["persona"], "F.R.I.D.A.Y.")

    def test_stop_speech_api(self):
        res = self.api.stop_speech()
        self.assertEqual(res["status"], "interrupted")
        self.assertFalse(res["is_speaking"])


if __name__ == "__main__":
    unittest.main()
