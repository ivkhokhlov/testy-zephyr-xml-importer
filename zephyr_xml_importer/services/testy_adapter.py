from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import importlib
from typing import Any, Mapping, Sequence


class TestyAdapterError(RuntimeError):
    pass


class BaseTestyAdapter:
    def get_suite_id(self, project_id: int, name: str, parent_id: int | None) -> int | None:
        raise NotImplementedError

    def create_suite(
        self,
        project_id: int,
        name: str,
        parent_id: int | None,
        attributes: Mapping[str, Any] | None,
    ) -> int:
        raise NotImplementedError

    def find_case_id_by_zephyr_key(self, project_id: int, zephyr_key: str) -> int | None:
        raise NotImplementedError

    def create_case_with_steps(
        self,
        project_id: int,
        suite_id: int,
        payload: Mapping[str, Any],
    ) -> int:
        raise NotImplementedError

    def update_case_with_steps(
        self,
        project_id: int,
        case_id: int,
        suite_id: int,
        payload: Mapping[str, Any],
    ) -> int:
        raise NotImplementedError

    def set_labels(self, project_id: int, case_id: int, labels: Sequence[str]) -> int:
        raise NotImplementedError

    def attach_file(self, project_id: int, case_id: int, filename: str, content: bytes) -> None:
        raise NotImplementedError


def _resolve_class(class_name: str, module_candidates: Sequence[str]) -> type:
    for module_name in module_candidates:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        if hasattr(module, class_name):
            return getattr(module, class_name)
    raise TestyAdapterError(
        f"Unable to import {class_name} from {', '.join(module_candidates)}"
    )


def _resolve_model(class_name: str, module_candidates: Sequence[str]) -> type | None:
    for module_name in module_candidates:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        if hasattr(module, class_name):
            return getattr(module, class_name)
    return None


@dataclass(frozen=True, slots=True)
class ProjectChoice:
    id: int
    name: str


def load_project_choices() -> tuple[list[ProjectChoice] | None, str | None]:
    model = _resolve_model("Project", ("testy.models", "testy.projects.models"))
    if model is None:
        return None, "Project model is not available"
    manager = getattr(model, "objects", None)
    if manager is None:
        return None, "Project model has no manager"
    try:
        queryset = manager.all()
    except Exception as exc:  # pragma: no cover - depends on TestY runtime
        return None, f"Unable to load projects: {exc}"
    try:
        queryset = queryset.order_by("name", "id")
    except Exception:
        pass
    try:
        items = list(queryset)
    except Exception as exc:  # pragma: no cover - depends on TestY runtime
        return None, f"Unable to iterate projects: {exc}"

    projects: list[ProjectChoice] = []
    for item in items:
        try:
            project_id = int(getattr(item, "id"))
        except Exception:
            continue
        name = getattr(item, "name", None)
        if name is None:
            name = getattr(item, "title", None)
        if name is None:
            name = str(project_id)
        projects.append(ProjectChoice(id=project_id, name=str(name)))

    if not projects:
        return None, "No projects available"

    projects.sort(key=lambda project: (project.name.casefold(), project.id))
    return projects, None


