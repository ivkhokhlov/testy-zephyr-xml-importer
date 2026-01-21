import csv
from io import StringIO

from zephyr_xml_importer.services.importer import import_into_testy
from zephyr_xml_importer.services.testy_adapter import InMemoryTestyAdapter


def _parse_report(csv_text: str) -> list[list[str]]:
    return list(csv.reader(StringIO(csv_text)))


def test_import_skips_existing_cases_by_zephyr_key():
    xml = """<project>
  <folders>
    <folder fullPath="ui" index="1" />
  </folders>
  <testCases>
    <testCase id="1" key="EX-1">
      <name>Case one</name>
      <folder>ui</folder>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description>Do</description>
          </step>
        </steps>
      </testScript>
    </testCase>
    <testCase id="2" key="EX-2">
      <name>Case two</name>
      <folder>ui</folder>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description>Done</description>
          </step>
        </steps>
      </testScript>
    </testCase>
  </testCases>
</project>"""
    adapter = InMemoryTestyAdapter()
    existing_suite_id = adapter.create_suite(1, "Existing", None, {})
    existing_case_id = adapter.create_case_with_steps(
        1,
        existing_suite_id,
        {"name": "Seed", "attributes": {"zephyr": {"key": "EX-1"}}},
    )

    result = import_into_testy(xml.encode("utf-8"), project_id=1, adapter=adapter)

    assert result.summary.cases == 2
    assert result.summary.created == 1
    assert result.summary.reused == 1
    assert result.summary.updated == 0
    assert result.summary.skipped == 1
    assert result.summary.failed == 0
    assert len(adapter.cases) == 2

    rows = _parse_report(result.report_csv)
    header = rows[0]
    key_index = header.index("zephyr_key")
    action_index = header.index("action")
    case_id_index = header.index("testy_case_id")
    rows_by_key = {row[key_index]: row for row in rows[1:]}

    assert rows_by_key["EX-1"][action_index] == "skipped"
    assert rows_by_key["EX-1"][case_id_index] == str(existing_case_id)
    assert rows_by_key["EX-2"][action_index] == "created"


def test_import_strips_labels_from_payload_but_sets_labels():
    xml = """<project>
  <testCases>
    <testCase id="1" key="EX-10">
      <name>Case label</name>
      <labels>
        <label><![CDATA[  Smoke  ]]></label>
      </labels>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description>Do</description>
          </step>
        </steps>
      </testScript>
    </testCase>
  </testCases>
</project>"""
    adapter = InMemoryTestyAdapter()

    result = import_into_testy(xml.encode("utf-8"), project_id=1, adapter=adapter)

    assert result.summary.cases == 1
    assert result.summary.created == 1
    assert result.summary.reused == 0
    assert result.summary.updated == 0
    assert result.summary.skipped == 0
    assert result.summary.failed == 0
    case = next(iter(adapter.cases.values()))
    assert "labels" not in case.payload
    assert case.labels == ["Smoke"]


def test_import_precreates_folder_tree_from_folders_list():
    xml = """<project>
  <folders>
    <folder fullPath="ui" index="1" />
    <folder fullPath="ui/forms" index="2" />
    <folder fullPath="api/auth" index="3" />
  </folders>
  <testCases></testCases>
</project>"""
    adapter = InMemoryTestyAdapter()

    result = import_into_testy(xml.encode("utf-8"), project_id=1, adapter=adapter)

    assert result.summary.cases == 0
    assert result.summary.folders == 3
    assert len(adapter.suites) == 4

    def find_suite(name: str, parent_name: str | None = None):
        for suite in adapter.suites.values():
            if suite.name != name:
                continue
            if parent_name is None and suite.parent_id is None:
                return suite
            if parent_name is not None:
                parent = adapter.suites.get(suite.parent_id)
                if parent and parent.name == parent_name:
                    return suite
        return None

    ui = find_suite("ui")
    assert ui is not None
    forms = find_suite("forms", parent_name="ui")
    assert forms is not None
    api = find_suite("api")
    assert api is not None
    auth = find_suite("auth", parent_name="api")
    assert auth is not None

    assert ui.attributes["zephyr"]["folderFullPath"] == "ui"
    assert forms.attributes["zephyr"]["folderFullPath"] == "ui/forms"
    assert api.attributes["zephyr"]["folderFullPath"] == "api"
    assert auth.attributes["zephyr"]["folderFullPath"] == "api/auth"
