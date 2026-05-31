"""Entry point for ``python -m arxivist``."""

from __future__ import annotations

import sys

from arxivist.cli import main

if __name__ == "__main__":
    sys.exit(main())
