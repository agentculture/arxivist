# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is (read first)

`arxivist` is an **AgentCulture mesh agent**. Its stated domain (see `pyproject.toml`
and `README.md`):

> Agent + CLI that fetches arXiv papers, maintains a knowledge base, implements
> paper solutions, and benchmarks them against the papers' claims.

**That domain is not built yet.** The code currently in `arxivist/` is the
**culture-agent-template scaffold** — an agent-first introspection CLI (`whoami`,
`learn`, `explain`, `overview`, `doctor`, `cli`) and nothing arXiv-specific. The
runtime prose in `README.md`, `arxivist/cli/_commands/learn.py`, and
`arxivist/explain/catalog.py` still literally describes the package as "a clonable
template for AgentCulture mesh agents." When you build the real domain, you will be
*replacing* that template prose, not adding alongside it.

So there are two distinct kinds of work here, and they call for different mindsets:

- **Extending the agent** — adding arXiv fetch / knowledge-base / implement /
  benchmark functionality. This is greenfield: add new noun groups following the
  existing CLI pattern (below) and retire the template framing as you go.
- **Maintaining the scaffold** — CI, skill re-syncs, version bumps, identity. The
  conventions below are load-bearing and enforced in CI; keep them green.

## Commands

This is a `uv`-managed, Python 3.12+ package. The runtime has **zero third-party
dependencies** (`dependencies = []` in `pyproject.toml`) — keep it that way unless
the domain genuinely requires a dependency, because the empty-deps property is part
of the agent-first design. `teken`, `pytest`, lint tools, etc. are dev-only.

```bash
uv sync                                  # install deps + the package (editable)

# Tests
uv run pytest -n auto                     # full suite, parallel (what CI runs)
uv run pytest "tests/test_cli.py::test_whoami_text"   # a single test
uv run pytest -k whoami                    # tests matching a keyword
bash .claude/skills/run-tests/scripts/test.sh -p      # same, via the run-tests skill

# The CLI itself (two equivalent entry points)
uv run arxivist <verb> [--json]
uv run python -m arxivist <verb>

# Lint (CI's `lint` job runs all of these; line length is 100 everywhere)
uv run black --check arxivist tests
uv run isort --check-only arxivist tests
uv run flake8 arxivist tests
uv run bandit -c pyproject.toml -r arxivist
markdownlint-cli2 "**/*.md" "#node_modules" "#.local" "#.claude/skills" "#.teken"

# The agent-first rubric gate (CI's hardest gate — see below)
uv run teken cli doctor . --strict
```

To auto-fix formatting before committing: `uv run black arxivist tests` and
`uv run isort arxivist tests`.

## CLI architecture

A single argparse application, deliberately structured so an *agent* (not just a
human) can discover and drive it. The pieces:

- **`arxivist/cli/__init__.py`** — `main(argv)` builds the parser, registers every
  command, parses, and dispatches. This is the entry point for both `arxivist` and
  `python -m arxivist`.
