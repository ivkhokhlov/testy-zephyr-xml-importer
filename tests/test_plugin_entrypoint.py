from pathlib import Path
import tomllib


def test_entrypoint_metadata_present():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    entry_points = data.get("project", {}).get("entry-points", {})
    testy_group = entry_points.get("testy")

    assert testy_group is not None, "Missing [project.entry-points.\"testy\"] in pyproject.toml"
    assert (
        testy_group.get("zephyr-xml-importer") == "zephyr_xml_importer.hooks"
    ), "Entry point should reference zephyr_xml_importer.hooks"
