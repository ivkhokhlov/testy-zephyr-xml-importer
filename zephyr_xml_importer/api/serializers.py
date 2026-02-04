from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Mapping

ON_DUPLICATE_CHOICES = {"skip", "upsert"}
METADATA_SOURCE_CHOICES = {
    "attributes_then_meta_labels",
    "attributes_only",
    "meta_labels_only",
}
KEY_STRATEGY_CHOICES = {"existing_only", "synthetic"}


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


@dataclass(frozen=True, slots=True)
class ExportRequestData:
    project_id: int
    suite_id: int | None
    include_children: bool
    case_ids: list[int] | None
    strip_zephyr_key_prefix: bool
    metadata_source: str
    key_strategy: str
    include_extra_testy_fields: bool


class ImportValidationError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Invalid import request")
        self.errors = errors


class ExportValidationError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Invalid export request")
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


def validate_export_request(data: Mapping[str, Any]) -> ExportRequestData:
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

    suite_id_raw = _unwrap(data.get("suite_id"))
    suite_id: int | None = None
    if suite_id_raw not in (None, ""):
        if isinstance(suite_id_raw, int):
            suite_id = suite_id_raw
        elif isinstance(suite_id_raw, str) and suite_id_raw.strip().isdigit():
            suite_id = int(suite_id_raw.strip())
        else:
            errors["suite_id"] = "suite_id must be an integer"
    if suite_id is not None and suite_id <= 0:
        errors["suite_id"] = "suite_id must be positive"

    include_children = _coerce_bool(
        _unwrap(data.get("include_children")),
        default=True,
        field="include_children",
        errors=errors,
    )
    strip_zephyr_key_prefix = _coerce_bool(
        _unwrap(data.get("strip_zephyr_key_prefix")),
        default=True,
        field="strip_zephyr_key_prefix",
        errors=errors,
    )

    metadata_source_raw = _unwrap(data.get("metadata_source", "attributes_then_meta_labels"))
    metadata_source = (
        str(metadata_source_raw).strip() if metadata_source_raw is not None else ""
    ) or "attributes_then_meta_labels"
    if metadata_source not in METADATA_SOURCE_CHOICES:
        errors["metadata_source"] = (
            "metadata_source must be one of: attributes_then_meta_labels, attributes_only, "
            "meta_labels_only"
        )

    key_strategy_raw = _unwrap(data.get("key_strategy", "existing_only"))
    key_strategy = str(key_strategy_raw).strip() if key_strategy_raw is not None else ""
    if not key_strategy:
        key_strategy = "existing_only"
    if key_strategy not in KEY_STRATEGY_CHOICES:
        errors["key_strategy"] = "key_strategy must be 'existing_only' or 'synthetic'"

    include_extra_testy_fields = _coerce_bool(
        _unwrap(data.get("include_extra_testy_fields")),
        default=False,
        field="include_extra_testy_fields",
        errors=errors,
    )

    case_ids_raw = _unwrap(data.get("case_ids"))
    case_ids: list[int] | None = None
    if case_ids_raw not in (None, ""):
        case_ids = []
        if isinstance(case_ids_raw, str):
            tokens = [t for t in case_ids_raw.replace(";", ",").split(",") if t.strip()]
            values: list[str | int] = tokens
        elif isinstance(case_ids_raw, (list, tuple, set)):
            values = list(case_ids_raw)
        else:
            values = [case_ids_raw]
        for item in values:
            if isinstance(item, int):
                value = item
            elif isinstance(item, str) and item.strip().isdigit():
                value = int(item.strip())
            else:
                errors["case_ids"] = "case_ids must be a list of integers or comma-separated string"
                break
            if value <= 0:
                errors["case_ids"] = "case_ids must contain positive integers"
                break
            case_ids.append(value)
        if case_ids:
            seen: set[int] = set()
            case_ids = [cid for cid in case_ids if not (cid in seen or seen.add(cid))]
        else:
            case_ids = None

    if errors:
        raise ExportValidationError(errors)

    return ExportRequestData(
        project_id=project_id or 0,
        suite_id=suite_id,
        include_children=include_children,
        case_ids=case_ids,
        strip_zephyr_key_prefix=strip_zephyr_key_prefix,
        metadata_source=metadata_source,
        key_strategy=key_strategy,
        include_extra_testy_fields=include_extra_testy_fields,
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

    class ExportRequestSerializer(serializers.Serializer):
        project_id = serializers.IntegerField()
        suite_id = serializers.IntegerField(required=False, allow_null=True)
        include_children = serializers.BooleanField(required=False, default=True)
        case_ids = serializers.ListField(
            child=serializers.IntegerField(),
            required=False,
            allow_empty=True,
        )
        strip_zephyr_key_prefix = serializers.BooleanField(required=False, default=True)
        metadata_source = serializers.ChoiceField(
            required=False,
            default="attributes_then_meta_labels",
            choices=sorted(METADATA_SOURCE_CHOICES),
        )
        key_strategy = serializers.ChoiceField(
            required=False,
            default="existing_only",
            choices=sorted(KEY_STRATEGY_CHOICES),
        )
        include_extra_testy_fields = serializers.BooleanField(required=False, default=False)
