import unittest
from types import SimpleNamespace

import handlers
from states import AdminVouchersStates

from handlers import parse_admin_int_input, validate_voucher_numeric_value


class VoucherAdminInputTests(unittest.TestCase):
    def test_parse_plain_digits(self):
        self.assertEqual(parse_admin_int_input("18000"), 18000)

    def test_parse_comma_and_space(self):
        self.assertEqual(parse_admin_int_input("19,000"), 19000)
        self.assertEqual(parse_admin_int_input("19 000"), 19000)
        self.assertEqual(parse_admin_int_input("19.000"), 19000)
        self.assertEqual(parse_admin_int_input("19_000"), 19000)

    def test_parse_invalid(self):
        self.assertIsNone(parse_admin_int_input("19k"))
        self.assertIsNone(parse_admin_int_input(""))
        self.assertIsNone(parse_admin_int_input("   "))

    def test_validate_price_bounds(self):
        value, err = validate_voucher_numeric_value("price", "18000")
        self.assertEqual(value, 18000)
        self.assertIsNone(err)

        value, err = validate_voucher_numeric_value("price", "0")
        self.assertIsNone(value)
        self.assertIsNotNone(err)

        value, err = validate_voucher_numeric_value("price", "10000001")
        self.assertIsNone(value)
        self.assertIsNotNone(err)

    def test_validate_almaz_bounds(self):
        value, err = validate_voucher_numeric_value("almaz", "450")
        self.assertEqual(value, 450)
        self.assertIsNone(err)

        value, err = validate_voucher_numeric_value("almaz", "0")
        self.assertIsNone(value)
        self.assertIsNotNone(err)


class _DummyState:
    def __init__(self, data):
        self._data = data
        self.last_state = None

    async def get_data(self):
        return self._data

    async def set_state(self, value):
        self.last_state = value


class _DummyMessage:
    def __init__(self, text, user_id=1):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))


class _DummyDB:
    def __init__(self, row):
        self.row = row
        self.execute_args = None
        self.fetchrow_calls = 0

    async def fetchrow(self, _query, _voucher_id):
        self.fetchrow_calls += 1
        return self.row

    async def execute(self, _query, value, voucher_id):
        self.execute_args = (value, voucher_id)


class VoucherAdminHandlerTypeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._orig_db = handlers.db
        self._orig_require_role = handlers.require_role
        self._orig_log_admin_action = handlers.log_admin_action

        async def _allow_role(_message, _roles):
            return "superadmin"

        async def _noop_log(**_kwargs):
            return None

        handlers.require_role = _allow_role
        handlers.log_admin_action = _noop_log

    async def asyncTearDown(self):
        handlers.db = self._orig_db
        handlers.require_role = self._orig_require_role
        handlers.log_admin_action = self._orig_log_admin_action

    async def test_price_update_passes_int_to_db_execute(self):
        handlers.db = _DummyDB({"id": 1, "name": "Weekly", "almaz": 450, "price": 17000})
        state = _DummyState({"field": "price", "voucher_id": 1})
        message = _DummyMessage("19,000")

        await handlers.admin_edit_voucher_save(message, state)

        self.assertIsNotNone(handlers.db.execute_args)
        self.assertEqual(handlers.db.execute_args[1], 1)
        self.assertIsInstance(handlers.db.execute_args[0], int)
        self.assertEqual(handlers.db.execute_args[0], 19000)
        self.assertEqual(state.last_state, AdminVouchersStates.menu)

    async def test_invalid_numeric_format_rejected(self):
        handlers.db = _DummyDB({"id": 1, "name": "Weekly", "almaz": 450, "price": 17000})
        state = _DummyState({"field": "price", "voucher_id": 1})
        message = _DummyMessage("19k")

        await handlers.admin_edit_voucher_save(message, state)

        self.assertIsNone(handlers.db.execute_args)
        self.assertTrue(message.answers)


if __name__ == "__main__":
    unittest.main()
