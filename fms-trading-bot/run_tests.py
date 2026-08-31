#!/usr/bin/env python3
r"""Run every test. No dependencies, no pytest.

    .\.venv\Scripts\python.exe run_tests.py
    .\.venv\Scripts\python.exe run_tests.py ladder

These exist because each one is a bug that reached a live account. A test
here is not hypothetical: it is a thing that already cost money once.
Run this before pushing, and after changing anything in fmsbot/.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main(argv: list[str]) -> int:
    only = argv[1] if len(argv) > 1 else ""
    names = sorted(m.name for m in pkgutil.iter_modules([str(ROOT / "tests")])
                   if m.name.startswith("test_"))
    if only:
        names = [n for n in names if only in n]
    if not names:
        print(f"No tests matching '{only}'.")
        return 1

    passed = failed = 0
    for name in names:
        module = importlib.import_module(f"tests.{name}")
        for attr in sorted(dir(module)):
            if not attr.startswith("test_"):
                continue
            fn = getattr(module, attr)
            if not callable(fn):
                continue
            label = f"{name}.{attr}"
            try:
                fn()
            except Exception:
                failed += 1
                print(f"FAIL  {label}")
                print("      " + traceback.format_exc().replace("\n", "\n      "))
            else:
                passed += 1
                print(f"ok    {label}")

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
