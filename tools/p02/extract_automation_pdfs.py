#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTLine, LTTextLineHorizontal
except ImportError as error:
    print(f"required dependency missing: {error}", file=sys.stderr)
    raise SystemExit(2) from error

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.extract_help import (
    ExtractionError,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)
from tools.p02.validate_source_records import semantic_errors

SCHEMA_PATH = REPOSITORY_ROOT / "protocol" / "json-schema" / "source-record-v1.schema.json"
PRIVATE_EVIDENCE_ROOT = REPOSITORY_ROOT / "implementation" / "p02" / "evidence"
EXTRACTOR_ID = "automation-pdf-extractor"
EXTRACTOR_VERSION = "0.1.0"
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_PAGES = 1_000
MAX_TEXT_LINES = 1_000_000
MAX_RECORDS = 50_000

SOURCE_SPECS = (
    ("action_table", "action_source_id", "action_input"),
    ("parameter_table", "parameter_source_id", "parameter_input"),
    ("automation_object", "automation_source_id", "automation_input"),
    ("automation_event", "event_source_id", "event_input"),
)
PARAMETER_SECTION = re.compile(r"^(\d+)\)\s*([^:]+?)\s*:\s*(.+)$")
OBJECT_HEADING = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:")
EVENT_SUMMARY_HEADING = re.compile(r"^IHwpObjectEvents\(")
AUTOMATION_ITEM = re.compile(r"^(.+?)\((Property|Method)\)$")
EVENT_METHOD = re.compile(
    r"^STDMETHOD\(([A-Za-z_][A-Za-z0-9_]*)\)\((.*)\)$"
)
DECLARATION = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)")


@dataclass(frozen=True)
class TextLine:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


@dataclass(frozen=True)
class HorizontalLine:
    x0: float
    y: float
    x1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0


@dataclass(frozen=True)
class PageLayout:
    number: int
    width: float
    height: float
    text_lines: tuple[TextLine, ...]
    horizontal_lines: tuple[HorizontalLine, ...]


@dataclass(frozen=True)
class SourceInput:
    source_kind: str
    source_id: str
    path: Path
    source_entry: dict
    content: bytes


@dataclass
class ParsedItem:
    source_kind: str
    source_id: str
    source_sha256: str
    page_start: int
    page_end: int
    section: str
    name: str
    description: str | None
    parameters: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ExtractionConfig:
    source_lock: Path
    action_source_id: str
    action_input: Path
    parameter_source_id: str
    parameter_input: Path
    automation_source_id: str
    automation_input: Path
    event_source_id: str
    event_input: Path
    output_root: Path
    output_relative: str


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def compact_cell(lines: list[TextLine]) -> str:
    return "".join(normalize_text(line.text) for line in sorted(lines, key=lambda item: -item.y0))


def prose_cell(lines: list[TextLine]) -> str:
    return normalize_text(" ".join(line.text for line in sorted(lines, key=lambda item: -item.y0)))


