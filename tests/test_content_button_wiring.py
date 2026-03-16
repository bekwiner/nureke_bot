import unittest
from pathlib import Path


class ContentButtonWiringTests(unittest.TestCase):
    def test_main_menu_keyboard_supports_extra_buttons(self):
        source = Path("keyboards.py").read_text(encoding="utf-8")
        self.assertIn("def main_menu_keyboard(extra_buttons: list[str] | None = None):", source)
        self.assertIn("keyboard.append([KeyboardButton(text=cleaned)])", source)

    def test_admin_menu_contains_content_upload_entry(self):
        source = Path("keyboards.py").read_text(encoding="utf-8")
        self.assertIn("📥 Bo'limga yuklash", source)

    def test_schema_and_handlers_exist(self):
        database_source = Path("database.py").read_text(encoding="utf-8")
        handlers_source = Path("handlers.py").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS content_buttons", database_source)
        self.assertIn("CONTENT_BUTTON_SAVED", handlers_source)
        self.assertIn("user_dynamic_content_button_router", handlers_source)


if __name__ == "__main__":
    unittest.main()
