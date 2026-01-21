import csv
from io import StringIO

from zephyr_xml_importer.services.importer import dry_run_import


def _parse_report(csv_text: str) -> list[list[str]]:
    return list(csv.reader(StringIO(csv_text)))


def test_dry_run_emits_validation_warnings():
    long_name = "A" * 260
    xml = f"""<project>
  <testCases>
    <testCase id="1" key="DUP-1">
      <name>Case one</name>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description><![CDATA[]]></description>
            <expectedResult><![CDATA[]]></expectedResult>
          </step>
        </steps>
      </testScript>
    </testCase>
    <testCase id="2" key="DUP-1">
      <name>Case two</name>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description>Do it</description>
          </step>
        </steps>
      </testScript>
    </testCase>
    <testCase id="3" key="LONG-1">
      <name><![CDATA[{long_name}]]></name>
      <testScript type="text">Plain text</testScript>
    </testCase>
  </testCases>
</project>"""
    result = dry_run_import(xml.encode("utf-8"))

    assert "Duplicate Zephyr key in XML: DUP-1" in result.warnings
    assert any(
        warning.startswith("Test case name too long") for warning in result.warnings
    )
    assert "Empty step 1 in Zephyr case DUP-1" in result.warnings

    rows = _parse_report(result.report_csv)
    header = rows[0]
    warnings_index = header.index("warnings")
    id_index = header.index("zephyr_id")
    rows_by_id = {row[id_index]: row for row in rows[1:]}

    case_one_warnings = rows_by_id["1"][warnings_index]
    assert "Duplicate Zephyr key in XML: DUP-1" in case_one_warnings
    assert "Empty step 1 in Zephyr case DUP-1" in case_one_warnings

    case_two_warnings = rows_by_id["2"][warnings_index]
    assert "Duplicate Zephyr key in XML: DUP-1" in case_two_warnings
    assert "Empty step 1 in Zephyr case DUP-1" not in case_two_warnings

    case_three_warnings = rows_by_id["3"][warnings_index]
    assert "Test case name too long" in case_three_warnings
