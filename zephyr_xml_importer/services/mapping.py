from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .attachments import AttachmentMatchResult, AttachmentZipIndex, match_attachments
from .models import ZephyrTestCase, ZephyrStep
from .sanitize import sanitize_html


def _normalize_label(label: str) -> str:
    return " ".join(label.split())


def _normalized_labels(raw_labels: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in raw_labels:
        cleaned = _normalize_label(raw)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _add_label(labels: list[str], seen: set[str], label: str | None) -> None:
    if not label:
        return
    cleaned = _normalize_label(label)
    if not cleaned or cleaned in seen:
        return
    seen.add(cleaned)
    labels.append(cleaned)


def _normalize_value(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = _normalize_label(value)
    return cleaned or None


def _build_step_scenario(step: ZephyrStep) -> str:
    desc = sanitize_html(step.description)
    test_data = sanitize_html(step.test_data)
    if desc:
        if test_data:
            return f"{desc}\n\nTest data:\n{test_data}"
        return desc
    if test_data:
        return f"Test data:\n{test_data}"
    return f"Step {step.index + 1} (empty in Zephyr)"


def flatten_steps_to_scenario(steps: list[ZephyrStep]) -> str:
    parts: list[str] = []
    for s in sorted(steps, key=lambda x: x.index):
        step_scenario = _build_step_scenario(s)
        exp = sanitize_html(s.expected_result)

        chunk = []
        chunk.append(f"Step {s.index + 1}")
        if step_scenario:
            chunk.append(step_scenario)
        if exp:
            chunk.append(f"Expected:\n{exp}")
        parts.append("\n".join(chunk).strip())
    return "\n\n".join([p for p in parts if p]).strip()


def build_testy_payload_from_zephyr(
    tc: ZephyrTestCase,
    *,
    prefix_with_zephyr_key: bool = True,
    meta_labels: bool = True,
    append_jira_issues_to_description: bool = True,
    embed_testdata_to_description: bool = True,
) -> dict[str, Any]:
    """
    Pure mapping helper: build a dictionary that a future importer can translate into
    TestCaseService().case_with_steps_create(...) kwargs.

    This repo starts without TestY installed; integration happens later.
    """
    zephyr_key = (tc.key or "").strip()
    name = (tc.name or "").strip() or "(Unnamed test case)"
    if prefix_with_zephyr_key and zephyr_key:
        name = f"[{zephyr_key}] {name}"

    setup = sanitize_html(tc.precondition)
    description = sanitize_html(tc.objective)

    # Steps-based default (Zephyr export commonly uses steps)
    is_steps = (tc.test_script_type or "").lower() == "steps" or bool(tc.steps)
    if is_steps:
        scenario = flatten_steps_to_scenario(tc.steps)
    else:
        scenario = sanitize_html(tc.test_script_text)
    if not scenario:
        # Required by TestY model: scenario must be non-empty
        scenario = f"(Imported from Zephyr {zephyr_key or 'unknown'}; no scenario content)"

    labels = _normalized_labels(tc.labels)
    seen_labels = set(labels)

    if meta_labels:
        status = _normalize_value(tc.status)
        priority = _normalize_value(tc.priority)
        owner = _normalize_value(tc.owner)
        if status:
            _add_label(labels, seen_labels, f"zephyr:status={status}")
        if priority:
            _add_label(labels, seen_labels, f"zephyr:priority={priority}")
        if owner:
            _add_label(labels, seen_labels, f"zephyr:owner={owner}")

    attributes = {
        "zephyr": {
            "id": tc.zephyr_id,
            "key": tc.key,
            "folder": tc.folder,
            "status": tc.status,
            "priority": tc.priority,
            "owner": tc.owner,
            "createdBy": tc.created_by,
            "createdOn": tc.created_on,
            "updatedBy": tc.updated_by,
            "updatedOn": tc.updated_on,
            "issues": [asdict(i) for i in tc.issues],
            "attachments": list(tc.attachments),
            "paramType": tc.param_type,
            "parameters": list(tc.parameters),
            "testDataWrapper": tc.test_data_wrapper,
        }
    }

    return {
        "name": name,
        "setup": setup,
        "scenario": scenario,
        "expected": "",
        "teardown": "",
        "description": description,
        "is_steps": is_steps,
        "attributes": attributes,
        "labels": labels,
        "steps": [
            {
                "sort_order": s.index,
                "name": f"Step {s.index + 1}",
                "scenario": _build_step_scenario(s),
                "expected": sanitize_html(s.expected_result),
            }
            for s in sorted(tc.steps, key=lambda x: x.index)
        ],
    }


def match_attachments_for_testcase(
    tc: ZephyrTestCase,
    zip_index: AttachmentZipIndex | None,
) -> AttachmentMatchResult:
    return match_attachments(tc.attachments, zip_index)
