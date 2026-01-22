from __future__ import annotations

from typing import Any, Mapping

from .permissions import IsAdminForZephyrImport
from .serializers import ImportRequestData, ImportValidationError, validate_import_request
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
except Exception:  # pragma: no cover - DRF optional for unit tests
    Response = None
    APIView = object
    drf_status = None

try:
    from .serializers import ImportRequestSerializer
except Exception:  # pragma: no cover
    ImportRequestSerializer = None


def _extract_payload(request: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    data = getattr(request, "data", None)
    if data is not None:
        try:
            payload.update(data)
        except Exception:
            payload.update(dict(data))
    files = getattr(request, "FILES", None)
    if files is not None:
        try:
            payload.update(files)
        except Exception:
            pass
    return payload


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


def build_import_response(request_data: ImportRequestData) -> dict[str, Any]:
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
            response = {
                "status": "failed",
                "errors": exc.errors,
                "dry_run": bool(payload.get("dry_run")),
            }
            if Response is None:
                return response
            return Response(response, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            response = {
                "status": "failed",
                "errors": {"detail": str(exc)},
                "dry_run": bool(payload.get("dry_run")),
            }
            if Response is None:
                return response
            return Response(response, status=drf_status.HTTP_400_BAD_REQUEST)

        response_data = build_import_response(request_data)
        if Response is None:
            return response_data
        status_code = (
            drf_status.HTTP_200_OK
            if response_data.get("status") == "success"
            else drf_status.HTTP_400_BAD_REQUEST
        )
        return Response(response_data, status=status_code)
