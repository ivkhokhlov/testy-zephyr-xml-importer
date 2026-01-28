from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Mapping

ON_DUPLICATE_CHOICES = {"skip", "upsert"}


@dataclass(frozen=True, slots=True)
class ImportRequestData:
    project_id: int
    xml_file: str | Path | BinaryIO | bytes
    attachments_zip: str | Path | BinaryIO | bytes | None
    dry_run: bool
    prefix_with_zephyr_key: bool
    meta_labels: bool
    append_jira_issues_to_description: bool
    embed_testdata_to_description: bool
    on_duplicate: str


class ImportValidationError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Invalid import request")
        self.errors = errors


def _unwrap(value: Any) -> Any:
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return value


def _coerce_bool(value: Any, *, default: bool, field: str, errors: dict[str, str]) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    errors[field] = "must be a boolean"
    return default


def _is_file_source(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (bytes, bytearray, Path)):
        return True
    return hasattr(value, "read")


def validate_import_request(data: Mapping[str, Any]) -> ImportRequestData:
    errors: dict[str, str] = {}

    project_id_raw = _unwrap(data.get("project_id"))
    project_id: int | None = None
    if project_id_raw is None:
        errors["project_id"] = "project_id is required"
    elif isinstance(project_id_raw, int):
        project_id = project_id_raw
    elif isinstance(project_id_raw, str) and project_id_raw.strip().isdigit():
        project_id = int(project_id_raw.strip())
    else:
        errors["project_id"] = "project_id must be an integer"

    if project_id is not None and project_id <= 0:
        errors["project_id"] = "project_id must be positive"

    xml_file = _unwrap(data.get("xml_file"))
    if not _is_file_source(xml_file):
        errors["xml_file"] = "xml_file is required"

    attachments_zip = _unwrap(data.get("attachments_zip"))
    if attachments_zip is not None and not _is_file_source(attachments_zip):
        errors["attachments_zip"] = "attachments_zip must be a file"

    dry_run = _coerce_bool(
        _unwrap(data.get("dry_run")),
        default=False,
        field="dry_run",
        errors=errors,
    )
    prefix_with_zephyr_key = _coerce_bool(
        _unwrap(data.get("prefix_with_zephyr_key")),
        default=True,
        field="prefix_with_zephyr_key",
        errors=errors,
    )
    meta_labels = _coerce_bool(
        _unwrap(data.get("meta_labels")),
        default=True,
        field="meta_labels",
        errors=errors,
    )
    append_jira_issues_to_description = _coerce_bool(
        _unwrap(data.get("append_jira_issues_to_description")),
        default=True,
        field="append_jira_issues_to_description",
        errors=errors,
    )
    embed_testdata_to_description = _coerce_bool(
        _unwrap(data.get("embed_testdata_to_description")),
        default=True,
        field="embed_testdata_to_description",
        errors=errors,
    )

    on_duplicate_raw = _unwrap(data.get("on_duplicate", "skip"))
    on_duplicate = str(on_duplicate_raw).strip().lower() if on_duplicate_raw is not None else "skip"
    if on_duplicate not in ON_DUPLICATE_CHOICES:
        errors["on_duplicate"] = "on_duplicate must be 'skip' or 'upsert'"

    if errors:
        raise ImportValidationError(errors)

    return ImportRequestData(
        project_id=project_id or 0,
        xml_file=xml_file,
        attachments_zip=attachments_zip,
        dry_run=dry_run,
        prefix_with_zephyr_key=prefix_with_zephyr_key,
        meta_labels=meta_labels,
        append_jira_issues_to_description=append_jira_issues_to_description,
        embed_testdata_to_description=embed_testdata_to_description,
        on_duplicate=on_duplicate,
    )


try:
    from rest_framework import serializers
except Exception:  # pragma: no cover - DRF optional for unit tests
    serializers = None

if serializers:  # pragma: no cover - DRF optional for unit tests

    class ImportRequestSerializer(serializers.Serializer):
        project_id = serializers.IntegerField()
        xml_file = serializers.FileField()
        attachments_zip = serializers.FileField(required=False, allow_null=True)
        dry_run = serializers.BooleanField(required=False, default=False)
        prefix_with_zephyr_key = serializers.BooleanField(required=False, default=True)
        meta_labels = serializers.BooleanField(required=False, default=True)
        append_jira_issues_to_description = serializers.BooleanField(required=False, default=True)
        embed_testdata_to_description = serializers.BooleanField(required=False, default=True)
        on_duplicate = serializers.ChoiceField(
            required=False,
            default="skip",
            choices=sorted(ON_DUPLICATE_CHOICES),
        )
