RFC 0004: Tree-Based Multi-Suite Selector for Export

Problem statement

The Export UI currently supports scoping by a single `suite_id` via a manual numeric input. This
creates two usability problems:

- Users often do not know suite ids and must switch context to find them.
- Exporting multiple suites requires repeated exports (one suite id at a time), which is slow and
  error-prone.

We want a tree-based suite selector with checkboxes so a user can manually select one or many
suites (by id) directly in the Export UI.

Motivation

- Reduce friction and mistakes when scoping exports.
- Enable “export several areas at once” workflows without requiring users to remember or look up
  suite ids.
- Make the export scope more discoverable by showing the suite hierarchy (parent/child suites).

Goals

- Add a tree-based suite selector (checkboxes) to the Export UI that supports selecting one or many
  suites.
- Suite selection uses standard tree checkbox behavior: selecting a suite selects all of its
  descendants (and unselecting unselects all descendants).
- Add a search filter in the suite selector (by suite name and/or full suite path).
- Extend the Export API to accept multiple suite ids in a backward-compatible way.
- Fully move suite scoping in the UI to the tree selector (no manual suite id input).
- Keep the existing `suite_id` field working for API clients.
- Do not impose a maximum selection size in the UI/API; users may export the full project scope.
- Keep the implementation dependency-free (vanilla JS, no external frontend libraries).

Non-goals

- Adding suite selection to the Import flow.
- Supporting “include children but exclude some descendants” (include/exclude semantics).
- Editing suites (create/rename/move) from this plugin.
- Changing export formatting, mappings, or XLSX structure.

Proposed design

External behavior / user-facing impact

- Export page (`/plugins/zephyr-xml-importer/export/`) adds a “Suites (optional)” section:
  - After selecting a project, the UI loads the project suite tree and renders it as a nested list.
  - Users can select one or many suites via checkboxes.
  - The UI shows a small “Selected: N suites” indicator and can optionally show the selected ids.
  - Checking a suite checkbox selects the suite and all of its descendants (and unchecking
    unselects all descendants). Parent checkboxes use an `indeterminate` state for partial
    selection.
  - The suite list is sorted by full suite path for stable navigation.
  - The suite selector includes a text search filter to quickly find suites by name/path.
  - The existing “Suite id (optional)” numeric input is removed from the UI (suite scoping is
    performed via the tree selector).

API and interfaces

Export endpoint (existing)

- Endpoint: `POST /plugins/zephyr-xml-importer/export/` (multipart form).
- Add a new optional field:
  - `suite_ids` (optional): comma-separated list of suite ids (e.g. `10,12,15`).
- Backward compatibility:
  - `suite_id` (existing, optional) continues to work unchanged.
  - If `suite_ids` is present and non-empty, it takes precedence over `suite_id`.
  - `include_children` (existing) remains supported for the `suite_id` path.

Suite tree endpoint (new)

- Endpoint: `GET /plugins/zephyr-xml-importer/suites/`
- Query params:
  - `project_id` (required): project id to list suites for.
- Response (JSON):
  - `status: "success" | "failed"`
  - `suites: [{ id, name, parent_id, description? }]` on success
  - `errors` on failure (same error shape conventions as other plugin endpoints)
- Access control:
  - Reuse `IsAdminForZephyrImport` to keep this data admin-only (consistent with other endpoints).
- Data scope:
  - Only suites within the requested `project_id` are returned.
  - Fields are limited to those needed for navigation and display (no case data).

Data model changes

- Extend `ExportRequestData` to include `suite_ids: list[int] | None`.
- No database migrations.

Backend selection semantics

- If no suite filter is provided (`suite_ids` absent/empty and `suite_id` absent): export all suites
  in the project (current behavior).
- If suite filter is provided:
  - If `suite_ids` is provided:
    - Treat it as an explicit set of suites to include (exact match).
    - Ignore `include_children` to avoid surprising behavior; descendants must be present in
      `suite_ids` to be included (the UI handles this via cascading selection).
  - Else, if `suite_id` is provided:
    - Keep the current behavior: if `include_children=true`, include descendants (include-self);
      otherwise only the given suite.
- Validation:
  - Every provided suite id must exist in the target project; otherwise fail the export with a
    clear error.
  - Deduplicate suite ids.

Frontend (Export UI) design

- Data loading:
  - On project selection change, request `GET ../suites/?project_id=<id>` with
    `credentials: "same-origin"`.
  - Render a loading state and handle endpoint errors gracefully.