def load_pdf_source_entry(source_lock_path: Path, source_id: str) -> tuple[str, dict]:
    content = read_regular_file(source_lock_path, 8 * 1024 * 1024)
    try:
        source_lock = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"invalid UTF-8 source lock: {error}") from error
    source_lock_id = source_lock.get("source_lock_id")
    if not isinstance(source_lock_id, str) or not source_lock_id:
        raise ExtractionError("source lock is missing source_lock_id")
    matches = [entry for entry in source_lock.get("sources", []) if entry.get("source_id") == source_id]
    if len(matches) != 1:
        raise ExtractionError(f"expected exactly one source-lock entry for {source_id}")
    entry = matches[0]
    if entry.get("kind") != "pdf_manual":
        raise ExtractionError(f"source-lock entry is not pdf_manual: {source_id}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
        raise ExtractionError(f"source-lock entry has invalid SHA-256: {source_id}")
    if entry.get("license_state") not in {"restricted", "public_reference"}:
        raise ExtractionError(f"source-lock entry has unsupported license_state: {source_id}")
    return source_lock_id, entry


def extract_layout(content: bytes) -> list[PageLayout]:
    pages: list[PageLayout] = []
    line_count = 0
    try:
        pdf_pages = extract_pages(io.BytesIO(content))
        for page_number, page in enumerate(pdf_pages, 1):
            if page_number > MAX_PAGES:
                raise ExtractionError(f"PDF page limit exceeded: {MAX_PAGES}")
            text_lines: list[TextLine] = []
            horizontal_lines: list[HorizontalLine] = []

            def visit(item: object) -> None:
                nonlocal line_count
                if isinstance(item, LTTextLineHorizontal):
                    text = normalize_text(item.get_text())
                    if text:
                        line_count += 1
                        if line_count > MAX_TEXT_LINES:
                            raise ExtractionError(f"PDF text-line limit exceeded: {MAX_TEXT_LINES}")
                        text_lines.append(
                            TextLine(
                                x0=float(item.x0),
                                y0=float(item.y0),
                                x1=float(item.x1),
                                y1=float(item.y1),
                                text=text,
                            )
                        )
                    return
                if isinstance(item, LTLine) and abs(float(item.y1) - float(item.y0)) <= 0.5:
                    horizontal_lines.append(
                        HorizontalLine(
                            x0=float(min(item.x0, item.x1)),
                            y=float((item.y0 + item.y1) / 2),
                            x1=float(max(item.x0, item.x1)),
                        )
                    )
                    return
                if hasattr(item, "__iter__"):
                    for child in item:  # type: ignore[union-attr]
                        visit(child)

            visit(page)
            pages.append(
                PageLayout(
                    number=page_number,
                    width=float(page.width),
                    height=float(page.height),
                    text_lines=tuple(sorted(text_lines, key=lambda item: (-item.y0, item.x0))),
                    horizontal_lines=tuple(horizontal_lines),
                )
            )
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError(f"PDF layout extraction failed: {error}") from error
    if not pages:
        raise ExtractionError("PDF contains no pages")
    return pages


def row_intervals(
    page: PageLayout, *, minimum_width: float, minimum_right: float
) -> list[tuple[float, float]]:
    boundaries = sorted(
        {
            round(line.y, 1)
            for line in page.horizontal_lines
            if line.width >= minimum_width and line.x1 >= minimum_right
        },
        reverse=True,
    )
    return [
        (upper, lower)
        for upper, lower in zip(boundaries, boundaries[1:], strict=False)
        if upper - lower >= 2.0
    ]


def lines_in_interval(page: PageLayout, upper: float, lower: float) -> list[TextLine]:
    return [
        line
        for line in page.text_lines
        if lower - 0.2 <= (line.y0 + line.y1) / 2 <= upper + 0.2
    ]


def parameter_row_intervals(page: PageLayout) -> list[tuple[float, float]]:
    intervals = row_intervals(page, minimum_width=600.0, minimum_right=750.0)
    if not intervals:
        return intervals
    lowest_boundary = intervals[-1][1]
    orphan_type_anchors = sorted(
        {
            round((line.y0 + line.y1) / 2, 1)
            for line in page.text_lines
            if 35.0 < (line.y0 + line.y1) / 2 < lowest_boundary
            and re.search(r"P[IM]T_[A-Z0-9_]+", line.text)
        },
        reverse=True,
    )
    if not orphan_type_anchors:
        return intervals
    upper = lowest_boundary
    for index, anchor in enumerate(orphan_type_anchors):
        lower = (
            (anchor + orphan_type_anchors[index + 1]) / 2
            if index + 1 < len(orphan_type_anchors)
            else max(35.0, anchor - 12.0)
        )
        if upper - lower >= 2.0:
            intervals.append((upper, lower))
        upper = lower
    return intervals


def append_continuation(items: list[ParsedItem], source_kind: str, page: int, text: str) -> None:
    if not items or items[-1].source_kind != source_kind:
        raise ExtractionError(f"{source_kind} description continuation has no preceding item on page {page}")
    item = items[-1]
    item.description = normalize_text(" ".join(part for part in (item.description, text) if part))
    item.page_end = page


def parse_action_table(source: SourceInput, pages: list[PageLayout]) -> list[ParsedItem]:
    items: list[ParsedItem] = []
    for page in pages:
        if not any(line.text == "Action ID" for line in page.text_lines):
            continue
        for upper, lower in row_intervals(page, minimum_width=600.0, minimum_right=750.0):
            lines = lines_in_interval(page, upper, lower)
            action = compact_cell([line for line in lines if line.x0 < 250.0])
            parameter_set = compact_cell([line for line in lines if 250.0 <= line.x0 < 380.0])
            description = prose_cell([line for line in lines if 380.0 <= line.x0 < 630.0])
            remark = prose_cell([line for line in lines if line.x0 >= 630.0])
            if not any((action, parameter_set, description, remark)):
                continue
            if not action:
                if parameter_set or remark:
                    raise ExtractionError(f"ambiguous action continuation on page {page.number}")
                append_continuation(items, "action_table", page.number, description)
                continue
            if action == "Action ID":
                continue
            if len(action) > 1024 or not re.search(r"[A-Za-z0-9]", action):
                raise ExtractionError(f"invalid Action ID on page {page.number}: {action!r}")
            combined_description = description or None
            if remark:
                combined_description = normalize_text(
                    " ".join(part for part in (combined_description, f"비고: {remark}") if part)
                )
            parameters = []
            if parameter_set:
                parameters.append(
                    {
                        "ordinal": 0,
                        "original_name": parameter_set,
                        "declared_type": "ParameterSet ID",
                        "direction": "unknown",
                        "required": None,
                        "description_ko": None,
                    }
                )
            items.append(
                ParsedItem(
                    source_kind="action_table",
                    source_id=source.source_id,
                    source_sha256=source.source_entry["sha256"],
                    page_start=page.number,
                    page_end=page.number,
                    section="Action Table",
                    name=action,
                    description=combined_description,
                    parameters=parameters,
                )
            )
    if not items:
        raise ExtractionError("ActionTable parser produced no records")
    seen: set[str] = set()
    duplicates = {item.name for item in items if item.name in seen or seen.add(item.name)}
    if duplicates:
        raise ExtractionError(f"duplicate Action ID values: {sorted(duplicates)[:10]}")
    return items


def parse_parameter_table(source: SourceInput, pages: list[PageLayout]) -> list[ParsedItem]:
    items: list[ParsedItem] = []
    row_errors: list[str] = []
    current_section: str | None = None
    for page in pages:
        header_names = {line.text for line in page.text_lines}
        required_headers = {"Item ID", "Type", "SubType", "Description"}
        if not required_headers.issubset(header_names):
            continue
        description_x = max(
            (line for line in page.text_lines if line.text == "Description"),
            key=lambda line: line.y0,
        ).x0
        type_header_x = max(
            (line for line in page.text_lines if line.text == "Type"),
            key=lambda line: line.y0,
        ).x0
        subtype_header_x = max(
            (line for line in page.text_lines if line.text == "SubType"),
            key=lambda line: line.y0,
        ).x0
        type_subtype_cutoff = (type_header_x + subtype_header_x) / 2
        events: list[tuple[float, int, object]] = []
        for line in page.text_lines:
            match = PARAMETER_SECTION.match(line.text)
            if line.x0 < 160.0 and match:
                events.append((line.y0, 0, (match.group(2).strip(), line.text)))
        for upper, lower in parameter_row_intervals(page):
            events.append(((upper + lower) / 2, 1, (upper, lower)))
        for _, event_kind, payload in sorted(events, key=lambda event: (-event[0], event[1])):
            if event_kind == 0:
                section_id, section_label = payload  # type: ignore[misc]
                current_section = f"{section_id} | {section_label}"
                continue
            upper, lower = payload  # type: ignore[misc]
            lines = lines_in_interval(page, upper, lower)
            description = prose_cell(
                [line for line in lines if line.x0 >= description_x - 5.0]
            )
            metadata_lines = [line for line in lines if line.x0 < description_x - 5.0]
            item_parts: list[TextLine] = []
            subtype_parts: list[TextLine] = []
            type_values: list[str] = []
            subtype_type_values: list[str] = []
            for line in metadata_lines:
                merged = re.fullmatch(
                    r"(.*?)(P[IM]T_[A-Z0-9_]+)(?:\s+(.+))?", line.text
                )
                if merged:
                    prefix = merged.group(1).strip()
                    if prefix:
                        item_parts.append(
                            TextLine(line.x0, line.y0, line.x1, line.y1, prefix)
                        )
                        type_values.append(merged.group(2))
                    elif line.x0 < type_subtype_cutoff:
                        type_values.append(merged.group(2))
                    else:
                        subtype_type_values.append(merged.group(2))
                    if merged.group(3):
                        subtype_parts.append(
                            TextLine(line.x0, line.y0, line.x1, line.y1, merged.group(3))
                        )
                elif line.x0 < 210.0:
                    item_parts.append(line)
                else:
                    subtype_parts.append(line)
            item_id = compact_cell(item_parts)
            if len(type_values) > 1:
                raise ExtractionError(
                    f"multiple declared types in one parameter row on page {page.number}: {type_values}"
                )
            if len(subtype_type_values) > 1:
                raise ExtractionError(
                    f"multiple subtype tokens in one parameter row on page {page.number}: "
                    f"{subtype_type_values}"
                )
            declared_type = type_values[0] if type_values else ""
            subtype_values = [*subtype_type_values]
            textual_subtype = compact_cell(subtype_parts)
            if textual_subtype:
                subtype_values.append(textual_subtype)
            if len(subtype_values) > 1:
                raise ExtractionError(
                    f"multiple subtype values in one parameter row on page {page.number}: "
                    f"{subtype_values}"
                )
            subtype = subtype_values[0] if subtype_values else ""
            if not any((item_id, declared_type, subtype, description)):
                continue
            if item_id == "Item ID":
                continue
            if not item_id:
                if declared_type or subtype:
                    raise ExtractionError(f"ambiguous parameter continuation on page {page.number}")
                append_continuation(items, "parameter_table", page.number, description)
                continue
            if current_section is None:
                raise ExtractionError(f"parameter row has no section on page {page.number}: {item_id}")
            if declared_type and not re.fullmatch(r"P[IM]T_[A-Z0-9_]+", declared_type):
                row_errors.append(
                    f"parameter row has invalid declared type on page {page.number}: "
                    f"{item_id}={declared_type!r}"
                )
                continue
            if not declared_type and not subtype:
                row_errors.append(
                    f"parameter row has no Type or SubType on page {page.number}: {item_id}"
                )
                continue
            if declared_type:
                normalized_type = declared_type
            else:
                normalized_type = "[Type missing]"
            if subtype:
                normalized_type += f" [SubType={subtype}]"
            items.append(
                ParsedItem(
                    source_kind="parameter_table",
                    source_id=source.source_id,
                    source_sha256=source.source_entry["sha256"],
                    page_start=page.number,
                    page_end=page.number,
                    section=current_section,
                    name=item_id,
                    description=description or None,
                    parameters=[
                        {
                            "ordinal": 0,
                            "original_name": item_id,
                            "declared_type": normalized_type,
                            "direction": "unknown",
                            "required": None,
                            "description_ko": description or None,
                        }
                    ],
                )
            )
    if not items:
        raise ExtractionError("ParameterSetTable parser produced no records")
    if row_errors:
        raise ExtractionError("; ".join(row_errors[:50]))
    keys = [(item.section, item.name) for item in items]
    if len(keys) != len(set(keys)):
        raise ExtractionError("duplicate ParameterSet section/Item ID pairs")
    return items


def split_parameter_specs(value: str) -> list[str]:
    value = normalize_text(value)
    if not value or value.lower() == "void":
        return []
    parts: list[str] = []
    depth = 0
    start = 0
    for index, character in enumerate(value):
        if character in "([<":
            depth += 1
        elif character in ")]>":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]


