#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import re
import sys


SUSPICIOUS_PATTERNS = [
    re.compile(r"рџ"),
    re.compile(r"вЂ"),
    re.compile(r"вќ"),
    re.compile(r"OвЂ"),
    re.compile(r"Ã."),
    re.compile(r"Â."),
]

ZWJ = "\u200d"
VS16 = "\ufe0f"


def is_suspicious_zwj(line: str, idx: int) -> bool:
    prev_char = line[idx - 1] if idx > 0 else ""
    next_char = line[idx + 1] if idx + 1 < len(line) else ""
    return not prev_char or not next_char


def is_suspicious_vs16(line: str, idx: int) -> bool:
    prev_char = line[idx - 1] if idx > 0 else ""
    return not prev_char


def scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for lineno, line in enumerate(lines, start=1):
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern.search(line):
                findings.append(f"{path}:{lineno}: {line.strip()}")
                break

        for idx, ch in enumerate(line):
            if ch == ZWJ and is_suspicious_zwj(line, idx):
                findings.append(f"{path}:{lineno}: suspicious standalone ZWJ")
                break
            if ch == VS16 and is_suspicious_vs16(line, idx):
                findings.append(f"{path}:{lineno}: suspicious standalone VS16")
                break
    return findings


def main() -> int:
    root = Path(".")
    py_files = []
    for p in root.rglob("*.py"):
        if ".venv" in p.parts or "venv" in p.parts or "__pycache__" in p.parts:
            continue
        if p.parts and p.parts[0] in {"tests", "scripts"}:
            continue
        py_files.append(p)

    findings: list[str] = []
    for path in py_files:
        findings.extend(scan_file(path))

    if findings:
        print("Mojibake/suspicious unicode sequences found:")
        for item in findings:
            safe_item = item.encode(sys.stdout.encoding or "utf-8", "backslashreplace").decode(
                sys.stdout.encoding or "utf-8"
            )
            print(safe_item)
        return 1

    print("No mojibake patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
