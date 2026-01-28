from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ZephyrFolder:
    full_path: str
    index: int | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ZephyrIssue:
    key: str
    summary: str | None = None


@dataclass(frozen=True, slots=True)
class ZephyrStep:
    index: int
    description: str | None = None
    expected_result: str | None = None
    test_data: str | None = None


@dataclass(frozen=True, slots=True)
class ZephyrTestDataCell:
    index: int | None = None
    name: str | None = None
    data_type: str | None = None
    value: str | None = None


@dataclass(frozen=True, slots=True)
class ZephyrTestDataRow:
    cells: list[ZephyrTestDataCell] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ZephyrTestDataTable:
    rows: list[ZephyrTestDataRow] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ZephyrTestCase:
    zephyr_id: str | None
    key: str | None
    name: str | None

    folder: str | None = None
    folder_description: str | None = None
    objective: str | None = None
    precondition: str | None = None

    status: str | None = None
    priority: str | None = None
    owner: str | None = None

    created_by: str | None = None
    created_on: str | None = None
    updated_by: str | None = None
    updated_on: str | None = None

    param_type: str | None = None
    parameters: list[str] = field(default_factory=list)
    test_data_wrapper: ZephyrTestDataTable | None = None

    labels: list[str] = field(default_factory=list)
    issues: list[ZephyrIssue] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)

    test_script_type: str | None = None  # "steps" or other
    test_script_text: str | None = None
    steps: list[ZephyrStep] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ZephyrParseResult:
    folders: dict[str, ZephyrFolder] = field(default_factory=dict)
    test_cases: list[ZephyrTestCase] = field(default_factory=list)
