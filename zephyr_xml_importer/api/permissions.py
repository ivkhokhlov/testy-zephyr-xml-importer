from __future__ import annotations

from typing import Any, Iterable

try:
    from rest_framework.permissions import BasePermission
except Exception:  # pragma: no cover - DRF optional for unit tests

    class BasePermission:  # type: ignore[too-many-ancestors]
        pass


try:
    from django.conf import settings
except Exception:  # pragma: no cover - Django optional for unit tests
    settings = None


def _admin_role_name() -> str:
    if settings is None:
        return "Admin"
    return getattr(settings, "ADMIN_ROLE_NAME", "Admin")


def _extract_role_name(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    name = getattr(value, "name", None)
    if isinstance(name, str):
        return name
    role_name = getattr(value, "role_name", None)
    if isinstance(role_name, str):
        return role_name
    return None


def _iter_role_names(user: Any) -> Iterable[str]:
    membership = getattr(user, "membership", None)
    if membership is not None:
        member_role = _extract_role_name(getattr(membership, "role", None))
        if member_role:
            yield member_role
        member_role_name = _extract_role_name(getattr(membership, "role_name", None))
        if member_role_name:
            yield member_role_name

    memberships = getattr(user, "memberships", None)
    if memberships is not None:
        try:
            for member in memberships:
                member_role = _extract_role_name(getattr(member, "role", None))
                if member_role:
                    yield member_role
                member_role_name = _extract_role_name(getattr(member, "role_name", None))
                if member_role_name:
                    yield member_role_name
        except TypeError:
            pass


class IsAdminForZephyrImport(BasePermission):
    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        user = getattr(request, "user", None)
        if user is None:
            return False
        if getattr(user, "is_superuser", False):
            return True
        admin_role_name = _admin_role_name()
        for role_name in _iter_role_names(user):
            if role_name == admin_role_name:
                return True
        return False
