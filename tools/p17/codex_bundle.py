"""Deterministic P17 Codex bundle core composition and validation."""
from __future__ import annotations

import io
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
from typing import Any, Mapping
import zipfile


ROOT = Path(__file__).resolve().parents[2]
P16_TOOLS = ROOT / "tools/p16"
if str(P16_TOOLS) not in sys.path:
    sys.path.insert(0, str(P16_TOOLS))

import skills_package as skills  # noqa: E402
import universal_package as universal  # noqa: E402


ARTIFACT_ROOT = ROOT / "artifacts/p17/packages"
AGENT_FILES = ("agents/hancom-document-engineer.md",)
COMMAND_SKILLS = {
    "commands/create.md": "create-hancom-document",
    "commands/edit.md": "edit-hancom-document",
    "commands/exam.md": "compose-math-exam",
    "commands/resume.md": "resume-hancom-project",
    "commands/validate.md": "validate-export-hancom",
}
CODEX_FILES = AGENT_FILES + tuple(COMMAND_SKILLS)
TEXT_LIMIT_BYTES = 16 * 1024
ARCHIVE_LIMIT_BYTES = 4 * 1024 * 1024
FORBIDDEN = (
    "[TODO:",
    "Authorization: Bearer",
    "HAction.",
    "<hp:",
    "<hs:",
    "C:\\",
    "D:\\",
)


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction()) if callable(is_junction) else False


def read_codex_entries(root: Path = ROOT) -> tuple[dict[str, bytes], list[str]]:
    entries: dict[str, bytes] = {}
    errors: list[str] = []
    for relative in CODEX_FILES:
        path = root / relative
        if _is_link_like(path) or not path.is_file():
            errors.append(f"source.path:{relative}")
            continue
        try:
            entries[relative] = path.read_bytes()
        except OSError:
            errors.append(f"source.read:{relative}")
    errors.extend(validate_codex_entries(entries))
    return entries, sorted(set(errors))


def validate_codex_entries(entries: Mapping[str, bytes]) -> list[str]:
    errors: list[str] = []
    if set(entries) != set(CODEX_FILES):
        errors.append("source.entries")
    for relative, value in entries.items():
        if not 1 <= len(value) <= TEXT_LIMIT_BYTES:
            errors.append(f"source.bytes:{relative}")
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"source.utf8:{relative}")
            continue
        if "\x00" in text or "\r" in text:
            errors.append(f"source.encoding:{relative}")
        if any(marker.casefold() in text.casefold() for marker in FORBIDDEN):
            errors.append(f"source.forbidden:{relative}")
        if relative in AGENT_FILES:
            fields, body, frontmatter_errors = skills.parse_frontmatter(text)
            errors.extend(f"agent.{error}" for error in frontmatter_errors)
            if (
                fields is None
                or fields.get("name") != "hancom-document-engineer"
                or not 40 <= len(fields.get("description", "")) <= 360
                or len(body.strip()) < 200
            ):
                errors.append("agent.contract")
        if relative in COMMAND_SKILLS:
            expected = COMMAND_SKILLS[relative]
            if not text.startswith("# Command\n\n") or f"Use the {expected} skill." not in text:
                errors.append(f"command.contract:{relative}")
    return sorted(set(errors))


def compose_entries() -> tuple[dict[str, bytes], list[str]]:
    base, base_errors = universal.read_base_entries()
    skill_entries, skill_errors = skills.read_component_entries()
    codex_entries, codex_errors = read_codex_entries()
    composed, compose_errors = skills.compose_plugin_entries(base, skill_entries)
    errors = base_errors + skill_errors + codex_errors + compose_errors
    if errors:
        return {}, sorted(set(errors))
    composed.update(codex_entries)
    errors.extend(validate_composed_entries(composed))
    return composed, sorted(set(errors))