- Rendering:
  - Build a tree from `{id, parent_id}` and display it as a nested list.
  - Sort nodes by full suite path (computed from parent pointers), case-insensitive.
  - Each node row displays:
    - checkbox
    - suite name
    - suite id (muted, for discoverability)
    - optional description tooltip/expander (optional; can be deferred)
  - Parent checkboxes reflect partial selection via the `indeterminate` state.
- Controls (minimum viable set):
  - “Clear selection” button.
  - “Select all” button (optionally scoped to current filter).
  - Search filter by suite name/path.
- Form submission:
  - When at least one suite is selected, submit `suite_ids` as a comma-separated string.
  - When none are selected, omit `suite_ids` (export remains unscoped unless `suite_id` is used).

Operational considerations

- Performance:
  - Suite trees can be large; the initial implementation loads all suites for a project in one
    request.
  - The UI renders collapsed by default (only root nodes expanded) to reduce DOM work.
  - If needed, add server-side paging later.
- Observability:
  - Log suite endpoint failures and export validation failures with enough context (project id,
    requested suite ids count), without logging sensitive content.

Security and privacy considerations

- The suite list endpoint is admin-only and scoped by `project_id`.
- Do not expose attachments, case content, or any cross-project data.
- Avoid reflecting raw server errors to the UI; return structured `errors` payloads consistent with
  existing endpoints.

Implementation plan

1) Extend export request validation to accept multi-suite input
   - Update `ExportRequestData` with `suite_ids`.
   - Update `validate_export_request` to parse `suite_ids` (comma-separated string) and apply
     precedence over `suite_id`.
   - Keep `suite_id` support for backwards compatibility.
   - Update DRF `ExportRequestSerializer` to align with multipart reality (accept string for
     `suite_ids` and `case_ids`, deferring parsing to `validate_export_request`).

2) Update export selection logic to handle multiple suites
   - Extend `export_testy_cases_to_xlsx(...)` and/or `collect_testy_cases_for_export(...)` to accept
     `suite_ids`.
   - Treat `suite_ids` as an explicit selection set (no descendant expansion).
   - Validate suite existence within the target project for all ids.

3) Add suite tree API endpoint
   - Add `SuitesView` (admin-only) under `zephyr_xml_importer/api/views.py`.
   - Add URL route `suites/` under `zephyr_xml_importer/api/urls.py`.
   - Implement listing via the TestY `TestSuite` model (id, name, parent_id, description).

4) Implement Export UI tree selector
   - Update `zephyr_xml_importer/templates/zephyr_xml_importer/export.html`:
     - Add a suite selector container, loading/error states, and selection controls.
     - Add JS to fetch suites, build the tree, maintain selection state, and submit `suite_ids`.
     - Remove the manual `suite_id` input (suite scoping is performed via the tree selector).
     - Add a search filter for suite name/path.

5) Tests and documentation
   - Add unit tests for `validate_export_request`:
     - parses `suite_ids`
     - precedence over `suite_id`
     - invalid/negative/empty handling
   - Add unit tests for suite id selection logic (validation + deduplication).
   - Add API tests for the suites endpoint error handling (missing project_id, invalid project_id).
   - Update docs:
     - `docs/usage.md` (Export UI + API fields)
     - `README.md` (Export API: add `suite_ids`)

Acceptance criteria

- Export UI displays a suite tree for the selected project and supports selecting one or many suites
  via checkboxes.
- Selecting a suite checkbox selects all descendants; unselecting unselects all descendants.
- Suite tree is sorted by full suite path.
- Export UI includes a working suite search filter.
- Export UI submits selected suite ids as `suite_ids` and exports only cases in those suites (and
  their descendants when explicitly selected via the tree).
- Export API accepts `suite_ids` as comma-separated ids; existing `suite_id` behavior remains
  supported.
- If both `suite_ids` and `suite_id` are provided, `suite_ids` is used.
- Suite listing endpoint returns suites for a project and is protected by the same admin-only
  permission as other plugin endpoints.
- Automated tests cover request validation and suite selection logic.

Risks

- Large suite trees may cause slow rendering or large JSON payloads.
  - Mitigation: render collapsed by default; consider optional search and/or lazy rendering if
    needed.
- Suite hierarchy may contain unexpected cycles or orphaned parent links (data integrity issues).
  - Mitigation: guard against cycles in tree-building and render orphans as roots.
- Differences across TestY versions in suite fields or hierarchy APIs.
  - Mitigation: query only stable fields (`id`, `name`, `parent_id`, optional `description`) and
    keep logic model-agnostic.

Open questions

None.
