from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable, Mapping

from .importer import NO_FOLDER_SUITE_NAME
from .sanitize import sanitize_html
from .testy_adapter import (
    CASE_MODEL_CANDIDATES,
    SUITE_MODEL_CANDIDATES,
    TestyAdapterError,
    _resolve_model,
    _resolve_project_model,
)
from .xlsx_exporter import ExportCase, ExportStep, XlsxExportResult, build_xlsx_export


logger = logging.getLogger(__name__)

METADATA_SOURCE_CHOICES = {"attributes_then_meta_labels", "attributes_only", "meta_labels_only"}
KEY_STRATEGY_CHOICES = {"existing_only", "synthetic"}
SYNTHETIC_KEY_PREFIX = "TESTY"


@dataclass(frozen=True, slots=True)
class SuiteInfo:
    suite_id: int
    name: str
    parent_id: int | None
    description: str | None


def export_testy_cases_to_xlsx(
    *,
    project_id: int,
    suite_id: int | None = None,
    include_children: bool = True,
    case_ids: list[int] | None = None,
    strip_zephyr_key_prefix: bool = True,
    metadata_source: str = "attributes_then_meta_labels",
    key_strategy: str = "existing_only",
) -> XlsxExportResult:
    export_cases = collect_testy_cases_for_export(
        project_id=project_id,
        suite_id=suite_id,
        include_children=include_children,
        case_ids=case_ids,
        strip_zephyr_key_prefix=strip_zephyr_key_prefix,
        metadata_source=metadata_source,
        key_strategy=key_strategy,
    )
    result = build_xlsx_export(export_cases)
    if result.warnings:
        logger.warning("Zephyr XLSX export warnings: %s", "; ".join(result.warnings))
    return result


def collect_testy_cases_for_export(
    *,
    project_id: int,
    suite_id: int | None,
    include_children: bool,
    case_ids: list[int] | None,
    strip_zephyr_key_prefix: bool,
    metadata_source: str,
    key_strategy: str,
) -> list[ExportCase]:
    if metadata_source not in METADATA_SOURCE_CHOICES:
        raise TestyAdapterError(f"Unsupported metadata_source '{metadata_source}'")
    if key_strategy not in KEY_STRATEGY_CHOICES:
        raise TestyAdapterError(f"Unsupported key_strategy '{key_strategy}'")

    project_model = _resolve_project_model()
    if project_model is None:
        raise TestyAdapterError("Project model is not available")
    if not project_model.objects.filter(id=project_id).exists():
        raise TestyAdapterError(f"Project {project_id} does not exist")

    suite_model = _resolve_model("TestSuite", SUITE_MODEL_CANDIDATES)
    case_model = _resolve_model("TestCase", CASE_MODEL_CANDIDATES)
    if suite_model is None:
        raise TestyAdapterError("TestSuite model is not available")
    if case_model is None:
        raise TestyAdapterError("TestCase model is not available")

    suites = list(
        suite_model.objects.filter(project_id=project_id).values(
            "id",
            "name",
            "parent_id",
            "description",
        )
    )
    suite_index = _build_suite_index(suites)
    suite_paths = _build_suite_paths(suite_index)

    scoped_suite_ids = _select_suite_ids(
        suite_model=suite_model,
        project_id=project_id,
        suite_id=suite_id,
        include_children=include_children,
        suite_index=suite_index,
    )

    case_queryset = case_model.objects.filter(project_id=project_id)
    if scoped_suite_ids is not None:
        case_queryset = case_queryset.filter(suite_id__in=scoped_suite_ids)
    if case_ids:
        case_queryset = case_queryset.filter(id__in=case_ids)
    if hasattr(case_model, "is_archive"):
        case_queryset = case_queryset.filter(is_archive=False)

    case_queryset = case_queryset.select_related("suite").prefetch_related(
        "steps",
        "labeled_items__label",
    )
    try:
        case_queryset = case_queryset.order_by("suite_id", "id")
    except Exception:
        pass

    export_cases: list[ExportCase] = []
    for case in case_queryset:
        export_cases.append(
            _build_export_case(
                case=case,
                suite_index=suite_index,
                suite_paths=suite_paths,
                strip_zephyr_key_prefix=strip_zephyr_key_prefix,
                metadata_source=metadata_source,
                key_strategy=key_strategy,
            )
        )
    return export_cases


