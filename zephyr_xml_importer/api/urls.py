from __future__ import annotations

try:
    from django.urls import path

    from .views import ExportView, HealthView, ImportView, IndexView, SuitesView
except Exception:  # pragma: no cover - Django optional for unit tests
    path = None
    ImportView = None
    ExportView = None
    IndexView = None
    SuitesView = None

if path and ImportView and ExportView and IndexView and SuitesView:
    urlpatterns = [
        path("", IndexView.as_view(), name="index"),
        path("import/", ImportView.as_view(), name="import"),
        path("export/", ExportView.as_view(), name="export"),
        path("suites/", SuitesView.as_view(), name="suites"),
        path("health/", HealthView.as_view(), name="health"),
    ]
else:  # pragma: no cover
    urlpatterns = []
