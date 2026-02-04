from pathlib import Path

import pytest

from zephyr_xml_importer.api.serializers import ImportValidationError, validate_import_request
from zephyr_xml_importer.api.views import handle_import_request


FIXTURE = Path(__file__).parent / "fixtures" / "sample.xml"


def test_validate_import_request_defaults_and_coercions():
    data = {
        "project_id": "42",
        "xml_file": b"<project />",
        "dry_run": "true",
    }
    request = validate_import_request(data)
    assert request.project_id == 42
    assert request.dry_run is True
    assert request.on_duplicate == "skip"
    assert request.prefix_with_zephyr_key is True
    assert request.meta_labels is True


def test_validate_import_request_missing_required_fields():
    with pytest.raises(ImportValidationError) as excinfo:
        validate_import_request({"project_id": 1})
    assert "xml_file" in excinfo.value.errors


def test_validate_import_request_invalid_on_duplicate():
    with pytest.raises(ImportValidationError) as excinfo:
        validate_import_request(
            {
                "project_id": 1,
                "xml_file": b"<project />",
                "on_duplicate": "replace",
            }
        )
    assert "on_duplicate" in excinfo.value.errors


def test_handle_import_request_dry_run_response():
    xml_bytes = FIXTURE.read_bytes()
    response = handle_import_request(
        {
            "project_id": 7,
            "xml_file": xml_bytes,
            "dry_run": True,
        }
    )
    assert response["status"] == "success"
    assert response["dry_run"] is True
    summary = response["summary"]
    assert summary == {
        "folders": 2,
        "cases": 1,
        "steps": 2,
        "labels": 5,
        "attachments": 2,
        "created": 1,
        "reused": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }
    assert "ES-T560" in response["report_csv"]
