#!/usr/bin/env python3
"""Independent Expat/ZIP managed-value oracle. Never launches native software."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import xml.parsers.expat as expat
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
PROFILE = "hwpx-agent.native-form-package.managed-values/v2"
QUALIFICATION = "complete_package_component_only_native_execution_protection_date_external_validation_and_routing_unqualified"
CAPTURE = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx"
CAPTURE_SHA = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7"
CASES = ("actual", "five-kinds", "empty-text", "reset-defaults", "clear-selections")
TAGS = ("edit", "checkBtn", "radioBtn", "comboBox", "listBox", "radioBtn")
MATRIX_VALUES = ("新 & <\"'> 🚀\r\n\tline", "INDETERMINATE", "UNCHECKED", "b", "a", "CHECKED")
INITIAL = ("initial & 한글", "CHECKED", "CHECKED", "a", "b", "UNCHECKED")
DEFAULTS = ("caller-default", "UNCHECKED", "CHECKED", "b", "a", "UNCHECKED")
ARCHIVE, PART, TOTAL = 32*1024*1024, 2*1024*1024, 16*1024*1024
RECEIPT_KEYS = {"profile", "source_package_sha256", "output_package_sha256", "source_v1_state_sha256", "source_v2_state_sha256", "target_v2_state_sha256", "document_flow_sha256", "typed_input_plan_sha256", "package_plan_sha256", "changed_controls", "changed_sections", "managed_value_edits", "preservation_policy", "zip_header_policy", "qualification"}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def duplicate_guard(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "value_oracle_duplicate_json")
        result[key] = value
    return result


def no_links(path):
    for candidate in (path, *path.parents):
        metadata = candidate.lstat()
        require(not stat.S_ISLNK(metadata.st_mode) and not getattr(metadata, "st_file_attributes", 0) & 0x400, "value_oracle_link_rejected")


def checked_bytes(path, maximum):
    no_links(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum, "value_oracle_file_bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and len(raw) == before.st_size, "value_oracle_file_drift")
    return raw


def directory_guard(directory, root=ROOT):
    require(directory.is_absolute() and ".." not in directory.parts, "value_oracle_directory_path")
    no_links(directory)
    resolved = directory.resolve(strict=True)
    base = (root / "fixtures/target-build").resolve(strict=True)
    require(resolved.parent == base and re.fullmatch(r"p09-40-component-[A-Za-z0-9_-]+", resolved.name) and resolved.is_dir(), "value_oracle_directory_boundary")
    return resolved


def load_zip(raw):
    require(0 < len(raw) <= ARCHIVE, "value_oracle_archive_limit")
    parts = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(0 < len(entries) <= 256, "value_oracle_entry_limit")
        total, names = 0, set()
        for entry in entries:
            path = PurePosixPath(entry.filename)
            require(entry.filename and not path.is_absolute() and not any(c in ("", ".", "..") for c in entry.filename.split("/")) and "\\" not in entry.filename and ":" not in entry.filename and not entry.is_dir(), "value_oracle_zip_path")
            require(entry.filename.casefold() not in names, "value_oracle_zip_alias")
            names.add(entry.filename.casefold())
            require(not entry.flag_bits & 1 and entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), "value_oracle_zip_method")
            total += entry.file_size
            require(0 <= entry.file_size <= PART and total <= TOTAL, "value_oracle_expanded_limit")
            with archive.open(entry) as stream:
                expanded = stream.read(PART + 1)
            require(len(expanded) == entry.file_size and len(expanded) <= PART, "value_oracle_expansion_drift")
            parts.append((entry.filename, entry.compress_type, expanded))
    require(parts[0][0] == "mimetype" and parts[0][1] == zipfile.ZIP_STORED, "value_oracle_mimetype_position")
    return parts


def tag_end(raw, start):
    quote = None
    for index in range(start, len(raw)):
        byte = raw[index]
        if quote is not None:
            if byte == quote:
                quote = None
        elif byte in (34, 39):
            quote = byte
        elif byte == 62:
            return index + 1
    raise ValueError("value_oracle_unterminated_tag")


def nodes(raw):
    require(len(raw) <= PART, "value_oracle_xml_limit")
    parser = expat.ParserCreate(namespace_separator="|")
    result, stack = [], []

    def start(name, attrs):
        require(len(result) < 65536 and len(stack) < 128, "value_oracle_xml_structure_limit")
        offset = parser.CurrentByteIndex
        end = tag_end(raw, offset)
        node = {"name": name, "attrs": attrs, "start": offset, "tag_end": end, "parent": stack[-1] if stack else None,
                "empty": raw[offset:end].endswith(b"/>"), "end": None, "content_end": None, "text": []}
        result.append(node)
        stack.append(len(result)-1)

    def end(name):
        require(bool(stack), "value_oracle_xml_stack")
        node = result[stack.pop()]
        require(node["name"] == name, "value_oracle_xml_stack")
        offset = node["tag_end"] if node["empty"] else parser.CurrentByteIndex
        require(node["empty"] or raw[offset:offset+2] == b"</", "value_oracle_xml_close")
        node["content_end"] = offset
        node["end"] = offset if node["empty"] else tag_end(raw, offset)
        node["text"] = "".join(node["text"])

    def characters(value):
        if stack:
            result[stack[-1]]["text"].append(value)

    def prohibited(*_):
        raise ValueError("value_oracle_dtd_entity_rejected")

    parser.StartElementHandler, parser.EndElementHandler, parser.CharacterDataHandler = start, end, characters
    parser.StartDoctypeDeclHandler = prohibited
    parser.EntityDeclHandler = prohibited
    parser.ExternalEntityRefHandler = prohibited
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.Parse(raw, True)
    require(not stack, "value_oracle_xml_stack")
    return result


def attribute_span(raw, node, name):
    tag = raw[node["start"]:node["tag_end"]]
    found = [m for m in re.finditer(rb"([A-Za-z_:][A-Za-z0-9_.:-]*)\s*=\s*([\"'])(.*?)\2", tag, re.S) if m[1] == name.encode("ascii")]
    require(len(found) == 1 and name in node["attrs"], "value_oracle_managed_attribute")
    return node["start"]+found[0].start(3), node["start"]+found[0].end(3)


def controls(raw):
    parsed = nodes(raw)
    children_by_parent = {}
    for index, child in enumerate(parsed):
        children_by_parent.setdefault(child["parent"], []).append(index)
    recognized = {HP+"|"+tag for tag in TAGS}
    result = []
    for index, node in enumerate(parsed):
        if node["name"] not in recognized:
            continue
        kind = node["name"].split("|")[-1]
        if kind == "edit":
            child_ids = [i for i in children_by_parent.get(index, ()) if parsed[i]["name"].split("|")[-1] == "text"]
            children = [parsed[i] for i in child_ids]
            require(len(children) == 1 and children[0]["name"] == HP+"|text", "value_oracle_text_ambiguity")
            child = children[0]
            require(not children_by_parent.get(child_ids[0]), "value_oracle_nested_text")
            require(child["empty"] or b"<" not in raw[child["tag_end"]:child["content_end"]], "value_oracle_text_markup")
            start, end = child["start"], child["end"]
            head = raw[start:child["tag_end"]][:-2 if child["empty"] else -1]
            qname = re.match(rb"<([^\s/>]+)", head)
            require(qname is not None, "value_oracle_text_name")
            slot = {"kind": kind, "start": start, "end": end, "node": node, "text": child, "head": head, "qname": qname[1], "value": child["text"]}
        else:
            name = "value" if kind in ("checkBtn", "radioBtn") else "selectedValue"
            start, end = attribute_span(raw, node, name)
            value = node["attrs"][name]
            slot = {"kind": kind, "start": start, "end": end, "node": node, "value": value if name == "value" or value else None}
        require(node["start"] <= start <= end <= node["end"], "value_oracle_slot_range")
        result.append(slot)
    return result


def preserved(raw, slot):
    fields = [PROFILE.encode(), raw[slot["node"]["start"]:slot["start"]], raw[slot["end"]:slot["node"]["end"]]]
    if slot["kind"] == "edit":
        fields.extend((slot["head"], slot["qname"]))
    digest = hashlib.sha256()
    for field in fields:
        digest.update(struct.pack("<Q", len(field)))
        digest.update(field)
    return digest.hexdigest()


def escape(value):
    require(isinstance(value, str) and len(value.encode()) <= PART and all(ord(c) >= 32 or c in "\r\n\t" for c in value) and not any(c in value for c in "\ufffe\uffff"), "value_oracle_xml_value")
    for a, b in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&apos;"), ("\r", "&#13;"), ("\n", "&#10;"), ("\t", "&#9;")):
        value = value.replace(a, b)
    require(len(value.encode()) <= PART, "value_oracle_escaped_limit")
    return value.encode()


def expected_section(raw, slots, values):
    require(len(slots) == len(values), "value_oracle_control_inventory")
    edits = []
    for slot, value in zip(slots, values):
        if slot["value"] == value:
            continue
        encoded = escape(value if value is not None else "")
        if slot["kind"] == "edit":
            child = slot["text"]
            if child["empty"]:
                start, end, replacement = slot["start"], slot["end"], slot["head"]+b">"+encoded+b"</"+slot["qname"]+b">"
            else:
                start, end, replacement = child["tag_end"], child["content_end"], encoded
        else:
            start, end, replacement = slot["start"], slot["end"], encoded
        edits.append((start, end, replacement))
    output, cursor = [], 0
    for start, end, replacement in edits:
        require(cursor <= start <= end <= len(raw), "value_oracle_edit_overlap")
        output.extend((raw[cursor:start], replacement))
        cursor = end
    output.append(raw[cursor:])
    result = b"".join(output)
    require(len(result) <= PART, "value_oracle_output_part_limit")
    return result, len(edits)


def recipes(case):
    if case == "actual":
        return ("edit",), None, ("P40 값 & <한글> \" ' 🚀",)
    if case == "five-kinds":
        return TAGS, INITIAL, MATRIX_VALUES
    if case == "reset-defaults":
        return TAGS, MATRIX_VALUES, DEFAULTS
    if case == "empty-text":
        return TAGS, ("", *INITIAL[1:]), ("value & 🚀", *INITIAL[1:])
    require(case == "clear-selections", "value_oracle_case")
    return TAGS, INITIAL, (*INITIAL[:3], None, None, INITIAL[-1])


def inspect_pair(case, source, output, receipt):
    require(case in CASES and type(receipt) is dict and set(receipt) == RECEIPT_KEYS, "value_oracle_receipt_schema")
    require(receipt["profile"] == PROFILE and receipt["qualification"] == QUALIFICATION and receipt["zip_header_policy"] == "rewritten_not_byte_exact" and receipt["preservation_policy"] == "all_expanded_parts_and_non_value_gaps_byte_exact_order_compression_preserved_text_empty_expansion_declared", "value_oracle_false_promotion")
    for key in RECEIPT_KEYS:
        if key.endswith("sha256"):
            require(type(receipt[key]) is str and re.fullmatch("[a-f0-9]{64}", receipt[key]), "value_oracle_receipt_digest")
    require(receipt["source_package_sha256"] == sha(source) and receipt["output_package_sha256"] == sha(output) and source != output, "value_oracle_package_identity")
    before, after = load_zip(source), load_zip(output)
    require([(n, m) for n, m, _ in before] == [(n, m) for n, m, _ in after], "value_oracle_inventory_order_compression")
    kinds, source_values, target_values = recipes(case)
    seen, changes, sections, kept = 0, 0, 0, []
    inventory = {}
    for (name, _, raw), (_, _, actual) in zip(before, after):
        inventory[name] = {"source_sha256": sha(raw), "output_sha256": sha(actual), "source_bytes": len(raw), "output_bytes": len(actual)}
        if not re.fullmatch(r"Contents/section[0-9]+\.xml", name):
            require(raw == actual, "value_oracle_nonsection_drift")
            continue
        slots = controls(raw)
        require([s["kind"] for s in slots] == list(kinds[seen:seen+len(slots)]), "value_oracle_native_type")
        if source_values is not None:
            require([s["value"] for s in slots] == list(source_values[seen:seen+len(slots)]), "value_oracle_source_values")
        expected, count = expected_section(raw, slots, target_values[seen:seen+len(slots)])
        require(actual == expected, "value_oracle_whole_section_gaps")
        fresh = controls(actual)
        require(len(fresh) == len(slots) and [s["value"] for s in fresh] == list(target_values[seen:seen+len(slots)]), "value_oracle_target_values")
        for b, a in zip(slots, fresh):
            require(preserved(raw, b) == preserved(actual, a), "value_oracle_preserved_fingerprint")
            require(not any(key.split("|")[-1] in ("id", "instid", "instId") for key in b["node"]["attrs"]) and not any(key.split("|")[-1] in ("id", "instid", "instId") for key in a["node"]["attrs"]), "value_oracle_invented_native_id")
            kept.append(preserved(raw, b))
        changes += count
        sections += bool(count)
        seen += len(slots)
    require(seen == len(kinds), "value_oracle_control_inventory")
    for key, value in (("changed_controls", changes), ("managed_value_edits", changes), ("changed_sections", sections)):
        require(type(receipt[key]) is int and receipt[key] == value, "value_oracle_receipt_count")
    require(changes > 0 and receipt["source_v2_state_sha256"] != receipt["target_v2_state_sha256"], "value_oracle_noop")
    return {"case": case, "controls": seen, "changed_controls": changes, "changed_sections": sections, "package_parts": len(before),
            "expanded_part_inventory": inventory, "managed_preserved_sha256": kept, "complete_expected_bytes_verified": True,
            "explicit_value_recipe_verified": True, "native_session_started": False}


def inspect_bundle(directory, root=ROOT):
    directory = directory_guard(directory, root)
    raw = checked_bytes(directory / "fixture-manifest.json", 64*1024)
    manifest = json.loads(raw, object_pairs_hook=duplicate_guard)
    require(type(manifest) is dict and set(manifest) == {"schema_version", "profile", "cases"} and manifest["schema_version"] == "hwpx-agent.p09-40-managed-value-component-bundle/v1" and manifest["profile"] == PROFILE, "value_oracle_manifest_schema")
    require(type(manifest["cases"]) is list and [r.get("case") for r in manifest["cases"] if type(r) is dict] == list(CASES), "value_oracle_case_inventory")
    expected_files, results, packages = {"fixture-manifest.json"}, [], {}
    total = len(raw)
    for row in manifest["cases"]:
        require(type(row) is dict and set(row) == {"case", "source", "output", "receipt"}, "value_oracle_case_schema")
        pair = []
        for label in ("source", "output"):
            item = row[label]
            name = row["case"]+"-"+label+".hwpx"
            require(type(item) is dict and set(item) == {"path", "sha256", "bytes"} and item["path"] == name and type(item["bytes"]) is int, "value_oracle_file_schema")
            value = checked_bytes(directory / name, ARCHIVE)
            require(len(value) == item["bytes"] and sha(value) == item["sha256"], "value_oracle_artifact_identity")
            expected_files.add(name)
            total += len(value)
            require(total <= 1024*1024, "value_oracle_bundle_limit")
            pair.append(value)
        packages[row["case"]] = pair
        results.append(inspect_pair(row["case"], *pair, row["receipt"]))
    require({p.name for p in directory.iterdir()} == expected_files, "value_oracle_file_inventory")
    capture = checked_bytes(root / CAPTURE, ARCHIVE)
    require(len(capture) == 14556 and sha(capture) == CAPTURE_SHA and packages["actual"][0] == capture, "value_oracle_actual_capture_identity")
    require(packages["reset-defaults"][0] == packages["five-kinds"][1] and packages["clear-selections"][0] == packages["five-kinds"][0], "value_oracle_transition_linkage")
    return {"schema_version": "hwpx-agent.p09-40-independent-managed-value-output-oracle/v1", "manifest_sha256": sha(raw), "artifact_files": len(expected_files), "artifact_bytes": total, "cases": results,
            "whole_package_and_gap_preservation": True, "zip_header_byte_identity_claimed": False, "native_session_started": False, "public_export_qualified": False, "native_execution_qualified": False, "green_rows": 0, "p09_complete": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_bundle(args.directory)
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile, expat.ExpatError):
        print(json.dumps({"state": "fail", "error_code": "managed_value_oracle_failed"})); return 2
    print(json.dumps({"state": "pass", "cases": len(result["cases"]), "artifact_files": result["artifact_files"], "oracle_sha256": sha(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()), "native_session_started": False})); return 0


if __name__ == "__main__":
    raise SystemExit(main())
