# TestY Zephyr Scale XML Importer

## English
### Overview
Native TestY plugin that imports Zephyr Scale XML/XLSX exports (Jira DC) into a selected TestY project. Supports dry‑run, optional ZIP attachments, idempotent create/skip by Zephyr key, and optional upsert.

### Features
- Import a single XML or XLSX file with optional attachments ZIP.
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
- UI: `/plugins/zephyr-xml-importer/import/`
- Health: `/plugins/zephyr-xml-importer/health/`

### API (multipart)
Fields:
- `project_id` (required)
- `xml_file` (required, XML or XLSX)
- `attachments_zip` (optional)
- `dry_run` (default false)
- `prefix_with_zephyr_key` (default true)
- `meta_labels` (default true)
- `append_jira_issues_to_description` (default true)
- `embed_testdata_to_description` (default true)
- `on_duplicate` (skip|upsert, default skip)

### Docs
See:
- `docs/overview.md`
- `docs/usage.md`
- `docs/mapping.md`
- `docs/deployment.md`
- `docs/troubleshooting.md`

---

## Русский
### Обзор
Нативный плагин TestY для импорта XML/XLSX‑экспортов Zephyr Scale (Jira DC) в выбранный проект TestY. Поддерживает dry‑run, ZIP‑вложения, идемпотентное создание/пропуск по ключу Zephyr и опциональный upsert.

### Возможности
- Импорт одного XML или XLSX и опционального ZIP с вложениями.
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
- UI: `/plugins/zephyr-xml-importer/import/`
- Health: `/plugins/zephyr-xml-importer/health/`

### API (multipart)
Поля:
- `project_id` (обязательно)
- `xml_file` (обязательно, XML или XLSX)
- `attachments_zip` (опционально)
- `dry_run` (по умолчанию false)
- `prefix_with_zephyr_key` (по умолчанию true)
- `meta_labels` (по умолчанию true)
- `append_jira_issues_to_description` (по умолчанию true)
- `embed_testdata_to_description` (по умолчанию true)
- `on_duplicate` (skip|upsert, по умолчанию skip)

### Документация
См.:
- `docs/overview.md`
- `docs/usage.md`
- `docs/mapping.md`
- `docs/deployment.md`
- `docs/troubleshooting.md`

Version: 0.1.2
