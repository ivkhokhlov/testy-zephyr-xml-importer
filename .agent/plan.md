# Plan (written by Planner each cycle)

Task: ZEP-100 — Importer integration via TestY services

Acceptance criteria:
- create-only skip by attributes.zephyr.key

Assumptions:
- A small adapter layer can hide TestY imports so unit tests run without TestY installed.
- TestY services follow the names referenced in spec_full_ru (TestSuiteService/TestCaseService).

Micro-steps:
- Review current dry-run flow in `zephyr_xml_importer/services/importer.py` and DRF view handling to locate integration points for real import.
- Define a minimal TestY adapter/protocol for suite creation, case lookup by `attributes.zephyr.key`, case creation with steps, label attachment, and file attachment.
- Implement a real TestY adapter with conditional imports (raise a clear runtime error if TestY is unavailable).
- Implement a create-only import path that builds suites from folder paths, skips duplicates via adapter lookup, creates cases + steps, and records report rows/summaries.
- Wire the non-dry-run API path to the new importer and return summary/report consistently with dry-run.
- Add unit tests using an in-memory adapter to validate skip-on-duplicate behavior and report actions.
- Run tests (and optional lint if available).

Files expected to change:
- zephyr_xml_importer/services/importer.py
- zephyr_xml_importer/services (new adapter module)
- zephyr_xml_importer/api/views.py
- tests (new/updated importer integration tests)

Verification steps:
- Run pytest -q.
- If available, run python -m ruff check .
