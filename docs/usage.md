# Usage / Использование

## English
### UI
1) Open `/plugins/zephyr-xml-importer/import/`.
2) Select a project.
3) Upload XML or XLSX file and optional ZIP.
4) Choose options (dry‑run, meta labels, etc.).
5) Run import and download CSV report if needed.

### Export UI
1) Open `/plugins/zephyr-xml-importer/export/`.
2) Select a project.
3) Optionally scope by suite id or explicit case ids.
4) Choose export options (metadata source, key strategy).
5) Run export and download the XLSX file.

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

### Export API (multipart)
Endpoint: `/plugins/zephyr-xml-importer/export/`

Fields:
- `project_id` (required)
- `suite_id` (optional)
- `include_children` (default true)
- `case_ids` (optional, comma-separated list)
- `strip_zephyr_key_prefix` (default true)
- `metadata_source` (attributes_then_meta_labels | attributes_only | meta_labels_only)
- `key_strategy` (existing_only | synthetic)

Example:
```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F project_id=1 \
  -F suite_id=10 \
  -F include_children=true \
  -F case_ids=101,102,205 \
  -F strip_zephyr_key_prefix=true \
  -F metadata_source=attributes_then_meta_labels \
  -F key_strategy=existing_only \
  https://<HOST>/plugins/zephyr-xml-importer/export/ \
  -o zephyr-scale-export.xlsx
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

### Экспорт (UI)
1) Откройте `/plugins/zephyr-xml-importer/export/`.
2) Выберите проект.
3) Опционально укажите suite id или список case id.
4) Выберите опции экспорта (источник метаданных, стратегия ключей).
5) Запустите экспорт и скачайте XLSX‑файл.

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

### Экспорт API (multipart)
Эндпоинт: `/plugins/zephyr-xml-importer/export/`

Поля:
- `project_id` (обязательно)
- `suite_id` (опционально)
- `include_children` (по умолчанию true)
- `case_ids` (опционально, список через запятую)
- `strip_zephyr_key_prefix` (по умолчанию true)
- `metadata_source` (attributes_then_meta_labels | attributes_only | meta_labels_only)
- `key_strategy` (existing_only | synthetic)

Пример:
```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F project_id=1 \
  -F suite_id=10 \
  -F include_children=true \
  -F case_ids=101,102,205 \
  -F strip_zephyr_key_prefix=true \
  -F metadata_source=attributes_then_meta_labels \
  -F key_strategy=existing_only \
  https://<HOST>/plugins/zephyr-xml-importer/export/ \
  -o zephyr-scale-export.xlsx
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
