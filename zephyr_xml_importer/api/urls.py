from __future__ import annotations

try:
    from django.urls import path

    from .views import HealthView, ImportView
except Exception:  # pragma: no cover - Django optional for unit tests
    path = None
    ImportView = None

if path and ImportView:
    urlpatterns = [
        path("import/", ImportView.as_view(), name="import"),
        path("health/", HealthView.as_view(), name="health"),
    ]
else:  # pragma: no cover
    urlpatterns = []