def _select_suite_ids(
    *,
    suite_model: type,
    project_id: int,
    suite_id: int | None,
    include_children: bool,
    suite_index: dict[int, SuiteInfo],
) -> list[int] | None:
    if suite_id is None:
        return None
    if suite_id not in suite_index:
        raise TestyAdapterError(f"Suite {suite_id} does not exist in project {project_id}")
    if not include_children:
        return [suite_id]

    try:
        suite_obj = suite_model.objects.get(id=suite_id, project_id=project_id)
    except Exception:
        suite_obj = None
    if suite_obj is not None and hasattr(suite_obj, "get_descendants"):
        try:
            return list(
                suite_obj.get_descendants(include_self=True).values_list("id", flat=True)
            )
        except Exception:
            pass

    children_map: dict[int | None, list[int]] = {}
    for info in suite_index.values():
        children_map.setdefault(info.parent_id, []).append(info.suite_id)

    selected: list[int] = []

    def walk(current_id: int) -> None:
        selected.append(current_id)
        for child_id in children_map.get(current_id, []):
            walk(child_id)

    walk(suite_id)
    return selected


def _build_suite_index(raw_suites: Iterable[Mapping[str, Any]]) -> dict[int, SuiteInfo]:
    index: dict[int, SuiteInfo] = {}
    for suite in raw_suites:
        suite_id = int(suite.get("id"))
        index[suite_id] = SuiteInfo(
            suite_id=suite_id,
            name=str(suite.get("name") or ""),
            parent_id=suite.get("parent_id"),
            description=(suite.get("description") or "").strip() or None,
        )
    return index


def _build_suite_paths(suite_index: dict[int, SuiteInfo]) -> dict[int, str]:
    cache: dict[int, str] = {}

    def build_path(suite_id: int) -> str:
        if suite_id in cache:
            return cache[suite_id]
        info = suite_index.get(suite_id)
        if info is None:
            cache[suite_id] = ""
            return ""
        name = info.name.strip()
        if info.parent_id is None:
            cache[suite_id] = name
            return name
        parent_path = build_path(info.parent_id)
        path = f"{parent_path}/{name}" if parent_path else name
        cache[suite_id] = path
        return path

    for suite_id in suite_index:
        build_path(suite_id)
    return cache


