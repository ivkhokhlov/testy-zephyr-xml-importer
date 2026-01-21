from zephyr_xml_importer.services.sanitize import sanitize_html


def test_sanitize_br_and_paragraph():
    assert sanitize_html("<p>Hello<br/>World</p>") == "Hello\nWorld"


def test_sanitize_list_items():
    assert sanitize_html("<ul><li>A</li><li>B</li></ul>") == "- A\n- B"


def test_sanitize_table_cells():
    assert sanitize_html("<table><tr><td>A</td><td>B</td></tr></table>") == "A\tB"


def test_sanitize_unescape_entities():
    assert sanitize_html("A&nbsp;B &amp; C") == "A B & C"
