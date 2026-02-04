RFC 0003: TestY Step Names: Import and Export Support

Problem statement

The importer currently assigns TestY step names automatically as `Step 1`, `Step 2`, etc. This is
lossy and often unhelpful because TestY supports meaningful, user-defined step names (titles).

Additionally, the exporter currently ignores TestY step names when generating a Zephyr Scale
compatible XLSX file. As a result, step names cannot be explicitly retrieved from exports, and
round-tripping (TestY -> XLSX -> TestY) loses step titles.

Motivation

- Improve readability and maintainability of imported step-by-step cases in TestY by supporting
  meaningful step titles instead of generic `Step N`.
- Preserve user intent: step titles often capture the purpose of an action at a glance.
- Enable round-trip and backup workflows where step titles can be exported and later restored.
- Keep Zephyr compatibility while still allowing TestY-specific metadata to be carried along in a
  well-defined, explicit way.

Goals

- Add an explicit way to define TestY step names during import (XML and XLSX inputs).
- Add an explicit way to include/retrieve TestY step names during export to Zephyr-compatible XLSX.
- Keep current behavior as the default (no behavior change unless options are provided/enabled).
- Ensure the representation is deterministic, testable, and does not require network calls.
- Provide clear validation and warnings when step-name inputs are malformed or cannot be applied.

Non-goals

- Building a full interactive “step editor” UI for per-step manual editing inside the import page.
- Attempting to store step titles in Zephyr Scale as a first-class field (Zephyr XLSX has no native
  step-title column).
- Automatic semantic summarization of steps (e.g., ML-based title generation).
- Two-way sync between TestY and Zephyr beyond producing/importing static artifacts.

Scope boundaries

- Import concerns (request fields, parsing, naming strategy, applying to `step.name`) are covered by
  RFC 0004.
- Export concerns (extracting `step.name` from TestY and embedding it into the XLSX artifact) are
  covered by RFC 0005.
- This RFC defines the shared intent, compatibility constraints, and the cross-RFC interface for how
  step titles are represented in XLSX exports to make them recoverable on import.

Child RFCs

- [RFC 0004: Import: Custom Step Names for TestY Steps](0004-import-custom-step-names-for-testy-steps.md)
  - Add import-time support for explicit step titles (manual overrides and safe templates).
- [RFC 0005: Export: Include TestY Step Names in Zephyr XLSX](0005-export-include-testy-step-names-in-zephyr-xlsx.md)
  - Add export-time support to include step titles in a Zephyr-compatible XLSX artifact.

Sequencing

1) Implement import-side support first (RFC 0004) so the system can consume explicit step-title
   inputs and can later restore step titles from exported artifacts.
2) Implement export-side support next (RFC 0005) to produce artifacts that include step titles in a
   deterministic, well-documented way.

Work checklist

- [ ] Define step-title data model and shared XLSX representation constraints. [RFC 0003: TestY Step Names: Import and Export Support](0003-testy-step-names-import-and-export-support.md)
- [ ] Document step-title precedence rules (overrides > template > default). [RFC 0003: TestY Step Names: Import and Export Support](0003-testy-step-names-import-and-export-support.md)
- [ ] Add import request fields and apply step-title mapping to `step.name`. [RFC 0004: Import: Custom Step Names for TestY Steps](0004-import-custom-step-names-for-testy-steps.md)
- [ ] Add XLSX parser support for reading exported step-title metadata (when present). [RFC 0004: Import: Custom Step Names for TestY Steps](0004-import-custom-step-names-for-testy-steps.md)
- [ ] Add export request fields to enable step-title inclusion. [RFC 0005: Export: Include TestY Step Names in Zephyr XLSX](0005-export-include-testy-step-names-in-zephyr-xlsx.md)
- [ ] Export step-title metadata into the XLSX artifact without breaking the Zephyr-compatible sheet. [RFC 0005: Export: Include TestY Step Names in Zephyr XLSX](0005-export-include-testy-step-names-in-zephyr-xlsx.md)