def parse_declared_parameters(item_name: str, description: str) -> list[dict]:
    labels = {"Description", "Declaration", "Parameters", "Remark"}
    blocks: dict[str, list[str]] = {label: [] for label in labels}
    current: str | None = None
    for token in re.split(r"\b(Description|Declaration|Parameters|Remark)\b", description):
        text = normalize_text(token)
        if text in labels:
            current = text
        elif current is not None and text:
            blocks[current].append(text)
    declaration = normalize_text(" ".join(blocks["Declaration"]))
    if not declaration:
        return []
    declaration_matches = list(DECLARATION.finditer(declaration))
    if not declaration_matches:
        raise ExtractionError(f"ambiguous automation declaration for {item_name}: {declaration}")
    descriptions: dict[str, str] = {}
    active_name: str | None = None
    for text in blocks["Parameters"]:
        parameter_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", text)
        if parameter_match:
            active_name = parameter_match.group(1)
            descriptions[active_name] = parameter_match.group(2)
        elif active_name is not None:
            descriptions[active_name] = normalize_text(f"{descriptions[active_name]} {text}")
    parsed_parameters: list[tuple[str, str, bool | None]] = []
    for declaration_match in declaration_matches:
        for specification in split_parameter_specs(declaration_match.group(2)):
            optional = specification.startswith("[") and specification.endswith("]")
            normalized_specification = (
                specification[1:-1].strip() if optional else specification
            )
            has_default = "=" in normalized_specification
            without_default = normalized_specification.split("=", 1)[0].strip()
            parameter_match = re.match(
                r"^(.*?)([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[\s*\])?$", without_default
            )
            if not parameter_match:
                raise ExtractionError(
                    f"ambiguous parameter declaration for {item_name}: {specification}"
                )
            declared_type = parameter_match.group(1).strip()
            original_name = parameter_match.group(2)
            if not declared_type:
                raise ExtractionError(f"missing parameter type for {item_name}.{original_name}")
            candidate = (
                original_name,
                declared_type,
                False if optional or has_default else None,
            )
            existing = next(
                (parameter for parameter in parsed_parameters if parameter[0] == original_name),
                None,
            )
            if existing is not None and existing != candidate:
                raise ExtractionError(
                    f"conflicting overload parameter for {item_name}.{original_name}"
                )
            if existing is None:
                parsed_parameters.append(candidate)
    parameters = [
        {
            "ordinal": ordinal,
            "original_name": original_name,
            "declared_type": declared_type,
            "direction": "unknown",
            "required": required,
            "description_ko": descriptions.get(original_name) or None,
        }
        for ordinal, (original_name, declared_type, required) in enumerate(parsed_parameters)
    ]
    return parameters


