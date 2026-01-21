from pathlib import Path

from zephyr_xml_importer.services.parser import parse_folders, iter_test_cases


FIXTURE = Path(__file__).parent / "fixtures" / "sample.xml"


def test_parse_folders_basic():
    folders = parse_folders(FIXTURE)
    assert len(folders) == 2
    assert "ui/Blacklists" in folders
    assert folders["ui/Blacklists"].index == 123
    assert folders["api/data_profiles"].index == 200


def test_iter_test_cases_core_fields():
    tcs = list(iter_test_cases(FIXTURE))
    assert len(tcs) == 1
    tc = tcs[0]
    assert tc.key == "ES-T560"
    assert tc.zephyr_id == "401225"
    assert tc.name.strip() == "Login works"
    assert tc.folder.strip() == "ui/Blacklists"
    assert tc.objective == "<p>Goal<br/>Line2</p>"
    assert tc.precondition == "<ul><li>User exists</li></ul>"
    assert tc.status == "Approved"


def test_iter_test_cases_extras():
    tc = list(iter_test_cases(FIXTURE))[0]
    assert tc.param_type == "TEST_DATA"
    assert tc.parameters == ["url", "role"]
    assert tc.labels == ["b2b", "smoke"]
    assert len(tc.issues) == 1
    assert tc.issues[0].key == "ES-7574"
    assert tc.issues[0].summary == "Something"
    assert tc.attachments == ["file1.csv", "file2.xlsx"]
    assert tc.test_script_type == "steps"
    assert tc.test_script_text is None
    assert len(tc.steps) == 2
    assert tc.steps[0].index == 0
    assert tc.steps[0].description == "Open login page"
    assert tc.steps[0].expected_result == "Page opens"
    assert tc.steps[0].test_data is None
    assert tc.steps[1].index == 1
    assert tc.steps[1].description is None
    assert tc.steps[1].expected_result is None
    assert tc.steps[1].test_data == "user=admin"
    assert tc.test_data_wrapper is not None
    wrapper = tc.test_data_wrapper
    assert len(wrapper.rows) == 2
    assert wrapper.rows[0].cells[0].name == "parameter"
    assert wrapper.rows[0].cells[0].data_type == "free_text_input"
    assert wrapper.rows[0].cells[0].value == "alpha"
    assert wrapper.rows[0].cells[1].value == "beta"
    assert wrapper.rows[1].cells[0].value == "gamma"
