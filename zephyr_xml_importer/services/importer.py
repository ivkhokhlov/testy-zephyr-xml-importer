from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, BinaryIO, Iterator, Mapping, cast
from zipfile import ZipFile

from .attachments import AttachmentZipIndex, build_zip_index
from .mapping import build_testy_payload_from_zephyr, match_attachments_for_testcase
from .parser import iter_test_cases, parse_folders_and_duplicate_key_counts
from .report import ReportRow, build_csv_report
from .testy_adapter import BaseTestyAdapter, TestyAdapterError, TestyServiceAdapter
from .validation import build_case_warnings


NO_FOLDER_SUITE_NAME = "(No folder)"
MAX_WARNING_PREVIEW = 50


@dataclass(frozen=True, slots=True)
class ImportSummary:
    folders: int
    cases: int
    steps: int
    labels: int
    attachments: int
    created: int = 0
    reused: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass(frozen=True, slots=True)
class DryRunImportResult:
    summary: ImportSummary
    report_csv: str
    warnings: list[str] = field(default_factory=list)


def _read_source_bytes(source: str | Path | BinaryIO | bytes) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    if isinstance(source, (str, Path)):
        with open(source, "rb") as handle:
            return handle.read()
    data = source.read()
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


def _build_zip_index(source: str | Path | BinaryIO | bytes | None) -> AttachmentZipIndex | None:
    if source is None:
        return None
    if isinstance(source, (bytes, bytearray)):
        return build_zip_index(bytes(source))
    if isinstance(source, (str, Path)):
        return build_zip_index(source)
    data = source.read()
    if isinstance(data, str):
        data = data.encode("utf-8")
    return build_zip_index(data)


def _copy_stream(source: BinaryIO, destination: BinaryIO, chunk_size: int = 1024 * 1024) -> None:
    while True:
        chunk = source.read(chunk_size)
        if not chunk:
            break
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        destination.write(chunk)


@contextmanager
def _open_seekable_xml_source(
    source: str | Path | BinaryIO | bytes,
) -> Iterator[BinaryIO]:
    if isinstance(source, (str, Path)):
        with open(source, "rb") as handle:
            yield handle
        return
    if isinstance(source, (bytes, bytearray)):
        buffer = BytesIO(bytes(source))
        yield buffer
        return
    stream = cast(BinaryIO, source)
    seekable = False
    try:
        seekable = bool(getattr(stream, "seekable", lambda: False)())
    except Exception:
        seekable = False
    if seekable:
        try:
            stream.seek(0)
        except Exception:
            seekable = False
        else:
            yield stream
            return
    with NamedTemporaryFile(mode="w+b") as tmp:
        _copy_stream(stream, tmp)
        tmp.flush()
        tmp.seek(0)
        yield tmp


