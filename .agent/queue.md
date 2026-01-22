# Queue

## Now
 


## Next

## Later
 

## Done
- [x] ZEP-200 — Draft implementation plan for Zephyr XML Importer UI (docs/zep-200-spec.md)
  - Acceptance: `docs/zep-200-plan.md` created with detailed plan for UI endpoints, templates, JS/CSRF behavior, response rendering, CSV download, and project list fallback.
  - Acceptance: plan lists expected files to change and tests to add.
- [x] ZEP-170 — Admin role check: restrict to TestY membership role if required
- [x] ZEP-160 — Dry-run validations: warn on missing folder, empty expected, cap warning preview
- [x] ZEP-150 — Packaging: add [build-system] to pyproject.toml for pip install reliability
- [x] ZEP-140 — XML streaming: avoid full XML in RAM, reduce passes
- [x] ZEP-130 — Suite tree from <folders>: create empty folders before case import
- [x] ZEP-120 — API response contract: summary created/reused/updated/skipped/failed + report_csv/report_url key
- [x] Fix pyproject.toml scope creep: remove Poetry/build-system block or align to spec (Python 3.11)
- [x] ZEP-110 — Mapping fixes: JSON-safe testDataWrapper, description embeds (issues/testdata/attachments), strip labels from create payload
- [x] ZEP-100 — Importer integration via TestY services (acceptance: create-only skip by attributes.zephyr.key)
- [x] ZEP-090 — Dry-run validations + warnings preview (acceptance: detects empty steps, long names, dup keys)
- [x] ZEP-080 — Pluggy hook + TestyPluginConfig + entry point metadata (acceptance: package exposes entrypoint group "testy")
- [x] ZEP-070 — DRF API: serializer + view + admin-only permission (acceptance: request validated, dry-run path works)
- [x] ZEP-060 — Attachments ZIP matcher by basename (acceptance: attaches found, reports missing)
- [x] ZEP-050 — CSV report builder (acceptance: report rows match actions + warnings/errors)
- [x] ZEP-040 — Mapping helpers: non-empty scenario + step placeholders + meta-labels (acceptance: mapping unit tests pass)
- [x] ZEP-032 — Parse steps + labels/issues/attachments + paramType/testDataWrapper (acceptance: fixture parsed fully)
- [x] ZEP-031 — Parse testcase core fields (acceptance: key/id/name/folder/objective/precondition extracted)
- [x] ZEP-030 — Implement streaming folder parser (acceptance: parse folder fullPath+index from XML fixture)
- [x] ZEP-020 — Implement HTML/CDATA sanitizer (acceptance: sanitizer tests for br/li/table/unescape pass)
- [x] ZEP-010 — Define Zephyr dataclasses and parse result shapes (acceptance: typed models + tests import cleanly)
- [x] Fix defusedxml dependency handling so tests can collect (fallback or vendored)
- [x] ZEP-000 — Harness bootstrap: 3-phase prompts + docs + test runner scaffold