def parse_automation_objects(source: SourceInput, pages: list[PageLayout]) -> list[ParsedItem]:
    items: list[ParsedItem] = []
    current_object: str | None = None
    for page in pages:
        skipping_event_summary = False
        events: list[tuple[float, int, object]] = []
        for line in page.text_lines:
            match = OBJECT_HEADING.match(line.text)
            if line.x0 < 160.0 and match:
                events.append((line.y0, 0, ("object", match.group(1), line.text)))
            elif line.x0 < 160.0 and EVENT_SUMMARY_HEADING.match(line.text):
                events.append((line.y0, 0, ("event_summary", "", line.text)))
        for upper, lower in row_intervals(page, minimum_width=440.0, minimum_right=540.0):
            events.append(((upper + lower) / 2, 1, (upper, lower)))
        for _, event_kind, payload in sorted(events, key=lambda event: (-event[0], event[1])):
            if event_kind == 0:
                heading_kind, object_id, object_label = payload  # type: ignore[misc]
                current_object = (
                    f"{object_id} | {object_label}" if heading_kind == "object" else None
                )
                skipping_event_summary = heading_kind == "event_summary"
                continue
            upper, lower = payload  # type: ignore[misc]
            lines = lines_in_interval(page, upper, lower)
            left_lines = [line for line in lines if line.x0 < 180.0]
            right_lines = [line for line in lines if line.x0 >= 180.0]
            item_name = compact_cell(left_lines)
            description = prose_cell(right_lines)
            if not item_name and not description:
                continue
            if item_name == "Item Name":
                continue
            if item_name and OBJECT_HEADING.match(item_name):
                continue
            if item_name and EVENT_SUMMARY_HEADING.match(item_name):
                continue
            if skipping_event_summary:
                continue
            if not item_name:
                append_continuation(items, "automation_object", page.number, description)
                continue
            if not AUTOMATION_ITEM.fullmatch(item_name):
                raise ExtractionError(
                    f"ambiguous automation item on page {page.number}: {item_name!r}"
                )
            if current_object is None:
                raise ExtractionError(f"automation item has no object on page {page.number}: {item_name}")
            items.append(
                ParsedItem(
                    source_kind="automation_object",
                    source_id=source.source_id,
                    source_sha256=source.source_entry["sha256"],
                    page_start=page.number,
                    page_end=page.number,
                    section=current_object,
                    name=item_name,
                    description=description or None,
                    parameters=[],
                )
            )
    if not items:
        raise ExtractionError("HwpAutomation parser produced no records")
    for item in items:
        item.parameters = parse_declared_parameters(item.name, item.description or "")
    keys = [(item.section, item.name) for item in items]
    if len(keys) != len(set(keys)):
        raise ExtractionError("duplicate automation object/item pairs")
    return items


