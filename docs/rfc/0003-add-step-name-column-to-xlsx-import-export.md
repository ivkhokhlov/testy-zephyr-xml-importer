RFC 0003: Add Step Name Column to XLSX Import/Export

Problem statement

TestY steps have a native `name` field (step title/header). Today the importer does not populate
this field from the source data and always auto-generates `Step 1`, `Step 2`, ... during import.
Likewise, the Zephyr Scale compatible XLSX exporter does not include step titles, so step names
cannot be round-tripped via XLSX.

This makes step titles effectively lossy:

- Importing Zephyr XML/XLSX into TestY always produces generic step names.
- Exporting TestY cases to Zephyr Scale XLSX cannot carry TestY step names for later re-import.

Motivation

- Preserve and/or manually define meaningful step titles in TestY without having to rename steps
  post-import.
- Enable a practical “export → edit in XLSX → import” workflow where step titles survive the
  round-trip when the XLSX is used as an interchange format for TestY.
- Keep Zephyr Scale mappings unaffected: extra columns in XLSX are expected to be harmless for
  Zephyr import workflows, while being useful for TestY re-import.

Goals

- Add support for an additional, optional XLSX column that represents the TestY step name
  (`step.name`).
- Export: add an option `include_extra_testy_fields` which, when enabled, includes extra
  TestY-specific columns (starting with step names) in the generated XLSX.
- Import (XLSX only): if the column is present and a cell is non-empty, use it as the TestY step
  name; otherwise fall back to the current `Step {n}` behavior.
- Keep backwards compatibility:
  - importing legacy XLSX files without the new column continues to work
  - XML import behavior remains unchanged

Non-goals

- Adding step-title support for Zephyr XML sources (there is no native field for it in the Zephyr
  XML export format).
- Changing how step scenario/expected result are mapped.
- Enforcing uniqueness or any semantic validation rules for step titles beyond basic trimming.

Proposed design

External behavior / user-facing impact

- XLSX export (`/plugins/zephyr-xml-importer/export/`) adds an export option:
  - `include_extra_testy_fields` (boolean, default false)
  - When false: generate a strict Zephyr-compatible XLSX (current behavior).
  - When true: include extra TestY-specific columns (a superset format) for round-trips back to
    TestY.
- When `include_extra_testy_fields=true`, the export includes one additional step-level column:
  - Header: `Step Name`
  - Meaning: TestY step `name` (human-readable title/header)
  - Scope: step-level; set per step row (rows that contain step content)
- XLSX import (`/plugins/zephyr-xml-importer/import/`):
  - If `Step Name` exists and a row provides a non-empty value, the imported TestY step uses it as
    `name` (title/header).
  - If missing/blank, importer continues to generate `Step {index+1}`.
  - Strictness: `Step Name` alone must not create a step. A row must still contain explicit step
    content (Step/Test Data/Expected Result) to be treated as a step row.
- XML import: unchanged (still generates `Step {index+1}`).

Column placement and compatibility

- The new column is added to the “Test Cases” sheet alongside the existing step-by-step columns.
- When `include_extra_testy_fields=true`, the exporter keeps all existing Zephyr columns and values
  unchanged and appends extra TestY-specific columns at the end.
- The importer detects columns by header name (normalized), so column order changes do not affect
  parsing.

Data model changes

- Extend `ZephyrStep` to carry an optional step title used only for TestY mapping:
  - `title: str | None = None`
- Extend the export payload step model (`ExportStep`) to include:
  - `title: str | None = None`

Parsing (XLSX)

- In `zephyr_xml_importer/services/xlsx_parser.py`:
  - Add a new header role (e.g. `HEADER_STEP_TITLE`) and header detection that recognizes
    `Step Name` (case/spacing-insensitive due to existing normalization).
  - When building a `ZephyrStep` from a row, read the step title cell and store it as
    `ZephyrStep.title`.

Mapping into TestY

- In `zephyr_xml_importer/services/mapping.py`:
  - When building step payloads, set `name` to:
    - `sanitize_html(step.title)` (trimmed) if present and non-empty
    - otherwise `Step {index+1}`

Exporting from TestY (XLSX)

- In `zephyr_xml_importer/services/testy_exporter.py`:
  - Extract the step `name` field from the TestY step model and set it to `ExportStep.title`.
- In `zephyr_xml_importer/services/xlsx_exporter.py`:
  - When `include_extra_testy_fields=true`, append `Step Name` to `XLSX_HEADERS`.
  - Emit `ExportStep.title` per step row when the option is enabled.
  - For non-step cases (plain text / BDD), leave the column empty.

Operational considerations

- No database migrations are required.
- The change is backward compatible for import (column optional).
- Exported XLSX becomes a superset only when `include_extra_testy_fields=true`.

Security and privacy considerations

- Step titles are treated as regular test content; no new sensitive data paths are introduced.
- Sanitization behavior remains consistent with existing import/export (HTML sanitized on mapping).

Implementation plan

1) Add the new step title field to internal models
   - Update `ZephyrStep` to include `title`.
   - Update `ExportStep` to include `title`.

2) Update XLSX parsing to read the new column
   - Implement header detection for `Step Name`.
   - Populate `ZephyrStep.title` while building steps.
   - Ensure legacy files (no column) still parse.

3) Update mapping to populate TestY step names
   - Use `ZephyrStep.title` when present; otherwise keep the existing `Step {n}` default.
   - Keep strictness: do not treat title-only rows as steps, and do not inject the step name into
     step scenario placeholders.

4) Update XLSX export to emit the new column behind an option
   - Add `include_extra_testy_fields` to export API + UI.
   - When enabled, add header and output values from `ExportStep.title`.
   - Extract TestY step `name` into `ExportStep.title`.

5) Tests and documentation
   - Update/add unit tests:
     - XLSX parser recognizes the new column and preserves titles in parsed steps.
     - XLSX export round-trips titles (export → parse).
     - Mapping uses provided title when present, and falls back when absent.
   - Update docs:
     - `docs/mapping.md` (Steps section) to document the new optional column behavior.

Acceptance criteria

- Export UI/API supports `include_extra_testy_fields` (default false).
- When `include_extra_testy_fields=false`, exported XLSX header matches the current Zephyr-compatible
  format (no extra columns added).
- When `include_extra_testy_fields=true`, exported XLSX includes a `Step Name` column in the header
  row.
- When exporting TestY step-based cases, the XLSX contains the step title per step row (from TestY
  step `name`).
- Importing an XLSX that contains `Step Name` populates TestY step names with those values
  (when non-empty).
- Importing an XLSX without the column (or with blank values) preserves the current behavior:
  `Step 1`, `Step 2`, ...
- Importing an XLSX where only `Step Name` is set (and Step/Test Data/Expected are empty) does not
  create a step row.
- XML import behavior remains unchanged.
- Automated tests covering XLSX parsing/export/mapping for step titles pass.

Risks

- Zephyr Scale importers may reject unknown columns in some environments/versions, making the
  exported XLSX less “compatible” than before. Mitigation: keep extra columns behind
  `include_extra_testy_fields` (default false).
- Header-name ambiguity: external tools may rename the column header. Mitigation: accept a small
  set of normalized aliases (e.g. `stepname`) in header detection.
- If TestY enforces any undocumented constraints on step names, import/update may fail at runtime.

Open questions

None.
