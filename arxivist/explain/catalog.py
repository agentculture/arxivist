"""Markdown catalog for ``arxivist explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
and ``("arxivist",)`` both resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# arxivist

A clonable template for AgentCulture mesh agents. It carries an agent-first CLI
(cited from the teken `python-cli` reference), a mesh identity (`culture.yaml` +
`CLAUDE.md`), the canonical guildmaster skill kit under `.claude/skills/`, and a
buildable/deployable package baseline. Clone it, rename the package, edit
`culture.yaml`, and you have a new agent.

## Verbs

- `arxivist whoami` — identity probe from `culture.yaml`.
- `arxivist learn` — structured self-teaching prompt.
- `arxivist explain <path>` — markdown docs for any noun/verb.
- `arxivist overview` — descriptive snapshot of the agent.
- `arxivist doctor` — check the agent-identity invariants.
- `arxivist cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `arxivist explain whoami`
- `arxivist explain doctor`
"""

_WHOAMI = """\
# arxivist whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    arxivist whoami
    arxivist whoami --json
"""

_LEARN = """\
# arxivist learn

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    arxivist learn
    arxivist learn --json
"""

_EXPLAIN = """\
# arxivist explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    arxivist explain arxivist
    arxivist explain whoami
    arxivist explain --json <path>
"""

_OVERVIEW = """\
# arxivist overview

Read-only descriptive snapshot of the agent: identity (from `culture.yaml`), the
verb surface, and the sibling-pattern artifacts the template carries. Accepts an
ignored `target` so a stray path never hard-fails.

## Usage

    arxivist overview
    arxivist overview --json
"""

_DOCTOR = """\
# arxivist doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`claude` → `CLAUDE.md`), plus a
skills-present check. Exits 1 when unhealthy.

## Usage

    arxivist doctor
    arxivist doctor --json
"""

_CLI = """\
# arxivist cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    arxivist cli overview
    arxivist cli overview --json
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("arxivist",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("doctor",): _DOCTOR,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
}