- **`arxivist/cli/_commands/`** — one module per verb/noun. Each exposes a
  `register(sub)` function that adds its subparser and sets `func` (and `json`) via
  `set_defaults`. `_build_parser()` calls each `register()` in turn. **This is the
  extension point**: to add a command, write a module with `register()` and add one
  call in `_build_parser()` (there's a `# Register your own noun groups here` marker).
- **`arxivist/cli/_output.py`** — the **strict stream split**: `emit_result` →
  stdout, `emit_error` / `emit_diagnostic` → stderr. They never mix. Agents parse
  stdout and rely on this. Every command takes `--json`; in JSON mode the payload
  goes to the same stream as text would.
- **`arxivist/cli/_errors.py`** — `CliError(code, message, remediation)` and the
  exit-code policy (`0` success, `1` user error, `2` environment error, `3+`
  reserved). All failures raise `CliError`; `_dispatch` catches it and wraps any
  *other* exception so **no Python traceback ever leaks to stderr**.
- **`arxivist/explain/`** — the `explain` catalog. `catalog.py` holds `ENTRIES`, a
  dict keyed by command-path tuples (`("whoami",)`, `("cli", "overview")`) mapping
  to verbatim markdown; `__init__.py`'s `resolve()` looks paths up and raises a
  `CliError` with a hint on a miss.

### Two cross-cutting contracts to preserve when adding commands

1. **Errors route through the structured format.** Don't let argparse print its
   default `prog: error: ...` / exit 2. Subparsers are created with
   `parser_class=_CliArgumentParser`, which overrides `.error()` to emit the
   `error:` / `hint:` format and exit `1`. When you add a *nested* noun group, pass
   `parser_class=type(p)` to its `add_subparsers` (see `_commands/cli.py`) or parse
   errors under that noun bypass the contract. `main()` pre-scans raw argv for
   `--json` (`_json_hint`) so even parse-time errors honor JSON mode.
2. **Every command/path is discoverable and self-describing.** A new verb needs:
   a `--json` flag, an `explain` catalog entry, and (if it's a noun group with
   action-verbs) its own `overview` sub-verb. These aren't style preferences — the
   `teken cli doctor . --strict` rubric gate checks them and **fails CI** otherwise.
   `learn`'s text must stay ≥200 chars and keep mentioning purpose, the command map,
   exit codes, `--json`, and `explain`. `tests/test_cli.py::test_every_catalog_path_resolves`
   asserts every `ENTRIES` key resolves, so keep the catalog and the registered
   commands in lockstep.

Identity (`whoami`, `doctor`, `overview`) is read from `culture.yaml` by a tiny
hand-rolled parser in `_commands/whoami.py` (`find_culture_yaml` walks up from
`__file__`; `read_agent_fields` reads the first agent block **without** a YAML
dependency — that's why it's not `pyyaml`). `doctor` mirrors the `steward doctor`
invariants: `prompt-file-present` and `backend-consistency` (`backend: claude` ⇒
`CLAUDE.md` must exist at the repo root — so this very file is load-bearing).

## Conventions enforced by CI

Two GitHub Actions workflows gate `main`:

- **`.github/workflows/tests.yml`** — three jobs:
  - `test`: `pytest -n auto` + coverage, then a SonarCloud scan that **fails the
    build on a red quality gate** (only when `SONAR_TOKEN` is set; fork PRs and
    token-less repos skip it and stay green). Coverage floor is `fail_under = 60`.
  - `lint`: black, isort, flake8, bandit, markdownlint, and `teken cli doctor .
    --strict`.
  - `version-check`: **every PR must bump `version` in `pyproject.toml`** — even
    docs/config/CI-only PRs. A PR whose version matches `main` fails and gets a
    comment. Use the **`version-bump` skill** (`major|minor|patch`); it also
    prepends a Keep-a-Changelog entry to `CHANGELOG.md`.
- **`.github/workflows/publish.yml`** — PyPI Trusted Publishing. PRs publish a
  `.devN` build to TestPyPI; pushes to `main` publish to PyPI. This is *why* the
  version bump is mandatory: a stale version means a failed publish.

SonarCloud note: `[tool.coverage.run] relative_files = true` is intentional — it
makes `coverage.xml` emit repo-relative paths so Sonar (`sonar.sources=arxivist`)
can map them. Absolute/`.venv` paths get silently dropped and coverage reads 0%.
Don't remove it. Project key is `agentculture_arxivist`.

## Skills (`.claude/skills/`)

The skill kit is **vendored cite-don't-import** from `guildmaster` (with three
skills — `think`, `spec-to-plan`, `assign-to-workforce` — originating in `devague`).
`docs/skill-sources.md` is the authoritative provenance ledger and re-sync
procedure. Rules:

- **Don't edit vendored script bodies.** Only consumer-identifying *prose* in
  `SKILL.md` is adapted, plus the load-bearing `type: command` frontmatter. To
  update a skill, re-sync from upstream per `docs/skill-sources.md`, don't hand-patch.
- These skills are excluded from lint (`markdownlint`, `sonar.exclusions`) precisely
  because they're verbatim copies — don't reformat them.
- Project-specific skills you'll actually use here: **`cicd`** (PR lifecycle via
  `devex pr` + SonarCloud gating: `status`, `await`), **`communicate`** (cross-repo
  issues + mesh messages via `agtag`), `version-bump`, `run-tests`, `sonarclaude`.
  `cicd`/`communicate` require `devex` (≥0.21) and `agtag` (≥0.1) on `PATH`.

## Git / PR workflow

Branch → implement → **bump the version** → open PR (the `cicd` skill wraps this) →
address review → merge. This repo lives in a multi-project workspace alongside its
AgentCulture siblings (`guildmaster`, `steward`, `teken`, …); always run commands
from the repo root. When posting on GitHub on the user's behalf, the
`cicd`/`communicate` scripts sign as `- arxivist (Claude)` automatically — don't add
a signature manually in bodies they author.

## Conventions and workflow

**Memory discipline — recall before, remember after.** This repo keeps its
eidetic memory **in-repo and public**: records resolve to
`<repo-root>/.eidetic/memory` — committed, and shared with the team and mesh
peers (the `claude` and `colleague` backends both read the same
`arxivist` scope), so memory travels with the repo, not a private
home-dir store. Make it a per-task habit:

- **`/recall` before you start.** Search the store for the area you're about
  to touch — prior decisions, gotchas, "have we done this before?" — so you
  build on what's already known instead of re-deriving it. Do this before
  non-trivial tasks, not just when asked.
- **`/remember` when something worth keeping surfaces.** A non-obvious
  decision and its rationale, a constraint, a fix and *why* it was needed, a
  gotcha that cost time, a fact the next session would otherwise re-learn.
  Capture it as it happens, not at the end when it's faded.

A plain `/remember` lands the note in `./.eidetic/memory` in this repo — no
flag needed (the wrappers here default to `--visibility public`; in-repo
routing needs `eidetic >= 0.10.0`, older CLIs keep records in `$HOME`). Keep
something out of the committed store only by passing `--visibility private`
(routes to `$HOME/.eidetic/memory`, never committed); `/recall` reads both
stores and merges. Don't store what the repo already records (code structure,
git history, what's already in this file or `CHANGELOG.md`) — store what you'd
have to re-derive. These are the `recall`/`remember` skills (`.claude/skills/`),
backed by the `eidetic` store.