def parse_manual_event_summary(source: SourceInput, pages: list[PageLayout]) -> list[ParsedItem]:
    items: list[ParsedItem] = []
    for page in pages:
        summary_heading = next(
            (
                line
                for line in page.text_lines
                if line.x0 < 160.0 and EVENT_SUMMARY_HEADING.match(line.text)
            ),
            None,
        )
        if summary_heading is None:
            continue
        next_object_y = max(
            (
                line.y0
                for line in page.text_lines
                if line.y0 < summary_heading.y0
                and line.x0 < 160.0
                and OBJECT_HEADING.match(line.text)
            ),
            default=0.0,
        )
        for upper, lower in row_intervals(page, minimum_width=440.0, minimum_right=540.0):
            if upper >= summary_heading.y0 or lower <= next_object_y:
                continue
            lines = lines_in_interval(page, upper, lower)
            name = compact_cell([line for line in lines if line.x0 < 210.0])
            return_type = compact_cell([line for line in lines if 210.0 <= line.x0 < 275.0])
            description = prose_cell([line for line in lines if line.x0 >= 275.0])
            if not any((name, return_type, description)):
                continue
            if name == "Item Name":
                continue
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise ExtractionError(
                    f"ambiguous manual event item on page {page.number}: {name!r}"
                )
            parameters = []
            if return_type and return_type != "없음":
                parameters.append(
                    {
                        "ordinal": 0,
                        "original_name": "Return",
                        "declared_type": return_type,
                        "direction": "unknown",
                        "required": None,
                        "description_ko": description or None,
                    }
                )
            preserved_description = description or None
            if return_type:
                preserved_description = normalize_text(
                    " ".join(
                        part
                        for part in (f"Return: {return_type}", preserved_description)
                        if part
                    )
                )
            items.append(
                ParsedItem(
                    source_kind="automation_event",
                    source_id=source.source_id,
                    source_sha256=source.source_entry["sha256"],
                    page_start=page.number,
                    page_end=page.number,
                    section=summary_heading.text,
                    name=name,
                    description=preserved_description,
                    parameters=parameters,
                )
            )
    if not items:
        raise ExtractionError("HwpAutomation event summary produced no records")
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise ExtractionError("duplicate HwpAutomation event summary items")
    return items


