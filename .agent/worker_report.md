Task: Implement UI for Zephyr XML Importer (native HTML page)

What changed:
- added project list loader with safe fallback when TestY models are unavailable
- served HTML UI from GET handler with project list context
- added self-contained template with form, JS fetch + CSRF, summary/warnings rendering, and CSV download
- packaged templates in pyproject for distribution
- added unit tests for project list helper

Files changed:
- zephyr_xml_importer/services/testy_adapter.py
- zephyr_xml_importer/api/views.py
- zephyr_xml_importer/templates/zephyr_xml_importer/import.html
- pyproject.toml
- tests/test_projects_ui.py

Commands run + results:
- pytest -q (pass)
