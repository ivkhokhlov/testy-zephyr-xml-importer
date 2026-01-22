from __future__ import annotations

from typing import Any, Mapping

from .permissions import IsAdminForZephyrImport
from .serializers import ImportRequestData, ImportValidationError, validate_import_request
from .. import __version__
from ..services.importer import DryRunImportResult, dry_run_import, import_into_testy
from ..services.testy_adapter import TestyAdapterError, load_project_choices

try:
    from django.shortcuts import render
except Exception:  # pragma: no cover - Django optional for unit tests
    render = None

try:
    from rest_framework.response import Response
    from rest_framework.views import APIView
    from rest_framework import status as drf_status
    from rest_framework.exceptions import ValidationError as DrfValidationError
except Exception:  # pragma: no cover - DRF optional for unit tests
    Response = None
    APIView = object
    drf_status = None
    DrfValidationError = None

try:
    from .serializers import ImportRequestSerializer
except Exception:  # pragma: no cover
    ImportRequestSerializer = None


def _normalize_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return value[0]
    return value


def _merge_mapping(target: dict[str, Any], source: Any) -> None:
    if source is None:
        return
    if hasattr(source, "lists"):
        try:
            for key, values in source.lists():
                target[key] = _normalize_value(values)
            return
        except Exception:
            pass
    if hasattr(source, "items"):
        try:
            for key, value in source.items():
                target[key] = _normalize_value(value)
            return
        except Exception:
            pass
    try:
        for key, value in dict(source).items():
            target[key] = _normalize_value(value)
    except Exception:
        return


def _extract_payload(request: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    data = getattr(request, "data", None)
    if data is None:
        data = getattr(request, "POST", None)
    _merge_mapping(payload, data)
    files = getattr(request, "FILES", None)
    _merge_mapping(payload, files)
    return payload


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return False


def _error_response(errors: Any, payload: Mapping[str, Any]) -> Any:
    response = {
        "status": "failed",
        "errors": errors,
        "dry_run": _coerce_bool(payload.get("dry_run")),
    }
    if Response is None:
        return response
    return Response(response, status=drf_status.HTTP_400_BAD_REQUEST)


def _build_response_from_result(result: DryRunImportResult, *, dry_run: bool) -> dict[str, Any]:
    return {
        "status": "success",
        "dry_run": dry_run,
        "summary": {
            "folders": result.summary.folders,
            "cases": result.summary.cases,
            "steps": result.summary.steps,
            "labels": result.summary.labels,
            "attachments": result.summary.attachments,
            "created": result.summary.created,
            "reused": result.summary.reused,
            "updated": result.summary.updated,
            "skipped": result.summary.skipped,
            "failed": result.summary.failed,
        },
        "report_csv": result.report_csv,
        "warnings": result.warnings,
    }


def build_import_response(request_data: ImportRequestData, *, user: Any | None = None) -> dict[str, Any]:
    try:
        if request_data.dry_run:
            result = dry_run_import(
                request_data.xml_file,
                attachments_zip=request_data.attachments_zip,
                prefix_with_zephyr_key=request_data.prefix_with_zephyr_key,
                meta_labels=request_data.meta_labels,
                append_jira_issues_to_description=request_data.append_jira_issues_to_description,
                embed_testdata_to_description=request_data.embed_testdata_to_description,
            )
        else:
            result = import_into_testy(
                request_data.xml_file,
                project_id=request_data.project_id,
                attachments_zip=request_data.attachments_zip,
                prefix_with_zephyr_key=request_data.prefix_with_zephyr_key,
                meta_labels=request_data.meta_labels,
                append_jira_issues_to_description=request_data.append_jira_issues_to_description,
                embed_testdata_to_description=request_data.embed_testdata_to_description,
                on_duplicate=request_data.on_duplicate,
                user=user,
            )
        return _build_response_from_result(result, dry_run=request_data.dry_run)
    except TestyAdapterError as exc:
        return {
            "status": "failed",
            "dry_run": request_data.dry_run,
            "errors": [str(exc)],
        }


def handle_import_request(data: Mapping[str, Any]) -> dict[str, Any]:
    request_data = validate_import_request(data)
    return build_import_response(request_data)


def build_health_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "plugin": "zephyr-xml-importer",
        "version": __version__,
    }


class ImportView(APIView):  # type: ignore[misc]
    permission_classes = [IsAdminForZephyrImport]

    def get(self, request, *args, **kwargs):  # type: ignore[override]
        projects: list[Any] | None = None
        project_list_error: str | None = None
        try:
            projects, project_list_error = load_project_choices()
        except Exception as exc:  # pragma: no cover - depends on TestY runtime
            projects = None
            project_list_error = str(exc)

        context = {
            "projects": projects,
            "project_list_error": project_list_error,
        }
        if render is None:
            return {
                "status": "failed",
                "errors": {"detail": "HTML UI is unavailable in this environment"},
            }
        return render(request, "zephyr_xml_importer/import.html", context)

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        payload = _extract_payload(request)
        try:
            if ImportRequestSerializer is not None:
                serializer = ImportRequestSerializer(data=payload)
                serializer.is_valid(raise_exception=True)
                request_data = validate_import_request(serializer.validated_data)
            else:
                request_data = validate_import_request(payload)
        except ImportValidationError as exc:
            return _error_response(exc.errors, payload)
        except Exception as exc:
            if DrfValidationError is not None and isinstance(exc, DrfValidationError):
                return _error_response(exc.detail, payload)
            return _error_response({"detail": str(exc)}, payload)

        response_data = build_import_response(request_data, user=getattr(request, "user", None))
        if Response is None:
            return response_data
        status_code = (
            drf_status.HTTP_200_OK
            if response_data.get("status") == "success"
            else drf_status.HTTP_400_BAD_REQUEST
        )
        return Response(response_data, status=status_code)


class HealthView(APIView):  # type: ignore[misc]
    permission_classes = [IsAdminForZephyrImport]

    def get(self, request, *args, **kwargs):  # type: ignore[override]
        payload = build_health_payload()
        if Response is None:
            return payload
        return Response(payload, status=drf_status.HTTP_200_OK)
