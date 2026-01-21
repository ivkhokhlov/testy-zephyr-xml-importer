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