Proposed design

External behavior / user-facing impact

- Import (UI/API):
  - Add optional inputs to define TestY step titles:
    - A safe template for generating titles.
    - Optional per-case/per-step overrides (CSV/JSON) to explicitly set titles.
  - Default remains unchanged: step titles are generated as `Step {index+1}`.
- Export (UI/API):
  - Add an option to include TestY step titles in the exported XLSX artifact.
  - Default remains unchanged: existing exports continue to be Zephyr-compatible and do not include
    TestY-specific step-title metadata unless explicitly enabled.

APIs and interfaces (inputs/outputs, contracts)

- Import will accept optional step-title inputs (see RFC 0004 for exact request fields and formats).
- Export will accept an option to include step-title metadata (see RFC 0005 for exact request fields).
- Shared representation constraint:
  - The primary “Zephyr Scale compatible” worksheet must remain structurally compatible with Zephyr
    Scale’s XLSX expectations (headers and main sheet data).
  - Step-title data must be carried either:
    - out-of-band (recommended): an additional worksheet that Zephyr can ignore, or
    - in-band (optional): encoding in step description text with a stable marker (only if explicitly
      enabled due to visible user impact in Zephyr).

Data model changes (if any)

- No persistent database changes are required in this plugin.
- Step titles are stored in TestY’s existing step model field (`name`) and are read/written via the
  existing create/update case-with-steps flows.

Operational considerations (config, rollout, observability)

- Rollout is additive and backwards compatible:
  - New request fields are optional with defaults preserving current behavior.
  - Export includes step titles only when the new flag is enabled.
- Add warnings for:
  - step-title override rows that do not match any case or reference invalid step indices
  - titles that exceed TestY field limits (if known) or exceed a conservative length cap

Security and privacy considerations (as applicable)

- Step titles may contain sensitive information; exporting them should remain admin-only and scoped
  to the selected project, consistent with existing export permissions.
- Importing from user-supplied override files must avoid code execution; template substitution must
  be purely string-based with an allowlist of variables.

Implementation plan

1) Define shared rules and constraints
   - Define precedence: explicit per-step overrides > template-generated titles > default `Step N`.
   - Define normalization and safety rules (trimming, collapsing whitespace, conservative max length).

2) Implement import support (RFC 0004)
   - Extend import request validation and importer pipeline to accept step-title inputs.
   - Apply titles to the mapped payload’s `steps[].name` before writing to TestY.

3) Implement export support (RFC 0005)
   - Extend export request validation and exporter pipeline to include step titles in the XLSX
     artifact when enabled, without changing the main Zephyr-compatible sheet by default.

4) Documentation
   - Update mapping and usage documentation to explain how step titles are generated and how to
     override/include them for round-trip workflows.

Acceptance criteria

- Import supports explicit step titles (template and/or overrides) while keeping the default behavior.
- Export can explicitly include TestY step titles in the generated XLSX artifact behind an option.
- Exported step titles can be restored on import (when using the plugin’s own exported artifacts).
- Existing imports/exports continue to work unchanged when the new options are not used.

Risks

- Zephyr Scale importer behavior around additional worksheets is unknown; adding a “metadata” sheet
  could be ignored, or it could break some Zephyr import flows.
- In-band encoding of step titles (if implemented) may clutter step descriptions in Zephyr and could
  confuse users; it must be opt-in.
- TestY step title length/validation rules may differ by version; conservative truncation may still
  be lossy.

Open questions

- What are the exact validation rules for TestY step `name` (max length, allowed characters, whether
  empty is allowed)?
- Does Zephyr Scale (Jira DC) XLSX import ignore additional worksheets, or does it require a single
  specific sheet name/order?
- Should the default title strategy be changed from `Step N` to something more descriptive (e.g.,
  derived from the first line of the step scenario), or should we keep `Step N` as the default
  indefinitely for backwards compatibility?

