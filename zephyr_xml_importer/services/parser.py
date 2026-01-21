from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, cast

from defusedxml import ElementTree as DefusedET

from .models import ZephyrFolder, ZephyrIssue, ZephyrStep, ZephyrTestCase


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
                full_path = elem.attrib.get("fullPath") or ""
                index_raw = elem.attrib.get("index")
                idx = int(index_raw) if index_raw and index_raw.isdigit() else None
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

            zephyr_id = elem.attrib.get("id")
            key = elem.attrib.get("key")
            param_type = elem.attrib.get("paramType")

            # helper: find direct children by tag
            def text_of(tag: str) -> str | None:
                child = elem.find(tag)
                if child is None:
                    return None
                if child.text is None:
                    return None
                return child.text

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
            )

            # TODO: parse labels/issues/attachments/testScript/steps/testDataWrapper
            yield tc
            elem.clear()
    finally:
        if close_me:
            f.close()
