import ast
import re
import unittest
from pathlib import Path


def _load_normalize_menu_text():
    source = Path("handlers.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn_node = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "normalize_menu_text"
    )
    module = ast.Module(body=[fn_node], type_ignores=[])
    namespace = {"re": re}
    exec(compile(module, filename="handlers.py", mode="exec"), namespace)
    return namespace["normalize_menu_text"]


normalize_menu_text = _load_normalize_menu_text()


class AdminTextNormalizationTests(unittest.TestCase):
    def test_keeps_plain_label(self):
        self.assertEqual(normalize_menu_text("💳 Voucherlar"), "voucherlar")

    def test_handles_mojibake_prefix(self):
        self.assertIn("voucher", normalize_menu_text("рџ’і Voucherlar"))

    def test_normalizes_apostrophe_and_spaces(self):
        value = normalize_menu_text("📞 Admin bilan bog‘lanish   matni")
        self.assertIn("admin bilan bog lanish matni", value)


if __name__ == "__main__":
    unittest.main()
