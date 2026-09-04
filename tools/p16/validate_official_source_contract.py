from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_official_source_contract as builder  # noqa: E402


SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_CATEGORIES = {
    "accessibility",
    "architecture",
    "bridge",
    "claim_boundary",
    "csp",
    "design",
    "file_flow",
    "manifest",
    "result_data",
    "security",
    "ui_resource",
    "validation",
}
ALLOWED_WEB_HOSTS = {"developers.openai.com", "modelcontextprotocol.io"}
ALLOWED_IMMUTABLE_HOSTS = {"github.com", "raw.githubusercontent.com"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_https_url(value: Any, hosts: set[str]) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in hosts and not parsed.username and not parsed.password


def is_https_origin(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and isinstance(parsed.hostname, str)
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )


def has_wildcard(value: Any) -> bool:
    if isinstance(value, str):
        return "*" in value
    if isinstance(value, list):
        return any(has_wildcard(item) for item in value)
    if isinstance(value, dict):
        return any(has_wildcard(item) for item in value.values())
    return False


def validate(source_lock: Any, contract: Any, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    expected_source_lock = builder.build_source_lock()
    if source_lock != expected_source_lock:
        errors.append("source_lock.exact")

    if not isinstance(source_lock, dict):
        return errors + ["source_lock.shape"]

    documents = source_lock.get("mutable_documents")
    if not isinstance(documents, list) or len(documents) != len(builder.MUTABLE_DOCUMENTS):
        errors.append("mutable_documents.count")
        documents = []
    document_ids: list[str] = []
    document_urls: list[str] = []
    for index, entry in enumerate(documents):
        if not isinstance(entry, dict):
            errors.append(f"mutable_documents[{index}].shape")
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str):
            errors.append(f"mutable_documents[{index}].id")
        else:
            document_ids.append(identifier)
        url = entry.get("url")
        snapshot_url = entry.get("snapshot_url")
        if not is_https_url(url, ALLOWED_WEB_HOSTS):
            errors.append(f"mutable_documents[{index}].url")
        else:
            document_urls.append(url)
        if not is_https_url(snapshot_url, ALLOWED_WEB_HOSTS) or not str(snapshot_url).endswith(".md"):
            errors.append(f"mutable_documents[{index}].snapshot_url")
        if not isinstance(entry.get("content_length_bytes"), int) or entry["content_length_bytes"] <= 0:
            errors.append(f"mutable_documents[{index}].content_length_bytes")
        if not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"]):
            errors.append(f"mutable_documents[{index}].sha256")
        topics = entry.get("topics")
        if not isinstance(topics, list) or not topics or any(not isinstance(topic, str) for topic in topics):
            errors.append(f"mutable_documents[{index}].topics")
    if len(document_ids) != len(set(document_ids)):
        errors.append("mutable_documents.ids_unique")
    if len(document_urls) != len(set(document_urls)):
        errors.append("mutable_documents.urls_unique")

    immutable_sources = source_lock.get("immutable_sources")
    if not isinstance(immutable_sources, list) or len(immutable_sources) != len(builder.IMMUTABLE_SOURCES):
        errors.append("immutable_sources.count")
        immutable_sources = []
    immutable_ids: list[str] = []
    for index, entry in enumerate(immutable_sources):
        if not isinstance(entry, dict):
            errors.append(f"immutable_sources[{index}].shape")
            continue
        identifier = entry.get("id")
        if isinstance(identifier, str):
            immutable_ids.append(identifier)
        else:
            errors.append(f"immutable_sources[{index}].id")
        if not is_https_url(entry.get("url"), ALLOWED_IMMUTABLE_HOSTS):
            errors.append(f"immutable_sources[{index}].url")
        if not isinstance(entry.get("commit"), str) or not GIT_COMMIT.fullmatch(entry["commit"]):
            errors.append(f"immutable_sources[{index}].commit")
        if entry.get("kind") == "content_at_commit":
            if not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"]):
                errors.append(f"immutable_sources[{index}].sha256")
            if not isinstance(entry.get("content_length_bytes"), int) or entry["content_length_bytes"] <= 0:
                errors.append(f"immutable_sources[{index}].content_length_bytes")
    if len(immutable_ids) != len(set(immutable_ids)):
        errors.append("immutable_sources.ids_unique")

    packages = source_lock.get("package_locks")
    if not isinstance(packages, list) or len(packages) != len(builder.PACKAGE_LOCKS):
        errors.append("package_locks.count")
        packages = []
    package_ids: list[str] = []
    for index, entry in enumerate(packages):
        if not isinstance(entry, dict):
            errors.append(f"package_locks[{index}].shape")
            continue
        if isinstance(entry.get("id"), str):
            package_ids.append(entry["id"])
        else:
            errors.append(f"package_locks[{index}].id")
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", str(entry.get("version", ""))):
            errors.append(f"package_locks[{index}].version")
        if not isinstance(entry.get("integrity"), str) or not entry["integrity"].startswith("sha512-"):
            errors.append(f"package_locks[{index}].integrity")
        if not is_https_url(entry.get("tarball"), {"registry.npmjs.org"}):
            errors.append(f"package_locks[{index}].tarball")
    if len(package_ids) != len(set(package_ids)):
        errors.append("package_locks.ids_unique")

    requirements = source_lock.get("requirements")
    if not isinstance(requirements, list) or len(requirements) != len(builder.REQUIREMENTS):
        errors.append("requirements.count")
        requirements = []
    requirement_ids: list[str] = []
    categories: set[str] = set()
    known_sources = set(document_ids) | set(immutable_ids)
    for index, entry in enumerate(requirements):
        if not isinstance(entry, dict):
            errors.append(f"requirements[{index}].shape")
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"P16-R[0-9]{2}", identifier):
            errors.append(f"requirements[{index}].id")
        else:
            requirement_ids.append(identifier)
        category = entry.get("category")
        if isinstance(category, str):
            categories.add(category)
        else:
            errors.append(f"requirements[{index}].category")
        if entry.get("normative") not in {"MUST", "SHOULD"}:
            errors.append(f"requirements[{index}].normative")
        sources = entry.get("sources")
        if not isinstance(sources, list) or not sources or any(source not in known_sources for source in sources):
            errors.append(f"requirements[{index}].sources")
        statement = entry.get("statement")
        if not isinstance(statement, str) or len(statement) < 20:
            errors.append(f"requirements[{index}].statement")
    if requirement_ids != [f"P16-R{index:02d}" for index in range(1, len(builder.REQUIREMENTS) + 1)]:
        errors.append("requirements.order")
    if categories != REQUIRED_CATEGORIES:
        errors.append("requirements.categories")

    if source_lock.get("portable_bridge") != "mcp_apps":
        errors.append("portable_bridge")
    if source_lock.get("chatgpt_extension_policy") != "feature_detect_window_openai_only_when_no_shared_mcp_apps_equivalent":
        errors.append("chatgpt_extension_policy")
    csp_policy = source_lock.get("csp_policy")
    if not isinstance(csp_policy, dict):
        errors.append("csp_policy")
    else:
        if csp_policy.get("wildcard_allowed") is not False or csp_policy.get("origin_scheme") != "https":
            errors.append("csp_policy.defaults")
        for field in ("connect_domains", "resource_domains", "frame_domains", "redirect_domains"):
            values = csp_policy.get(field)
            if not isinstance(values, list):
                errors.append(f"csp_policy.{field}")
                continue
            if has_wildcard(values):
                errors.append(f"csp_policy.{field}.wildcard")
            for value in values:
                if not is_https_origin(value):
                    errors.append(f"csp_policy.{field}.origin")

    deferred = source_lock.get("deferred_evidence")
    if not isinstance(deferred, list) or not deferred or any(entry.get("state") != "unverified" for entry in deferred if isinstance(entry, dict)):
        errors.append("deferred_evidence")

    if not isinstance(contract, dict):
        return errors + ["contract.shape"]
    try:
        expected_contract = builder.build_contract(expected_source_lock, root)
    except (FileNotFoundError, OSError):
        expected_contract = None
        errors.append("contract.local_sources_missing")
    if expected_contract is not None and contract != expected_contract:
        errors.append("contract.exact")
    claims = contract.get("claims")
    if not isinstance(claims, dict):
        errors.append("contract.claims")
    else:
        for claim in ("plugin_bundle_implemented", "widget_implemented", "developer_mode_tested", "public_or_production_ready", "hangul_or_com_invoked"):
            if claims.get(claim) is not False:
                errors.append(f"contract.claims.{claim}")
    return sorted(set(errors))


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "hwpx-agent-p16-source-lock/1.0", "Accept": "text/markdown,text/plain,*/*"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - allowlisted HTTPS sources only
        return response.read()


