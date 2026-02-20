import ast
import unittest
from pathlib import Path


def _load_detect_broadcast_type():
    source = Path("handlers.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn_node = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "detect_broadcast_type"
    )
    module = ast.Module(body=[fn_node], type_ignores=[])
    namespace = {"Message": object}
    exec(compile(module, filename="handlers.py", mode="exec"), namespace)
    return namespace["detect_broadcast_type"]


detect_broadcast_type = _load_detect_broadcast_type()


class _Dummy:
    def __init__(self, **kwargs):
        fields = [
            "poll",
            "sticker",
            "animation",
            "video_note",
            "voice",
            "video",
            "photo",
            "audio",
            "document",
            "contact",
            "location",
            "text",
        ]
        for field in fields:
            setattr(self, field, kwargs.get(field))


class BroadcastTypeDetectionTests(unittest.TestCase):
    def test_detect_text(self):
        self.assertEqual(detect_broadcast_type(_Dummy(text="hi")), "text")

    def test_detect_photo(self):
        self.assertEqual(detect_broadcast_type(_Dummy(photo=[object()])), "photo")

    def test_detect_poll_priority(self):
        self.assertEqual(detect_broadcast_type(_Dummy(poll=object(), text="fallback")), "poll")


if __name__ == "__main__":
    unittest.main()
