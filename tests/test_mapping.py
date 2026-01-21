from pathlib import Path

from zephyr_xml_importer.services.parser import iter_test_cases
from zephyr_xml_importer.services.mapping import build_testy_payload_from_zephyr


FIXTURE = Path(__file__).parent / "fixtures" / "sample.xml"


def test_mapping_scenario_non_empty_even_without_steps_parsed_yet():
    tc = next(iter_test_cases(FIXTURE))
    payload = build_testy_payload_from_zephyr(tc, prefix_with_zephyr_key=True)
    assert payload["name"].startswith("[ES-T560]")
    assert isinstance(payload["scenario"], str)
    assert payload["scenario"].strip() != ""