def parse_signature_parameters(signature: str, item_name: str) -> list[dict]:
    parameters: list[dict] = []
    for ordinal, specification in enumerate(split_parameter_specs(signature)):
        parameter_match = re.match(
            r"^(.*?)([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[\s*\])?$", specification
        )
        if not parameter_match or not parameter_match.group(1).strip():
            raise ExtractionError(f"ambiguous event parameter for {item_name}: {specification}")
        parameters.append(
            {
                "ordinal": ordinal,
                "original_name": parameter_match.group(2),
                "declared_type": parameter_match.group(1).strip(),
                "direction": "unknown",
                "required": None,
                "description_ko": None,
            }
        )
    return parameters


def parse_automation_events(source: SourceInput, pages: list[PageLayout]) -> list[ParsedItem]:
    items: list[ParsedItem] = []
    for page in pages:
        for line in page.text_lines:
            if not line.text.startswith("STDMETHOD("):
                continue
            match = EVENT_METHOD.fullmatch(line.text)
            if not match:
                raise ExtractionError(
                    f"ambiguous STDMETHOD declaration on page {page.number}: {line.text}"
                )
            name = match.group(1)
            items.append(
                ParsedItem(
                    source_kind="automation_event",
                    source_id=source.source_id,
                    source_sha256=source.source_entry["sha256"],
                    page_start=page.number,
                    page_end=page.number,
                    section="2. IHwpObjectEvents 인터페이스 구현",
                    name=name,
                    description=None,
                    parameters=parse_signature_parameters(match.group(2), name),
                )
            )
    if not items:
        raise ExtractionError("EventHandler parser produced no event declarations")
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise ExtractionError("duplicate EventHandler STDMETHOD declarations")
    return items