def check_git_ref(url: str, ref: str, expected_commit: str) -> str | None:
    completed = subprocess.run(
        ["git", "ls-remote", url + ".git", ref],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return f"git_ref.fetch:{url}:{ref}"
    fields = completed.stdout.strip().split()
    if len(fields) != 2 or fields[0] != expected_commit or fields[1] != ref:
        return f"git_ref.drift:{url}:{ref}"
    return None


def check_online(source_lock: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for entry in source_lock["mutable_documents"]:
        try:
            payload = fetch_bytes(entry["snapshot_url"])
        except Exception as error:  # noqa: BLE001 - bounded diagnostic surface
            errors.append(f"online.document.fetch:{entry['id']}:{type(error).__name__}")
            continue
        if len(payload) != entry["content_length_bytes"]:
            errors.append(f"online.document.length:{entry['id']}")
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            errors.append(f"online.document.sha256:{entry['id']}")

    for entry in source_lock["immutable_sources"]:
        if entry["kind"] in {"git_commit", "git_tag"}:
            error = check_git_ref(entry["url"], entry["ref"], entry["commit"])
            if error is not None:
                errors.append(error)
        elif entry["kind"] == "content_at_commit":
            try:
                payload = fetch_bytes(entry["url"])
            except Exception as error:  # noqa: BLE001 - bounded diagnostic surface
                errors.append(f"online.immutable.fetch:{entry['id']}:{type(error).__name__}")
                continue
            if len(payload) != entry["content_length_bytes"]:
                errors.append(f"online.immutable.length:{entry['id']}")
            if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
                errors.append(f"online.immutable.sha256:{entry['id']}")

    for entry in source_lock["package_locks"]:
        package_path = quote(entry["name"], safe="")
        url = f"https://registry.npmjs.org/{package_path}/{entry['version']}"
        try:
            metadata = json.loads(fetch_bytes(url))
        except Exception as error:  # noqa: BLE001 - bounded diagnostic surface
            errors.append(f"online.package.fetch:{entry['id']}:{type(error).__name__}")
            continue
        if metadata.get("version") != entry["version"]:
            errors.append(f"online.package.version:{entry['id']}")
        distribution = metadata.get("dist")
        if not isinstance(distribution, dict) or distribution.get("integrity") != entry["integrity"]:
            errors.append(f"online.package.integrity:{entry['id']}")
        if not isinstance(distribution, dict) or distribution.get("tarball") != entry["tarball"]:
            errors.append(f"online.package.tarball:{entry['id']}")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the P16-01 official source lock.")
    parser.add_argument("--check-online", action="store_true", help="Re-fetch official mutable sources and verify the frozen snapshot.")
    args = parser.parse_args()
    source_lock = read_json(builder.SOURCE_LOCK_PATH)
    contract = read_json(builder.CONTRACT_PATH)
    errors = validate(source_lock, contract)
    if not errors and args.check_online:
        errors.extend(check_online(source_lock))
    if errors:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "decision": "PASS",
                "online": args.check_online,
                "documents": len(source_lock["mutable_documents"]),
                "immutable_sources": len(source_lock["immutable_sources"]),
                "packages": len(source_lock["package_locks"]),
                "requirements": len(source_lock["requirements"]),
                "local_source_locks": len(contract["source_locks"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
