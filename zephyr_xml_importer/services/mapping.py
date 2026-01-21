from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import ZephyrTestCase, ZephyrStep
from .sanitize import sanitize_html


def flatten_steps_to_scenario(steps: list[ZephyrStep]) -> str:
    parts: list[str] = []
    for s in sorted(steps, key=lambda x: x.index):
        desc = sanitize_html(s.description)
        exp = sanitize_html(s.expected_result)
        td = sanitize_html(s.test_data)

        chunk = []
        chunk.append(f"Step {s.index + 1}")
        if desc:
            chunk.append(desc)
        if td:
            chunk.append(f"Test data:\n{td}")
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
    is_steps = True
    scenario = flatten_steps_to_scenario(tc.steps)
    if not scenario:
        # Required by TestY model: scenario must be non-empty
        scenario = f"(Imported from Zephyr {zephyr_key or 'unknown'}; no steps content)"

    labels = list(tc.labels)

    if meta_labels:
        if tc.status:
            labels.append(f"zephyr:status={tc.status}")
        if tc.priority:
            labels.append(f"zephyr:priority={tc.priority}")
        if tc.owner:
            labels.append(f"zephyr:owner={tc.owner}")

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
                "scenario": sanitize_html(s.description) or f"Step {s.index + 1} (empty in Zephyr)",
                "expected": sanitize_html(s.expected_result),
            }
            for s in sorted(tc.steps, key=lambda x: x.index)
        ],
    }
