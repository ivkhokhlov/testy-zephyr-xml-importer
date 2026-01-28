from __future__ import annotations

from pathlib import Path

import pytest

try:
    import openpyxl
except Exception:  # pragma: no cover - dependency should be installed in runtime
    openpyxl = None

from zephyr_xml_importer.services.xlsx_parser import build_folders_from_cases, iter_test_cases_xlsx


@pytest.mark.skipif(openpyxl is None, reason="openpyxl is required for XLSX parsing")
def test_iter_test_cases_xlsx(tmp_path: Path) -> None:
    workbook_path = tmp_path / "export.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
            "Key",
            "Name",
            "Status",
            "Precondition",
            "Objective",
            "Folder",
            "Folder Description",
            "Priority",
            "Labels",
            "Owner",
            "Coverage (Issues)",
            "Test Script (Step-by-Step) - Step",
            "Test Script (Step-by-Step) - Test Data",
            "Test Script (Step-by-Step) - Expected Result",
            "Test Script (Plain Text)",
            "Test Script (BDD)",
        ]
    )
    ws.append(
        [
            "ES-T1",
            "Login works",
            "Approved",
            "User exists",
            "Goal",
            "/ui/Login",
            "Login form checks",
            "High",
            "smoke, regression",
            "alice",
            "ES-1; ES-2",
            "Open page",
            "user=admin",
            "Page opens",
            None,
            None,
        ]
    )
    ws.append(
        [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "Submit form",
            None,
            "Dashboard opens",
            None,
            None,
        ]
    )
    ws.append(
        [
            "ES-T2",
            "Plain case",
            "Draft",
            None,
            None,
            "",
            None,
            "Low",
            "label1",
            "bob",
            "",
            None,
            None,
            None,
            "Scenario text",
            None,
        ]
    )
    wb.save(workbook_path)
    wb.close()

    cases = list(iter_test_cases_xlsx(workbook_path))
    assert len(cases) == 2

    first = cases[0]
    assert first.key == "ES-T1"
    assert first.name == "Login works"
    assert first.folder == "/ui/Login"
    assert first.folder_description == "Login form checks"
    assert first.labels == ["smoke", "regression"]
    assert [issue.key for issue in first.issues] == ["ES-1", "ES-2"]
    assert first.test_script_type == "steps"
    assert first.test_script_text is None
    assert len(first.steps) == 2
    assert first.steps[0].description == "Open page"
    assert first.steps[0].expected_result == "Page opens"
    assert first.steps[1].description == "Submit form"
    assert first.steps[1].expected_result == "Dashboard opens"

    second = cases[1]
    assert second.key == "ES-T2"
    assert second.test_script_type == "plain"
    assert second.test_script_text == "Scenario text"
    assert second.steps == []

    folders = build_folders_from_cases(cases)
    assert "/ui/Login" in folders
    assert folders["/ui/Login"].description == "Login form checks"
