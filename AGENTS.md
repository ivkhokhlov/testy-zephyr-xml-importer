# Repository Guidelines

## Project Structure & Module Organization
- `zephyr_xml_importer/` contains the plugin code. `api/` defines endpoints, serializers, and permissions; `services/` holds parsing, mapping, validation, and import logic; `templates/` contains the HTML UI.
- `tests/` houses the pytest suite; `tests/fixtures/` includes sample XML and attachment ZIP data.
- `docs/` provides product docs (overview, usage, mapping, deployment, troubleshooting).
- `scripts/` contains helper scripts for local automation.
- `tmp/` contains development-only materials (examples, a TestY main repo checkout, and sample files); do not commit contents.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates and activates a local virtualenv.
- `pip install -e "./[dev]"` installs the plugin in editable mode with dev dependencies.
- `pytest -q` runs the full test suite (configured in `pyproject.toml`).
- `pytest tests/test_importer_integration.py` runs a focused test module.
- `ruff check .` runs linting; use `ruff check . --fix` to auto-apply safe fixes.

## Coding Style & Naming Conventions
- Python 3.11 codebase; use 4-space indentation and keep line length at 100 chars (ruff).
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Tests follow `tests/test_*.py` and `test_*` function naming.

## Testing Guidelines
- Framework: pytest (no explicit coverage target in repo).
- Add tests alongside new behavior; prefer unit tests in `tests/` and fixtures in `tests/fixtures/`.
- Keep tests deterministic and fast; avoid network calls.

## Commit & Pull Request Guidelines
- Commit messages are short and imperative. The history mixes plain summaries with Conventional Commits (`feat:`, `fix:`); prefer the Conventional Commit style for user-facing changes.
- PRs should include a clear description, test results (e.g., `pytest -q`), and doc updates in `docs/` when behavior changes. Include screenshots if you modify the HTML UI.

## Configuration & Security Notes
- This is a TestY plugin; do not commit secrets or real customer data. Use sample fixtures for tests.
- When updating API behavior, verify both the UI (`templates/`) and API endpoints (`zephyr_xml_importer/api/`).
