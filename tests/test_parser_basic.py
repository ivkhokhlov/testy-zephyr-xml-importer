from pathlib import Path

from zephyr_xml_importer.services.parser import parse_folders, iter_test_cases


FIXTURE = Path(__file__).parent / "fixtures" / "sample.xml"


def test_parse_folders_basic():
    folders = parse_folders(FIXTURE)
    assert "ui/Blacklists" in folders
    assert folders["ui/Blacklists"].index == 123


def test_iter_test_cases_core_fields():
    tcs = list(iter_test_cases(FIXTURE))
    assert len(tcs) == 1
    tc = tcs[0]
    assert tc.key == "ES-T560"
    assert tc.zephyr_id == "401225"
    assert tc.name.strip() == "Login works"
    assert tc.folder.strip() == "ui/Blacklists"
    assert tc.status == "Approved"
