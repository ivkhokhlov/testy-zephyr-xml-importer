# Spec (concise) — Zephyr Scale XML Importer for TestY

Full original RU spec: `docs/spec_full_ru.md`.

## Goal
Native TestY plugin (TestY 2.1.2, Python 3.11.9) that lets an **admin** upload one Zephyr Scale XML export
(and optionally a ZIP of attachments) and import into a chosen TestY project.

Constraints:
- one XML per import
- manual upload only
- import runs synchronously (no Celery); dry-run required
- import always into project root, reproducing Zephyr folder structure
- admin-only access

## Input format (Zephyr Scale XML export)
- root `<project>`
- `<folders>` contains `<folder fullPath="a/b/c" index="123" />`
- `<testCases>` contains `<testCase id="..." key="ES-T123" paramType="...">...</testCase>`
  - `name`, `folder`, `objective`, `precondition`, `status`, `priority`, `owner`, created/updated fields
  - `labels/label`
  - `issues/issue(key,summary)`
  - `attachments/attachment/name` (names only)
  - `testScript` usually steps:
    - `<testScript type="steps"><steps><step index="...">...</step></steps></testScript>`
    - step fields: `description`, `expectedResult`, `testData`
  - `testDataWrapper` for TEST_DATA

## Mapping rules (must-haves)
### Suites (folders)
- Split folder fullPath by `/`, create nested `TestSuite` per segment.
- Reuse existing suite if same name under same parent in the project.
- For testcases without folder: place under a root suite like `(No folder)`.

Store trace in `suite.attributes`:
```json
{"zephyr": {"folderFullPath": "a/b/c", "folderIndex": 123}}
```

### TestCase
- `name`: default prefix with Zephyr key: `"[ES-T123] Original name"` (toggleable)
- `setup`: from `precondition` (sanitized)
- `description`: from `objective` (sanitized), optionally append Jira issues + attachments list
- `scenario` (required in TestY): must be non-empty
  - if steps-based: generate a flattened scenario from steps
  - if plain text: scenario is the plain text
- `is_steps`: True for steps-based

Always store extra metadata in `attributes.zephyr` (id/key/folder/status/priority/owner/timestamps/issues/attachments/paramType/parameters/testDataWrapper).

### Steps
- sort_order: `int(step.@index)`
- name: `"Step {index+1}"`
- scenario: sanitized description (+ testData block if present)
- expected: sanitized expectedResult
- If scenario is empty after sanitization:
  - use testData, else placeholder `"Step {index+1} (empty in Zephyr)"`, and emit warning.

### Labels
- Transfer Zephyr labels → TestY labels (strip, collapse spaces).
- Optional: normalize to lower.
- For status/priority/owner add meta-labels (default ON):
  - `zephyr:status=Approved`
  - `zephyr:priority=Low`
  - `zephyr:owner=JIRAUSER...`

### Attachments
XML has only names; plugin accepts optional `attachments_zip`:
- match by basename
- if found, attach to testcase
- if missing, warn and keep in attributes + report

## Idempotency
Default: create-only
- if a testcase already exists where `attributes.zephyr.key == <key>` → skip
Optional: `on_duplicate=upsert` updates everything.

## API
Base: `/plugins/zephyr-xml-importer/`

POST `/import/` (multipart):
- project_id (required)
- xml_file (required)
- attachments_zip (optional)
- dry_run (default false)
- prefix_with_zephyr_key (default true)
- meta_labels (default true)
- append_jira_issues_to_description (default true)
- embed_testdata_to_description (default true)
- on_duplicate: skip|upsert (default skip)

Response JSON:
- status: success|failed
- dry_run
- summary counts (folders/cases/steps/labels/attachments)
- report (CSV inline or URL)

Dry-run:
- parse + validate + warnings preview, no DB writes.

## Report (CSV)
One row per testcase:
- zephyr_key, zephyr_id, folder_full_path
- testy_suite_id, testy_case_id
- action (created|skipped|updated|failed)
- steps_count, labels_count
- attachments_in_xml, attachments_attached, attachments_missing
- warnings, error

## Security
Endpoint access: admin-only:
- `request.user.is_superuser` OR membership role name == settings.ADMIN_ROLE_NAME (default 'Admin').

