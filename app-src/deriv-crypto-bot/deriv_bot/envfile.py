"""Locating, loading, and diagnosing the .env file.

A missing or half-filled `.env` is the most common way a first run fails, and
the failure is silent by nature: the bot just says a value is not set. This
module turns that into a specific diagnosis — where it looked, what it found,
which line is wrong, and what to type instead.

It also catches the Windows trap where Notepad's "Save As" silently appends
`.txt`, leaving `.env.txt` on disk while the bot looks for `.env`.
"""

from __future__ import annotations

import os

# Keys the bot cannot start without.
REQUIRED_KEYS = ("DERIV_APP_ID", "DERIV_API_TOKEN")

# Names Windows editors commonly leave behind instead of a plain ".env".
_MISNAMED = (".env.txt", ".env.text", "env", "env.txt", ".env.example.txt")


def search_paths() -> list[str]:
    """Where a .env is looked for, in order: the working directory, then the
    package's parent (so the bot works when launched from elsewhere).

    Deduplicated — the two coincide when the bot is run from its own folder,
    and listing the same path twice in a diagnosis reads like a bug.
    """
    package_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ordered = [os.path.abspath(".env"), os.path.join(package_parent, ".env")]
    seen: list[str] = []
    for path in ordered:
        normalised = os.path.normpath(path)
        if normalised not in seen:
            seen.append(normalised)
    return seen


def find() -> str | None:
    """The first .env that exists, or None."""
    for path in search_paths():
        if os.path.isfile(path):
            return path
    return None


def find_misnamed() -> list[str]:
    """Files that look like a .env saved under the wrong name."""
    found = []
    for directory in {os.path.dirname(p) for p in search_paths()}:
        for name in _MISNAMED:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                found.append(candidate)
    return found


def dotenv_installed() -> bool:
    try:
        import dotenv  # noqa: F401
    except ImportError:
        return False
    return True


def load() -> str | None:
    """Load the first .env found. Returns its path, or None if none loaded.

    Existing environment variables win, so `set DERIV_API_TOKEN=... && python
    -m deriv_bot` overrides the file rather than being silently ignored.
    """
    if not dotenv_installed():
        return None
    from dotenv import load_dotenv

    path = find()
    if path:
        load_dotenv(path, override=False)
        return path
    return None


def read_key_line(path: str, key: str) -> tuple[int, str] | None:
    """Find the line defining `key`, returning (line number, raw line)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if stripped.split("=", 1)[0].strip() == key:
                    return number, line.rstrip("\n")
    except OSError:
        return None
    return None


def _status(key: str) -> str:
    raw = os.environ.get(key)
    if raw is None:
        return "not set"
    if not raw.strip():
        return "EMPTY"
    if key == "DERIV_API_TOKEN":
        return f"set ({len(raw.strip())} characters)"
    return f"set ({raw.strip()})"


def diagnose() -> list[str]:
    """Explain, line by line, why configuration did not load.

    Returns printable lines. Never reveals the token itself — only whether one
    is present and how long it is.
    """
    lines: list[str] = []
    add = lines.append

    path = find()
    add("  Diagnosis:")

    if path:
        add(f"    .env file        FOUND  {path}")
    else:
        add("    .env file        NOT FOUND")
        for candidate in search_paths():
            add(f"                     looked in: {candidate}")

    misnamed = find_misnamed()
    if misnamed and not path:
        add("")
        add("    A file with a similar name exists:")
        for item in misnamed:
            add(f"      {item}")
        add("    Notepad appends .txt unless you pick 'All Files' when saving.")
        add("    Rename it to exactly '.env' (no extension):")
        add(f"      Rename-Item '{misnamed[0]}' '.env'")

    if not dotenv_installed():
        add("")
        add("    python-dotenv    NOT INSTALLED  <-- .env cannot be read")
        add("    Install it:  .venv\\Scripts\\python.exe -m pip install python-dotenv")
        add("    (Or set the variables directly in your shell instead.)")
    else:
        add("    python-dotenv    installed")

    add("")
    for key in REQUIRED_KEYS:
        state = _status(key)
        marker = "  <-- this is the problem" if state in {"not set", "EMPTY"} else ""
        add(f"    {key:<17}{state}{marker}")

    # Point at the exact line to edit.
    broken = [k for k in REQUIRED_KEYS if _status(k) in {"not set", "EMPTY"}]
    if path and broken:
        key = broken[0]
        located = read_key_line(path, key)
        add("")
        if located:
            number, text = located
            add(f"  Line {number} of your .env currently reads:")
            add(f"      {text.strip()}")
        else:
            add(f"  Your .env has no {key} line at all.")
        add("")
        add("  It needs the value straight after the '=', with no spaces and")
        add("  no quotes:")
        add(f"      {key}=your_actual_value_here")
        add("")
        add("  Edit it with:   notepad .env")
        add("  Save with Ctrl+S and close Notepad, then run this again.")

    if not path:
        add("")
        add("  Create it from the template, then edit it:")
        add("      Copy-Item .env.example .env      # PowerShell")
        add("      cp .env.example .env             # macOS / Linux")

    return lines


# Deriv API tokens are short fixed-length alphanumeric strings. The exact
# length is not contractual, so this is a plausibility band rather than a rule.
_TYPICAL_TOKEN_LENGTH = 15
_PLACEHOLDERS = {
    "your_token_here",
    "your_actual_value_here",
    "youractualvaluehere",
    "token",
    "changeme",
    "xxx",
}


def mask(token: str) -> str:
    """A token preview safe to show on screen or paste into a chat."""
    clean = token.strip()
    if len(clean) <= 4:
        return "*" * len(clean)
    return f"{clean[:2]}{'*' * (len(clean) - 4)}{clean[-2:]}"


def inspect_token(token: str) -> list[str]:
    """Flag shapes that suggest a mis-copied token.

    Deriv only ever says "the token is invalid", which is true for a revoked
    token, a partial paste, and a copied token *name* alike. These heuristics
    separate those cases without the value ever leaving the machine.
    """
    problems: list[str] = []
    clean = token.strip()

    if clean.lower() in _PLACEHOLDERS or clean.lower().startswith("your_"):
        problems.append("It is still the placeholder text, not a real token.")
        return problems

    if any(ch.isspace() for ch in clean):
        problems.append(
            "It contains a space. A token has none - the paste was probably "
            "incomplete or picked up surrounding text."
        )

    if clean[:1] in {'"', "'"} or clean[-1:] in {'"', "'"}:
        problems.append("It is wrapped in quotes. Remove them - the value needs no quotes.")

    if clean.startswith("http") or "deriv.com" in clean.lower():
        problems.append("It looks like a URL. Copy the token value itself, not a link.")

    if len(clean) < 10:
        problems.append(
            f"It is only {len(clean)} characters. Deriv tokens are around "
            f"{_TYPICAL_TOKEN_LENGTH} - this looks like a partial copy."
        )
    elif len(clean) > 64:
        problems.append(
            f"It is {len(clean)} characters, far longer than a Deriv token. "
            "You may have copied more than the token field."
        )

    if not clean.replace("-", "").replace("_", "").isalnum():
        problems.append(
            "It contains punctuation a Deriv token would not have - check for "
            "a trailing comment or stray characters on the line."
        )

    return problems


def explain(error: Exception) -> str:
    """A complete, printable explanation for a configuration failure."""
    parts = ["", f"  Configuration error: {error}", ""]
    parts.extend(diagnose())
    parts.append("")
    return "\n".join(parts)
