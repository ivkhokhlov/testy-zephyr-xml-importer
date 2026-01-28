# Usage / Использование

## English
### UI
1) Open `/plugins/zephyr-xml-importer/import/`.
2) Select a project.
3) Upload XML or XLSX file and optional ZIP.
4) Choose options (dry‑run, meta labels, etc.).
5) Run import and download CSV report if needed.

### API (multipart)
Endpoint: `/plugins/zephyr-xml-importer/import/`

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

Example with JWT:
```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F project_id=1 \
  -F dry_run=true \
  -F "xml_file=@/path/to/export.xml;type=application/xml" \
  -F "attachments_zip=@/path/to/attachments.zip;type=application/zip" \
  https://<HOST>/plugins/zephyr-xml-importer/import/
```

XLSX variant:
```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F project_id=1 \
  -F dry_run=true \
  -F "xml_file=@/path/to/export.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  https://<HOST>/plugins/zephyr-xml-importer/import/
```

Example with session cookies:
```bash
curl -i \
  -b "csrftoken=<CSRF>; sessionid=<SESSION>" \
  -H "X-CSRFToken: <CSRF>" \
  -F project_id=1 \
  -F dry_run=true \
  -F "xml_file=@/path/to/export.xml;type=application/xml" \
  https://<HOST>/plugins/zephyr-xml-importer/import/
```

### Health endpoint
```bash
curl -i -H "Authorization: Bearer <ACCESS_TOKEN>" \
  https://<HOST>/plugins/zephyr-xml-importer/health/
```

### Response format
Success:
```json
{
  "status": "success",
  "dry_run": true,
  "summary": {
    "folders": 3,
    "cases": 10,
    "steps": 25,
    "labels": 12,
    "attachments": 4,
    "created": 10,
    "reused": 0,
    "updated": 0,
    "skipped": 0,
    "failed": 0
  },
  "report_csv": "...",
  "warnings": ["..."]
}
```

Failed:
```json
{
  "status": "failed",
  "dry_run": false,
  "errors": {"detail": "..."}
}
```

---

## Русский
### Интерфейс
1) Откройте `/plugins/zephyr-xml-importer/import/`.
2) Выберите проект.
3) Загрузите XML или XLSX и опциональный ZIP.
4) Укажите опции (dry‑run, meta‑labels и т.д.).
5) Запустите импорт и при необходимости скачайте CSV‑отчёт.

### API (multipart)
Эндпоинт: `/plugins/zephyr-xml-importer/import/`

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

Пример с JWT:
```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F project_id=1 \
  -F dry_run=true \
  -F "xml_file=@/path/to/export.xml;type=application/xml" \
  -F "attachments_zip=@/path/to/attachments.zip;type=application/zip" \
  https://<HOST>/plugins/zephyr-xml-importer/import/
```

Вариант XLSX:
```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F project_id=1 \
  -F dry_run=true \
  -F "xml_file=@/path/to/export.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  https://<HOST>/plugins/zephyr-xml-importer/import/
```

Пример с session cookie:
```bash
curl -i \
  -b "csrftoken=<CSRF>; sessionid=<SESSION>" \
  -H "X-CSRFToken: <CSRF>" \
  -F project_id=1 \
  -F dry_run=true \
  -F "xml_file=@/path/to/export.xml;type=application/xml" \
  https://<HOST>/plugins/zephyr-xml-importer/import/
```

### Health‑эндпоинт
```bash
curl -i -H "Authorization: Bearer <ACCESS_TOKEN>" \
  https://<HOST>/plugins/zephyr-xml-importer/health/
```

### Формат ответа
Успех:
```json
{
  "status": "success",
  "dry_run": true,
  "summary": {
    "folders": 3,
    "cases": 10,
    "steps": 25,
    "labels": 12,
    "attachments": 4,
    "created": 10,
    "reused": 0,
    "updated": 0,
    "skipped": 0,
    "failed": 0
  },
  "report_csv": "...",
  "warnings": ["..."]
}
```

Ошибка:
```json
{
  "status": "failed",
  "dry_run": false,
  "errors": {"detail": "..."}
}
```
