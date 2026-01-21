Ниже — **полное и подробное описание задачи (ТЗ)** для разработки *нативного* плагина TestY **(версия 2.1.2 / Python 3.11.9)**, который импортирует **Zephyr Scale XML export (Jira Plugin / DC)** напрямую в TestY, максимально перенося данные, и аккуратно сохраняя “лишнее” в `attributes`.

---

# Техническое задание: Плагин TestY “Zephyr Scale XML Importer”

## 0) Контекст и цель

### Цель

Сделать отдельный репозиторий (GitHub) с плагином для TestY, который позволяет **админу** загрузить **Zephyr Scale XML export** и выполнить **одноразовый ручной импорт** в выбранный проект TestY.

### Основной приоритет переноса (по твоим ответам)

1. **Папки + тест-кейсы** (иерархия suites + cases)
2. **Вложения + теги (labels) + статусы/приоритеты**
3. Всё остальное (issues, параметры, test data, кто создал/обновил и т.п.) — сохранить максимально полно в `attributes` и/или “читабельно” в описании

### Ограничения

* Импорт **только одного XML за раз**.
* Импорт запускается **вручную** через загрузку XML.
* Импорт **всегда в корень проекта TestY**, строго повторяя структуру Zephyr (путь папок).
* **Синхронный запуск** (без Celery/прогресса); режим dry-run нужен.
* Права запуска: **только админы** (проверка проектных прав не требуется).

---

## 1) Анализ входного формата (по твоему примеру XML)

### Структура XML (ключевое)

В твоём файле наблюдается формат:

* Корневой блок `<project>...`
* `<folders>`: список папок

  * `<folder fullPath="ui/Черные списки" index="123" />`
  * глубина путей до ~5 сегментов
* `<testCases>`: список `<testCase ...>`

  * у `<testCase>` есть `id`, `key`, иногда `paramType="PARAMETER" | "TEST_DATA"`
  * основные поля кейса: `name`, `folder`, `objective`, `precondition`, `status`, `priority`, `owner`, `createdBy/On`, `updatedBy/On`
  * `labels` (несколько `<label>`)
  * `issues` (несколько `<issue><key>…</key><summary>…</summary></issue>`)
  * `attachments`: в XML **только имена файлов** `<attachment><name>file.csv</name></attachment>` (без бинарного содержимого)
  * `testScript`:

    * в примере массово: `type="steps"` и `<steps><step index="...">...</step></steps>`
    * у `step` встречаются: `description`, `expectedResult`, `testData`
  * `testDataWrapper` при `paramType="TEST_DATA"` (табличные данные, rows/columns)

### Важные наблюдения для импорта

* В твоём файле **все testScript = steps**, но по твоим словам в реальности может быть и Plain Text — плагин должен быть готов.
* Встречаются HTML/CDATA внутри objective/precondition/step fields:

  * `<br>`, `<ul><li>`, `<ol><li>`, `<table><tr><td>`, `<code>`, `<a href=...>`
* Есть шаги, у которых **description пустой** или вообще все поля пустые — это критично, потому что в TestY:

  * `TestCaseStep.scenario` — **обязательное** поле (нельзя создать шаг с пустым сценарием).
* В TestY `TestCase.scenario` тоже **обязательное** поле (в модели оно не `blank=True`), поэтому даже для step-based кейса нужно заполнить `scenario` чем-то ненулевым/непустым (подробности ниже в маппинге).

---

## 2) Что именно создаём в TestY (целевая модель и “нативность”)

### Объекты TestY (по репозиторию 2.1.2)

* `TestSuite` — дерево с `parent` и `project`, имя `name`, описание `description`, `attributes` (JSON).
* `TestCase` — принадлежит suite+project, поля:

  * `name` (обязательно)
  * `setup` (blank=True)
  * `scenario` (**обязательно**)
  * `expected` (blank=True)
  * `teardown` (blank=True)
  * `description` (blank=True)
  * `is_steps` (bool)
  * `attributes` (JSON)
* `TestCaseStep` — принадлежит test_case+project:

  * `name` (обязательно)
  * `scenario` (**обязательное**)
  * `expected` (blank=True)
  * `sort_order` (обязательно)
* `Label`/`LabeledItem` — метки, ставятся через `LabelService`.
* `Attachment` — вложения, attach на любой content_object, ставятся через `AttachmentService`.

