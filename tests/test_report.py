import csv
from io import StringIO

from zephyr_xml_importer.services.report import (
    REPORT_HEADER,
    ReportRow,
    build_csv_report,
)


def _parse_report(csv_text: str) -> list[list[str]]:
    return list(csv.reader(StringIO(csv_text)))


def test_report_header_order():
    csv_text = build_csv_report([])
    rows = _parse_report(csv_text)
    assert rows[0] == REPORT_HEADER
    assert len(rows) == 1


def test_report_row_serialization_and_warning_dedup():
    row = ReportRow(
        zephyr_key="ES-T1",
        zephyr_id="100",
        folder_full_path="Root/Child",
        testy_suite_id=10,
        testy_case_id=20,
        action="created",
        steps_count=3,
        labels_count=2,
        attachments_in_xml=1,
        attachments_attached=1,
        attachments_missing=0,
        warnings=[" Missing attachment ", "Empty step", "Missing attachment"],
        error=None,
    )
    csv_text = build_csv_report([row])
    rows = _parse_report(csv_text)
    assert rows[1] == [
        "ES-T1",
        "100",
        "Root/Child",
        "10",
        "20",
        "created",
        "3",
        "2",
        "1",
        "1",
        "0",
        "Missing attachment | Empty step",
        "",
    ]


def test_report_error_column():
    row = ReportRow(
        zephyr_key=None,
        zephyr_id=None,
        folder_full_path=None,
        testy_suite_id=None,
        testy_case_id=None,
        action="failed",
        steps_count=0,
        labels_count=0,
        attachments_in_xml=0,
        attachments_attached=0,
        attachments_missing=0,
        warnings=[],
        error="Validation error",
    )
    csv_text = build_csv_report([row])
    rows = _parse_report(csv_text)
    assert rows[1][-2] == ""
    assert rows[1][-1] == "Validation error"
