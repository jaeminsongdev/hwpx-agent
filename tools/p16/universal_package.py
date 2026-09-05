from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import tempfile
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import UUID
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "plugins/hwpx-agent"
ARTIFACT_ROOT = ROOT / "artifacts/p16/packages"
REGISTRATION_ROOT = ROOT / "artifacts/p16/registrations"
OFFICIAL_SOURCE_LOCK_SHA256 = "0757dd53d1f1400383f9534df8edd7b491b28af1f310d40beb090b5b8c30072b"
BASE_ENTRIES = (
    ".codex-plugin/plugin.json",
    "README.md",
    "assets/icon.png",
    "assets/logo.png",
)
TEXT_LIMITS = {
    ".codex-plugin/plugin.json": 16 * 1024,
    "README.md": 32 * 1024,
}
ASSET_LIMIT_BYTES = 1024 * 1024
PACKAGE_LIMIT_BYTES = 3 * 1024 * 1024
REGISTERED_APP_ID = re.compile(r"^plugin_asdk_app_[A-Za-z0-9_-]{8,192}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_PLACEHOLDERS = (
    "[TODO:",
    "YOUR_ORG",
    "example.com",
    "REPLACE_AFTER",
    "PROPRIETARY-OR-TBD",
)
FORBIDDEN_ID_MARKERS = ("REPLACE", "EXAMPLE", "FAKE", "TEST", "TODO")
FORBIDDEN_MANIFEST_TOKENS = (
    "HAction.",
    "HWPFrame.",
    "Authorization: Bearer",
    "C:\\",
    "D:\\",
)


class DuplicateKeyError(ValueError):
    pass


@dataclass(frozen=True)
class RegistrationBinding:
    evidence_id: str
    registered_app_id: str
    endpoint_url: str


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction()) if callable(is_junction) else False


