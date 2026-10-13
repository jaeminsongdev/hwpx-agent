#!/usr/bin/env python3
"""Bounded independent oracle for the P09-17 auto-number target fixture."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

PARAGRAPH_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
SECTION_PATH = "Contents/section0.xml"
MAX_PACKAGE_BYTES = 4 * 1024 * 1024
MAX_ENTRY_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 64
MAX_TOTAL_ENTRY_BYTES = 8 * 1024 * 1024
SCHEMA_VERSION = "hwpx-agent.p09-17-field-auto-number-target-oracle/v2"
EXPECTED_TYPES = ["PAGE", "PICTURE", "TABLE", "EQUATION"]
AUTO_ATTRIBUTES = {"num", "numType"}
FORMAT_ATTRIBUTES = {"type", "userChar", "prefixChar", "suffixChar", "supscript"}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def local_name(tag: str) -> tuple[str, str]:
    if not isinstance(tag, str):
        raise ValueError("non_element_xml_node")
    match = re.fullmatch(r"\{([^{}]+)\}([^{}]+)", tag)
    if match is None:
        raise ValueError("unqualified_element")
    return match.group(1), match.group(2)


def bounded_bytes(path: Path, maximum: int) -> bytes:
    # 해석 전에 링크를 검사하고, 크기를 제한한 단일 스냅샷만 읽는다.
    if any(item.is_symlink() or item.is_junction() for item in (path, *path.parents)):
        raise ValueError("package_not_regular_file")
    if not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("package_size_invalid")
    with path.open("rb") as handle:
        data = handle.read(maximum + 1)
    if not data or len(data) > maximum:
        raise ValueError("package_size_invalid")
    return data


def inspect(
    path: Path,
    expected_sha256: str | None,
    *,
    expected_projection: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    package = bounded_bytes(path, MAX_PACKAGE_BYTES)
    package_sha256 = sha256(package)
    if expected_sha256 is not None and package_sha256 != expected_sha256:
        raise ValueError("package_sha256_mismatch")

    # 해시를 검사한 바이트와 ZIP을 검사한 바이트가 반드시 같아야 한다.
    with zipfile.ZipFile(io.BytesIO(package), "r") as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_ENTRIES:
            raise ValueError("entry_count_invalid")
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or names.count(SECTION_PATH) != 1:
            raise ValueError("entry_identity_invalid")
        for entry in entries:
            if (
                entry.is_dir()
                or "\\" in entry.filename
                or entry.filename.startswith("/")
                or ".." in Path(entry.filename).parts
                or entry.flag_bits & 0x1
                or entry.file_size > MAX_ENTRY_BYTES
                or entry.file_size < 0
                or ":" in entry.filename
                or any(part in ("", ".", "..") for part in entry.filename.split("/"))
            ):
                raise ValueError("entry_policy_invalid")
        if sum(entry.file_size for entry in entries) > MAX_TOTAL_ENTRY_BYTES:
            raise ValueError("total_entry_size_invalid")
        section = archive.read(SECTION_PATH)

    if not section or len(section) > MAX_ENTRY_BYTES:
        raise ValueError("section_size_invalid")
    lowered = section.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise ValueError("active_xml_construct_rejected")
    root = ElementTree.fromstring(
        section,
        parser=ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True, insert_pis=True)),
    )
    if root.tag != "{http://www.hancom.co.kr/hwpml/2011/section}sec":
        raise ValueError("section_root_invalid")
    parent_by_child = {child: parent for parent in root.iter() for child in parent}
    projections: list[dict[str, object]] = []
    object_context: list[dict[str, object]] = []
    for element in root.iter():
        namespace, name = local_name(element.tag)
        if namespace != PARAGRAPH_NS or name != "autoNum":
            continue
        parent = parent_by_child.get(element)
        if parent is None or local_name(parent.tag) != (PARAGRAPH_NS, "ctrl"):
            raise ValueError("auto_number_parent_invalid")
        if set(element.attrib) != AUTO_ATTRIBUTES:
            raise ValueError("auto_number_attributes_invalid")
        children = list(element)
        if len(children) != 1 or local_name(children[0].tag) != (
            PARAGRAPH_NS,
            "autoNumFormat",
        ):
            raise ValueError("auto_number_children_invalid")
        format_element = children[0]
        if set(format_element.attrib) != FORMAT_ATTRIBUTES or list(format_element):
            raise ValueError("auto_number_format_invalid")
        if any(
            (value or "").strip()
            for value in (element.text, format_element.text, format_element.tail)
        ):
            raise ValueError("auto_number_text_invalid")
        if format_element.attrib != {
            "type": "DIGIT",
            "userChar": "",
            "prefixChar": "",
            "suffixChar": "",
            "supscript": "0",
        }:
            raise ValueError("auto_number_format_profile_mismatch")
        number_text = element.attrib["num"]
        if re.fullmatch(r"0|[1-9][0-9]{0,9}", number_text) is None:
            raise ValueError("auto_number_noncanonical")
        number = int(number_text)
        if number > 2_147_483_647:
            raise ValueError("auto_number_out_of_range")
        projections.append({"native_type": element.attrib["numType"], "number": number})
        ancestor = parent
        caption_present = False
        while ancestor is not None:
            if ancestor.tag == f"{{{PARAGRAPH_NS}}}caption":
                caption_present = True
            ancestor = parent_by_child.get(ancestor)
        object_context.append({
            "native_type": element.attrib["numType"],
            "caption_ancestor_present": caption_present,
        })

    native_types = [item["native_type"] for item in projections]
    if native_types != EXPECTED_TYPES:
        raise ValueError("field_projection_mismatch")
    if expected_projection is not None:
        if (
            not isinstance(expected_projection, list)
            or len(expected_projection) != len(EXPECTED_TYPES)
            or any(
                not isinstance(item, dict)
                or set(item) != {"native_type", "number"}
                or item.get("native_type") != kind
                or type(item.get("number")) is not int
                or not 0 <= item["number"] <= 2_147_483_647
                for item, kind in zip(expected_projection, EXPECTED_TYPES)
            )
        ):
            raise ValueError("expected_projection_invalid")
        semantic_state = "pass" if projections == expected_projection else "fail"
    else:
        semantic_state = "not_run"
    return {
        "schema_version": SCHEMA_VERSION,
        "state": semantic_state if expected_projection is not None else "structural_only",
        "structural_state": "pass",
        "semantic_state": semantic_state,
        "error_code": "semantic_projection_mismatch" if semantic_state == "fail" else None,
        "package_sha256": package_sha256,
        "package_bytes": len(package),
        "section_sha256": sha256(section),
        "section_bytes": len(section),
        "field_count": len(projections),
        "projection": projections,
        "expected_projection": expected_projection,
        "native_object_counts": {
            name: sum(element.tag == f"{{{PARAGRAPH_NS}}}{name}" for element in root.iter())
            for name in ("pic", "tbl", "equation")
        },
        "field_object_context": object_context,
        "actual_hangul": False,
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "green_rows": 0,
        "p09_complete": False,
        "product_complete": False,
        "raw_document_text_present": False,
        "user_document_scanned": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--expected-sha256", default=None)
    args = parser.parse_args()
    if args.expected_sha256 is not None and re.fullmatch(r"[0-9a-f]{64}", args.expected_sha256) is None:
        parser.error("--expected-sha256 must be lowercase SHA-256")
    try:
        result = inspect(args.package, args.expected_sha256)
    except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "state": "failed",
                    "error_code": str(error) if type(error) is ValueError else "package_inspection_failed",
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
