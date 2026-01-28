import csv
from io import BytesIO, StringIO

from zephyr_xml_importer.services.importer import MAX_WARNING_PREVIEW, dry_run_import


def _parse_report(csv_text: str) -> list[list[str]]:
    return list(csv.reader(StringIO(csv_text)))


def test_dry_run_emits_validation_warnings(tmp_path):
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
    xml_path = tmp_path / "cases.xml"
    xml_path.write_text(xml, encoding="utf-8")
    result = dry_run_import(xml_path)

    assert "Duplicate Zephyr key in XML: DUP-1" in result.warnings
    assert any(warning.startswith("Test case name too long") for warning in result.warnings)
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


def test_dry_run_warns_on_missing_folder_and_empty_expected(tmp_path):
    xml = """<project>
  <folders>
    <folder fullPath="Known/Path" index="1" />
  </folders>
  <testCases>
    <testCase id="1" key="NO-FOLDER">
      <name>Case no folder</name>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description>Do thing</description>
            <expectedResult>Ok</expectedResult>
          </step>
        </steps>
      </testScript>
    </testCase>
    <testCase id="2" key="BAD-FOLDER">
      <name>Case bad folder</name>
      <folder>Missing/Path</folder>
      <testScript type="steps">
        <steps>
          <step index="0">
            <description>Do thing</description>
            <expectedResult><![CDATA[]]></expectedResult>
          </step>
        </steps>
      </testScript>
    </testCase>
  </testCases>
</project>"""
    xml_path = tmp_path / "missing-folder.xml"
    xml_path.write_text(xml, encoding="utf-8")
    result = dry_run_import(xml_path)

    assert "Missing folder in Zephyr case NO-FOLDER" in result.warnings
    assert "Folder not found in Zephyr export: Missing/Path for case BAD-FOLDER" in result.warnings
    assert "Empty expected result for step 1 in Zephyr case BAD-FOLDER" in result.warnings

    rows = _parse_report(result.report_csv)
    header = rows[0]
    warnings_index = header.index("warnings")
    id_index = header.index("zephyr_id")
    rows_by_id = {row[id_index]: row for row in rows[1:]}

    assert "Missing folder in Zephyr case NO-FOLDER" in rows_by_id["1"][warnings_index]
    assert (
        "Folder not found in Zephyr export: Missing/Path for case BAD-FOLDER"
        in rows_by_id["2"][warnings_index]
    )
    assert (
        "Empty expected result for step 1 in Zephyr case BAD-FOLDER"
        in rows_by_id["2"][warnings_index]
    )


def test_dry_run_caps_warning_preview_without_truncating_report(tmp_path):
    long_name = "A" * 260
    cases: list[str] = []
    total_cases = MAX_WARNING_PREVIEW + 2
    for idx in range(total_cases):
        case_id = idx + 1
        key = f"WARN-{case_id}"
        cases.append(
            f"""    <testCase id="{case_id}" key="{key}">
      <name><![CDATA[{long_name}]]></name>
      <folder>Root</folder>
      <testScript type="text">Plain text</testScript>
    </testCase>"""
        )
    xml = (
        "<project>\n"
        "  <folders>\n"
        '    <folder fullPath="Root" index="1" />\n'
        "  </folders>\n"
        "  <testCases>\n" + "\n".join(cases) + "\n  </testCases>\n"
        "</project>"
    )
    xml_path = tmp_path / "warnings-cap.xml"
    xml_path.write_text(xml, encoding="utf-8")
    result = dry_run_import(xml_path)

    assert len(result.warnings) == MAX_WARNING_PREVIEW

    rows = _parse_report(result.report_csv)
    header = rows[0]
    warnings_index = header.index("warnings")
    last_row = rows[-1]
    assert "Test case name too long" in last_row[warnings_index]
    assert f"WARN-{total_cases}" in last_row[warnings_index]


def test_dry_run_accepts_non_seekable_stream():
    class NonSeekableBytesIO:
        def __init__(self, data: bytes) -> None:
            self._bio = BytesIO(data)

        def read(self, size: int = -1):
            return self._bio.read(size)

        def seekable(self) -> bool:
            return False

    xml = """<project>
  <testCases>
    <testCase id="1" key="DUP-1">
      <name>Case one</name>
      <testScript type="text">Plain text</testScript>
    </testCase>
    <testCase id="2" key="DUP-1">
      <name>Case two</name>
      <testScript type="text">Plain text</testScript>
    </testCase>
  </testCases>
</project>"""
    result = dry_run_import(NonSeekableBytesIO(xml.encode("utf-8")))

    assert result.summary.cases == 2
    assert "Duplicate Zephyr key in XML: DUP-1" in result.warnings
