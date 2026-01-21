from __future__ import annotations

try:
    from django.urls import path

    from .views import ImportView
except Exception:  # pragma: no cover - Django optional for unit tests
    path = None
    ImportView = None

if path and ImportView:
    urlpatterns = [
        path("import/", ImportView.as_view(), name="import"),
    ]
else:  # pragma: no cover
    urlpatterns = []
