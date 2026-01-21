from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, cast

try:
    from defusedxml import ElementTree as DefusedET
except ImportError:  # pragma: no cover - fallback for test environments without defusedxml
    import xml.etree.ElementTree as DefusedET

from .models import (
    ZephyrFolder,
    ZephyrIssue,
    ZephyrStep,
    ZephyrTestCase,
    ZephyrTestDataCell,
    ZephyrTestDataRow,
    ZephyrTestDataTable,
)


def _open_binary(source: str | Path | BinaryIO | bytes) -> BinaryIO:
    if isinstance(source, (str, Path)):
        return open(source, "rb")
    if isinstance(source, (bytes, bytearray)):
        return BytesIO(bytes(source))
    return cast(BinaryIO, source)


def parse_folders(source: str | Path | BinaryIO | bytes) -> dict[str, ZephyrFolder]:
    """
    Parse `<folders>` into a mapping full_path -> ZephyrFolder.

    Streaming requirement: use iterparse and clear elements.
    """
    folders: dict[str, ZephyrFolder] = {}
    f = _open_binary(source)
    close_me = isinstance(source, (str, Path))
    try:
        # iterparse yields elements; we watch for end of <folder>
        for event, elem in DefusedET.iterparse(f, events=("end",)):
            if elem.tag == "folder":
                full_path = (elem.attrib.get("fullPath") or "").strip()
                index_raw = elem.attrib.get("index")
                idx = None
                if index_raw is not None:
                    try:
                        idx = int(index_raw)
                    except ValueError:
                        idx = None
                if full_path:
                    folders[full_path] = ZephyrFolder(full_path=full_path, index=idx)
            elem.clear()
        return folders
    finally:
        if close_me:
            f.close()


