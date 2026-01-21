from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from zephyr_xml_importer.api.permissions import IsAdminForZephyrImport, _admin_role_name


@dataclass
class DummyRole:
    name: Optional[str] = None
    role_name: Optional[str] = None


@dataclass
class DummyMembership:
    role: object | None = None
    role_name: Optional[str] = None


@dataclass
class DummyUser:
    is_superuser: bool = False
    membership: DummyMembership | None = None
    memberships: Iterable[DummyMembership] | None = None
    role_name: Optional[str] = None


class DummyRequest:
    def __init__(self, user: DummyUser | None) -> None:
        self.user = user


def test_permission_allows_superuser():
    permission = IsAdminForZephyrImport()
    user = DummyUser(is_superuser=True)
    assert permission.has_permission(DummyRequest(user), None) is True


def test_permission_allows_membership_role_name():
    permission = IsAdminForZephyrImport()
    user = DummyUser(membership=DummyMembership(role_name=_admin_role_name()))
    assert permission.has_permission(DummyRequest(user), None) is True


def test_permission_allows_memberships_role_object():
    permission = IsAdminForZephyrImport()
    admin_role = _admin_role_name()
    memberships = [DummyMembership(role=DummyRole(name=admin_role))]
    user = DummyUser(memberships=memberships)
    assert permission.has_permission(DummyRequest(user), None) is True


def test_permission_denies_non_membership_role_name():
    permission = IsAdminForZephyrImport()
    user = DummyUser(role_name=_admin_role_name())
    assert permission.has_permission(DummyRequest(user), None) is False
