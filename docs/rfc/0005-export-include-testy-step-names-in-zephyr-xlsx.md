RFC 0005: Export: Include TestY Step Names in Zephyr XLSX

Parent RFC

[RFC 0003: TestY Step Names: Import and Export Support](0003-testy-step-names-import-and-export-support.md).

Problem statement

The exporter currently generates a Zephyr Scale compatible XLSX from TestY cases but does not export
TestY step titles (`step.name`). This makes step titles impossible to explicitly retrieve from
exports, and it breaks round-trip workflows where users expect step titles to be preserved.

Motivation

- Enable explicit retrieval of TestY step titles in exported artifacts.
- Support round-trip workflows within this plugin (TestY -> XLSX -> TestY) without losing step
  titles.
- Keep Zephyr XLSX compatibility while still providing an explicit, structured place for TestY-only
  metadata.

Goals

- Add an export option that includes step titles in the XLSX artifact.
- Preserve current behavior by default (no changes unless the new option is enabled).
- Keep the main Zephyr-compatible worksheet unchanged to avoid breaking Zephyr import expectations.
- Provide a deterministic, documented representation that can be parsed back on import (RFC 0004).

Non-goals

- Adding a Zephyr-specific “step title” field (not supported by Zephyr XLSX columns).
- Guaranteeing that Zephyr will preserve step titles if the file is imported into Zephyr and later
  exported back from Zephyr.
- Changing the existing “Test Cases” worksheet mapping for steps (description/test data/expected).

Proposed design

External behavior / user-facing impact

- Export UI (`/plugins/zephyr-xml-importer/export/`):
  - Add a new option: “Include TestY step titles (metadata sheet)”.
- Export API:
  - Add a boolean or enum field controlling whether step titles are included.
  - Default: disabled.

APIs and interfaces (inputs/outputs, contracts)

New export request field (proposal):

- `include_step_names` (boolean, default `false`)
  - When `false`: produce the existing XLSX (single “Test Cases” sheet) unchanged.
  - When `true`: include an additional worksheet that exports step titles alongside identifiers.

XLSX representation (recommended)

- Keep the existing worksheet (e.g., `Test Cases`) unchanged and Zephyr-compatible.
- Add a second worksheet, for example: `TestY Step Names`.
  - Headers (proposal):
    - `Key` (Zephyr key; required for stable join when present)
    - `Case ID` (TestY case id; informational)
    - `Step Sort Order` (integer, 0-based; matches TestY step `sort_order`)
    - `Step Name` (TestY step `name`)
  - One row per step.

Notes:

- This approach avoids polluting Zephyr step descriptions while still providing explicit step-title
  data for users and for round-trip import into TestY (RFC 0004 can treat this sheet as an overrides
  source when present).
- If Zephyr import tooling rejects additional sheets, users can disable this option.

Data extraction rules (TestY -> XLSX)

- For each exported case:
  - Extract steps sorted by `(sort_order, id)` using existing exporter logic.
  - For each step, export:
    - `Key`: `case.attributes.zephyr.key` when available (or synthetic key if enabled by existing
      `key_strategy`).
    - `Case ID`: `case.id`.
    - `Step Sort Order`: `step.sort_order` (integer; default 0 if missing).
    - `Step Name`: `step.name` as stored in TestY.

Operational considerations (config, rollout, observability)

- Add warnings if:
  - a case has steps but has no stable key and `key_strategy=existing_only` (step-title sheet rows
    may not be joinable on import).
  - step names are empty (if allowed) or exceed a conservative length cap (truncate and warn).

Security and privacy considerations (as applicable)

- Step titles may contain sensitive information; keep export admin-only, consistent with existing
  permissions.

Implementation plan

1) Extend export request validation and UI
   - Add `include_step_names` to `api/serializers.py` export request validation and DRF serializer.
   - Add a checkbox in `templates/zephyr_xml_importer/export.html` and thread it through the request.

2) Extract step names in exporter pipeline
   - Extend `services/testy_exporter.py` to read `step.name` in addition to `scenario`/`expected`.
   - Decide how to represent step titles for cases without keys under different `key_strategy` modes.

3) Write a metadata worksheet
   - Extend `services/xlsx_exporter.py` to optionally add a second sheet with step-title rows and
     stable headers.
   - Keep the existing sheet’s headers and row layout unchanged.

4) Tests and docs
   - Add unit tests verifying:
     - default export unchanged when `include_step_names=false`
     - when enabled, the second sheet exists with expected headers and rows
   - Update `docs/usage.md` and/or `docs/mapping.md` to document the new option and its limitations.

Acceptance criteria

- Export without the new option produces the same XLSX structure as today (backwards compatible).
- Export with `include_step_names=true` produces an XLSX with an additional `TestY Step Names` sheet
  containing one row per step with `Key`, `Case ID`, `Step Sort Order`, and `Step Name`.
- Export remains functional and Zephyr-compatible for the main `Test Cases` sheet.
- The step-title metadata is sufficient for the importer to restore titles when re-importing the
  plugin’s own export artifacts (given stable keys).

Risks

- Zephyr import tooling may fail or behave unexpectedly when extra worksheets are present.
- If cases have no stable keys, step-title metadata may not be joinable on import without additional
  identifiers (case id is TestY-specific and not present in Zephyr-originated files).
- Step sorting differences between TestY and Zephyr (e.g., missing/duplicate `sort_order`) could
  misalign titles if join keys are insufficient.

Open questions

- Should the metadata sheet join key include both `Key` and `Name` to provide a fallback when keys
  are missing, at the risk of ambiguity?
- Should `include_step_names` be a boolean, or an enum to allow future modes (e.g., in-band encoding
  in the step description)?
