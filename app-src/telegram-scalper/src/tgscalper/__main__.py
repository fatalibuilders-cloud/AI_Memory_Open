"""Allows `python -m tgscalper ...` as well as the installed `tgscalper` script."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