def record_id(item: ParsedItem) -> str:
    identity = "\0".join(
        (item.source_kind, item.source_sha256, item.section, item.name, str(item.page_start))
    )
    return f"source:{item.source_kind}:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def source_record(item: ParsedItem, source_lock_id: str, ordinal: int) -> dict:
    page_value = f"p{item.page_start:06d}"
    if item.page_end != item.page_start:
        page_value += f"-p{item.page_end:06d}"
    return {
        "schema_version": "hwpx-agent.source-record/v1",
        "record_id": record_id(item),
        "source_lock_id": source_lock_id,
        "source_id": item.source_id,
        "source_sha256": item.source_sha256,
        "source_kind": item.source_kind,
        "locator": {
            "kind": "automation_item",
            "value": f"{item.source_kind}/{page_value}",
            "section": item.section,
            "anchor": item.name,
        },
        "original_name": item.name,
        "description_ko": item.description,
        "parameters": item.parameters,
        "availability": {
            "product": "hancom_hangul",
            "target_profile_id": None,
            "minimum_version": None,
            "maximum_version": None,
            "locales": ["ko-KR"],
            "support_scope": "documentation_only",
        },
        "extraction": {
            "extractor_id": EXTRACTOR_ID,
            "extractor_version": EXTRACTOR_VERSION,
            "record_ordinal": ordinal,
        },
    }