def _collect_warnings(
    row_warnings: list[str],
    warnings: list[str],
    seen: set[str],
) -> None:
    for warning in row_warnings:
        cleaned = " ".join(warning.split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            warnings.append(cleaned)


def dry_run_import(
    xml_source: str | Path | BinaryIO | bytes,
    *,
    attachments_zip: str | Path | BinaryIO | bytes | None = None,
    prefix_with_zephyr_key: bool = True,
    meta_labels: bool = True,
    append_jira_issues_to_description: bool = True,
    embed_testdata_to_description: bool = True,
) -> DryRunImportResult:
    zip_index = _build_zip_index(attachments_zip)

    rows: list[ReportRow] = []
    warnings: list[str] = []
    seen_warnings: set[str] = set()

    case_count = 0
    step_count = 0
    label_count = 0
    attachment_count = 0

    with _open_seekable_xml_source(xml_source) as xml_stream:
        folders, duplicate_key_counts = parse_folders_and_duplicate_key_counts(xml_stream)
        xml_stream.seek(0)

        for tc in iter_test_cases(xml_stream):
            case_count += 1
            payload = build_testy_payload_from_zephyr(
                tc,
                prefix_with_zephyr_key=prefix_with_zephyr_key,
                meta_labels=meta_labels,
                append_jira_issues_to_description=append_jira_issues_to_description,
                embed_testdata_to_description=embed_testdata_to_description,
            )
            steps = payload.get("steps", [])
            labels = payload.get("labels", [])
            step_count += len(steps)
            label_count += len(labels)

            attachment_result = match_attachments_for_testcase(tc, zip_index)
            case_warnings = build_case_warnings(
                tc,
                payload["name"],
                duplicate_key_counts,
                folders=folders,
            )
            attachment_count += attachment_result.attachments_in_xml

            row_warnings = [*case_warnings, *attachment_result.warnings]
            _collect_warnings(row_warnings, warnings, seen_warnings)

            rows.append(
                ReportRow(
                    zephyr_key=tc.key,
                    zephyr_id=tc.zephyr_id,
                    folder_full_path=tc.folder,
                    testy_suite_id=None,
                    testy_case_id=None,
                    action="created",
                    steps_count=len(steps),
                    labels_count=len(labels),
                    attachments_in_xml=attachment_result.attachments_in_xml,
                    attachments_attached=attachment_result.attachments_attached,
                    attachments_missing=attachment_result.attachments_missing,
                    warnings=row_warnings,
                    error=None,
                )
            )

    summary = ImportSummary(
        folders=len(folders),
        cases=case_count,
        steps=step_count,
        labels=label_count,
        attachments=attachment_count,
        created=case_count,
        reused=0,
        updated=0,
        skipped=0,
        failed=0,
    )
    report_csv = build_csv_report(rows)
    warnings_preview = warnings[:MAX_WARNING_PREVIEW]
    return DryRunImportResult(summary=summary, report_csv=report_csv, warnings=warnings_preview)


def _suite_attributes(folder_path: str | None, folder_index: int | None) -> dict[str, object]:
    return {
        "zephyr": {
            "folderFullPath": folder_path,
            "folderIndex": folder_index,
        }
    }


def _payload_without_labels(payload: Mapping[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload)
    cleaned.pop("labels", None)
    return cleaned


def import_into_testy(
    xml_source: str | Path | BinaryIO | bytes,
    *,
    project_id: int,
    attachments_zip: str | Path | BinaryIO | bytes | None = None,
    prefix_with_zephyr_key: bool = True,
    meta_labels: bool = True,
    append_jira_issues_to_description: bool = True,
    embed_testdata_to_description: bool = True,
    on_duplicate: str = "skip",
    adapter: BaseTestyAdapter | None = None,
    user: Any | None = None,
) -> DryRunImportResult:
    zip_bytes = _read_source_bytes(attachments_zip) if attachments_zip is not None else None
    zip_index = build_zip_index(zip_bytes) if zip_bytes is not None else None
    zip_archive = ZipFile(BytesIO(zip_bytes)) if zip_bytes is not None else None

    if adapter is None:
        adapter = TestyServiceAdapter(user=user)

    rows: list[ReportRow] = []
    warnings: list[str] = []
    seen_warnings: set[str] = set()

    case_count = 0
    step_count = 0
    label_count = 0
    attachment_count = 0
    created_count = 0
    reused_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        with _open_seekable_xml_source(xml_source) as xml_stream:
            folders, duplicate_key_counts = parse_folders_and_duplicate_key_counts(xml_stream)
            xml_stream.seek(0)

            suite_cache: dict[tuple[int | None, str], int] = {}

            def ensure_suite(name: str, parent_id: int | None, folder_path: str | None) -> int:
                cache_key = (parent_id, name)
                cached = suite_cache.get(cache_key)
                if cached is not None:
                    return cached
                existing = adapter.get_suite_id(project_id, name, parent_id)
                if existing is None:
                    folder_meta = folders.get(folder_path or "")
                    suite_id = adapter.create_suite(
                        project_id,
                        name,
                        parent_id,
                        _suite_attributes(folder_path, folder_meta.index if folder_meta else None),
                    )
                else:
                    suite_id = existing
                suite_cache[cache_key] = suite_id
                return suite_id

            def suite_id_for_folder(folder_path: str | None) -> int:
                cleaned = (folder_path or "").strip()
                if not cleaned:
                    return ensure_suite(NO_FOLDER_SUITE_NAME, None, None)
                parts = [part.strip() for part in cleaned.split("/") if part.strip()]
                parent_id: int | None = None
                current_path = ""
                for part in parts:
                    current_path = f"{current_path}/{part}" if current_path else part
                    parent_id = ensure_suite(part, parent_id, current_path)
                return parent_id or ensure_suite(NO_FOLDER_SUITE_NAME, None, None)

            def precreate_folder_suites() -> None:
                for folder_path in sorted(folders):
                    cleaned = folder_path.strip()
                    if not cleaned:
                        continue
                    parts = [part.strip() for part in cleaned.split("/") if part.strip()]
                    parent_id: int | None = None
                    current_path = ""
                    for part in parts:
                        current_path = f"{current_path}/{part}" if current_path else part
                        parent_id = ensure_suite(part, parent_id, current_path)

            precreate_folder_suites()

            for tc in iter_test_cases(xml_stream):
                case_count += 1
                payload = build_testy_payload_from_zephyr(
                    tc,
                    prefix_with_zephyr_key=prefix_with_zephyr_key,
                    meta_labels=meta_labels,
                    append_jira_issues_to_description=append_jira_issues_to_description,
                    embed_testdata_to_description=embed_testdata_to_description,
                )
                payload_for_write = _payload_without_labels(payload)
                steps = payload.get("steps", [])
                labels = payload.get("labels", [])
                step_count += len(steps)
                label_count += len(labels)

                attachment_result = match_attachments_for_testcase(tc, zip_index)
                case_warnings = build_case_warnings(
                    tc,
                    payload["name"],
                    duplicate_key_counts,
                    folders=folders,
                )
                attachment_count += attachment_result.attachments_in_xml

                row_warnings = [*case_warnings, *attachment_result.warnings]

                action = "created"
                case_id: int | None = None
                suite_id: int | None = None
                error: str | None = None
                attachments_attached = 0

                try:
                    existing_case_id = None
                    zephyr_key = (tc.key or "").strip()
                    if zephyr_key:
                        existing_case_id = adapter.find_case_id_by_zephyr_key(project_id, zephyr_key)

                    if existing_case_id and on_duplicate == "skip":
                        action = "skipped"
                        case_id = existing_case_id
                    else:
                        suite_id = suite_id_for_folder(tc.folder)
                        if existing_case_id and on_duplicate == "upsert":
                            try:
                                case_id = adapter.update_case_with_steps(
                                    project_id,
                                    existing_case_id,
                                    suite_id,
                                    payload_for_write,
                                )
                                action = "updated"
                            except NotImplementedError:
                                action = "skipped"
                                case_id = existing_case_id
                                row_warnings.append(
                                    "Upsert requested but adapter does not support updates"
                                )
                        else:
                            case_id = adapter.create_case_with_steps(
                                project_id,
                                suite_id,
                                payload_for_write,
                            )
                            action = "created"

                        if case_id is not None:
                            try:
                                adapter.set_labels(project_id, case_id, labels)
                            except Exception as exc:
                                row_warnings.append(f"Failed to set labels: {exc}")

                            if zip_archive is not None and attachment_result.matched:
                                for matched in attachment_result.matched:
                                    try:
                                        data = zip_archive.read(matched)
                                        filename = Path(matched).name or matched
                                        adapter.attach_file(project_id, case_id, filename, data)
                                        attachments_attached += 1
                                    except Exception as exc:
                                        row_warnings.append(f"Failed to attach '{matched}': {exc}")
                except TestyAdapterError as exc:
                    action = "failed"
                    error = str(exc)
                except Exception as exc:
                    action = "failed"
                    error = str(exc)

                if action == "created":
                    created_count += 1
                elif action == "updated":
                    updated_count += 1
                elif action == "skipped":
                    skipped_count += 1
                    if case_id is not None:
                        reused_count += 1
                elif action == "failed":
                    failed_count += 1

                _collect_warnings(row_warnings, warnings, seen_warnings)

                rows.append(
                    ReportRow(
                        zephyr_key=tc.key,
                        zephyr_id=tc.zephyr_id,
                        folder_full_path=tc.folder,
                        testy_suite_id=suite_id,
                        testy_case_id=case_id,
                        action=action,
                        steps_count=len(steps),
                        labels_count=len(labels),
                        attachments_in_xml=attachment_result.attachments_in_xml,
                        attachments_attached=attachments_attached,
                        attachments_missing=attachment_result.attachments_missing,
                        warnings=row_warnings,
                        error=error,
                    )
                )
    finally:
        if zip_archive is not None:
            zip_archive.close()

    summary = ImportSummary(
        folders=len(folders),
        cases=case_count,
        steps=step_count,
        labels=label_count,
        attachments=attachment_count,
        created=created_count,
        reused=reused_count,
        updated=updated_count,
        skipped=skipped_count,
        failed=failed_count,
    )
    report_csv = build_csv_report(rows)
    return DryRunImportResult(summary=summary, report_csv=report_csv, warnings=warnings)