class TestyServiceAdapter(BaseTestyAdapter):
    def __init__(self) -> None:
        try:
            suite_service_cls = _resolve_class(
                "TestSuiteService",
                (
                    "testy.services",
                    "testy.services.suites",
                    "testy.services.test_suites",
                ),
            )
            case_service_cls = _resolve_class(
                "TestCaseService",
                (
                    "testy.services",
                    "testy.services.cases",
                    "testy.services.test_cases",
                ),
            )
            label_service_cls = _resolve_class(
                "LabelService",
                ("testy.services", "testy.services.labels"),
            )
            attachment_service_cls = _resolve_class(
                "AttachmentService",
                ("testy.services", "testy.services.attachments"),
            )
        except Exception as exc:  # pragma: no cover - depends on TestY runtime
            raise TestyAdapterError(
                "TestY services are not available; install TestY to run real imports."
            ) from exc

        self._suite_service = suite_service_cls()
        self._case_service = case_service_cls()
        self._label_service = label_service_cls()
        self._attachment_service = attachment_service_cls()
        self._suite_model = _resolve_model(
            "TestSuite",
            ("testy.models", "testy.suites.models"),
        )
        self._case_model = _resolve_model(
            "TestCase",
            ("testy.models", "testy.cases.models"),
        )

    def get_suite_id(self, project_id: int, name: str, parent_id: int | None) -> int | None:
        if self._suite_model is None:  # pragma: no cover - requires TestY
            return None
        existing = (
            self._suite_model.objects.filter(
                project_id=project_id,
                name=name,
                parent_id=parent_id,
            )
            .order_by("id")
            .first()
        )
        return existing.id if existing else None

    def create_suite(
        self,
        project_id: int,
        name: str,
        parent_id: int | None,
        attributes: Mapping[str, Any] | None,
    ) -> int:
        payload = {
            "project_id": project_id,
            "name": name,
            "parent_id": parent_id,
            "description": "",
            "attributes": dict(attributes or {}),
        }
        suite = self._suite_service.suite_create(**payload)
        suite_id = getattr(suite, "id", None)
        if suite_id is None:  # pragma: no cover - depends on TestY runtime
            raise TestyAdapterError("TestSuiteService.suite_create did not return an id")
        return int(suite_id)

    def find_case_id_by_zephyr_key(self, project_id: int, zephyr_key: str) -> int | None:
        if self._case_model is None:  # pragma: no cover - requires TestY
            return None
        existing = (
            self._case_model.objects.filter(
                project_id=project_id,
                attributes__zephyr__key=zephyr_key,
            )
            .order_by("id")
            .first()
        )
        return existing.id if existing else None

    def create_case_with_steps(
        self,
        project_id: int,
        suite_id: int,
        payload: Mapping[str, Any],
    ) -> int:
        data = dict(payload)
        data.update({"project_id": project_id, "suite_id": suite_id})
        case = self._case_service.case_with_steps_create(**data)
        case_id = getattr(case, "id", None)
        if case_id is None:  # pragma: no cover - depends on TestY runtime
            raise TestyAdapterError("TestCaseService.case_with_steps_create did not return an id")
        return int(case_id)

    def update_case_with_steps(
        self,
        project_id: int,
        case_id: int,
        suite_id: int,
        payload: Mapping[str, Any],
    ) -> int:
        data = dict(payload)
        data.update({"project_id": project_id, "suite_id": suite_id, "case_id": case_id})
        case = self._case_service.case_with_steps_update(**data)
        updated_id = getattr(case, "id", None)
        if updated_id is None:  # pragma: no cover - depends on TestY runtime
            raise TestyAdapterError("TestCaseService.case_with_steps_update did not return an id")
        return int(updated_id)

    def set_labels(self, project_id: int, case_id: int, labels: Sequence[str]) -> int:
        if not labels:
            return 0
        if self._case_model is None:  # pragma: no cover - requires TestY
            raise TestyAdapterError("TestCase model is not available for label assignment")
        case_obj = self._case_model.objects.get(id=case_id)
        try:
            self._label_service.set(case_obj, labels, project_id=project_id)
        except TypeError:  # pragma: no cover - depends on TestY runtime
            self._label_service.set(case_obj, labels)
        return len(labels)

    def attach_file(self, project_id: int, case_id: int, filename: str, content: bytes) -> None:
        if self._case_model is None:  # pragma: no cover - requires TestY
            raise TestyAdapterError("TestCase model is not available for attachments")
        case_obj = self._case_model.objects.get(id=case_id)
        try:
            from django.core.files.base import ContentFile  # pragma: no cover - depends on TestY runtime
        except Exception:  # pragma: no cover - depends on TestY runtime
            ContentFile = None  # type: ignore[assignment]
        file_obj = ContentFile(content, name=filename) if ContentFile else BytesIO(content)
        try:
            self._attachment_service.attachment_set_content_object(
                case_obj,
                file_obj,
                filename=filename,
                project_id=project_id,
            )
        except TypeError:  # pragma: no cover - depends on TestY runtime
            self._attachment_service.attachment_set_content_object(case_obj, file_obj)


