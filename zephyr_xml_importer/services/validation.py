from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import ZephyrStep, ZephyrTestCase
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
) -> list[str]:
    warnings: list[str] = []
    key = _clean_key(tc.key)

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

    if tc.steps:
        for step in tc.steps:
            if _is_step_empty(step):
                warnings.append(_format_empty_step_warning(step.index, key))

    return warnings


def _clean_key(value: str | None) -> str:
    return (value or "").strip()


def _is_step_empty(step: ZephyrStep) -> bool:
    return not sanitize_html(step.description) and not sanitize_html(step.test_data)


def _format_empty_step_warning(step_index: int, key: str) -> str:
    if key:
        return f"Empty step {step_index + 1} in Zephyr case {key}"
    return f"Empty step {step_index + 1} in Zephyr case (missing key)"