### “Нативный” способ создания

Плагин не должен напрямую писать в БД “в обход логики”. Надо использовать сервисы ядра:

* Создание suites: `TestSuiteService().suite_create(...)`
* Создание cases+steps: `TestCaseService().case_with_steps_create(...)`
* (опционально апдейт) `TestCaseService().case_with_steps_update(...)`
* Labels: `LabelService().set(...)`
* Attachments: `AttachmentService().attachment_set_content_object(...)`

---

## 3) Критерии “успешного импорта”

Импорт считается успешным, если:

### Must-have (обязательные поля, иначе миграция бесполезна)

* Создана **иерархия suites** (по папкам Zephyr).
* Созданы **test cases** в правильных suites.
* Перенесены:

  * `name`
  * `precondition` → setup
  * `objective` → description
  * `steps.description` + `steps.expectedResult` → шаги TestY
  * `labels` → labels TestY

### Priority-2

* Вложения: если есть возможность получить файл (через zip или иной механизм) — прикрепить в TestY, иначе хотя бы сохранить список имён и отразить в отчёте.
* Статус/приоритет: сохранить и сделать удобным для фильтрации (лучше через meta-labels + attributes).

### Остальное (priority-3)

* issues (Jira keys+summary), параметризация, testDataWrapper, created/updated/owner и т.д. — максимально сохранить в `attributes`, опционально частично в description.

---

## 4) Маппинг Zephyr → TestY (конкретные правила)

### 4.1 Suites: папки Zephyr → дерево TestSuite

**Источник:**

* `<folders><folder fullPath="a/b/c" index="..."/></folders>`
* `<testCase><folder><![CDATA[a/b/c]]></folder>`

**Правило:**

* `fullPath` разбивается по `/` на сегменты.
* В TestY создаются вложенные `TestSuite`:

  * `a` (parent=None)
  * `b` (parent=a)
  * `c` (parent=b)

**Повторное использование suites:**

* Если suite с таким `name` уже существует под тем же `parent` в этом проекте — использовать существующую (не создавать дубль).
* (опционально) дополнительно хранить в suite.attributes Zephyr-путь, чтобы проще было отлаживать.

**suite.description**

* В Zephyr описания папок нет — оставляем пустым.

**suite.attributes**

* Добавить “след” источника:

```json
{
  "zephyr": {
    "folderFullPath": "a/b/c",
    "folderIndex": 123
  }
}
```

**Особый случай: testCase без folder**

* Создать/использовать отдельную suite в корне:

  * например: `"(No folder)"` или `"Без папки"`
    и складывать туда такие кейсы.

---

### 4.2 TestCase: поля кейса

**Источник:**

* `<testCase id="..." key="ES-T123"> ... </testCase>`

**Куда в TestY:**

* `TestCase.name` ← Zephyr `<name>`

  * Рекомендуемый дефолт: **префикс ключом** Zephyr, чтобы сохранить идентичность:

    * `"[ES-T123] Оригинальное имя"`
  * Должна быть опция отключить префикс, но дефолт лучше оставить включенным (помогает уникальности и трассировке).
* `TestCase.setup` ← Zephyr `<precondition>` (после санитизации HTML)
* `TestCase.description` ← Zephyr `<objective>` (после санитизации HTML)

  * (опционально) в конец description добавить блок:

    * “Связанные Jira issues: ES-1234 …”
    * “Вложения в Zephyr: file1, file2 …” если zip не пришёл
* `TestCase.is_steps`:

  * если `testScript type="steps"` → `True`
  * если `plain text` → `False` (см. ниже)
* `TestCase.scenario` (**обязательное поле в TestY!**):

  * Для `type="steps"`: **сгенерировать плоский сценарий** из шагов (даже если шаги тоже создаются структурировано).

    * Это критично: иначе модель TestY не даст создать кейс, т.к. `scenario` не `blank=True`.
  * Для `plain text`: `scenario = текст скрипта`

**TestCase.expected**:

* Для steps-кейсов — можно оставить пустым (не обязательно).
* Для plain text можно оставить пустым или, если Zephyr даёт отдельное expected поле (в другой схеме), положить туда.

**TestCase.attributes (максимум полезного из XML)**
Хранить все метаданные, которые не имеют прямого поля в TestY:

