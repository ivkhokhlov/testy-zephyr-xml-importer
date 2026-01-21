from pathlib import Path

from zephyr_xml_importer.services.attachments import build_zip_index, match_attachments


FIXTURE = Path(__file__).parent / "fixtures" / "attachments.zip"


def test_zip_index_detects_duplicate_basenames():
    index = build_zip_index(FIXTURE)
    assert "duplicate.txt" in index.duplicate_basenames
    assert index.by_basename["duplicate.txt"] == [
        "dup/duplicate.txt",
        "other/duplicate.txt",
    ]


def test_match_attachments_reports_missing_and_duplicates():
    index = build_zip_index(FIXTURE)
    result = match_attachments(
        ["file1.csv", "file2.xlsx", "missing.doc", "duplicate.txt"],
        index,
    )
    assert result.attachments_in_xml == 4
    assert result.attachments_attached == 3
    assert result.attachments_missing == 1
    assert result.matched == [
        "file1.csv",
        "nested/file2.xlsx",
        "dup/duplicate.txt",
    ]
    assert result.missing == ["missing.doc"]
    assert any("missing.doc" in warning for warning in result.warnings)
    assert any("duplicate.txt" in warning for warning in result.warnings)


def test_match_attachments_without_zip_marks_missing():
    result = match_attachments(["file1.csv"], None)
    assert result.attachments_in_xml == 1
    assert result.attachments_attached == 0
    assert result.attachments_missing == 1
    assert result.missing == ["file1.csv"]