@dataclass(slots=True)
class InMemorySuite:
    suite_id: int
    project_id: int
    name: str
    parent_id: int | None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InMemoryCase:
    case_id: int
    project_id: int
    suite_id: int
    payload: dict[str, Any]
    labels: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)


class InMemoryTestyAdapter(BaseTestyAdapter):
    def __init__(self) -> None:
        self._next_suite_id = 1
        self._next_case_id = 1
        self.suites: dict[int, InMemorySuite] = {}
        self.cases: dict[int, InMemoryCase] = {}
        self._suite_index: dict[tuple[int, int | None, str], int] = {}
        self._case_index: dict[tuple[int, str], int] = {}

    def get_suite_id(self, project_id: int, name: str, parent_id: int | None) -> int | None:
        return self._suite_index.get((project_id, parent_id, name))

    def create_suite(
        self,
        project_id: int,
        name: str,
        parent_id: int | None,
        attributes: Mapping[str, Any] | None,
    ) -> int:
        suite_id = self._next_suite_id
        self._next_suite_id += 1
        suite = InMemorySuite(
            suite_id=suite_id,
            project_id=project_id,
            name=name,
            parent_id=parent_id,
            attributes=dict(attributes or {}),
        )
        self.suites[suite_id] = suite
        self._suite_index[(project_id, parent_id, name)] = suite_id
        return suite_id

    def find_case_id_by_zephyr_key(self, project_id: int, zephyr_key: str) -> int | None:
        key = zephyr_key.strip()
        if not key:
            return None
        return self._case_index.get((project_id, key))

    def create_case_with_steps(
        self,
        project_id: int,
        suite_id: int,
        payload: Mapping[str, Any],
    ) -> int:
        case_id = self._next_case_id
        self._next_case_id += 1
        payload_dict = dict(payload)
        case = InMemoryCase(
            case_id=case_id,
            project_id=project_id,
            suite_id=suite_id,
            payload=payload_dict,
        )
        self.cases[case_id] = case
        zephyr_key = _extract_zephyr_key(payload_dict)
        if zephyr_key:
            self._case_index[(project_id, zephyr_key)] = case_id
        return case_id

    def update_case_with_steps(
        self,
        project_id: int,
        case_id: int,
        suite_id: int,
        payload: Mapping[str, Any],
    ) -> int:
        if case_id not in self.cases:
            raise KeyError(f"Unknown case id {case_id}")
        payload_dict = dict(payload)
        case = self.cases[case_id]
        case.project_id = project_id
        case.suite_id = suite_id
        case.payload = payload_dict
        zephyr_key = _extract_zephyr_key(payload_dict)
        if zephyr_key:
            self._case_index[(project_id, zephyr_key)] = case_id
        return case_id

    def set_labels(self, project_id: int, case_id: int, labels: Sequence[str]) -> int:
        if case_id not in self.cases:
            raise KeyError(f"Unknown case id {case_id}")
        case = self.cases[case_id]
        case.labels = list(labels)
        return len(case.labels)

    def attach_file(self, project_id: int, case_id: int, filename: str, content: bytes) -> None:
        if case_id not in self.cases:
            raise KeyError(f"Unknown case id {case_id}")
        case = self.cases[case_id]
        case.attachments.append(filename)


def _extract_zephyr_key(payload: Mapping[str, Any]) -> str | None:
    try:
        key = payload.get("attributes", {}).get("zephyr", {}).get("key")
    except Exception:
        return None
    if not key:
        return None
    return str(key).strip() or None