def serialize_records(records: list[dict]) -> bytes:
    return (json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_records(config: ExtractionConfig) -> tuple[list[dict], dict[str, dict]]:
    source_lock_ids: set[str] = set()
    sources: dict[str, SourceInput] = {}
    layouts: dict[str, list[PageLayout]] = {}
    for source_kind, id_field, path_field in SOURCE_SPECS:
        source_id = getattr(config, id_field)
        path = getattr(config, path_field)
        source_lock_id, entry = load_pdf_source_entry(config.source_lock, source_id)
        source_lock_ids.add(source_lock_id)
        content = read_regular_file(path, MAX_INPUT_BYTES)
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_sha256 != entry["sha256"]:
            raise ExtractionError(
                f"source SHA-256 mismatch for {source_id}: expected {entry['sha256']}, actual {actual_sha256}"
            )
        source = SourceInput(source_kind, source_id, path, entry, content)
        sources[source_kind] = source
        layouts[source_kind] = extract_layout(content)
    if len(source_lock_ids) != 1:
        raise ExtractionError("all PDF sources must share one source_lock_id")
    source_lock_id = next(iter(source_lock_ids))
    parsed: list[ParsedItem] = []
    parsed.extend(parse_action_table(sources["action_table"], layouts["action_table"]))
    parsed.extend(parse_parameter_table(sources["parameter_table"], layouts["parameter_table"]))
    parsed.extend(parse_automation_objects(sources["automation_object"], layouts["automation_object"]))
    parsed.extend(
        parse_manual_event_summary(sources["automation_object"], layouts["automation_object"])
    )
    parsed.extend(parse_automation_events(sources["automation_event"], layouts["automation_event"]))
    if len(parsed) > MAX_RECORDS:
        raise ExtractionError(f"record limit exceeded: {MAX_RECORDS}")
    records = [source_record(item, source_lock_id, ordinal) for ordinal, item in enumerate(parsed)]
    if "\ufffd" in json.dumps(records, ensure_ascii=False):
        raise ExtractionError("generated records contain Unicode replacement characters")
    ids = [record["record_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ExtractionError("generated record_id values are not unique")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    violations: list[str] = []
    for ordinal, record in enumerate(records):
        violations.extend(
            f"record {ordinal}: {error.message}" for error in validator.iter_errors(record)
        )
        violations.extend(f"record {ordinal}: {error}" for error in semantic_errors(record))
    if violations:
        raise ExtractionError("generated SourceRecord validation failed: " + "; ".join(violations[:20]))
    coverage = {
        source.source_id: {
            "source_kinds": sorted(
                {item.source_kind for item in parsed if item.source_id == source.source_id}
            ),
            "source_sha256": source.source_entry["sha256"],
            "page_count": len(layouts[source_kind]),
            "record_count": sum(1 for item in parsed if item.source_id == source.source_id),
            "record_pages": sorted(
                {
                    page
                    for item in parsed
                    if item.source_id == source.source_id
                    for page in range(item.page_start, item.page_end + 1)
                }
            ),
        }
        for source_kind, source in sources.items()
    }
    return records, coverage


def run(config: ExtractionConfig) -> dict:
    source_lock_snapshot = read_regular_file(config.source_lock, 8 * 1024 * 1024)
    entries = [
        load_pdf_source_entry(config.source_lock, getattr(config, id_field))[1]
        for _, id_field, _ in SOURCE_SPECS
    ]
    if any(entry["license_state"] == "restricted" for entry in entries) and os.path.normcase(
        str(config.output_root.absolute())
    ) != os.path.normcase(str(PRIVATE_EVIDENCE_ROOT.absolute())):
        raise ExtractionError("restricted sources may publish only to implementation/p02/evidence")
    snapshots = {
        path_field: read_regular_file(getattr(config, path_field), MAX_INPUT_BYTES)
        for _, _, path_field in SOURCE_SPECS
    }
    records, coverage = build_records(config)
    if read_regular_file(config.source_lock, 8 * 1024 * 1024) != source_lock_snapshot:
        raise ExtractionError("source lock changed during extraction")
    for _, _, path_field in SOURCE_SPECS:
        if read_regular_file(getattr(config, path_field), MAX_INPUT_BYTES) != snapshots[path_field]:
            raise ExtractionError(f"source changed during extraction: {path_field}")
    output = resolve_output(config.output_root, config.output_relative)
    serialized = serialize_records(records)
    publish_no_overwrite(output, serialized)
    return {
        "schema_version": "hwpx-agent.automation-pdf-extraction-receipt/v1",
        "extractor_id": EXTRACTOR_ID,
        "extractor_version": EXTRACTOR_VERSION,
        "output_sha256": hashlib.sha256(serialized).hexdigest(),
        "record_count": len(records),
        "coverage": coverage,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--action-source-id", required=True)
    parser.add_argument("--action-input", type=Path, required=True)
    parser.add_argument("--parameter-source-id", required=True)
    parser.add_argument("--parameter-input", type=Path, required=True)
    parser.add_argument("--automation-source-id", required=True)
    parser.add_argument("--automation-input", type=Path, required=True)
    parser.add_argument("--event-source-id", required=True)
    parser.add_argument("--event-input", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run(ExtractionConfig(**vars(arguments)))
    except Exception as error:
        print(json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
