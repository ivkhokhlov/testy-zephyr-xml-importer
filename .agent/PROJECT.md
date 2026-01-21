# PROJECT (single source of truth for the harness)

PROJECT_NAME: "testy-zephyr-xml-importer"
REPO_KIND: "new repo"

## Brief
Build a native TestY plugin (TestY v2.1.2 / Python 3.11.9) that imports Zephyr Scale XML export into TestY.
Admin uploads one XML (and optional ZIP with attachments) and triggers a synchronous import into a selected TestY project.
Dry-run mode must validate and report warnings without DB writes.

## Primary stack
Python 3.11.9
- defusedxml for streaming XML parsing
- Django REST Framework endpoints (when integrating into TestY)
- pytest for unit tests
- (optional) ruff for lint/format

## Commands
TEST_CMD: "pytest -q"
LINT_CMD: "python -m ruff check ."
FORMAT_CMD: "python -m ruff format ."
RUN_CMD: ""

## Policies
DO_NOT_TOUCH_OUTSIDE_REPO: true
NETWORK_ALLOWED: "no"
AUTO_COMMIT: "yes"

## Budgets (soft)
PLANNER_MAX_MINUTES: 2
WORKER_MAX_MINUTES: 12
JUDGE_MAX_MINUTES: 3

## Definition of Done (global)
- Parser + sanitizer + mapping unit tests pass
- Dry-run returns correct summary + warnings preview and writes nothing
- Import creates:
  - suites hierarchy
  - cases in correct suites
  - steps with non-empty scenario
  - labels (+ meta-labels for status/priority/owner)
  - attachments from ZIP when available
- CSV report produced (one row per testcase)
- Admin-only permissions enforced

## Optional notes
- Keep TestY-specific imports behind adapters so unit tests can run without TestY installed.
- Prefer deterministic HTML sanitization (no heavy HTML parser dependency unless truly needed).
- Exapmle of Zepyr import .xml file tmp/zephyr-scale-tests-export288313852528022991.xml
