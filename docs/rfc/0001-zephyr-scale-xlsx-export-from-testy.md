RFC 0001: Zephyr Scale XLSX Export from TestY

Problem statement

The plugin currently supports importing Zephyr Scale exports (XML/XLSX, Jira DC) into a selected TestY
project, but it does not support exporting TestY data back into Zephyr Scale. This blocks reverse
migrations and makes it hard to move test cases from TestY to Zephyr Scale without manual copy/paste
or custom one-off scripts.

Motivation

- Enable bidirectional migration (Zephyr Scale <-> TestY) using a supported, shareable artifact (XLSX).
- Reduce user friction when switching tools or consolidating projects.
- Reuse the plugin’s existing mapping knowledge (folders, steps, labels) to produce consistent output.
- Provide a deterministic, admin-only export flow aligned with the current import UI/API.

Goals

- Add an admin-only export capability that generates an XLSX file compatible with Zephyr Scale’s
  test case import expectations (Jira DC).
- Export TestY suites/cases into Zephyr Scale “folders” and “test cases” while preserving hierarchy.
- Support step-by-step test cases (rows per step) and non-step test scripts (plain text; BDD optional).
- Preserve Zephyr metadata when available (round-trip friendliness) by preferring
  `case.attributes.zephyr.*` and/or `zephyr:*` meta-labels.
- Provide validation/warnings for unsupported or lossy mappings (e.g., overly long cells, empty steps).

Non-goals

- Full two-way sync, incremental updates, or conflict resolution between systems.
- Exporting executions (test cycles/runs/results) or linking to Jira issues beyond basic key lists.
- Exporting binary attachments (file contents). At most, export attachment names/notes if feasible.
- Perfect field-level fidelity for data that does not exist in TestY or was previously flattened during
  import (e.g., separating Zephyr “Objective” vs appended metadata).

Proposed design

External behavior / user-facing impact

- Add a new page and API endpoint for export:
  - UI: `/plugins/zephyr-xml-importer/export/` (admin-only).
  - API: `POST /plugins/zephyr-xml-importer/export/` returns an `.xlsx` file as an attachment.
- The export UI allows selecting a TestY project and optional filters (scope selection) and triggers a
  file download.

APIs and interfaces (inputs/outputs, contracts)

- Request fields (initial proposal; exact names to match existing serializer style):
  - `project_id` (required)
  - `suite_id` (optional) and `include_children` (default true) to export a subtree
  - `case_ids` (optional) to export an explicit list
  - `strip_zephyr_key_prefix` (default true): remove leading `"[KEY] "` from case names
  - `metadata_source` (default `attributes_then_meta_labels`):
    - prefer `attributes.zephyr.*` if present, else parse `zephyr:status=...`, etc.
  - `key_strategy` (default `existing_only`):
    - `existing_only`: populate Zephyr “Key” only when known
    - `synthetic`: generate stable synthetic keys for row grouping (see Risks/Open questions)
- Response:
  - Success: `200` with `Content-Type:
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` and
    `Content-Disposition: attachment; filename="zephyr-scale-export-<project>-<date>.xlsx"`.
  - Failure: `400` JSON error response following the existing import error shape.

Data model changes (if any)

- None required. The exporter reads TestY suites/cases/steps/labels and produces an XLSX artifact.
- Optional future enhancement (out of scope): persist export job state for large projects.

Operational considerations (config, rollout, observability)

- Rollout is additive: new endpoint(s) and template(s) only; no breaking changes to import.
- Use the existing admin permission (`IsAdminForZephyrImport`) to protect export endpoints.
- Add structured warnings in logs (and optionally in a JSON “dry-run export” mode later) for:
  - fields exceeding Excel cell limits (~32k characters)
  - cases with empty required fields (name, scenario/steps)
  - unsupported formatting (HTML that must be stripped)

Security and privacy considerations (as applicable)

- Export is restricted to admins; ensure the endpoint cannot be used by non-admin users.
- Ensure project scoping is enforced server-side (no exporting another project by passing IDs).
- Avoid embedding sensitive internal identifiers unless required (prefer Zephyr keys when known).

XLSX format and mapping rules

The exporter will generate a workbook that matches (as closely as possible) the Zephyr Scale XLSX
format this plugin already parses (via `services/xlsx_parser.py`). The initial implementation will use
a single worksheet with a stable header order.

Suggested columns (minimum viable set; names chosen to align with existing parser heuristics):

- `Key`
- `Name`
- `Status`
- `Precondition`
- `Objective`
- `Folder`
- `Folder Description`
- `Priority`
- `Labels`
- `Owner`
- `Issues`
- `Test Script (Step-by-step) Step`
- `Test Script (Step-by-step) Test Data`
- `Test Script (Step-by-step) Expected Result`
- `Test Script (Plain Text)`
- `Test Script (BDD)`

Mapping (TestY -> Zephyr Scale XLSX):

