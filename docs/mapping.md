# Mapping rules / Правила маппинга

## English
### Suites (folders)
- Split `folder` path by `/` and create nested suites.
- If `folder` is empty, cases are placed into `(No folder)`.
- Each suite stores Zephyr trace in `attributes.zephyr`:
  `{"folderFullPath": "a/b", "folderIndex": 123}`.

### Test case
- `name` optionally prefixed with Zephyr key: `[KEY] Name`.
- `setup` from `precondition` (sanitized).
- `description` from `objective` (sanitized) plus optional Jira issues and attachment list.
- `scenario` must be non‑empty; for steps it is flattened, for text it is the script text.
- `is_steps` true when Zephyr uses steps.
- Always stores full Zephyr metadata in `attributes.zephyr`.

### Steps
- `sort_order` = step index, `name` = `Step {index+1}`.
- `scenario` = description + testData (if present).
- `expected` = expectedResult (sanitized).
- If scenario is empty, a placeholder is used and a warning is emitted.

### Labels
- Zephyr labels -> TestY labels (trimmed, collapsed spaces).
- Meta‑labels (optional):
  - `zephyr:status=...`
  - `zephyr:priority=...`
  - `zephyr:owner=...`

### Attachments
- Export contains names only; ZIP is optional.
- Matching by basename (without paths).
- Missing files generate warnings and remain in attributes/report.

### Idempotency
- Default: skip if `attributes.zephyr.key` already exists.
- Optional `on_duplicate=upsert` updates existing cases.

---

## Русский
### Suites (папки)
- Поле `folder` делится по `/`, создаётся иерархия suites.
- Если `folder` пустой — кейсы идут в `(No folder)`.
- В `attributes.zephyr` сохраняется след Zephyr:
  `{"folderFullPath": "a/b", "folderIndex": 123}`.

### Тест‑кейс
- `name` опционально с префиксом ключа Zephyr: `[KEY] Name`.
- `setup` из `precondition` (санитайз).
- `description` из `objective` (санитайз) + опционально Jira issues и список вложений.
- `scenario` всегда не пустой; для steps — свёрнутый сценарий, для текста — исходный текст.
- `is_steps` true, если Zephyr использует steps.
- Всегда сохраняются метаданные в `attributes.zephyr`.

### Шаги
- `sort_order` = индекс шага, `name` = `Step {index+1}`.
- `scenario` = description + testData (если есть).
- `expected` = expectedResult (санитайз).
- Если сценарий пустой — ставится заглушка и выдаётся предупреждение.

### Метки
- Метки Zephyr -> метки TestY (trim + collapse spaces).
- Метки‑метаданные (опционально):
  - `zephyr:status=...`
  - `zephyr:priority=...`
  - `zephyr:owner=...`

### Вложения
- В экспорте только имена; ZIP опционален.
- Сопоставление по имени файла (без пути).
- Отсутствующие файлы → предупреждения и запись в отчёт.

### Идемпотентность
- По умолчанию: пропуск, если `attributes.zephyr.key` уже существует.
- `on_duplicate=upsert` — обновление существующих кейсов.