def iter_test_cases(source: str | Path | BinaryIO | bytes) -> Iterator[ZephyrTestCase]:
    """
    Yield ZephyrTestCase objects streaming from `<testCases>`.

    This is intentionally partial; the loop will extend it (steps, labels, issues, etc.).
    """
    f = _open_binary(source)
    close_me = isinstance(source, (str, Path))
    try:
        for event, elem in DefusedET.iterparse(f, events=("end",)):
            if elem.tag != "testCase":
                continue

            def clean_text(text: str | None) -> str | None:
                if text is None:
                    return None
                cleaned = text.strip()
                return cleaned if cleaned else None

            def parse_int(value: str | None) -> int | None:
                if value is None:
                    return None
                try:
                    return int(value)
                except ValueError:
                    return None

            zephyr_id = clean_text(elem.attrib.get("id"))
            key = clean_text(elem.attrib.get("key"))
            param_type = clean_text(elem.attrib.get("paramType"))

            # helper: find direct children by tag
            def text_of(tag: str) -> str | None:
                child = elem.find(tag)
                if child is None:
                    return None
                return clean_text(child.text)

            def text_of_child(parent: DefusedET.Element, tag: str) -> str | None:
                child = parent.find(tag)
                if child is None:
                    return None
                return clean_text(child.text)

            labels: list[str] = []
            labels_elem = elem.find("labels")
            if labels_elem is not None:
                for label_elem in labels_elem.findall("label"):
                    label = clean_text(label_elem.text)
                    if label:
                        labels.append(label)

            issues: list[ZephyrIssue] = []
            issues_elem = elem.find("issues")
            if issues_elem is not None:
                for issue_elem in issues_elem.findall("issue"):
                    issue_key = text_of_child(issue_elem, "key")
                    if issue_key:
                        issues.append(
                            ZephyrIssue(
                                key=issue_key,
                                summary=text_of_child(issue_elem, "summary"),
                            )
                        )

            attachments: list[str] = []
            attachments_elem = elem.find("attachments")
            if attachments_elem is not None:
                for attachment_elem in attachments_elem.findall("attachment"):
                    name = text_of_child(attachment_elem, "name")
                    if name:
                        attachments.append(name)

            parameters: list[str] = []
            parameters_elem = elem.find("parameters")
            if parameters_elem is not None:
                param_entries: list[tuple[int | None, int, str]] = []
                for order, param_elem in enumerate(parameters_elem.findall("parameter")):
                    name = text_of_child(param_elem, "name")
                    if not name:
                        continue
                    idx = parse_int(param_elem.attrib.get("index"))
                    param_entries.append((idx, order, name))
                if param_entries:
                    if any(idx is not None for idx, _, _ in param_entries):
                        param_entries.sort(
                            key=lambda entry: (
                                entry[0] is None,
                                entry[0] if entry[0] is not None else entry[1],
                                entry[1],
                            )
                        )
                    parameters = [name for _, _, name in param_entries]

            test_data_wrapper: ZephyrTestDataTable | None = None
            wrapper_elem = elem.find("testDataWrapper")
            if wrapper_elem is not None:
                rows: list[ZephyrTestDataRow] = []
                for row_elem in wrapper_elem.findall("testDataRow"):
                    columns_elem = row_elem.find("testDataColumns")
                    if columns_elem is None:
                        continue
                    cell_entries: list[tuple[int | None, int, ZephyrTestDataCell]] = []
                    for order, cell_elem in enumerate(columns_elem.findall("testData")):
                        idx = parse_int(cell_elem.attrib.get("index"))
                        name = text_of_child(cell_elem, "name")
                        data_type = text_of_child(cell_elem, "type")
                        value = text_of_child(cell_elem, "value")
                        if idx is None and not (name or data_type or value):
                            continue
                        cell_entries.append(
                            (
                                idx,
                                order,
                                ZephyrTestDataCell(
                                    index=idx,
                                    name=name,
                                    data_type=data_type,
                                    value=value,
                                ),
                            )
                        )
                    if cell_entries:
                        if any(idx is not None for idx, _, _ in cell_entries):
                            cell_entries.sort(
                                key=lambda entry: (
                                    entry[0] is None,
                                    entry[0] if entry[0] is not None else entry[1],
                                    entry[1],
                                )
                            )
                        rows.append(ZephyrTestDataRow(cells=[cell for _, _, cell in cell_entries]))
                if rows:
                    test_data_wrapper = ZephyrTestDataTable(rows=rows)

            test_script_type = None
            test_script_text = None
            steps: list[ZephyrStep] = []
            test_script_elem = elem.find("testScript")
            if test_script_elem is not None:
                test_script_type = clean_text(test_script_elem.attrib.get("type"))
                text_elem = test_script_elem.find("text")
                if text_elem is not None:
                    test_script_text = clean_text(text_elem.text)
                else:
                    test_script_text = clean_text(test_script_elem.text)

                steps_elem = test_script_elem.find("steps")
                if steps_elem is not None:
                    for order, step_elem in enumerate(steps_elem.findall("step")):
                        idx = parse_int(step_elem.attrib.get("index"))
                        if idx is None:
                            idx = order
                        steps.append(
                            ZephyrStep(
                                index=idx,
                                description=text_of_child(step_elem, "description"),
                                expected_result=text_of_child(step_elem, "expectedResult"),
                                test_data=text_of_child(step_elem, "testData"),
                            )
                        )

            tc = ZephyrTestCase(
                zephyr_id=zephyr_id,
                key=key,
                name=text_of("name"),
                folder=text_of("folder"),
                objective=text_of("objective"),
                precondition=text_of("precondition"),
                status=text_of("status"),
                priority=text_of("priority"),
                owner=text_of("owner"),
                created_by=text_of("createdBy"),
                created_on=text_of("createdOn"),
                updated_by=text_of("updatedBy"),
                updated_on=text_of("updatedOn"),
                param_type=param_type,
                parameters=parameters,
                test_data_wrapper=test_data_wrapper,
                labels=labels,
                issues=issues,
                attachments=attachments,
                test_script_type=test_script_type,
                test_script_text=test_script_text,
                steps=steps,
            )

            yield tc
            elem.clear()
    finally:
        if close_me:
            f.close()
