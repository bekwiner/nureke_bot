import re
import unittest
from pathlib import Path


PATTERNS = [
    re.compile(r"рџ"),
    re.compile(r"вЂ"),
    re.compile(r"вќ"),
    re.compile(r"OвЂ"),
    re.compile(r"Ã."),
    re.compile(r"Â."),
]


class NoMojibakePatternsTests(unittest.TestCase):
    def test_no_mojibake_in_python_sources(self):
        problems = []
        for path in Path(".").rglob("*.py"):
            if ".venv" in path.parts or "venv" in path.parts or "__pycache__" in path.parts:
                continue
            if path.parts and path.parts[0] in {"tests", "scripts"}:
                continue
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if any(p.search(line) for p in PATTERNS):
                    problems.append(f"{path}:{lineno}:{line.strip()}")

        self.assertFalse(problems, "Mojibake patterns found:\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