```json
{
  "zephyr": {
    "id": "401225",
    "key": "ES-T560",
    "folder": "api/data_profiles/group",
    "status": "Approved",
    "priority": "Normal",
    "owner": "JIRAUSER53027",
    "createdBy": "...",
    "createdOn": "2024-07-01 09:22:13 UTC",
    "updatedBy": "...",
    "updatedOn": "...",
    "issues": [
      {"key": "ES-7574", "summary": "..."}
    ],
    "attachments": ["file1.csv", "file2.xlsx"],
    "paramType": "TEST_DATA",
    "parameters": ["url", "login", "password"],
    "testDataWrapper": [
      {"field_name": "timezone"},
      {"field_name": "is_ignored_black_list"}
    ]
  }
}
```

---

### 4.3 Steps: Zephyr steps → TestCaseStep

**Источник:**

```xml
<step index="2">
  <description><![CDATA[...]]></description>
  <expectedResult><![CDATA[...]]></expectedResult>
  <testData><![CDATA[...]]></testData>
</step>
```

**Правило:**

* `TestCaseStep.sort_order` = `int(step.@index)`
* `TestCaseStep.name` = `"Step {index+1}"` (или `"Шаг {index+1}"`)
* `TestCaseStep.scenario` = `sanitize(description)` + (если есть testData → добавить отдельным блоком)
* `TestCaseStep.expected` = `sanitize(expectedResult)`

**Критичное правило для пустых шагов**
Поскольку `TestCaseStep.scenario` нельзя пустым:

* Если после санитизации `description` пустой:

  * использовать `testData` (если есть),
  * иначе поставить placeholder, например: `"Step {index+1} (empty in Zephyr)"`.
* Это должно фиксироваться в отчёте как warning.

---

### 4.4 Labels (теги)

**Источник:**

```xml
<labels>
  <label><![CDATA[b2b]]></label>
</labels>
```

**Правило:**

* Каждую метку Zephyr перенести как label TestY:

  * `{'name': 'b2b'}`
* Нормализация:

  * Минимальная и безопасная: `strip()`, замена множественных пробелов на один.
  * Регистр лучше **не ломать**, но можно добавить опцию `normalize_labels_to_lower=true`.

---

### 4.5 Status / Priority / Owner (priority 2)

В TestY нет нативных полей “status/priority/owner” для тест-кейса → сохраняем в `attributes`, и **дополнительно** (по умолчанию) делаем **meta-labels** для удобного поиска/фильтрации.

**Meta-labels формат (дефолт ON):**

* `zephyr:status=Approved`
* `zephyr:priority=Low`
* `zephyr:owner=JIRAUSER53027`

---

### 4.6 Jira issues (priority 3)

Переносим:
- `attributes.zephyr.issues`
- (опционально) строкой в `description`: `Jira: ES-7574, ES-7692`

---

### 4.7 Parameterization: PARAMETER / TEST_DATA (priority 3)

Всегда:
- сохранить `paramType`, `parameters`, `testDataWrapper` в `attributes.zephyr`.

Опционально (по умолчанию ON):
- embed “Parameters:” / “Test data rows:” в description.

---

### 4.8 Attachments (priority 2)

v1:
- API принимает optional `attachments_zip`
- match by basename
- attach to testcase if found; else warn + keep name in attributes

---

## 5) Поведение при повторном запуске (идемпотентность)

Default: create-only + skip duplicates by `attributes.zephyr.key`.
Optional upsert (off by default).

---

## 6) Интерфейс плагина: REST API + затем UI
Base: `/plugins/zephyr-xml-importer/...`

---

## 7) API контракт

POST `/plugins/zephyr-xml-importer/import/` (multipart):
- project_id
- xml_file
- attachments_zip (optional)
- dry_run, prefix_with_zephyr_key, meta_labels, append_jira_issues_to_description, embed_testdata_to_description
- on_duplicate: skip|upsert

Dry-run validates and returns warnings, no DB writes.

---

## 8) Отчёт по импорту
CSV: one row per testcase, includes action, ids, warnings/errors.

---

## 9) Безопасность
Admin-only:
- superuser OR membership role name == settings.ADMIN_ROLE_NAME ('Admin').

---

## 10) Реализация в коде: структура репозитория плагина

```
testy-zephyr-xml-importer/
  pyproject.toml
  README.md
  zephyr_xml_importer/
    hooks.py
    api/...
    services/...
    tests/...
```

---

## 15) Definition of Done
See original spec.
