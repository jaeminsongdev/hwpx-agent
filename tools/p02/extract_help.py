#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import unicodedata
import uuid

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as error:
    print(f"required dependency missing: {error}", file=sys.stderr)
    raise SystemExit(2) from error

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "protocol" / "json-schema" / "source-record-v1.schema.json"
EXTRACTOR_ID = "html-help-extractor"
EXTRACTOR_VERSION = "0.1.0"
MAX_INPUT_BYTES = 32 * 1024 * 1024
MAX_CAPTURED_TEXT = 1_000_000
MAX_RECORDS = 10_000
OUTPUT_RELATIVE = re.compile(r"^[A-Za-z0-9._/-]+$")
VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class ExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractionConfig:
    source_lock: Path
    source_id: str
    input_path: Path
    output_root: Path
    output_relative: str
    record_kind: str = "help"
    product: str = "hancom_hangul"
    target_profile_id: str | None = None
    minimum_version: str | None = None
    maximum_version: str | None = None
    locale: str = "ko-KR"
    support_scope: str = "documentation_only"


@dataclass(frozen=True)
class Heading:
    tag: str
    text: str
    anchor: str | None
    ordinal: int
    line: int
    column: int


class HeadingParser(HTMLParser):
    CAPTURE_TAGS = {"title", "h1", "h2", "h3", "h4", "h5", "h6"}
    SKIP_TAGS = {"script", "style", "template", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[Heading] = []
        self._capture_tag: str | None = None
        self._capture_anchor: str | None = None
        self._capture_position: tuple[int, int] | None = None
        self._capture_text: list[str] = []
        self._skip_depth = 0
        self._captured_characters = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth or tag not in self.CAPTURE_TAGS:
            return
        if self._capture_tag is not None:
            raise ExtractionError("nested title/heading tags are unsupported")
        attributes = {name.lower(): value for name, value in attrs if value is not None}
        self._capture_tag = tag
        self._capture_anchor = attributes.get("id") or attributes.get("name")
        self._capture_position = self.getpos()
        self._capture_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth or tag != self._capture_tag:
            return
        text = normalize_text("".join(self._capture_text))
        if text:
            if len(self.headings) >= MAX_RECORDS:
                raise ExtractionError(f"record limit exceeded: {MAX_RECORDS}")
            if self._capture_position is None:
                raise ExtractionError("heading source position is unavailable")
            self.headings.append(
                Heading(
                    tag=tag,
                    text=text,
                    anchor=normalize_text(self._capture_anchor)
                    if self._capture_anchor
                    else None,
                    ordinal=len(self.headings),
                    line=self._capture_position[0],
                    column=self._capture_position[1],
                )
            )
        self._capture_tag = None
        self._capture_anchor = None
        self._capture_position = None
        self._capture_text = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth or self._capture_tag is None:
            return
        self._captured_characters += len(data)
        if self._captured_characters > MAX_CAPTURED_TEXT:
            raise ExtractionError(f"captured text limit exceeded: {MAX_CAPTURED_TEXT}")
        self._capture_text.append(data)


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def is_link_like(path: Path, metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def read_regular_file(path: Path, maximum_bytes: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise ExtractionError(f"cannot stat input: {path}: {error}") from error
    if is_link_like(path, before) or not stat.S_ISREG(before.st_mode):
        raise ExtractionError(f"input must be a regular non-link file: {path}")
    if before.st_size > maximum_bytes:
        raise ExtractionError(f"input exceeds {maximum_bytes} bytes: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ExtractionError(f"cannot open input without following links: {path}: {error}") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino) != (
            opened.st_dev,
            opened.st_ino,
        ):
            raise ExtractionError(f"input identity changed while opening: {path}")
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            content = stream.read(maximum_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > maximum_bytes:
        raise ExtractionError(f"input exceeds {maximum_bytes} bytes: {path}")
    try:
        after = path.lstat()
    except OSError as error:
        raise ExtractionError(f"cannot restat input: {path}: {error}") from error
    if is_link_like(path, after) or (opened.st_dev, opened.st_ino) != (
        after.st_dev,
        after.st_ino,
    ):
        raise ExtractionError(f"input identity changed while reading: {path}")
    if len(content) != opened.st_size or opened.st_size != after.st_size:
        raise ExtractionError(f"input size changed while reading: {path}")
    return content


def decode_html(content: bytes) -> str:
    if b"\x00" in content:
        raise ExtractionError("HTML input contains NUL bytes")
    prefix = content[:8192].decode("ascii", errors="ignore")
    declared = re.search(r"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)", prefix, re.IGNORECASE)
    candidates: list[str] = []
    if declared:
        normalized = declared.group(1).lower().replace("_", "-")
        aliases = {
            "utf-8": "utf-8-sig",
            "utf8": "utf-8-sig",
            "cp949": "cp949",
            "euc-kr": "cp949",
            "ks-c-5601-1987": "cp949",
        }
        if normalized not in aliases:
            raise ExtractionError(f"unsupported declared HTML encoding: {normalized}")
        candidates.append(aliases[normalized])
    candidates.extend(encoding for encoding in ("utf-8-sig", "cp949") if encoding not in candidates)
    for encoding in candidates:
        try:
            return content.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            continue
    raise ExtractionError("HTML input is neither strict UTF-8 nor CP949")


def load_source_entry(source_lock_path: Path, source_id: str) -> tuple[str, dict]:
    content = read_regular_file(source_lock_path, 8 * 1024 * 1024)
    try:
        source_lock = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"invalid UTF-8 source lock: {error}") from error
    if source_lock.get("schema_version") != "hwpx-agent.source-lock/v2":
        raise ExtractionError("unsupported source-lock schema_version")
    source_lock_id = source_lock.get("source_lock_id")
    if not isinstance(source_lock_id, str):
        raise ExtractionError("source lock has no source_lock_id")
    sources = source_lock.get("sources")
    if not isinstance(sources, list) or not all(isinstance(entry, dict) for entry in sources):
        raise ExtractionError("source lock sources must be an array of objects")
    matches = [entry for entry in sources if entry.get("source_id") == source_id]
    if len(matches) != 1:
        raise ExtractionError(f"source_id must match exactly one lock entry: {source_id}")
    entry = matches[0]
    if entry.get("kind") != "web_help":
        raise ExtractionError(f"source kind is not web_help: {entry.get('kind')}")
    if entry.get("license_state") not in {"public_reference", "restricted"}:
        raise ExtractionError(f"source license_state is not admitted: {entry.get('license_state')}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
        raise ExtractionError("source lock SHA-256 is malformed")
    return source_lock_id, entry


def parse_headings(content: bytes) -> list[Heading]:
    parser = HeadingParser()
    try:
        parser.feed(decode_html(content))
        parser.close()
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError(f"HTML parser failed: {error}") from error
    if parser._capture_tag is not None:  # fail closed on a truncated heading
        raise ExtractionError(f"unclosed capture tag: {parser._capture_tag}")
    if not parser.headings:
        raise ExtractionError("HTML contains no title or heading records")
    return parser.headings


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-._")
    if len(normalized) < 3:
        normalized = f"source-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return normalized[:160]


def build_records(config: ExtractionConfig, source_lock_id: str, entry: dict, content: bytes) -> list[dict]:
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != entry["sha256"]:
        raise ExtractionError(
            f"source SHA-256 mismatch: expected {entry['sha256']}, actual {actual_sha256}"
        )
    if config.record_kind not in {"help", "webhwp"}:
        raise ExtractionError(f"unsupported help record kind: {config.record_kind}")
    if config.record_kind == "webhwp" and config.product != "webhwp":
        raise ExtractionError("webhwp records require product=webhwp")
    for name, version in (
        ("minimum_version", config.minimum_version),
        ("maximum_version", config.maximum_version),
    ):
        if version is not None and not VERSION.fullmatch(version):
            raise ExtractionError(f"{name} is not a supported numeric version")
    if config.minimum_version is not None and config.maximum_version is not None:
        minimum = tuple(int(part) for part in config.minimum_version.split("."))
        maximum = tuple(int(part) for part in config.maximum_version.split("."))
        width = max(len(minimum), len(maximum))
        if minimum + (0,) * (width - len(minimum)) > maximum + (0,) * (
            width - len(maximum)
        ):
            raise ExtractionError("minimum_version is greater than maximum_version")
    if config.support_scope == "current_pc_candidate" and (
        config.target_profile_id is None
        or config.minimum_version is None
        or config.minimum_version != config.maximum_version
    ):
        raise ExtractionError(
            "current_pc_candidate requires a target profile and one exact version"
        )
    headings = parse_headings(content)
    source_slug = slug(config.source_id)
    records = []
    for heading in headings:
        locator = (
            {"kind": "anchor", "value": heading.anchor, "section": heading.tag}
            if heading.anchor
            else {
                "kind": "section",
                "value": f"{heading.tag}@L{heading.line}:C{heading.column}",
            }
        )
        records.append(
            {
                "schema_version": "hwpx-agent.source-record/v1",
                "record_id": f"{source_slug}:help:{heading.ordinal:06d}",
                "source_lock_id": source_lock_id,
                "source_id": config.source_id,
                "source_sha256": actual_sha256,
                "source_kind": config.record_kind,
                "locator": locator,
                "original_name": heading.text,
                "description_ko": None,
                "parameters": [],
                "availability": {
                    "product": config.product,
                    "target_profile_id": config.target_profile_id,
                    "minimum_version": config.minimum_version,
                    "maximum_version": config.maximum_version,
                    "locales": [config.locale],
                    "support_scope": config.support_scope,
                },
                "extraction": {
                    "extractor_id": EXTRACTOR_ID,
                    "extractor_version": EXTRACTOR_VERSION,
                    "record_ordinal": heading.ordinal,
                },
            }
        )
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    violations = [
        f"record {index}: {violation.message}"
        for index, record in enumerate(records)
        for violation in validator.iter_errors(record)
    ]
    if violations:
        raise ExtractionError("generated SourceRecord validation failed: " + "; ".join(violations))
    return records


def serialize_records(records: list[dict]) -> bytes:
    return (json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def resolve_output(root_value: Path, relative_value: str) -> Path:
    if "\\" in relative_value or not OUTPUT_RELATIVE.fullmatch(relative_value):
        raise ExtractionError("output-relative contains unsupported characters")
    relative = PurePosixPath(relative_value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ExtractionError("output-relative must be a normal repository-style relative path")
    for part in relative.parts:
        if part.endswith(".") or part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
            raise ExtractionError(f"output-relative contains a reserved path component: {part}")
    root = root_value.absolute()
    try:
        root_metadata = root.lstat()
    except OSError as error:
        raise ExtractionError(f"cannot stat output root: {error}") from error
    if is_link_like(root, root_metadata) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ExtractionError("output root must be an existing non-link directory")
    output = root.joinpath(*relative.parts)
    parent = output.parent
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as error:
            raise ExtractionError(f"output parent must already exist: {current}: {error}") from error
        if is_link_like(current, metadata) or not stat.S_ISDIR(metadata.st_mode):
            raise ExtractionError(f"output parent is not a normal directory: {current}")
    if parent != current:
        raise ExtractionError("output parent resolution failed")
    return output


def publish_no_overwrite(output: Path, content: bytes) -> None:
    staging = output.parent / f".{output.name}.{uuid.uuid4().hex}.staging"
    descriptor: int | None = None
    try:
        descriptor = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(staging, output)
    except FileExistsError as error:
        raise ExtractionError(f"output or staging path already exists: {output}") from error
    except OSError as error:
        raise ExtractionError(f"atomic no-overwrite publication failed: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            staging.unlink(missing_ok=True)
        except OSError:
            pass


def run(config: ExtractionConfig) -> dict:
    source_lock_id, entry = load_source_entry(config.source_lock, config.source_id)
    if entry["license_state"] == "restricted" and os.path.normcase(
        str(config.output_root.absolute())
    ) != os.path.normcase(str((ROOT / "implementation/p02/evidence").absolute())):
        raise ExtractionError("restricted sources may publish only to implementation/p02/evidence")
    content = read_regular_file(config.input_path, MAX_INPUT_BYTES)
    records = build_records(config, source_lock_id, entry, content)
    payload = serialize_records(records)
    if read_regular_file(config.input_path, MAX_INPUT_BYTES) != content:
        raise ExtractionError("source changed during extraction")
    output = resolve_output(config.output_root, config.output_relative)
    publish_no_overwrite(output, payload)
    return {
        "schema_version": "hwpx-agent.help-extraction-receipt/v1",
        "source_lock_id": source_lock_id,
        "source_id": config.source_id,
        "source_sha256": entry["sha256"],
        "license_state": entry["license_state"],
        "record_count": len(records),
        "output_relative": config.output_relative,
        "output_sha256": hashlib.sha256(payload).hexdigest(),
        "source_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    parser.add_argument("--record-kind", choices=("help", "webhwp"), default="help")
    parser.add_argument("--product", choices=("hancom_hangul", "webhwp"), default="hancom_hangul")
    parser.add_argument("--target-profile-id")
    parser.add_argument("--minimum-version")
    parser.add_argument("--maximum-version")
    parser.add_argument("--locale", default="ko-KR")
    parser.add_argument(
        "--support-scope",
        choices=("documentation_only", "current_pc_candidate"),
        default="documentation_only",
    )
    arguments = parser.parse_args()
    config = ExtractionConfig(
        source_lock=arguments.source_lock,
        source_id=arguments.source_id,
        input_path=arguments.input,
        output_root=arguments.output_root,
        output_relative=arguments.output_relative,
        record_kind=arguments.record_kind,
        product=arguments.product,
        target_profile_id=arguments.target_profile_id,
        minimum_version=arguments.minimum_version,
        maximum_version=arguments.maximum_version,
        locale=arguments.locale,
        support_scope=arguments.support_scope,
    )
    try:
        receipt = run(config)
    except ExtractionError as error:
        print(json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
