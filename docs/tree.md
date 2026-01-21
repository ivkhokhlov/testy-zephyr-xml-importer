# Project tree (curated)

- `AGENTS.md` — persistent instructions for agents
- `.agent/` — durable state for loop runs
  - `PROJECT.md` — single source of truth (edit per environment)
  - `queue.md` — backlog (Judge marks done)
  - `plan.md` — current plan (Planner writes each cycle)
  - `worker_report.md` — what Worker did
  - `judge_feedback.md` — what to do next
  - `progress.md` — append-only log
- `docs/`
  - `spec.md` — concise spec
  - `spec_full_ru.md` — full RU spec (reference)
  - `dev.md` — how to run locally
  - `tree.md` — this file
- `zephyr_xml_importer/` — plugin package
- `tests/` — unit tests
- `scripts/` — loop helper scripts

