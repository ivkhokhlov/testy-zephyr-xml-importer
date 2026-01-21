# AGENTS.md — TestY Zephyr Scale XML Importer (loop-driven)

This repository is intended to be worked on by autonomous coding agents in a loop (Planner → Worker → Judge).
State MUST be persisted in `.agent/` because each run starts with limited chat context.

## Project goal
Build a native TestY plugin (TestY v2.1.2 / Python 3.11.9) that imports **Zephyr Scale XML export (Jira DC plugin)** into a selected TestY project via a REST endpoint, with dry-run support.

Authoritative spec:
- `docs/spec.md` (concise, authoritative)
- `docs/spec_full_ru.md` (full original RU spec; reference only)

## Non-negotiable rules
- Do not touch anything outside the repo.
- Do not read secrets; do not access ~/.ssh, env secrets, password stores.
- Do not use the network unless explicitly allowed in `.agent/PROJECT.md`.
- Always keep changes incremental and reviewable.
- Always run tests at the end of each Worker iteration.

## Commands
- Tests: `pytest -q`
- Lint (optional): `python -m ruff check .`
- Format (optional): `python -m ruff format .`

If ruff is not installed, lint/format may be skipped; tests must still run.

## Code style
- Python 3.11+
- Use type hints and `dataclasses` for parsed Zephyr entities.
- Prefer pure functions for parsing/sanitization/mapping (unit-testable without TestY).
- Isolate TestY-specific imports behind small adapters so unit tests can run without TestY installed.

## Definition of Done (high level)
- Plugin appears in `GET /plugins/` in TestY when installed.
- `POST /plugins/zephyr-xml-importer/import/` supports:
  - dry-run (no DB writes)
  - real import (creates suites/cases/steps/labels, attachments when ZIP provided)
  - idempotency: create-only by default (skip duplicates by `attributes.zephyr.key`), optional upsert
- Correct mapping rules per `docs/spec.md`
- CSV report produced (at least “one row per testcase”)

## Where state lives (must update each cycle)
- `.agent/queue.md` — backlog (Judge marks done)
- `.agent/plan.md` — current task plan (Planner writes)
- `.agent/worker_report.md` — what was implemented (Worker writes)
- `.agent/judge_feedback.md` — actionable feedback for next Worker attempt (Judge writes)
- `.agent/progress.md` — append-only log

## Scope note
Early iterations should focus on:
1) XML streaming parser (defusedxml iterparse)
2) HTML→text sanitizer (deterministic)
3) Mapping logic and validations (no empty scenarios)
Only then implement TestY/DRF integration.
