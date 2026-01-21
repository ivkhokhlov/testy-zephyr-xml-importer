from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Sequence, cast
from zipfile import ZipFile


@dataclass(frozen=True, slots=True)
class AttachmentZipIndex:
    by_basename: dict[str, list[str]]
    duplicate_basenames: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class AttachmentMatchResult:
    attachments_in_xml: int
    attachments_attached: int
    attachments_missing: int
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _open_binary(source: str | Path | BinaryIO | bytes) -> BinaryIO:
    if isinstance(source, (str, Path)):
        return open(source, "rb")
    if isinstance(source, (bytes, bytearray)):
        return BytesIO(bytes(source))
    return cast(BinaryIO, source)


def _basename(raw_name: str) -> str:
    cleaned = raw_name.strip()
    if not cleaned:
        return ""
    normalized = cleaned.replace("\\", "/")
    return normalized.rsplit("/", 1)[-1].strip()


def build_zip_index(source: str | Path | BinaryIO | bytes) -> AttachmentZipIndex:
    by_basename: dict[str, list[str]] = {}
    f = _open_binary(source)
    close_me = isinstance(source, (str, Path, bytes, bytearray))
    try:
        with ZipFile(f) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                basename = _basename(info.filename)
                if not basename:
                    continue
                by_basename.setdefault(basename, []).append(info.filename)
    finally:
        if close_me:
            f.close()

    duplicate_basenames = {name for name, paths in by_basename.items() if len(paths) > 1}
    for paths in by_basename.values():
        paths.sort()
    return AttachmentZipIndex(by_basename=by_basename, duplicate_basenames=duplicate_basenames)


def match_attachments(
    attachment_names: Sequence[str],
    zip_index: AttachmentZipIndex | None,
) -> AttachmentMatchResult:
    cleaned_names = [name.strip() for name in attachment_names if name and name.strip()]
    attachments_in_xml = len(cleaned_names)
    if attachments_in_xml == 0:
        return AttachmentMatchResult(
            attachments_in_xml=0,
            attachments_attached=0,
            attachments_missing=0,
        )

    matched: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    duplicate_warned: set[str] = set()
    missing_warned: set[str] = set()

    if zip_index is None:
        for name in cleaned_names:
            missing.append(name)
            if name not in missing_warned:
                warnings.append(f"Attachment missing in ZIP: {name}")
                missing_warned.add(name)
        return AttachmentMatchResult(
            attachments_in_xml=attachments_in_xml,
            attachments_attached=0,
            attachments_missing=len(missing),
            matched=matched,
            missing=missing,
            warnings=warnings,
        )

    for name in cleaned_names:
        basename = _basename(name)
        if not basename:
            missing.append(name)
            if name not in missing_warned:
                warnings.append(f"Attachment missing in ZIP: {name}")
                missing_warned.add(name)
            continue

        candidates = zip_index.by_basename.get(basename, [])
        if not candidates:
            missing.append(name)
            if name not in missing_warned:
                warnings.append(f"Attachment missing in ZIP: {name}")
                missing_warned.add(name)
            continue

        selected = candidates[0]
        matched.append(selected)
        if basename in zip_index.duplicate_basenames and basename not in duplicate_warned:
            warnings.append(
                f"Duplicate attachment basename '{basename}' in ZIP; using '{selected}'."
            )
            duplicate_warned.add(basename)

    return AttachmentMatchResult(
        attachments_in_xml=attachments_in_xml,
        attachments_attached=len(matched),
        attachments_missing=len(missing),
        matched=matched,
        missing=missing,
        warnings=warnings,
    )
