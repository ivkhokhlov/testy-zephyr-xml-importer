"""Plugin entrypoint for TestY.

This module is intentionally light because unit tests in this repo do not require TestY installed.
When running inside TestY, `testy.plugins.hooks` will be importable and the config will be used by TestY.

Implementation is deferred to later tasks in `.agent/queue.md`.
"""

from __future__ import annotations

try:
    from testy.plugins.hooks import TestyPluginConfig, hookimpl  # type: ignore
except Exception:  # pragma: no cover
    TestyPluginConfig = object  # type: ignore

    def hookimpl(fn):  # type: ignore
        return fn


class ZephyrXmlImporterConfig(TestyPluginConfig):  # type: ignore
    package_name = "zephyr_xml_importer"
    verbose_name = "Zephyr Scale XML importer"
    description = "Import Zephyr Scale XML export into TestY"
    version = "0.1.0"
    plugin_base_url = "zephyr-xml-importer"
    urls_module = "zephyr_xml_importer.api.urls"
    index_reverse_name = "import"
    min_version = "2.1.2"


@hookimpl
def config():
    return ZephyrXmlImporterConfig
