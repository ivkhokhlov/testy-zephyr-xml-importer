# ZEP-200 Plan — UI for Zephyr XML Importer

## Goal
Provide a native HTML UI at `/plugins/zephyr-xml-importer/import/` that lets admins select a project, upload XML + optional ZIP, choose import options, run dry-run/real import, and view results (summary, warnings, CSV download).

## Scope and constraints
- Same URL for GET (HTML) and POST (multipart API).
- Admin-only access (reuse existing permission class).
- No reliance on DRF browsable API; page must be template-based and self-contained.
- No external CSS/JS; include minimal inline styling and script.
- If projects list cannot be loaded, show manual `project_id` input.

## Implementation plan

### 1) View and routing
- Keep the URL path `import/` and name `import` so `index_reverse_name` remains valid.
- Extend the existing `ImportView` to support `get()` returning HTML.
  - Use `django.shortcuts.render` or `TemplateResponse` when Django is available.
  - Preserve `post()` behavior for API responses.
- Continue using `IsAdminForZephyrImport` permission for both GET and POST.

### 2) Project list retrieval with fallback
- Add a helper in `zephyr_xml_importer/services/testy_adapter.py` (or a new `services/projects.py`) to load project choices when running inside TestY:
  - Attempt to import a Project model from likely modules (e.g., `testy.models`, `testy.projects.models`).
  - Return a list of lightweight items (`id`, `name`) sorted by name or id.
  - On import/model errors, return `None` so the UI can fall back to manual input.
- In `ImportView.get()`, populate template context:
  - `projects`: list of choices or `None`.
  - `project_list_error`: optional message for the template when projects are unavailable.

### 3) Template layout (HTML + minimal CSS)
- Add template file: `zephyr_xml_importer/templates/zephyr_xml_importer/import.html`.
- Two-panel layout:
  - Left: form inputs and buttons.
  - Right: result/status panel.
- Form fields:
  - `project_id` select if `projects` present; otherwise text input.
  - `xml_file` file input (accept `.xml`).
  - `attachments_zip` file input (accept `.zip`).
  - Checkboxes: `dry_run`, `prefix_with_zephyr_key`, `meta_labels`, `append_jira_issues_to_description`, `embed_testdata_to_description`.
  - Select: `on_duplicate` (skip/upsert).
- Buttons:
  - Run (submit)
  - Download CSV (disabled until success)
  - Reset (reset to defaults)

### 4) JavaScript behavior
- Intercept form submit and build `FormData` manually so all booleans are sent.
  - Append booleans as strings `"true"`/`"false"`.
  - Include selected `project_id` or manual input.
- CSRF handling:
  - Read `csrftoken` cookie.
  - Send `X-CSRFToken` header.
  - Use `credentials: 'same-origin'`.
- Fetch `POST` to the current page URL (`window.location.href` or `form.action`).
- Response handling:
  - If `status == success`:
    - Render summary badges from `summary`.
    - Render warnings list (cap at 50, show `+N more` if available).
    - Enable “Download CSV” button and cache `report_csv` (or set `report_url`).
  - If `status == failed`:
    - Render `errors` as JSON.
    - Clear summary/warnings.
    - Disable “Download CSV”.

### 5) CSV download handling
- If response includes `report_csv`, create a `Blob` and trigger download on button click.
- If response includes `report_url`, set a download link instead.
- Use a stable filename like `zephyr-import-report.csv` (optionally include timestamp).

### 6) Warnings cap and “+N more”
- UI should show the first 50 warnings.
- To display `+N more`, add a backend field when needed:
  - Option A: include `warnings_total` in API responses (total count before cap).
  - Option B: include `warnings_overflow` (number of warnings beyond those returned).
- Update the UI to compute the `+N more` line if either field exists; otherwise omit the suffix.

### 7) Package template assets
- Ensure the template is shipped with the package:
  - Add `tool.setuptools.package-data` in `pyproject.toml` or a `MANIFEST.in` entry for `templates/**`.

## Tests to add
- Unit tests for project list helper (pure Python):
  - returns `None` when models are missing.
  - returns list of `{id, name}` when provided a fake model (use monkeypatch).
- If adding `warnings_total`/`warnings_overflow`:
  - extend existing importer tests to assert the new field for dry-run results.
- Keep tests Django-free (guard or isolate imports); verify `pytest -q` still passes.

## Expected files to change
- `zephyr_xml_importer/api/views.py` (add GET handler / template rendering).
- `zephyr_xml_importer/api/urls.py` (if routing adjustments are needed for UI view).
- `zephyr_xml_importer/services/testy_adapter.py` (project list helper).
- `zephyr_xml_importer/templates/zephyr_xml_importer/import.html` (new template).
- `pyproject.toml` or `MANIFEST.in` (include templates in package data).
- `tests/test_projects_ui.py` (new unit tests for project list helper).
- `tests/test_importer_warnings.py` (if adding warnings total/overflow).

## Verification
- `pytest -q`
- `python -m ruff check .` (if ruff available)