def validate_composed_entries(entries: Mapping[str, bytes]) -> list[str]:
    errors: list[str] = []
    expected = set(universal.BASE_ENTRIES) | set(skills.expected_entry_names()) | set(CODEX_FILES)
    if set(entries) != expected:
        errors.append("bundle.entries")
    manifest_bytes = entries.get(".codex-plugin/plugin.json")
    manifest, manifest_errors = (
        universal.load_json_bytes(manifest_bytes, "manifest")
        if isinstance(manifest_bytes, bytes)
        else (None, ["manifest.missing"])
    )
    errors.extend(manifest_errors)
    if manifest is not None:
        if manifest.get("skills") != "./skills/":
            errors.append("manifest.skills")
        if "apps" in manifest or "mcpServers" in manifest:
            errors.append("manifest.unqualified_connection")
        base_manifest = dict(manifest)
        base_manifest.pop("skills", None)
        errors.extend(universal.validate_manifest(base_manifest))
    codex_subset = {name: entries[name] for name in CODEX_FILES if name in entries}
    errors.extend(validate_codex_entries(codex_subset))
    serialized = b"\n".join(entries.values())
    if any(marker.casefold().encode() in serialized.lower() for marker in FORBIDDEN):
        errors.append("bundle.forbidden")
    if sum(len(value) for value in entries.values()) > ARCHIVE_LIMIT_BYTES:
        errors.append("bundle.bytes")
    return sorted(set(errors))


def deterministic_zip_bytes(entries: Mapping[str, bytes]) -> bytes:
    return universal.deterministic_zip_bytes(entries)


def validate_archive(path: Path) -> list[str]:
    if _is_link_like(path) or not path.is_file():
        return ["archive.path"]
    try:
        archive_bytes = path.read_bytes()
    except OSError:
        return ["archive.read"]
    errors: list[str] = []
    if not 1 <= len(archive_bytes) <= ARCHIVE_LIMIT_BYTES:
        errors.append("archive.bytes")
    entries: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), mode="r") as archive:
            infos = archive.infolist()
            if len(infos) != len({info.filename for info in infos}):
                errors.append("archive.duplicate_entry")
            if sum(info.file_size for info in infos) > ARCHIVE_LIMIT_BYTES:
                errors.append("archive.expanded_bytes")
            for info in infos:
                candidate = PurePosixPath(info.filename)
                if (
                    candidate.is_absolute()
                    or ".." in candidate.parts
                    or "\\" in info.filename
                    or ":" in info.filename
                    or info.is_dir()
                ):
                    errors.append("archive.entry_path")
                    continue
                if info.file_size > ARCHIVE_LIMIT_BYTES:
                    errors.append("archive.entry_bytes")
                    continue
                if (
                    info.compress_type != zipfile.ZIP_STORED
                    or info.date_time != (1980, 1, 1, 0, 0, 0)
                    or info.create_system != 3
                    or (info.external_attr >> 16) != 0o100644
                    or info.flag_bits & 0x1
                ):
                    errors.append("archive.metadata")
                entries[info.filename] = archive.read(info)
    except (OSError, RuntimeError, zipfile.BadZipFile):
        return sorted(set(errors + ["archive.format"]))
    expected, compose_errors = compose_entries()
    errors.extend(compose_errors)
    if entries != expected:
        errors.append("archive.content")
    if archive_bytes != deterministic_zip_bytes(entries):
        errors.append("archive.determinism")
    return sorted(set(errors))


def publish_archive(output: Path) -> tuple[dict[str, Any] | None, list[str]]:
    entries, errors = compose_entries()
    resolved = output.resolve()
    if output.suffix.casefold() != ".zip":
        errors.append("output.extension")
    if output.exists():
        errors.append("output.exists")
    if _is_link_like(output.parent):
        errors.append("output.link")
    if resolved.is_relative_to(ROOT.resolve()) and not resolved.is_relative_to(ARTIFACT_ROOT.resolve()):
        errors.append("output.tracked_tree")
    if errors:
        return None, sorted(set(errors))
    archive_bytes = deterministic_zip_bytes(entries)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
        )
    except OSError:
        return None, ["output.publish"]
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(archive_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary_name, output)
    except FileExistsError:
        return None, ["output.exists"]
    except OSError:
        return None, ["output.publish"]
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return {
        "archive": str(output.resolve()),
        "bytes": len(archive_bytes),
        "entries": len(entries),
        "sha256": universal.sha256_bytes(archive_bytes),
        "kind": "codex_bundle_core_unregistered",
    }, []
