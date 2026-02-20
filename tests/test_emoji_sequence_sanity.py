import ast
import unittest
from pathlib import Path


def _is_emojiish(ch: str) -> bool:
    if not ch:
        return False
    cp = ord(ch)
    if 0x1F300 <= cp <= 0x1FAFF:
        return True
    if 0x2600 <= cp <= 0x27BF:
        return True
    if ch in {
        "\u2642",
        "\u2640",
        "\u2b05",
        "\u2b07",
        "\u21a9",
        "\u23f1",
        "#",
        "*",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    }:
        return True
    return False


def _suspicious_sequences(text: str):
    issues = []
    for idx, ch in enumerate(text):
        if ch == "\u200d":
            prev_ch = text[idx - 1] if idx > 0 else ""
            next_ch = text[idx + 1] if idx + 1 < len(text) else ""
            if not _is_emojiish(prev_ch) or not _is_emojiish(next_ch):
                issues.append((idx, "ZWJ"))
        elif ch == "\ufe0f":
            prev_ch = text[idx - 1] if idx > 0 else ""
            if not _is_emojiish(prev_ch):
                issues.append((idx, "VS16"))
    return issues


def _string_literals_from_file(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value


class EmojiSequenceSanityTests(unittest.TestCase):
    def test_no_suspicious_sequences_in_ui_strings(self):
        targets = [Path("handlers.py"), Path("keyboards.py")]
        problems = []

        for target in targets:
            for value in _string_literals_from_file(target):
                for idx, kind in _suspicious_sequences(value):
                    problems.append(f"{target}:{kind}@{idx}:{value!r}")

        self.assertFalse(
            problems,
            "Found suspicious standalone ZWJ/VS16 sequences:\n" + "\n".join(problems),
        )


if __name__ == "__main__":
    unittest.main()
