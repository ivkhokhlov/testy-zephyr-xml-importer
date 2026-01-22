# Technical Spec: UI for the “Zephyr Scale XML Importer” plugin

## 1) UI Goal

Build a **simple native page** in TestY where an administrator can:

1. Select a TestY project.
2. Upload a **Zephyr Scale XML export** (required file).
3. Optionally upload a **ZIP with attachments**.
4. Configure import behavior using checkboxes.
5. Start a **dry-run** or a **real import**.
6. Get the result:
   - summary (how many folders/cases/steps/labels/attachments)
   - warnings
   - CSV report (download)

The UI must work in TestY **2.1.2 / Python 3.11.9** without depending on TestY’s frontend (React), since this is a separate plugin.

---

## 2) Entry point and access

- Page URLs:
  - `GET /plugins/zephyr-xml-importer/import/` — HTML UI
  - `POST /plugins/zephyr-xml-importer/import/` — import API (multipart/form-data)

- In the TestY plugins list (`GET /plugins/`), the **Plugin index** link must lead to this page.

- Access permissions:
  - only `is_superuser` **or** a user with the `Admin` role (`settings.ADMIN_ROLE_NAME`).

---

## 3) Page structure

The page is split into 2 panels:

### 3.1 Left panel “Import”

Form fields:

1) **Project**
- `project_id` (required)
- UI:
  - a select with projects (id + name)
  - if the project list is unavailable (request error / no model) — show a “manual project_id input” field.

2) **XML**
- `xml_file` (required)
- accept: `.xml`

3) **Attachments ZIP**
- `attachments_zip` (optional)
- accept: `.zip`
- hint: “matching by filename (basename) without paths”

4) **Import options** (checkbox / select)
- `dry_run` (default: false)
- `prefix_with_zephyr_key` (default: true)
- `meta_labels` (default: true)
- `append_jira_issues_to_description` (default: true)
- `embed_testdata_to_description` (default: true)
- `on_duplicate` (select: `skip|upsert`, default: `skip`)

Buttons:
- **Run** (submit)
- **Download CSV report** (disabled until a successful response is received)
- **Reset** (reset to defaults)

### 3.2 Right panel “Result”

Shows:

- request execution status
- summary as “badges”:
  - folders
  - cases
  - steps
  - labels
  - attachments
  - created
  - reused
  - updated
  - skipped
  - failed

- warnings:
  - show the **first 50**
  - if there are more warnings — show “+ N more”

---

## 4) UI behavior

### 4.1 Sending the request

- The UI does `fetch()` to the same URL (where the page is opened), method `POST`, `multipart/form-data`.
- **Always** send boolean options explicitly (`true|false`), because unchecked checkboxes aren’t submitted by the browser.
- For SessionAuth/TestY, CSRF must be supported:
  - read the `csrftoken` cookie
  - send header `X-CSRFToken`
  - `credentials: 'same-origin'`

### 4.2 Handling the response

If `status == success`:

- render the summary
- enable the “Download CSV” button
- get CSV from `report_csv` and download via `Blob`
- render warnings as a list

If `status == failed`:

- show `errors` (as JSON)
- clear the summary
- keep the “Download CSV” button disabled

---

## 5) Non-functional requirements

- The UI must not depend on DRF Browsable API (in production often only JSONRenderer is enabled).
- The UI must be “self-contained” and shipped with the plugin (templates inside the package).
- Minimal styling is allowed (no external CSS).
