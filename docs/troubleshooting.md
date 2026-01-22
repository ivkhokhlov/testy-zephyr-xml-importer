# Troubleshooting / Диагностика

## English
### Non‑JSON response in UI
If the UI shows a non‑JSON error, the response likely came from WAF/edge or a login page. Check route/WAF logs and allowlist the endpoint.

### 400 Bad Request in port‑forward
Usually `DisallowedHost`. Use a correct `Host` header or add the host to `ALLOWED_HOSTS`.

Example:
```bash
curl -i -H "Host: testy.example.com" http://127.0.0.1:18080/plugins/zephyr-xml-importer/import/
```

### 401 Unauthorized
Provide session cookies or JWT token. Health and import endpoints require admin access.

### 403 CSRF
Ensure CSRF cookie + `X-CSRFToken` header for session auth. Add origin to `CSRF_TRUSTED_ORIGINS`.

### “xml_file is not a file”
In curl, use `@` to upload a file:
`-F "xml_file=@/path/to/export.xml"`.

### Attachments missing
Provide ZIP with files named as in XML (match by basename). Missing files create warnings.

### Empty steps
Zephyr steps without description/testData/expected generate warnings; placeholders are used.

---

## Русский
### Non‑JSON ошибка в UI
Если UI показывает non‑JSON ошибку, ответ, скорее всего, пришёл от WAF/edge или страницы логина. Проверьте логи WAF/route и добавьте allowlist.

### 400 Bad Request при port‑forward
Обычно это `DisallowedHost`. Используйте правильный `Host` или добавьте его в `ALLOWED_HOSTS`.

Пример:
```bash
curl -i -H "Host: testy.example.com" http://127.0.0.1:18080/plugins/zephyr-xml-importer/import/
```

### 401 Unauthorized
Нужны session cookie или JWT токен. Health и import доступны только админам.

### 403 CSRF
Нужны CSRF cookie и заголовок `X-CSRFToken` для session auth. Добавьте origin в `CSRF_TRUSTED_ORIGINS`.

### “xml_file не файл”
В curl используйте `@` для файла:
`-F "xml_file=@/path/to/export.xml"`.

### Вложения не найдены
Передайте ZIP с файлами, имена должны совпадать с XML (по basename). Отсутствующие → предупреждения.

### Пустые шаги
Пустые шаги Zephyr (без description/testData/expected) вызывают предупреждения; ставятся заглушки.
