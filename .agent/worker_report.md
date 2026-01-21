Task: ZEP-170 — Admin role check: restrict to TestY membership role if required

What changed:
- Limited admin-role checks to membership roles only (plus superuser).
- Added unit tests covering membership role allow and non-membership role deny paths.

Files changed:
- zephyr_xml_importer/api/permissions.py
- tests/test_permissions.py

Commands run:
- pytest -q (pass)
- python -m ruff check . (fail: No module named ruff)

Failures:
- Lint failed because ruff is not installed in the environment.
