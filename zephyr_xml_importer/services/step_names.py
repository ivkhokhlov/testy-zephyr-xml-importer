from __future__ import annotations

import csv
import json
import re
import string
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, BinaryIO

from .models import ZephyrStep, ZephyrTestCase
from .sanitize import sanitize_html


DEFAULT_MAX_STEP_NAME_LENGTH = 255
STEP_NAME_TEMPLATE_ALLOWED_FIELDS = {
    "case_name",
    "description",
    "expected",
    "index",
    "index0",
    "key",
}


StepNameOverrides = dict[str, dict[int, str]]


class StepNameOverridesParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StepNameTemplate:
    template: str

    def render(
        self,
        *,
        key: str,
        case_name: str,
        step: ZephyrStep,
    ) -> str:
        mapping = {
            "index": step.index + 1,
            "index0": step.index,
            "key": key,
            "case_name": case_name,
            "description": sanitize_html(step.description),
            "expected": sanitize_html(step.expected_result),
        }
        return self.template.format_map(mapping)


def validate_step_name_template(value: Any) -> tuple[StepNameTemplate | None, list[str]]:
    if value is None:
        return None, []
    if not isinstance(value, str):
        return None, ["step_name_template must be a string"]

    template = value.strip()
    if not template:
        return None, []

    formatter = string.Formatter()
    try:
        parts = list(formatter.parse(template))
    except ValueError as exc:
        return None, [f"Invalid step_name_template: {exc}"]

    for _, field_name, format_spec, conversion in parts:
        if field_name is None:
            continue
        if conversion is not None:
            return None, ["step_name_template: conversions (e.g. !r) are not supported"]
        if format_spec:
            return None, ["step_name_template: format specs (e.g. :03d) are not supported"]
        if field_name not in STEP_NAME_TEMPLATE_ALLOWED_FIELDS:
            allowed = ", ".join(sorted(STEP_NAME_TEMPLATE_ALLOWED_FIELDS))
            return None, [f"step_name_template: unknown variable '{field_name}' (allowed: {allowed})"]

    return StepNameTemplate(template=template), []


def parse_step_name_overrides(
    source: str | Path | BinaryIO | bytes | None,
) -> tuple[StepNameOverrides, list[str]]:
    if source is None:
        return {}, []

    data = _read_source_bytes(source)
    if not data:
        return {}, []

    suffix = _extract_suffix(source)
    kind = _detect_kind(data, suffix=suffix)

    text: str
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise StepNameOverridesParseError("step_name_overrides must be UTF-8") from exc

    if kind == "json":
        return _parse_overrides_json(text)
    return _parse_overrides_csv(text)


def apply_step_names_to_payload(
    tc: ZephyrTestCase,
    payload: dict[str, Any],
    *,
    template: StepNameTemplate | None,
    overrides: StepNameOverrides,
    max_length: int = DEFAULT_MAX_STEP_NAME_LENGTH,
) -> list[str]:
    steps_payload = payload.get("steps", [])
    if not steps_payload:
        return []

    warnings: list[str] = []
    zephyr_steps = sorted(tc.steps, key=lambda step: step.index)

    key = (tc.key or "").strip()
    case_name = (tc.name or "").strip() or "(Unnamed test case)"

    override_map: dict[int, str] = {}
    if key:
        override_map = overrides.get(key, {})

    steps_payload_sorted = sorted(steps_payload, key=lambda item: int(item.get("sort_order", 0)))
    step_count = len(steps_payload_sorted)

    if override_map:
        for override_index in sorted(override_map):
            if override_index < 0 or override_index >= step_count:
                warnings.append(
                    f"Step name override out of range for case {key}: step_index={override_index + 1}"
                )

    for position, step_payload in enumerate(steps_payload_sorted):
        step_index0 = int(step_payload.get("sort_order", position))
        default_name = f"Step {step_index0 + 1}"

        resolved = override_map.get(step_index0)
        if resolved is None and template is not None and position < len(zephyr_steps):
            try:
                resolved = template.render(key=key, case_name=case_name, step=zephyr_steps[position])
            except Exception as exc:
                warnings.append(
                    f"Failed to render step_name_template for {key or case_name} step {step_index0 + 1}: "
                    f"{exc}"
                )
                resolved = None

        resolved = _normalize_step_name(resolved) if resolved is not None else None
        if not resolved:
            resolved = default_name

        if len(resolved) > max_length:
            warnings.append(
                f"Step name too long ({len(resolved)} > {max_length}) for "
                f"{key or case_name} step {step_index0 + 1}; truncating"
            )
            resolved = resolved[:max_length]

        step_payload["name"] = resolved

    return warnings


