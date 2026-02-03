from __future__ import annotations

try:
    from django.urls import path

    from .views import ExportView, HealthView, ImportView
except Exception:  # pragma: no cover - Django optional for unit tests
    path = None
    ImportView = None
    ExportView = None

if path and ImportView and ExportView:
    urlpatterns = [
        path("import/", ImportView.as_view(), name="import"),
        path("export/", ExportView.as_view(), name="export"),
        path("health/", HealthView.as_view(), name="health"),
    ]
else:  # pragma: no cover
    urlpatterns = []
