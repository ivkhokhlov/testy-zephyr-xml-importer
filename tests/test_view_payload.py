from __future__ import annotations

from io import BytesIO

from zephyr_xml_importer.api import views


class DummyMapping:
    def __init__(self, mapping: dict[str, list[object]]) -> None:
        self._mapping = mapping

    def lists(self):
        return list(self._mapping.items())


class DummyRequest:
    def __init__(self, data: DummyMapping | None, files: DummyMapping | None) -> None:
        self.data = data
        self.FILES = files


def test_extract_payload_unwraps_list_values():
    file_obj = BytesIO(b"<project />")
    data = DummyMapping(
        {
            "project_id": ["7"],
            "dry_run": ["false"],
            "on_duplicate": ["skip"],
        }
    )
    files = DummyMapping({"xml_file": [file_obj]})

    payload = views._extract_payload(DummyRequest(data, files))

    assert payload["project_id"] == "7"
    assert payload["dry_run"] == "false"
    assert payload["on_duplicate"] == "skip"
    assert payload["xml_file"] is file_obj
