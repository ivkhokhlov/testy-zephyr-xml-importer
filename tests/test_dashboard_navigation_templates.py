from __future__ import annotations

import re
from pathlib import Path


TEMPLATES_DIR = (
    Path(__file__).resolve().parents[1]
    / "zephyr_xml_importer"
    / "templates"
    / "zephyr_xml_importer"
)


def _read_template(filename: str) -> str:
    return (TEMPLATES_DIR / filename).read_text(encoding="utf-8")


def _extract_header(html: str) -> str:
    marker = '<header class="header">'
    start = html.find(marker)
    assert start != -1, "Expected header block in template"
    end = html.find("</header>", start)
    assert end != -1, "Expected closing </header> tag in template"
    return html[start : end + len("</header>")]


def test_dashboard_has_no_header_nav_and_two_primary_ctas():
    html = _read_template("index.html")
    header = _extract_header(html)

    assert '<div class="nav">' not in header

    primary_links = re.findall(r'<a[^>]*\bclass="[^"]*\bprimary\b[^"]*"[^>]*>', html)
    assert len(primary_links) == 2

    assert re.search(r'href="import/"[^>]*>\s*Start Import\s*</a>', html)
    assert re.search(r'href="export/"[^>]*>\s*Start Export\s*</a>', html)


def test_import_page_header_has_back_and_switch_links():
    html = _read_template("import.html")
    header = _extract_header(html)

    assert '<div class="nav">' in header
    assert 'href="../"' in header
    assert 'href="../export/"' in header
    assert "Back to Dashboard" in header
    assert "Switch to Export" in header
    assert "primary" not in header


def test_export_page_header_has_back_and_switch_links():
    html = _read_template("export.html")
    header = _extract_header(html)

    assert '<div class="nav">' in header
    assert 'href="../"' in header
    assert 'href="../import/"' in header
    assert "Back to Dashboard" in header
    assert "Switch to Import" in header
    assert "primary" not in header

