from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Sequence

REPORT_HEADER = [
    "zephyr_key",
    "zephyr_id",
    "folder_full_path",
    "testy_suite_id",
    "testy_case_id",
    "action",
    "steps_count",
    "labels_count",
    "attachments_in_xml",
    "attachments_attached",
    "attachments_missing",
    "warnings",
    "error",
]


@dataclass(frozen=True, slots=True)
class ReportRow:
    zephyr_key: str | None
    zephyr_id: str | None
    folder_full_path: str | None
    testy_suite_id: int | None
    testy_case_id: int | None
    action: str
    steps_count: int
    labels_count: int
    attachments_in_xml: int
    attachments_attached: int
    attachments_missing: int
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


def _format_optional(value: object | None) -> str:
    if value is None:
        return ""
    return str(value)


def _format_warnings(warnings: Sequence[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for warning in warnings:
        cleaned = " ".join(warning.split())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return " | ".join(ordered)


def _row_to_cells(row: ReportRow) -> list[str]:
    return [
        _format_optional(row.zephyr_key),
        _format_optional(row.zephyr_id),
        _format_optional(row.folder_full_path),
        _format_optional(row.testy_suite_id),
        _format_optional(row.testy_case_id),
        row.action,
        str(row.steps_count),
        str(row.labels_count),
        str(row.attachments_in_xml),
        str(row.attachments_attached),
        str(row.attachments_missing),
        _format_warnings(row.warnings),
        _format_optional(row.error),
    ]


def build_csv_report(rows: Sequence[ReportRow]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(REPORT_HEADER)
    for row in rows:
        writer.writerow(_row_to_cells(row))
    return output.getvalue()
