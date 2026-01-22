from zephyr_xml_importer.api.views import build_health_payload


def test_build_health_payload():
    payload = build_health_payload()
    assert payload["status"] == "ok"
    assert payload["plugin"] == "zephyr-xml-importer"
    assert payload["version"]
