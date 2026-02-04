from __future__ import annotations

import pytest

from zephyr_xml_importer.services import testy_adapter
from zephyr_xml_importer.services.testy_exporter import SuiteInfo, _select_suite_ids


class DummySuiteModel:
    class objects:
        @staticmethod
        def get(*args, **kwargs):
            raise RuntimeError("get should not be called for explicit suite_ids")


def test_select_suite_ids_validates_and_dedupes():
    suite_index = {
        1: SuiteInfo(suite_id=1, name="Root", parent_id=None, description=None),
        2: SuiteInfo(suite_id=2, name="Child", parent_id=1, description=None),
        3: SuiteInfo(suite_id=3, name="Other", parent_id=None, description=None),
    }

    selected = _select_suite_ids(
        suite_model=DummySuiteModel,
        project_id=1,
        suite_id=None,
        suite_ids=[2, 1, 2],
        include_children=True,
        suite_index=suite_index,
    )

    assert selected == [2, 1]


def test_select_suite_ids_rejects_missing_suite():
    suite_index = {
        1: SuiteInfo(suite_id=1, name="Root", parent_id=None, description=None),
    }

    with pytest.raises(testy_adapter.TestyAdapterError):
        _select_suite_ids(
            suite_model=DummySuiteModel,
            project_id=1,
            suite_id=None,
            suite_ids=[1, 99],
            include_children=True,
            suite_index=suite_index,
        )
