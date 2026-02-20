import ast
import asyncio
import unittest
from pathlib import Path


def _load_mark_withdraw_as_edited():
    source = Path("handlers.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn_node = next(
        node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "mark_withdraw_as_edited"
    )
    module = ast.Module(body=[fn_node], type_ignores=[])

    class _DB:
        def __init__(self, result: str):
            self.result = result
            self.calls = []

        async def execute(self, query, *args):
            self.calls.append((query, args))
            return self.result

    db = _DB("UPDATE 1")
    namespace = {"db": db, "utc_now": lambda: "NOW"}
    exec(compile(module, filename="handlers.py", mode="exec"), namespace)
    return namespace["mark_withdraw_as_edited"], db


class WithdrawEditUpdateTests(unittest.TestCase):
    def test_marks_status_edited(self):
        func, db = _load_mark_withdraw_as_edited()
        ok = asyncio.run(func(10, 999, "new text"))
        self.assertTrue(ok)
        query, args = db.calls[0]
        self.assertIn("SET status = 'edited'", query)
        self.assertEqual(args[1], 999)
        self.assertEqual(args[2], "new text")
        self.assertEqual(args[3], 10)


if __name__ == "__main__":
    unittest.main()