def warn_for_unknown_override_keys(overrides: StepNameOverrides, case_keys: set[str]) -> list[str]:
    warnings: list[str] = []
    for key in sorted(overrides):
        cleaned = key.strip()
        if cleaned and cleaned not in case_keys:
            warnings.append(f"Step name override key not found in import payload: {cleaned}")
    return warnings


def merge_step_name_overrides(
    base: StepNameOverrides,
    override: StepNameOverrides,
) -> StepNameOverrides:
    merged: StepNameOverrides = {key: dict(step_map) for key, step_map in base.items()}
    for key, step_map in override.items():
        bucket = merged.setdefault(key, {})
        for index0, name in step_map.items():
            bucket[index0] = name
    return merged


def _read_source_bytes(source: str | Path | BinaryIO | bytes) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    if isinstance(source, (str, Path)):
        with open(source, "rb") as handle:
            return handle.read()
    data = source.read()
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


def _extract_suffix(source: Any) -> str | None:
    if isinstance(source, (str, Path)):
        return Path(source).suffix.lower()
    name = getattr(source, "name", None)
    if isinstance(name, str):
        return Path(name).suffix.lower()
    return None


def _detect_kind(data: bytes, *, suffix: str | None) -> str:
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    stripped = data.lstrip()
    if stripped.startswith(b"[") or stripped.startswith(b"{"):
        return "json"
    return "csv"


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def _normalize_step_name(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _parse_overrides_csv(text: str) -> tuple[StepNameOverrides, list[str]]:
    stream = StringIO(text)
    reader = csv.DictReader(stream)
    raw_fields = reader.fieldnames or []
    if not raw_fields:
        raise StepNameOverridesParseError("step_name_overrides CSV: missing header row")

    field_map: dict[str, str] = {}
    for raw in raw_fields:
        normalized = _normalize_header(raw)
        if normalized == "key" and "key" not in field_map:
            field_map["key"] = raw
        elif normalized in {"stepindex", "step_index"} and "step_index" not in field_map:
            field_map["step_index"] = raw
        elif normalized == "name" and "name" not in field_map:
            field_map["name"] = raw

    missing = [k for k in ("key", "step_index", "name") if k not in field_map]
    if missing:
        raise StepNameOverridesParseError(
            "step_name_overrides CSV: missing columns: " + ", ".join(missing)
        )

    overrides: StepNameOverrides = {}
    warnings: list[str] = []

    for line_number, row in enumerate(reader, start=2):
        key = _normalize_step_name(row.get(field_map["key"]))
        step_index_raw = _normalize_step_name(row.get(field_map["step_index"]))
        name = _normalize_step_name(row.get(field_map["name"]))

        if not key or not step_index_raw or name is None:
            warnings.append(f"step_name_overrides CSV row {line_number}: missing key/step_index/name")
            continue

        try:
            step_index = int(step_index_raw)
        except Exception:
            warnings.append(
                f"step_name_overrides CSV row {line_number}: invalid step_index '{step_index_raw}'"
            )
            continue

        if step_index <= 0:
            warnings.append(
                f"step_name_overrides CSV row {line_number}: step_index must be >= 1"
            )
            continue

        index0 = step_index - 1
        bucket = overrides.setdefault(key, {})
        existing = bucket.get(index0)
        if existing is not None and existing != name:
            warnings.append(
                f"step_name_overrides CSV row {line_number}: duplicate override for {key} "
                f"step {step_index}; overwriting"
            )
        bucket[index0] = name

    return overrides, warnings


def _parse_overrides_json(text: str) -> tuple[StepNameOverrides, list[str]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StepNameOverridesParseError(f"step_name_overrides JSON: {exc}") from exc

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise StepNameOverridesParseError("step_name_overrides JSON must be an array of objects")

    overrides: StepNameOverrides = {}
    warnings: list[str] = []

    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            warnings.append(f"step_name_overrides JSON item {idx}: expected object")
            continue
        key = _normalize_step_name(item.get("key"))
        step_index_raw = item.get("step_index")
        name = _normalize_step_name(item.get("name"))
        if key is None or name is None or step_index_raw is None:
            warnings.append(f"step_name_overrides JSON item {idx}: missing key/step_index/name")
            continue
        try:
            step_index = int(str(step_index_raw).strip())
        except Exception:
            warnings.append(
                f"step_name_overrides JSON item {idx}: invalid step_index '{step_index_raw}'"
            )
            continue
        if step_index <= 0:
            warnings.append(f"step_name_overrides JSON item {idx}: step_index must be >= 1")
            continue
        index0 = step_index - 1
        bucket = overrides.setdefault(key, {})
        existing = bucket.get(index0)
        if existing is not None and existing != name:
            warnings.append(
                f"step_name_overrides JSON item {idx}: duplicate override for {key} "
                f"step {step_index}; overwriting"
            )
        bucket[index0] = name

    return overrides, warnings

