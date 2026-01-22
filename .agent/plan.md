# Plan

Task: Implement UI for Zephyr XML Importer (native HTML page).

Steps:
- Add project list loader with safe fallback for missing TestY models.
- Serve HTML template from GET /plugins/zephyr-xml-importer/import/.
- Build self-contained template with form, JS fetch, CSRF header, and result rendering.
- Ensure templates are packaged in distribution.
- Add unit tests for project list helper and run pytest.

Status: completed.
