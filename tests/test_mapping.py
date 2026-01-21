from pathlib import Path

from zephyr_xml_importer.services.mapping import build_testy_payload_from_zephyr
from zephyr_xml_importer.services.models import ZephyrStep, ZephyrTestCase
from zephyr_xml_importer.services.parser import iter_test_cases


FIXTURE = Path(__file__).parent / "fixtures" / "sample.xml"


def test_mapping_scenario_non_empty_even_without_steps_parsed_yet():
    tc = next(iter_test_cases(FIXTURE))
    payload = build_testy_payload_from_zephyr(tc, prefix_with_zephyr_key=True)
    assert payload["name"].startswith("[ES-T560]")
    assert isinstance(payload["scenario"], str)
    assert payload["scenario"].strip() != ""


def test_mapping_step_scenario_uses_test_data_when_description_empty():
    tc = next(iter_test_cases(FIXTURE))
    payload = build_testy_payload_from_zephyr(tc, prefix_with_zephyr_key=True)
    step = payload["steps"][1]
    assert "user=admin" in step["scenario"]
    assert step["scenario"] != "Step 2 (empty in Zephyr)"


def test_mapping_step_placeholder_when_empty():
    tc = ZephyrTestCase(
        zephyr_id="42",
        key="ES-T999",
        name="Empty step case",
        steps=[ZephyrStep(index=0)],
        test_script_type="steps",
    )
    payload = build_testy_payload_from_zephyr(tc)
    assert payload["steps"][0]["scenario"] == "Step 1 (empty in Zephyr)"


def test_mapping_meta_labels_toggle_and_normalization():
    tc = ZephyrTestCase(
        zephyr_id="100",
        key="ES-T100",
        name="Meta labels case",
        labels=["  Foo  ", "bar   baz", "Foo"],
        status=" Approved ",
        priority=" High ",
        owner=" John   Doe ",
        steps=[ZephyrStep(index=0, description="Do it")],
        test_script_type="steps",
    )
    payload = build_testy_payload_from_zephyr(tc, meta_labels=True)
    assert "Foo" in payload["labels"]
    assert "bar baz" in payload["labels"]
    assert "zephyr:status=Approved" in payload["labels"]
    assert "zephyr:priority=High" in payload["labels"]
    assert "zephyr:owner=John Doe" in payload["labels"]

    payload_no_meta = build_testy_payload_from_zephyr(tc, meta_labels=False)
    assert "zephyr:status=Approved" not in payload_no_meta["labels"]
    assert "zephyr:priority=High" not in payload_no_meta["labels"]
    assert "zephyr:owner=John Doe" not in payload_no_meta["labels"]


def test_mapping_description_embeds_issues_attachments_and_testdata():
    tc = next(iter_test_cases(FIXTURE))
    payload = build_testy_payload_from_zephyr(
        tc,
        append_jira_issues_to_description=True,
        embed_testdata_to_description=True,
    )
    description = payload["description"]
    assert "Goal" in description
    assert "Jira: ES-7574" in description
    assert "Attachments: file1.csv, file2.xlsx" in description
    assert "Parameters: url, role" in description
    assert "Test data rows:" in description
    assert "alpha" in description


def test_mapping_description_flags_can_disable_embeds():
    tc = next(iter_test_cases(FIXTURE))
    payload = build_testy_payload_from_zephyr(
        tc,
        append_jira_issues_to_description=False,
        embed_testdata_to_description=False,
    )
    description = payload["description"]
    assert "Jira:" not in description
    assert "Attachments:" not in description
    assert "Parameters:" not in description
    assert "Test data rows:" not in description


def test_mapping_test_data_wrapper_is_json_safe():
    tc = next(iter_test_cases(FIXTURE))
    payload = build_testy_payload_from_zephyr(tc)
    wrapper = payload["attributes"]["zephyr"]["testDataWrapper"]
    assert isinstance(wrapper, dict)
    assert wrapper["rows"][0]["cells"][0]["value"] == "alpha"
