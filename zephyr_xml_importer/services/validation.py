from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import ZephyrFolder, ZephyrStep, ZephyrTestCase
from .sanitize import sanitize_html


DEFAULT_MAX_NAME_LENGTH = 255


def build_duplicate_key_counts(test_cases: Iterable[ZephyrTestCase]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tc in test_cases:
        key = _clean_key(tc.key)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_case_warnings(
    tc: ZephyrTestCase,
    mapped_name: str,
    duplicate_key_counts: Mapping[str, int],
    *,
    max_name_length: int = DEFAULT_MAX_NAME_LENGTH,
    folders: Mapping[str, ZephyrFolder] | None = None,
) -> list[str]:
    warnings: list[str] = []
    key = _clean_key(tc.key)
    folder_path = _clean_folder_path(tc.folder)

    if key and duplicate_key_counts.get(key, 0) > 1:
        warnings.append(f"Duplicate Zephyr key in XML: {key}")

    name_length = len(mapped_name)
    if name_length > max_name_length:
        if key:
            warnings.append(
                f"Test case name too long ({name_length} > {max_name_length}) for {key}"
            )
        else:
            warnings.append(f"Test case name too long ({name_length} > {max_name_length})")

    if not folder_path:
        warnings.append(_format_missing_folder_warning(key))
    elif folders is not None and folder_path not in folders:
        warnings.append(_format_missing_folder_reference_warning(folder_path, key))

    if tc.steps:
        for step in tc.steps:
            if _is_step_empty(step):
                warnings.append(_format_empty_step_warning(step.index, key))
            if _is_expected_empty(step) and _has_step_scenario(step):
                warnings.append(_format_empty_expected_warning(step.index, key))

    return warnings


def _clean_key(value: str | None) -> str:
    return (value or "").strip()


def _clean_folder_path(value: str | None) -> str:
    return (value or "").strip()


def _is_step_empty(step: ZephyrStep) -> bool:
    return not sanitize_html(step.description) and not sanitize_html(step.test_data)


def _is_expected_empty(step: ZephyrStep) -> bool:
    return not sanitize_html(step.expected_result)


def _has_step_scenario(step: ZephyrStep) -> bool:
    return bool(sanitize_html(step.description) or sanitize_html(step.test_data))


def _format_empty_step_warning(step_index: int, key: str) -> str:
    if key:
        return f"Empty step {step_index + 1} in Zephyr case {key}"
    return f"Empty step {step_index + 1} in Zephyr case (missing key)"


def _format_empty_expected_warning(step_index: int, key: str) -> str:
    if key:
        return f"Empty expected result for step {step_index + 1} in Zephyr case {key}"
    return f"Empty expected result for step {step_index + 1} in Zephyr case (missing key)"


def _format_missing_folder_warning(key: str) -> str:
    if key:
        return f"Missing folder in Zephyr case {key}"
    return "Missing folder in Zephyr case (missing key)"


def _format_missing_folder_reference_warning(folder_path: str, key: str) -> str:
    if key:
        return f"Folder not found in Zephyr export: {folder_path} for case {key}"
    return f"Folder not found in Zephyr export: {folder_path} for case (missing key)"
