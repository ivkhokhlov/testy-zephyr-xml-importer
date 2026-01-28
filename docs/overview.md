# Overview / Обзор

## English
### Purpose
The plugin imports Zephyr Scale XML/XLSX exports (Jira DC) into a selected TestY project. It recreates the folder hierarchy as suites, creates test cases with steps, labels, and optional attachments, and produces a CSV report.

### Input
- One Zephyr Scale XML or XLSX export file.
- Optional ZIP with attachments referenced in the export (matched by basename).

### Output
- Suites, cases, steps, labels, attachments created in TestY.
- CSV report with per‑case status and warnings.

### Access control
Admin‑only (TestY admin role or superuser).

### Health endpoint
`/plugins/zephyr-xml-importer/health/` returns JSON status and version (admin‑only).

---

## Русский
### Назначение
Плагин импортирует XML/XLSX‑экспорт Zephyr Scale (Jira DC) в выбранный проект TestY. Он воссоздаёт иерархию папок как suites, создаёт тест‑кейсы со шагами, метками и (опционально) вложениями, а также формирует CSV‑отчёт.

### Входные данные
- Один XML или XLSX‑экспорт Zephyr Scale.
- Опциональный ZIP с вложениями, упомянутыми в экспорте (сопоставление по имени файла).

### Результат
- В TestY создаются suites, кейсы, шаги, метки, вложения.
- CSV‑отчёт по каждому кейсу с предупреждениями.

### Доступ
Только администраторы (роль администратора TestY или superuser).

### Health‑эндпоинт
`/plugins/zephyr-xml-importer/health/` возвращает JSON‑статус и версию (только для администраторов).
