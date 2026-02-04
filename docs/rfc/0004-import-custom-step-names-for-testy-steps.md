RFC 0004: Import: Custom Step Names for TestY Steps

Parent RFC

[RFC 0003: TestY Step Names: Import and Export Support](0003-testy-step-names-import-and-export-support.md).

Problem statement

When importing Zephyr Scale XML/XLSX, the plugin currently assigns TestY step titles automatically as
`Step 1`, `Step 2`, etc. Zephyr exports do not include a dedicated step-title field, but TestY steps
do have a `name` field that can store meaningful titles. Users want to explicitly define those step
titles at import time.

Motivation

- Improve imported test case quality in TestY by making steps easier to scan (meaningful titles).
- Avoid manual, post-import edits in TestY for large sets of cases.
- Support deterministic, repeatable imports by providing explicit inputs for step-title generation.
- Enable round-trip restoration of step titles from the plugin’s own exports (see RFC 0005).

Goals

- Add optional import-time support for custom step titles written to `steps[].name` in the TestY
  payload.
- Support both Zephyr XML and Zephyr XLSX imports.
- Provide at least two mechanisms:
  - Safe template-based generation for most cases.
  - Explicit per-case/per-step overrides for full control.
- Keep defaults unchanged if no step-title configuration is provided.
- Emit warnings (not hard failures) when override inputs are partially invalid (unknown case, bad
  step index), while still importing the rest.

Non-goals

- Building an interactive per-step editor UI (grid) inside the import page.
- Inferring titles using NLP/ML or external services.
- Changing how step `scenario`/`expected` fields are mapped, beyond what’s required to set the title.

Proposed design

External behavior / user-facing impact

- Import UI (`/plugins/zephyr-xml-importer/import/`):
  - Add an optional “Step titles” section with:
    - `step_name_template` (text input; optional)
    - `step_name_overrides` (file upload; optional; CSV or JSON)
  - Provide inline help with examples and precedence rules.
- Import API:
  - Accept the same optional fields in `POST` payload.

APIs and interfaces (inputs/outputs, contracts)

New import request fields (names are proposals; final naming should match existing serializer style):

- `step_name_template` (optional string)
  - Safe formatting with an allowlist of variables (no code execution).
  - Suggested variables:
    - `{index}`: 1-based step index
    - `{index0}`: 0-based step index
    - `{key}`: Zephyr test case key (if present)
    - `{case_name}`: Zephyr test case name (raw, before prefixing)
    - `{description}`: Zephyr step description (sanitized)
    - `{expected}`: Zephyr expected result (sanitized)
  - If the result is empty after trimming, fall back to default `Step {index}`.

- `step_name_overrides` (optional file: `.csv` or `.json`)
  - CSV format (recommended for humans):
    - Header row required: `key,step_index,name`
    - `step_index` is 1-based to be user-friendly.
    - Example:
      - `ES-T560,1,Open login page`
      - `ES-T560,2,Login as admin`
  - JSON format (recommended for API automation):
    - Array of objects: `{ "key": "ES-T560", "step_index": 1, "name": "Open login page" }`
    - Same 1-based indexing semantics.

Precedence and application:

- For each imported test case:
  1) If an override exists for `(key, step_index)`, use it.
  2) Else, if `step_name_template` is provided, render it and use it.
  3) Else, use current default: `Step {index+1}`.

Validation and warnings:

- If an override row references a case key not present in the import payload, add a warning and skip
  that override row.
- If an override row references a step index out of bounds for the target case, add a warning and
  skip that override row.
- If a generated/overridden title exceeds a conservative max length cap (e.g., 255 chars), truncate
  and warn (exact cap may be adjusted once TestY constraints are confirmed).

Compatibility notes:

- XML imports rely on Zephyr `testCase key="..."` as the case identifier for overrides.
- XLSX imports rely on the `Key` column value when present; if `Key` is missing, overrides cannot be
  reliably applied. In that case:
  - Use template-only titles, or
  - Optionally support overrides keyed by case name as a fallback (deferred unless needed).

Data model changes (if any)

- No changes to persistent storage in this plugin.
- The import pipeline will modify the mapped payload so that `steps[].name` uses the resolved titles.

Operational considerations (config, rollout, observability)

- All new request fields are optional and default to existing behavior.
- Dry-run mode should include step-title warnings in the warnings list / CSV report (as applicable).

Security and privacy considerations (as applicable)

- Template rendering must not allow code execution:
  - Implement via a strict `str.format_map`-style replacement on an allowlisted dict.
  - Do not allow arbitrary expressions, imports, or attribute access.
- Override files may contain sensitive text and should be processed in-memory without persistence.

Implementation plan

1) Extend request validation and serializers
   - Add optional fields to `api/serializers.py` import request validation and DRF serializer (when
     available).
   - Add basic file-type detection for overrides (`.csv` vs `.json`) and parse into a normalized
     in-memory structure: `dict[(key, step_index0)] -> title`.

2) Implement step-title resolution in mapping
   - Extend `services/mapping.build_testy_payload_from_zephyr(...)` to accept optional step-title
     inputs (template + overrides) and set `steps[].name` accordingly.
   - Keep `scenario`/`expected` mapping unchanged.

3) Wire through importer and dry-run
   - Thread new request fields through `services/importer.py` and `api/views.py` to mapping.
   - Ensure warnings are collected and surfaced in the existing warnings output.

4) UI updates
   - Add new inputs to `templates/zephyr_xml_importer/import.html` with help text and examples.

5) Tests and documentation
   - Add unit tests for:
     - default behavior unchanged (still `Step N`)
     - template titles applied
     - overrides applied and precedence over template
     - warnings for unknown case keys / invalid indices
   - Update `docs/mapping.md` and `docs/usage.md` to document step-title behavior.

Acceptance criteria

- With no new fields provided, step titles remain `Step 1`, `Step 2`, etc (backwards compatible).
- With `step_name_template` provided, imported TestY payload contains computed `steps[].name` values.
- With `step_name_overrides` provided, imported TestY payload contains overridden `steps[].name`
  values for matching case keys and step indices.
- Invalid override rows do not fail the entire import; they produce warnings and are skipped.

Risks

- Zephyr XLSX exports may omit `Key` for some rows; applying overrides in that situation may be
  impossible or ambiguous.
- TestY may enforce stricter constraints on step titles than assumed (length/requiredness).
- Users may expect overrides keyed by something other than Zephyr key (e.g., case name); supporting
  that safely may require additional disambiguation rules.

Open questions

- Should overrides support `zephyr_id` in addition to `key` to handle missing/duplicate keys?
- What conservative max length should be used for step titles before TestY constraints are confirmed?
- Should the importer support overrides keyed by case name (and if so, how to handle duplicates)?

