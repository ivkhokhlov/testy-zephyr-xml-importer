# Deployment / Развёртывание

## English
### Install into TestY
- Install the package into the backend environment (Docker image or venv).
- Restart backend so entry points are loaded.
- The plugin registers via the `testy` entry‑point group.

### OKD notes
- Ensure `ALLOWED_HOSTS` contains your route host.
- Ensure `CSRF_TRUSTED_ORIGINS` contains the HTTPS origin.
- Configure upload size limits in route/ingress if XML/XLSX/ZIP are large.
- If a WAF is present, allowlist:
  - `POST /plugins/zephyr-xml-importer/import/` (multipart/form-data)
  - `GET /plugins/zephyr-xml-importer/health/`

### Environment variables
TestY reads JSON lists from env:
- `ALLOWED_HOSTS` — example: `["testy.example.com"]`
- `CSRF_TRUSTED_ORIGINS` — example: `["https://testy.example.com"]`

---

## Русский
### Установка в TestY
- Установите пакет в окружение backend (Docker образ или venv).
- Перезапустите backend, чтобы подхватились entry‑points.
- Плагин регистрируется через группу entry‑points `testy`.

### Особенности OKD
- Убедитесь, что `ALLOWED_HOSTS` содержит ваш route host.
- Убедитесь, что `CSRF_TRUSTED_ORIGINS` содержит HTTPS origin.
- Настройте лимиты загрузки в route/ingress для больших XML/XLSX/ZIP.
- При наличии WAF добавьте allowlist:
  - `POST /plugins/zephyr-xml-importer/import/` (multipart/form-data)
  - `GET /plugins/zephyr-xml-importer/health/`

### Переменные окружения
TestY читает JSON‑списки из окружения:
- `ALLOWED_HOSTS` — пример: `["testy.example.com"]`
- `CSRF_TRUSTED_ORIGINS` — пример: `["https://testy.example.com"]`