- Folder path:
  - Derive Zephyr `Folder` by walking the suite parent chain and joining suite names with `/`.
  - If a case is in the project root (no suite), export `Folder` as empty.
  - Export `Folder Description` from the suite description for the folder associated with the case’s
    suite path (best-effort).
- Test case identity:
  - If the case originated from Zephyr import and has `attributes.zephyr.key`, export it as `Key`.
  - Otherwise, leave `Key` empty by default (see Open questions for Zephyr behavior).
  - Export `Name` from the TestY case name; optionally strip the `[KEY] ` prefix used on import.
- Test case content:
  - `Precondition` from TestY `setup` (sanitized to plain text).
  - `Objective` from TestY `description` (sanitized to plain text).
  - Script type:
    - If `is_steps` is true and steps exist: export as step-by-step rows.
    - Else: export as plain text in `Test Script (Plain Text)` from TestY `scenario`.
    - Optional future: detect BDD and populate `Test Script (BDD)` instead.
- Steps:
  - One row per step.
  - First row contains case-level fields plus step fields.
  - Subsequent rows may omit repeated case-level fields (closer to Zephyr export style) while
    continuing to populate step columns.
  - Map step fields by reversing the importer’s formatting:
    - If a step scenario contains the delimiter `\\n\\nTest data:\\n`, split it into
      `Step` (description) and `Test Data`. Otherwise, put the whole scenario into `Step`.
    - Map TestY step `expected` to `Expected Result`.
- Labels and metadata:
  - `Labels` is a comma-separated list of non-meta TestY labels.
  - `Status`, `Priority`, `Owner` are populated using:
    - `attributes.zephyr.status|priority|owner` if present, else
    - `zephyr:status=...`, `zephyr:priority=...`, `zephyr:owner=...` meta-labels if present.
  - `Issues` is populated from `attributes.zephyr.issues[].key` when available.

Implementation plan

1) Add a Zephyr XLSX exporter service
   - Implement `services/xlsx_exporter.py` that can build an XLSX workbook (openpyxl write-only) from
     an in-memory list of “export rows”.
   - Enforce Excel cell constraints and produce a warnings list.
   - Prefer generating an XLSX that can be parsed by `iter_test_cases_xlsx` (self-consistency).

2) Add TestY data extraction for export
   - Add a small “read adapter” (separate from `BaseTestyAdapter` to avoid breaking import)
     that loads suites/cases/steps/labels using the Django ORM when running inside TestY.
   - Support scoping: by project, optional suite subtree, optional explicit case IDs.

3) Add API endpoint and serializer
   - Add `ExportRequestData` validation in `api/serializers.py` (parallel to import).
   - Add `ExportView` in `api/views.py`:
     - `GET` renders a new template with project selection and export options.
     - `POST` returns an XLSX file response.
   - Register the endpoint in `api/urls.py`.

4) Add HTML UI
   - Add a new template `templates/zephyr_xml_importer/export.html` (or extend the existing import
     page with an Export panel) to trigger export and download the XLSX.

5) Add tests and docs
   - Add unit tests that:
     - generate an XLSX from a small in-memory representation and load it back using
       `iter_test_cases_xlsx`, asserting that the parsed cases match the intended structure.
   - Update `docs/usage.md` with export instructions and example `curl` usage.

Acceptance criteria

- An admin can export a TestY project (or subset) into an `.xlsx` file via UI and API.
- The exported XLSX includes folders, cases, and steps in the expected Zephyr Scale layout.
- The exported XLSX can be parsed by this plugin’s existing XLSX parser without errors.
- Manual verification: importing the exported XLSX into Zephyr Scale (Jira DC) creates/updates test
  cases with correct names, folders, steps, and labels (within documented limitations).
- Export fails safely with a clear error when run outside a TestY runtime (no ORM/services available).

Risks

- Zephyr Scale import expectations may differ from Zephyr Scale export structure (different required
  headers, sheets, or semantics). This could require adjusting the exporter to a dedicated “import
  template” rather than mirroring exports.
- For new TestY cases without Zephyr keys, leaving `Key` empty may not be acceptable to Zephyr, or
  synthetic keys may be rejected. This impacts the minimum viable export strategy.
- Large projects may produce very large workbooks; memory usage and runtime must be managed
  (write-only mode, streaming response if needed).
- Round-trip lossiness is possible due to earlier sanitization and flattening of data on import.

Open questions

- Does Zephyr Scale (Jira DC) support importing test cases via XLSX directly, and if so, does it
  accept the same structure as its XLSX export?

Same structure

- If `Key` is empty, can Zephyr create new test cases? If not, what identifier should be used for
  new cases and for grouping step rows?

It can create new cases

- Are there additional required columns (e.g., component, automation status, custom fields) that must
  be present for successful import in common Zephyr deployments?

I dont know, you should research it


- How should folder descriptions be handled when multiple suites share the same path, or when suites
  have rich-text descriptions that require sanitization/truncation?

I dont know, you should research it
