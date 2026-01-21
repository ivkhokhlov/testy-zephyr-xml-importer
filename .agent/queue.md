# Queue

## Now
- [ ] ZEP-010 — Define Zephyr dataclasses and parse result shapes (acceptance: typed models + tests import cleanly)
- [ ] ZEP-020 — Implement HTML/CDATA sanitizer (acceptance: sanitizer tests for br/li/table/unescape pass)
- [ ] ZEP-030 — Implement streaming folder parser (acceptance: parse folder fullPath+index from XML fixture)

## Next
- [ ] ZEP-031 — Parse testcase core fields (acceptance: key/id/name/folder/objective/precondition extracted)
- [ ] ZEP-032 — Parse steps + labels/issues/attachments + paramType/testDataWrapper (acceptance: fixture parsed fully)
- [ ] ZEP-040 — Mapping helpers: non-empty scenario + step placeholders + meta-labels (acceptance: mapping unit tests pass)

## Later
- [ ] ZEP-050 — CSV report builder (acceptance: report rows match actions + warnings/errors)
- [ ] ZEP-060 — Attachments ZIP matcher by basename (acceptance: attaches found, reports missing)
- [ ] ZEP-070 — DRF API: serializer + view + admin-only permission (acceptance: request validated, dry-run path works)
- [ ] ZEP-080 — Pluggy hook + TestyPluginConfig + entry point metadata (acceptance: package exposes entrypoint group "testy")
- [ ] ZEP-090 — Dry-run validations + warnings preview (acceptance: detects empty steps, long names, dup keys)
- [ ] ZEP-100 — Importer integration via TestY services (acceptance: create-only skip by attributes.zephyr.key)

## Done
- [x] ZEP-000 — Harness bootstrap: 3-phase prompts + docs + test runner scaffold
