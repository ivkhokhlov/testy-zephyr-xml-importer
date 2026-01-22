from __future__ import annotations

from zephyr_xml_importer.services import testy_adapter


def test_load_project_choices_missing_model(monkeypatch):
    monkeypatch.setattr(testy_adapter, "_resolve_model", lambda *args, **kwargs: None)

    projects, error = testy_adapter.load_project_choices()

    assert projects is None
    assert error


def test_load_project_choices_with_fake_model(monkeypatch):
    class FakeProject:
        def __init__(self, project_id: int, name: str) -> None:
            self.id = project_id
            self.name = name

    class FakeQuerySet(list):
        def order_by(self, *args, **kwargs):
            return self

    class FakeManager:
        def __init__(self, items):
            self._items = FakeQuerySet(items)

        def all(self):
            return self._items

    class FakeModel:
        objects = FakeManager(
            [
                FakeProject(2, "Beta"),
                FakeProject(1, "Alpha"),
            ]
        )

    monkeypatch.setattr(testy_adapter, "_resolve_model", lambda *args, **kwargs: FakeModel)

    projects, error = testy_adapter.load_project_choices()

    assert error is None
    assert projects is not None
    assert [project.name for project in projects] == ["Alpha", "Beta"]