def _has_link_component(path: Path) -> bool:
    current = path.absolute()
    while True:
        if current.exists() and _is_link_like(current):
            return True
        if current.parent == current:
            return False
        current = current.parent


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def load_json_bytes(value: bytes, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return None, [f"{label}.utf8"]
    try:
        parsed = json.loads(text, object_pairs_hook=_object_without_duplicates)
    except DuplicateKeyError:
        return None, [f"{label}.duplicate_key"]
    except json.JSONDecodeError:
        return None, [f"{label}.json"]
    if not isinstance(parsed, dict):
        return None, [f"{label}.object"]
    return parsed, []


def _is_bounded_string(value: Any, minimum: int, maximum: int) -> bool:
    return isinstance(value, str) and minimum <= len(value) <= maximum and value == value.strip()


def _validate_relative_asset_path(raw: Any, expected: str) -> bool:
    if not isinstance(raw, str) or not raw.startswith("./") or "\\" in raw:
        return False
    candidate = PurePosixPath(raw[2:])
    return candidate.as_posix() == expected and not candidate.is_absolute() and ".." not in candidate.parts


def png_dimensions(value: bytes) -> tuple[int, int] | None:
    if len(value) < 24 or value[:8] != b"\x89PNG\r\n\x1a\n" or value[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", value[16:24])
    if width <= 0 or height <= 0:
        return None
    return width, height


def validate_manifest(manifest: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest.object"]
    allowed = {"name", "version", "description", "author", "keywords", "interface"}
    if set(manifest) != allowed:
        errors.append("manifest.fields")
    if manifest.get("name") != "hwpx-agent":
        errors.append("manifest.name")
    if manifest.get("version") != "0.1.0":
        errors.append("manifest.version")
    if not _is_bounded_string(manifest.get("description"), 20, 180):
        errors.append("manifest.description")

    author = manifest.get("author")
    if not isinstance(author, dict) or set(author) != {"name"} or not _is_bounded_string(author.get("name"), 3, 80):
        errors.append("manifest.author")

    keywords = manifest.get("keywords")
    if (
        not isinstance(keywords, list)
        or keywords != ["hwpx", "hancom", "document", "korean"]
        or len(set(keywords)) != len(keywords)
    ):
        errors.append("manifest.keywords")

    interface = manifest.get("interface")
    required_interface = {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "defaultPrompt",
        "brandColor",
        "composerIcon",
        "logo",
        "screenshots",
    }
    if not isinstance(interface, dict):
        return errors + ["manifest.interface"]
    if set(interface) != required_interface:
        errors.append("manifest.interface.fields")
    for key, limits in {
        "displayName": (3, 40),
        "shortDescription": (10, 80),
        "longDescription": (30, 240),
        "developerName": (3, 80),
    }.items():
        if not _is_bounded_string(interface.get(key), *limits):
            errors.append(f"manifest.interface.{key}")
    if interface.get("category") != "Productivity":
        errors.append("manifest.interface.category")
    if interface.get("capabilities") != ["Interactive", "Read", "Write"]:
        errors.append("manifest.interface.capabilities")
    prompts = interface.get("defaultPrompt")
    if (
        not isinstance(prompts, list)
        or not 1 <= len(prompts) <= 3
        or any(not _is_bounded_string(prompt, 8, 128) for prompt in prompts)
        or len(set(prompts)) != len(prompts)
    ):
        errors.append("manifest.interface.defaultPrompt")
    if interface.get("brandColor") != "#111827":
        errors.append("manifest.interface.brandColor")
    if not _validate_relative_asset_path(interface.get("composerIcon"), "assets/icon.png"):
        errors.append("manifest.interface.composerIcon")
    if not _validate_relative_asset_path(interface.get("logo"), "assets/logo.png"):
        errors.append("manifest.interface.logo")
    if interface.get("screenshots") != []:
        errors.append("manifest.interface.screenshots")

    serialized = json.dumps(manifest, ensure_ascii=False)
    if any(marker.casefold() in serialized.casefold() for marker in FORBIDDEN_PLACEHOLDERS):
        errors.append("manifest.placeholder")
    if any(token.casefold() in serialized.casefold() for token in FORBIDDEN_MANIFEST_TOKENS):
        errors.append("manifest.private_token")
    return sorted(set(errors))


def validate_base_entries(entries: Mapping[str, bytes]) -> list[str]:
    errors: list[str] = []
    if set(entries) != set(BASE_ENTRIES):
        errors.append("package.entries")
    total = sum(len(value) for value in entries.values())
    if total <= 0 or total > PACKAGE_LIMIT_BYTES:
        errors.append("package.total_bytes")

    for name, limit in TEXT_LIMITS.items():
        value = entries.get(name)
        if not isinstance(value, bytes):
            errors.append(f"{name}.missing")
            continue
        if not 1 <= len(value) <= limit:
            errors.append(f"{name}.bytes")
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{name}.utf8")
            continue
        if "\x00" in text:
            errors.append(f"{name}.nul")
        if "\r" in text:
            errors.append(f"{name}.line_endings")
        if any(marker.casefold() in text.casefold() for marker in FORBIDDEN_PLACEHOLDERS):
            errors.append(f"{name}.placeholder")

    manifest_bytes = entries.get(".codex-plugin/plugin.json")
    if isinstance(manifest_bytes, bytes):
        manifest, manifest_errors = load_json_bytes(manifest_bytes, "manifest")
        errors.extend(manifest_errors)
        if manifest is not None:
            errors.extend(validate_manifest(manifest))

    for name, expected_dimensions in {
        "assets/icon.png": (128, 128),
        "assets/logo.png": (512, 512),
    }.items():
        value = entries.get(name)
        if not isinstance(value, bytes):
            errors.append(f"{name}.missing")
            continue
        if not 1 <= len(value) <= ASSET_LIMIT_BYTES:
            errors.append(f"{name}.bytes")
        if png_dimensions(value) != expected_dimensions:
            errors.append(f"{name}.dimensions")
    return sorted(set(errors))


def read_base_entries(package_root: Path = PACKAGE_ROOT) -> tuple[dict[str, bytes], list[str]]:
    errors: list[str] = []
    entries: dict[str, bytes] = {}
    if not package_root.is_dir() or _has_link_component(package_root):
        return entries, ["package.root"]
    discovered: set[str] = set()
    for path in package_root.rglob("*"):
        relative = path.relative_to(package_root).as_posix()
        if _is_link_like(path):
            errors.append(f"package.symlink:{relative}")
            continue
        if path.is_file():
            discovered.add(relative)
            try:
                entries[relative] = path.read_bytes()
            except OSError:
                errors.append(f"package.read:{relative}")
    if discovered != set(BASE_ENTRIES):
        errors.append("package.entries")
    errors.extend(validate_base_entries(entries))
    return entries, sorted(set(errors))


def base_snapshot(entries: Mapping[str, bytes]) -> list[dict[str, Any]]:
    return [
        {"path": name, "bytes": len(entries[name]), "sha256": sha256_bytes(entries[name])}
        for name in sorted(entries)
    ]


def validate_registration_receipt(receipt: Any) -> tuple[RegistrationBinding | None, list[str]]:
    errors: list[str] = []
    required = {
        "schema_version",
        "evidence_id",
        "evidence_kind",
        "captured_at",
        "registered_app_id",
        "endpoint_url",
        "official_source_lock_sha256",
        "user_confirmed",
    }
    if not isinstance(receipt, dict):
        return None, ["receipt.object"]
    if set(receipt) != required:
        errors.append("receipt.fields")
    if receipt.get("schema_version") != "hwpx-agent.p16-registration-receipt/v1":
        errors.append("receipt.schema_version")
    if receipt.get("evidence_kind") != "actual_developer_mode_registration":
        errors.append("receipt.evidence_kind")
    if receipt.get("user_confirmed") is not True:
        errors.append("receipt.user_confirmed")

    evidence_id = receipt.get("evidence_id")
    try:
        parsed_id = UUID(evidence_id) if isinstance(evidence_id, str) else None
    except ValueError:
        parsed_id = None
    if parsed_id is None or str(parsed_id) != evidence_id or parsed_id.version != 4:
        errors.append("receipt.evidence_id")

    captured_at = receipt.get("captured_at")
    try:
        captured = datetime.fromisoformat(captured_at.replace("Z", "+00:00")) if isinstance(captured_at, str) else None
    except ValueError:
        captured = None
    if (
        captured is None
        or not isinstance(captured_at, str)
        or not captured_at.endswith("Z")
        or captured.tzinfo is None
        or captured.utcoffset() != timezone.utc.utcoffset(captured)
    ):
        errors.append("receipt.captured_at")

    registered_app_id = receipt.get("registered_app_id")
    if not isinstance(registered_app_id, str) or REGISTERED_APP_ID.fullmatch(registered_app_id) is None:
        errors.append("receipt.registered_app_id")
    elif any(marker in registered_app_id.upper() for marker in FORBIDDEN_ID_MARKERS):
        errors.append("receipt.registered_app_id_placeholder")

    endpoint_url = receipt.get("endpoint_url")
    parsed_url = urlparse(endpoint_url) if isinstance(endpoint_url, str) else None
    if (
        parsed_url is None
        or parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.path != "/mcp"
        or parsed_url.params
        or parsed_url.query
        or parsed_url.fragment
        or len(endpoint_url) > 512
    ):
        errors.append("receipt.endpoint_url")

    source_lock = receipt.get("official_source_lock_sha256")
    if source_lock != OFFICIAL_SOURCE_LOCK_SHA256 or not isinstance(source_lock, str) or SHA256.fullmatch(source_lock) is None:
        errors.append("receipt.official_source_lock_sha256")

    if errors:
        return None, sorted(set(errors))
    return RegistrationBinding(evidence_id, registered_app_id, endpoint_url), []


def validate_registration_binding(binding: RegistrationBinding) -> list[str]:
    errors: list[str] = []
    try:
        evidence_id = UUID(binding.evidence_id) if isinstance(binding.evidence_id, str) else None
    except ValueError:
        evidence_id = None
    if evidence_id is None or str(evidence_id) != binding.evidence_id or evidence_id.version != 4:
        errors.append("binding.evidence_id")
    if not isinstance(binding.registered_app_id, str) or REGISTERED_APP_ID.fullmatch(binding.registered_app_id) is None:
        errors.append("binding.registered_app_id")
    elif any(marker in binding.registered_app_id.upper() for marker in FORBIDDEN_ID_MARKERS):
        errors.append("binding.registered_app_id_placeholder")
    parsed_url = urlparse(binding.endpoint_url) if isinstance(binding.endpoint_url, str) else None
    if (
        parsed_url is None
        or parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.path != "/mcp"
        or parsed_url.params
        or parsed_url.query
        or parsed_url.fragment
        or not isinstance(binding.endpoint_url, str)
        or len(binding.endpoint_url) > 512
    ):
        errors.append("binding.endpoint_url")
    return sorted(set(errors))


def load_registration_receipt(path: Path) -> tuple[RegistrationBinding | None, list[str]]:
    resolved = path.resolve()
    if (
        not resolved.is_relative_to(REGISTRATION_ROOT.resolve())
        or _has_link_component(path)
        or not path.is_file()
    ):
        return None, ["receipt.path"]
    try:
        raw = path.read_bytes()
    except OSError:
        return None, ["receipt.read"]
    if not 1 <= len(raw) <= 16 * 1024:
        return None, ["receipt.bytes"]
    receipt, errors = load_json_bytes(raw, "receipt")
    if errors or receipt is None:
        return None, errors
    return validate_registration_receipt(receipt)


def compose_entries(
    base_entries: Mapping[str, bytes],
    binding: RegistrationBinding | None = None,
) -> tuple[dict[str, bytes], list[str]]:
    errors = validate_base_entries(base_entries)
    if errors:
        return {}, errors
    composed = dict(base_entries)
    if binding is None:
        return composed, []
    binding_errors = validate_registration_binding(binding)
    if binding_errors:
        return {}, binding_errors
    manifest, parse_errors = load_json_bytes(composed[".codex-plugin/plugin.json"], "manifest")
    if parse_errors or manifest is None:
        return {}, parse_errors
    manifest["apps"] = "./.app.json"
    composed[".codex-plugin/plugin.json"] = canonical_json_bytes(manifest)
    composed[".app.json"] = canonical_json_bytes(
        {
            "apps": {
                "hwpx-agent": {
                    "category": "Productivity",
                    "id": binding.registered_app_id,
                }
            }
        }
    )
    return composed, []


def deterministic_zip_bytes(entries: Mapping[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits = 0
            archive.writestr(info, entries[name])
    return output.getvalue()


def validate_archive(path: Path, *, registered: bool) -> list[str]:
    errors: list[str] = []
    if _has_link_component(path) or not path.is_file():
        return ["archive.path"]
    try:
        archive_bytes = path.read_bytes()
    except OSError:
        return ["archive.read"]
    if not 1 <= len(archive_bytes) <= PACKAGE_LIMIT_BYTES + 128 * 1024:
        errors.append("archive.bytes")
    entries: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), mode="r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                errors.append("archive.duplicate_entry")
            expected_names = set(BASE_ENTRIES) | ({".app.json"} if registered else set())
            if set(names) != expected_names:
                errors.append("archive.entries")
            for info in infos:
                candidate = PurePosixPath(info.filename)
                if candidate.is_absolute() or ".." in candidate.parts or info.is_dir():
                    errors.append("archive.entry_path")
                    continue
                if info.compress_type != zipfile.ZIP_STORED:
                    errors.append("archive.compression")
                if info.date_time != (1980, 1, 1, 0, 0, 0):
                    errors.append("archive.timestamp")
                if info.create_system != 3 or (info.external_attr >> 16) != 0o100644:
                    errors.append("archive.permissions")
                if info.flag_bits & 0x1:
                    errors.append("archive.encrypted")
                if info.file_size > PACKAGE_LIMIT_BYTES:
                    errors.append("archive.entry_bytes")
                    continue
                entries[info.filename] = archive.read(info)
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return sorted(set(errors + ["archive.format"]))

    if registered:
        app_bytes = entries.pop(".app.json", None)
        manifest_bytes = entries.get(".codex-plugin/plugin.json")
        app, app_errors = load_json_bytes(app_bytes, "app_manifest") if isinstance(app_bytes, bytes) else (None, ["app_manifest.missing"])
        manifest, manifest_errors = (
            load_json_bytes(manifest_bytes, "manifest")
            if isinstance(manifest_bytes, bytes)
            else (None, ["manifest.missing"])
        )
        errors.extend(app_errors)
        errors.extend(manifest_errors)
        if manifest is not None:
            if manifest.pop("apps", None) != "./.app.json":
                errors.append("manifest.apps")
            base_entries = dict(entries)
            base_entries[".codex-plugin/plugin.json"] = package_manifest = canonical_json_bytes(manifest)
            original_manifest = load_json_bytes((PACKAGE_ROOT / ".codex-plugin/plugin.json").read_bytes(), "source_manifest")[0]
            if original_manifest is None or manifest != original_manifest:
                errors.append("manifest.registered_base")
            errors.extend(validate_base_entries({**base_entries, ".codex-plugin/plugin.json": package_manifest}))
        if not isinstance(app, dict) or set(app) != {"apps"}:
            errors.append("app_manifest.fields")
        else:
            apps = app.get("apps")
            entry = apps.get("hwpx-agent") if isinstance(apps, dict) and set(apps) == {"hwpx-agent"} else None
            if not isinstance(entry, dict) or set(entry) != {"category", "id"}:
                errors.append("app_manifest.mapping")
            else:
                app_id = entry.get("id")
                if (
                    not isinstance(app_id, str)
                    or REGISTERED_APP_ID.fullmatch(app_id) is None
                    or any(marker in app_id.upper() for marker in FORBIDDEN_ID_MARKERS)
                ):
                    errors.append("app_manifest.id")
                if entry.get("category") != "Productivity":
                    errors.append("app_manifest.category")
    else:
        errors.extend(validate_base_entries(entries))

    if entries and archive_bytes != deterministic_zip_bytes(
        ({**entries, ".app.json": app_bytes} if registered and isinstance(app_bytes, bytes) else entries)
    ):
        errors.append("archive.determinism")
    return sorted(set(errors))


def _validate_output_path(output_path: Path, package_root: Path) -> list[str]:
    errors: list[str] = []
    resolved_output = output_path.resolve()
    resolved_package = package_root.resolve()
    if resolved_output.is_relative_to(resolved_package):
        errors.append("output.inside_source")
    if _has_link_component(output_path.parent):
        errors.append("output.link_component")
    if resolved_output.is_relative_to(ROOT.resolve()) and not resolved_output.is_relative_to(ARTIFACT_ROOT.resolve()):
        errors.append("output.tracked_tree")
    if output_path.suffix.lower() != ".zip":
        errors.append("output.extension")
    if output_path.exists():
        errors.append("output.exists")
    return sorted(set(errors))


def publish_archive(
    output_path: Path,
    package_root: Path = PACKAGE_ROOT,
    binding: RegistrationBinding | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    entries, errors = read_base_entries(package_root)
    errors.extend(_validate_output_path(output_path, package_root))
    if errors:
        return None, sorted(set(errors))
    composed, compose_errors = compose_entries(entries, binding)
    if compose_errors:
        return None, compose_errors
    archive_bytes = deterministic_zip_bytes(composed)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
        )
    except OSError:
        return None, ["output.publish"]
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(archive_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary_name, output_path)
    except FileExistsError:
        return None, ["output.exists"]
    except OSError:
        return None, ["output.publish"]
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return {
        "archive": str(output_path.resolve()),
        "bytes": len(archive_bytes),
        "entries": len(composed),
        "registered": binding is not None,
        "registration_evidence_id": binding.evidence_id if binding is not None else None,
        "sha256": sha256_bytes(archive_bytes),
    }, []
