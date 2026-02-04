from zephyr_xml_importer.api.views import handle_suites_request


def test_handle_suites_request_missing_project_id():
    response = handle_suites_request({})
    assert response["status"] == "failed"
    assert "project_id" in response["errors"]


def test_handle_suites_request_invalid_project_id():
    response = handle_suites_request({"project_id": "nope"})
    assert response["status"] == "failed"
    assert "project_id" in response["errors"]
