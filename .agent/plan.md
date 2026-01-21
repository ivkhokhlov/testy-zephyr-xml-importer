# Plan

Task: ZEP-170 — Admin role check: restrict to TestY membership role if required

Acceptance criteria:
- ZEP-170 — Admin role check: restrict to TestY membership role if required

Assumptions:
- TestY exposes a project membership via `request.user.membership` or `request.user.memberships`, each with `role`/`role_name`.

Micro-steps:
- Review security requirement in `docs/spec.md` and current permission logic in `zephyr_xml_importer/api/permissions.py`.
- Narrow role checks to membership role names only (plus `is_superuser`) to avoid over-permissive access.
- Keep `ADMIN_ROLE_NAME` fallback to "Admin" when settings are absent.
- Add/update unit tests to cover membership role allow and non-membership role deny cases.
- Run tests (and optional lint) to confirm behavior.

Files expected to change:
- zephyr_xml_importer/api/permissions.py
- tests/test_permissions.py

Verification steps:
- pytest -q
- python -m ruff check .
