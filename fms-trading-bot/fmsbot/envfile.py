"""Reading and rewriting .env, in one place.

Both preset.py and the phone's /risk command change settings on disk, and
the encoding rules here are not optional: Windows PowerShell's
`Set-Content -Encoding UTF8` and Notepad both prepend a byte-order mark,
which once became part of the first variable's NAME and silently blanked
TG_BOT_TOKEN. So this reads utf-8-sig and writes without a mark.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def read_lines(path: str | Path = ".env") -> list[str]:
    p = Path(path)
    if not p.is_file():
        return []
    return p.read_text(encoding="utf-8-sig").splitlines()


def apply(lines: list[str], values: dict) -> tuple[list[str], list[str]]:
    """Rewrite these keys in place; append any that are missing.

    Returns (new lines, human-readable changes). Comments, blank lines
    and key order are preserved: a settings file people hand-edit must
    still look like the one they edited.
    """
    wanted = {k: str(v) for k, v in values.items()}
    seen, out, changes = set(), [], []
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            key = s.partition("=")[0].strip()
            if key in wanted:
                old = s.partition("=")[2].split("#")[0].strip()
                new = wanted[key]
                if old != new:
                    changes.append(f"{key}: {old or '(empty)'} -> {new}")
                seen.add(key)
                out.append(f"{key}={new}")
                continue
        out.append(line)
    for key in (k for k in wanted if k not in seen):
        out.append(f"{key}={wanted[key]}")
        changes.append(f"{key}: (not set) -> {wanted[key]}")
    return out, changes


def save(values: dict, path: str | Path = ".env") -> list[str]:
    """Persist these settings. Returns what changed, [] if nothing did.

    A backup is kept because this rewrites the only file that holds the
    account's credentials.
    """
    p = Path(path)
    lines = read_lines(p)
    if not lines and not p.is_file():
        raise FileNotFoundError(f"{p} not found")
    new_lines, changes = apply(lines, values)
    if not changes:
        return []
    shutil.copyfile(p, p.with_suffix(p.suffix + ".bak"))
    # No BOM: utf-8, not utf-8-sig, whatever the platform prefers.
    p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return changes