def _build_export_case(
    *,
    case: Any,
    suite_index: dict[int, SuiteInfo],
    suite_paths: dict[int, str],
    strip_zephyr_key_prefix: bool,
    metadata_source: str,
    key_strategy: str,
) -> ExportCase:
    suite_id = getattr(case, "suite_id", None)
    suite_info = suite_index.get(int(suite_id)) if suite_id is not None else None
    folder_path = suite_paths.get(int(suite_id), "") if suite_id is not None else ""

    if suite_info and suite_info.parent_id is None and suite_info.name == NO_FOLDER_SUITE_NAME:
        folder_path = ""

    attributes = _safe_mapping(getattr(case, "attributes", None))
    zephyr_attributes = _safe_mapping(attributes.get("zephyr"))

    labels = _normalize_labels(_extract_case_labels(case))
    meta = _extract_metadata(labels, zephyr_attributes, metadata_source)

    key = _clean_value(zephyr_attributes.get("key"))
    if key_strategy == "synthetic" and not key:
        case_id = getattr(case, "id", None)
        if case_id is not None:
            key = f"{SYNTHETIC_KEY_PREFIX}-{case_id}"

    name = _clean_value(getattr(case, "name", None)) or "(Unnamed test case)"
    if strip_zephyr_key_prefix and key:
        prefix = f"[{key}] "
        if name.startswith(prefix):
            name = name[len(prefix) :]

    setup = sanitize_html(getattr(case, "setup", None))
    description = sanitize_html(getattr(case, "description", None))

    steps = _extract_steps(case)
    plain_text = None
    if not steps:
        plain_text = sanitize_html(getattr(case, "scenario", None)) or None

    issues = _extract_issue_keys(zephyr_attributes.get("issues"))

    return ExportCase(
        case_id=getattr(case, "id", None),
        key=key,
        name=name,
        status=meta.get("status"),
        precondition=setup or None,
        objective=description or None,
        folder=folder_path or None,
        folder_description=suite_info.description if suite_info else None,
        priority=meta.get("priority"),
        labels=[label for label in labels if not _is_meta_label(label)],
        owner=meta.get("owner"),
        issues=issues,
        steps=steps,
        plain_text=plain_text,
        bdd_text=None,
    )


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _clean_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _normalize_labels(raw_labels: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for label in raw_labels:
        cleaned = " ".join(str(label).split())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _is_meta_label(label: str) -> bool:
    return label.strip().lower().startswith("zephyr:")


def _extract_metadata(
    labels: list[str],
    zephyr_attributes: Mapping[str, Any],
    metadata_source: str,
) -> dict[str, str | None]:
    status = priority = owner = None
    if metadata_source in {"attributes_then_meta_labels", "attributes_only"}:
        status = _clean_value(zephyr_attributes.get("status"))
        priority = _clean_value(zephyr_attributes.get("priority"))
        owner = _clean_value(zephyr_attributes.get("owner"))

    if metadata_source in {"attributes_then_meta_labels", "meta_labels_only"}:
        if status is None:
            status = _extract_meta_label_value(labels, "status")
        if priority is None:
            priority = _extract_meta_label_value(labels, "priority")
        if owner is None:
            owner = _extract_meta_label_value(labels, "owner")

    return {"status": status, "priority": priority, "owner": owner}


def _extract_meta_label_value(labels: Iterable[str], key: str) -> str | None:
    prefix = f"zephyr:{key}="
    for label in labels:
        cleaned = label.strip()
        if cleaned.lower().startswith(prefix):
            value = cleaned[len(prefix) :].strip()
            return value or None
    return None


def _extract_case_labels(case: Any) -> list[str]:
    labels: list[str] = []
    labeled_items = getattr(case, "labeled_items", None)
    if labeled_items is not None:
        try:
            items = labeled_items.all()
        except Exception:
            items = labeled_items
        for item in items:
            label_obj = getattr(item, "label", None)
            name = getattr(label_obj, "name", None) if label_obj is not None else None
            if name is None:
                name = getattr(item, "name", None)
            if name is None:
                name = str(item)
            labels.append(str(name))
        return labels

    raw_labels = getattr(case, "labels", None)
    if raw_labels is None:
        return labels
    if isinstance(raw_labels, (list, tuple, set)):
        return [str(label) for label in raw_labels]
    return [str(raw_labels)]


def _extract_issue_keys(raw_issues: Any) -> list[str]:
    if not raw_issues:
        return []
    issues: list[str] = []
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if isinstance(item, dict):
                key = _clean_value(item.get("key"))
                if key:
                    issues.append(key)
            else:
                key = _clean_value(item)
                if key:
                    issues.append(key)
    else:
        key = _clean_value(raw_issues)
        if key:
            issues.append(key)
    return issues


def _extract_steps(case: Any) -> list[ExportStep]:
    is_steps = bool(getattr(case, "is_steps", False))
    steps_manager = getattr(case, "steps", None)
    if not is_steps or steps_manager is None:
        return []
    try:
        steps = list(steps_manager.all())
    except Exception:
        try:
            steps = list(steps_manager)
        except Exception:
            return []

    def step_key(step: Any) -> tuple[int, int]:
        sort_order = getattr(step, "sort_order", 0)
        step_id = getattr(step, "id", 0) or 0
        return int(sort_order), int(step_id)

    steps.sort(key=step_key)
    export_steps: list[ExportStep] = []
    for step in steps:
        scenario = sanitize_html(getattr(step, "scenario", None))
        description, test_data = _split_step_scenario(scenario)
        expected = sanitize_html(getattr(step, "expected", None))
        export_steps.append(
            ExportStep(
                description=description or None,
                test_data=test_data or None,
                expected_result=expected or None,
            )
        )
    return export_steps


def _split_step_scenario(value: str) -> tuple[str | None, str | None]:
    text = (value or "").strip()
    if not text:
        return None, None
    delimiter = "\n\nTest data:\n"
    if delimiter in text:
        desc, test_data = text.split(delimiter, 1)
        return desc.strip() or None, test_data.strip() or None
    prefix = "Test data:\n"
    if text.startswith(prefix):
        return None, text[len(prefix) :].strip() or None
    return text, None
