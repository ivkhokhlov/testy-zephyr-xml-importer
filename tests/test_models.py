from zephyr_xml_importer.services import (
    ZephyrFolder,
    ZephyrIssue,
    ZephyrParseResult,
    ZephyrStep,
    ZephyrTestCase,
    ZephyrTestDataCell,
    ZephyrTestDataRow,
    ZephyrTestDataTable,
)


def test_models_basic_instantiation():
    folder = ZephyrFolder(full_path="ui/Blacklists", index=123)
    issue = ZephyrIssue(key="ES-1", summary="Something")
    step = ZephyrStep(index=0, description="Open page")
    cell = ZephyrTestDataCell(index=0, name="login", data_type="free_text_input", value="admin")
    row = ZephyrTestDataRow(cells=[cell])
    table = ZephyrTestDataTable(rows=[row])
    tc = ZephyrTestCase(
        zephyr_id="401225",
        key="ES-T560",
        name="Login works",
        issues=[issue],
        steps=[step],
        test_data_wrapper=table,
    )

    result = ZephyrParseResult(
        folders={folder.full_path: folder},
        test_cases=[tc],
    )

    assert result.folders["ui/Blacklists"].index == 123
    assert result.test_cases[0].issues[0].key == "ES-1"
    wrapper = result.test_cases[0].test_data_wrapper
    assert wrapper.rows[0].cells[0].name == "login"
