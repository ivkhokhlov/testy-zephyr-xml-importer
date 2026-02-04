# TestY Zephyr Scale XML Importer

## English
### Overview
Native TestY plugin that imports Zephyr Scale XML/XLSX exports (Jira DC) into a selected TestY
project and exports TestY test cases back into a Zephyr Scale compatible XLSX file.

### Features
- Import a single XML or XLSX file with optional attachments ZIP.
- Export TestY suites/cases to Zephyr Scale compatible XLSX.
- Dry‑run with full validation, warnings, and CSV report.
- HTML UI + API endpoint.
- Idempotent import by `attributes.zephyr.key` (skip or upsert).

### Requirements
- TestY 2.1.2
- Python 3.11
- Admin access

### Install (local dev example)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e "./[dev]"
pytest -q
```

### Usage
- UI: `/plugins/zephyr-xml-importer/`
- Import: `/plugins/zephyr-xml-importer/import/`
- Export: `/plugins/zephyr-xml-importer/export/`
- Health: `/plugins/zephyr-xml-importer/health/`

### API (multipart)
Import fields:
- `project_id` (required)
- `xml_file` (required, XML or XLSX)
- `attachments_zip` (optional)
- `dry_run` (default false)
- `prefix_with_zephyr_key` (default true)
- `meta_labels` (default true)
- `append_jira_issues_to_description` (default true)
- `embed_testdata_to_description` (default true)
- `on_duplicate` (skip|upsert, default skip)

Export fields:
- `project_id` (required)
- `suite_ids` (optional, comma-separated list of suite ids)
- `suite_id` (optional)
- `include_children` (default true, used with `suite_id`)
- `case_ids` (optional, comma-separated list)
- `strip_zephyr_key_prefix` (default true)
- `metadata_source` (attributes_then_meta_labels | attributes_only | meta_labels_only)
- `key_strategy` (existing_only | synthetic)
- `include_extra_testy_fields` (default false, adds `Step Name` column)

Note: when `suite_ids` is provided, it takes precedence over `suite_id`.

### Docs
See:
- `docs/overview.md`
- `docs/usage.md`
- `docs/mapping.md`
- `docs/requirements-traceability.md`
- `docs/deployment.md`
- `docs/troubleshooting.md`

---

## Русский
### Обзор
Нативный плагин TestY для импорта XML/XLSX‑экспортов Zephyr Scale (Jira DC) в выбранный проект
TestY и экспорта тест‑кейсов из TestY обратно в совместимый с Zephyr Scale XLSX.

### Возможности
- Импорт одного XML или XLSX и опционального ZIP с вложениями.
- Экспорт suites/cases из TestY в совместимый с Zephyr Scale XLSX.
- Dry‑run с полной валидацией, предупреждениями и CSV‑отчётом.
- HTML‑интерфейс и API‑эндпоинт.
- Идемпотентность по `attributes.zephyr.key` (skip или upsert).

### Требования
- TestY 2.1.2
- Python 3.11
- Права администратора

### Установка (пример для локальной разработки)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e "./[dev]"
pytest -q
```

### Использование
- UI: `/plugins/zephyr-xml-importer/`
- Import: `/plugins/zephyr-xml-importer/import/`
- Export: `/plugins/zephyr-xml-importer/export/`
- Health: `/plugins/zephyr-xml-importer/health/`

### API (multipart)
Поля импорта:
- `project_id` (обязательно)
- `xml_file` (обязательно, XML или XLSX)
- `attachments_zip` (опционально)
- `dry_run` (по умолчанию false)
- `prefix_with_zephyr_key` (по умолчанию true)
- `meta_labels` (по умолчанию true)
- `append_jira_issues_to_description` (по умолчанию true)
- `embed_testdata_to_description` (по умолчанию true)
- `on_duplicate` (skip|upsert, по умолчанию skip)

Поля экспорта:
- `project_id` (обязательно)
- `suite_ids` (опционально, список suite id через запятую)
- `suite_id` (опционально)
- `include_children` (по умолчанию true, используется с `suite_id`)
- `case_ids` (опционально, список через запятую)
- `strip_zephyr_key_prefix` (по умолчанию true)
- `metadata_source` (attributes_then_meta_labels | attributes_only | meta_labels_only)
- `key_strategy` (existing_only | synthetic)
- `include_extra_testy_fields` (по умолчанию false, добавляет колонку `Step Name`)

Примечание: при наличии `suite_ids` поле `suite_id` игнорируется.

### Документация
См.:
- `docs/overview.md`
- `docs/usage.md`
- `docs/mapping.md`
- `docs/requirements-traceability.md`
- `docs/deployment.md`
- `docs/troubleshooting.md`

Version: 0.1.7
