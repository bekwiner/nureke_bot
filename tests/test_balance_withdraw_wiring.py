import unittest
from pathlib import Path


class BalanceWithdrawWiringTests(unittest.TestCase):
    def test_withdraw_button_callback_exists(self):
        source = Path("keyboards.py").read_text(encoding="utf-8")
        self.assertIn('callback_data="withdraw_start"', source)
        self.assertIn("Balansdagi almazni yechish", source)


if __name__ == "__main__":
    unittest.main()
