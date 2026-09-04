#!/usr/bin/env python3
"""Run the bounded P15-09 HTTPS/MCP Inspector staging acceptance."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import http.client
import json
import os
import platform
import queue
import re
import secrets
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"
SERVER_ENTRY = ROOT / "web/mcp-staging/dist/server.js"
DRIVER_NAME = "mcp-staging-driver.exe" if os.name == "nt" else "mcp-staging-driver"
DRIVER_PATH = ROOT / "target/debug" / DRIVER_NAME
PACKAGE_PATH = ROOT / "web/mcp-staging/package.json"
MAX_OUTPUT_BYTES = 2_000_000
INSPECTOR_TIMEOUT_SECONDS = 45
EXPECTED_TOOL_COUNT = 18
RESOURCE = "https://mcp.hwpx-agent.example"
ISSUER = "https://identity.hwpx-agent.example"
KEY_ID = "local-key-01"
SUBJECT = "p15-inspector-user"
PROJECT_ID = "prj_example01"
SCOPE = " ".join(
    [
        "artifact.read",
        "artifact.write",
        "job.cancel",
        "job.submit",
        "mirror.sync",
        "project.read",
        "project.write",
        "retention.manage",
    ]
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class AcceptanceError(RuntimeError):
    """A stable, non-secret staging acceptance failure."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def make_token(secret: bytes, now: int) -> str:
    header = {"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}
    claims = {
        "iss": ISSUER,
        "sub": SUBJECT,
        "aud": RESOURCE,
        "exp": now + 600,
        "nbf": now - 60,
        "iat": now - 60,
        "jti": f"p15-{secrets.token_hex(12)}",
        "scope": SCOPE,
        "token_kind": "user",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
    }
    signing_input = f"{base64url(canonical_bytes(header))}.{base64url(canonical_bytes(claims))}"
    signature = hmac.new(secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{base64url(signature)}"


def run_checked(command: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=False,
        timeout=INSPECTOR_TIMEOUT_SECONDS,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if len(completed.stdout) > MAX_OUTPUT_BYTES or len(completed.stderr) > MAX_OUTPUT_BYTES:
        raise AcceptanceError("subprocess output exceeded the acceptance bound")
    if completed.returncode != 0:
        diagnostic = redact_diagnostic(completed.stderr)
        raise AcceptanceError(
            f"subprocess failed with exit code {completed.returncode}: {diagnostic}"
        )
    try:
        return completed.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AcceptanceError("subprocess output was not UTF-8") from error


def redact_diagnostic(value: bytes) -> str:
    text = value[:2_000].decode("utf-8", errors="replace")
    text = re.sub(
        r"Bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
        "Bearer <redacted>",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b",
        "<redacted-jwt>",
        text,
    )
    compact = " ".join(text.split())
    return compact[:500] if compact else "no diagnostics"


def build_products() -> None:
    run_checked(["cargo", "build", "--locked", "-p", "mcp-staging-driver"])
    if os.name == "nt":
        command_shell = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        run_checked(
            [
                command_shell,
                "/d",
                "/s",
                "/c",
                "pnpm --filter @hwpx-agent/mcp-staging build",
            ]
        )
    else:
        run_checked(["pnpm", "--filter", "@hwpx-agent/mcp-staging", "build"])


def package_versions() -> tuple[str, str]:
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    return (
        package["dependencies"]["@modelcontextprotocol/server"],
        package["devDependencies"]["@modelcontextprotocol/inspector"],
    )


def inspector_entry() -> Path:
    package_root = ROOT / "web/mcp-staging/node_modules/@modelcontextprotocol/inspector"
    package = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
    relative = package.get("bin", {}).get("mcp-inspector")
    if not isinstance(relative, str):
        raise AcceptanceError("pinned Inspector executable was not found")
    entry = (package_root / relative).resolve()
    if not entry.is_file():
        raise AcceptanceError("pinned Inspector executable is not a file")
    return entry


def read_ready_line(process: subprocess.Popen[bytes]) -> dict[str, Any]:
    if process.stdout is None:
        raise AcceptanceError("staging server stdout is unavailable")
    output: queue.Queue[bytes | BaseException] = queue.Queue(maxsize=1)

    def reader() -> None:
        try:
            output.put(process.stdout.readline())
        except BaseException as error:  # pragma: no cover - platform pipe failure
            output.put(error)

    thread = threading.Thread(target=reader, name="p15-ready-reader", daemon=True)
    thread.start()
    try:
        item = output.get(timeout=30)
    except queue.Empty as error:
        raise AcceptanceError("staging server readiness timed out") from error
    if isinstance(item, BaseException):
        raise AcceptanceError("staging server readiness pipe failed") from item
    if not item or len(item) > 200_000:
        raise AcceptanceError("staging server readiness record was invalid")
    try:
        value = json.loads(item.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcceptanceError("staging server readiness record was malformed") from error
    if not isinstance(value, dict) or value.get("state") != "ready":
        raise AcceptanceError("staging server did not become ready")
    return value


def minimal_environment(extra: dict[str, str]) -> dict[str, str]:
    keep = [
        "SystemRoot",
        "WINDIR",
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "TEMP",
        "TMP",
        "LANG",
        "LC_ALL",
    ]
    environment = {name: os.environ[name] for name in keep if name in os.environ}
    environment.update(extra)
    environment["NO_PROXY"] = "127.0.0.1,localhost"
    environment["no_proxy"] = "127.0.0.1,localhost"
    for name in [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ]:
        environment.pop(name, None)
    return environment


def start_server(node: str, secret_text: str) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    environment = minimal_environment(
        {
            "HWPX_AGENT_ROOT": str(ROOT),
            "HWPX_AGENT_STAGING_DRIVER": str(DRIVER_PATH),
            "HWPX_AGENT_STAGING_HMAC_KEY_B64": secret_text,
            "HWPX_AGENT_STAGING_LIFETIME_SECONDS": "300",
        }
    )
    process = subprocess.Popen(
        [node, str(SERVER_ENTRY)],
        cwd=ROOT,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        ready = read_ready_line(process)
    except Exception:
        stop_server(process)
        raise
    return process, ready


def stop_server(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        if process.stdin is None:
            raise AcceptanceError("staging server input is unavailable for graceful shutdown")
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            raise AcceptanceError("staging server did not shut down gracefully")
    if process.returncode != 0:
        raise AcceptanceError("staging server exited unsuccessfully")
    if process.stdin is not None and not process.stdin.closed:
        process.stdin.close()
    if process.stdout is not None:
        process.stdout.close()
    if process.stderr is not None:
        diagnostic = process.stderr.read(MAX_OUTPUT_BYTES + 1)
        process.stderr.close()
        if len(diagnostic) > MAX_OUTPUT_BYTES:
            raise AcceptanceError("staging server diagnostics exceeded the acceptance bound")


def inspector_call(
    node: str,
    entry: Path,
    config_path: Path,
    certificate_path: Path,
    method: str,
    *,
    tool_name: str | None = None,
    arguments: dict[str, Any] | None = None,
    strict: bool = False,
) -> Any:
    command = [
        node,
        str(entry),
        "--cli",
        "--config",
        str(config_path),
        "--server",
        "hwpx-agent",
        "--method",
        method,
        "--format",
        "json",
        "--connect-timeout",
        "15000",
    ]
    if strict:
        command.append("--strict")
    if tool_name is not None:
        command.extend(["--tool-name", tool_name])
    if arguments is not None:
        command.extend(["--tool-args-json", json.dumps(arguments, separators=(",", ":"))])
    environment = minimal_environment(
        {
            "NODE_EXTRA_CA_CERTS": str(certificate_path),
            "MCP_CLIENT_CONFIG_PATH": str(config_path.parent / "client.json"),
        }
    )
    stdout = run_checked(command, env=environment).strip()
    if not stdout:
        raise AcceptanceError("Inspector returned an empty result")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as error:
        raise AcceptanceError("Inspector result was not one JSON object") from error


def result_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AcceptanceError("Inspector result was not an object")
    nested = value.get("result")
    if isinstance(nested, dict):
        return nested
    return value


def validate_tool_list(value: Any, catalog: dict[str, Any]) -> list[str]:
    payload = result_payload(value)
    tools = payload.get("tools")
    if not isinstance(tools, list) or len(tools) != EXPECTED_TOOL_COUNT:
        raise AcceptanceError("Inspector did not discover exactly eighteen tools")
    expected = {descriptor["name"]: descriptor for descriptor in catalog["tools"]}
    seen: list[str] = []
    for tool in tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            raise AcceptanceError("Inspector returned a malformed tool descriptor")
        name = tool["name"]
        descriptor = expected.get(name)
        if descriptor is None or name in seen:
            raise AcceptanceError("Inspector returned an unknown or duplicate tool")
        if tool.get("inputSchema") != descriptor["inputSchema"]:
            raise AcceptanceError("Inspector input schema drifted from the catalog")
        if tool.get("outputSchema") != descriptor["outputSchema"]:
            raise AcceptanceError("Inspector output schema drifted from the catalog")
        if tool.get("annotations") != descriptor["annotations"]:
            raise AcceptanceError("Inspector annotations drifted from the catalog")
        if tool.get("_meta") != descriptor["_meta"]:
            raise AcceptanceError("Inspector metadata drifted from the catalog")
        seen.append(name)
    expected_order = [descriptor["name"] for descriptor in catalog["tools"]]
    if seen != expected_order:
        raise AcceptanceError("Inspector tool order drifted from the catalog")
    return seen


def synthesize(node: dict[str, Any], depth: int = 0) -> Any:
    if depth > 64:
        raise AcceptanceError("schema fixture depth exceeded its bound")
    if "$ref" in node:
        return reference_sample(node["$ref"])
    if "const" in node:
        return node["const"]
    if "enum" in node:
        values = node["enum"]
        if not isinstance(values, list) or not values:
            raise AcceptanceError("schema fixture enum was empty")
        return values[0]
    if "oneOf" in node:
        branches = node["oneOf"]
        if not isinstance(branches, list) or not branches:
            raise AcceptanceError("schema fixture oneOf was empty")
        return synthesize(branches[0], depth + 1)
    kind = node.get("type")
    if kind == "object":
        properties = node.get("properties")
        required = node.get("required")
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise AcceptanceError("schema fixture object was malformed")
        return {name: synthesize(properties[name], depth + 1) for name in required}
    if kind == "array":
        count = node.get("minItems", 0)
        item = node.get("items")
        if not isinstance(count, int) or not 0 <= count <= 128 or not isinstance(item, dict):
            raise AcceptanceError("schema fixture array was malformed")
        return [synthesize(item, depth + 1) for _ in range(count)]
    if kind == "boolean":
        return False
    if kind in {"integer", "number"}:
        return node.get("minimum", 0)
    if kind == "null":
        return None
    if kind == "string":
        return string_sample(node)
    raise AcceptanceError("schema fixture type was unsupported")


def reference_sample(reference: str) -> str:
    values = {
        "#/$defs/artifact_id": "art_example01",
        "#/$defs/capability_id": "page.paper_preset",
        "#/$defs/checkpoint_id": "chk_example01",
        "#/$defs/cursor": "Y3Vyc29y",
        "#/$defs/idempotency_key": "123e4567-e89b-12d3-a456-426614174000",
        "#/$defs/job_id": "job_example01",
        "#/$defs/locale": "ko-KR",
        "#/$defs/media_type": "application/hwp+zip",
        "#/$defs/plan_id": "plan_example01",
        "#/$defs/project_id": PROJECT_ID,
        "#/$defs/request_id": "req_example01",
        "#/$defs/revision_id": "rev_example01",
        "#/$defs/target_profile": "hancom-hangul-2020-secondary",
        "#/$defs/template_contract_id": "tpl_example01",
        "#/$defs/timestamp": "2026-09-04T00:00:00Z",
    }
    try:
        return values[reference]
    except KeyError as error:
        raise AcceptanceError("schema fixture reference was unsupported") from error


def string_sample(node: dict[str, Any]) -> str:
    pattern = node.get("pattern", "")
    if pattern == "^[0-9a-f]{64}$":
        return "a" * 64
    if pattern.startswith("^snp_"):
        return "snp_example01"
    if pattern.startswith("^rcp_"):
        return "rcp_example01"
    if pattern.startswith("^[A-Z]"):
        return "TEST_CODE"
    if pattern.startswith(r"^[a-z][a-z0-9_]*(?:\."):
        return "page.paper"
    if pattern.startswith("^[a-z][a-z0-9_]"):
        return "stage"
    return "value"


def validate_call_result(
    value: Any, tool_name: str, request_id: str, catalog_sha256: str
) -> dict[str, Any]:
    payload = result_payload(value)
    if payload.get("isError") is not False:
        raise AcceptanceError(f"Inspector tool call failed for {tool_name}")
    structured = payload.get("structuredContent")
    metadata = payload.get("_meta")
    content = payload.get("content")
    if not isinstance(structured, dict) or structured.get("request_id") != request_id:
        raise AcceptanceError(f"Inspector result correlation failed for {tool_name}")
    if not isinstance(metadata, dict) or metadata.get("hwpx/requestId") != request_id:
        raise AcceptanceError(f"Inspector metadata correlation failed for {tool_name}")
    required_digests = [
        "hwpx/catalogSha256",
        "hwpx/errorCatalogSha256",
        "hwpx/quotaPolicySha256",
        "hwpx/telemetryPolicySha256",
    ]
    for key in required_digests:
        digest = metadata.get(key)
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            raise AcceptanceError(f"Inspector metadata digest was invalid for {tool_name}")
    if metadata["hwpx/catalogSha256"] != catalog_sha256:
        raise AcceptanceError(f"Inspector catalog digest drifted for {tool_name}")
    if not isinstance(content, list) or len(content) != 1:
        raise AcceptanceError(f"Inspector text fallback was invalid for {tool_name}")
    return {
        "tool": tool_name,
        "request_id": request_id,
        "is_error": False,
        "result_sha256": sha256_bytes(canonical_bytes(payload)),
        "structured_content_sha256": sha256_bytes(canonical_bytes(structured)),
        "metadata_digests": {key: metadata[key] for key in required_digests},
    }


def https_probe(
    port: int,
    context: ssl.SSLContext,
    *,
    method: str,
    path: str,
    body: bytes,
    headers: dict[str, str],
) -> tuple[int, dict[str, str]]:
    connection = http.client.HTTPSConnection(
        "127.0.0.1", port=port, context=context, timeout=15
    )
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        response.read(MAX_OUTPUT_BYTES)
        return response.status, {name.lower(): value for name, value in response.getheaders()}
    finally:
        connection.close()


def negative_probes(port: int, context: ssl.SSLContext, token: str) -> dict[str, Any]:
    body = canonical_bytes({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    base = {"Content-Type": "application/json", "Accept": "application/json"}
    auth = {**base, "Authorization": f"Bearer {token}"}
    probes: dict[str, Any] = {}
    status, headers = https_probe(port, context, method="POST", path="/mcp", body=body, headers=base)
    probes["missing_auth"] = status
    if status != 401 or "www-authenticate" not in headers:
        raise AcceptanceError("missing-auth probe did not fail closed")
    status, _ = https_probe(
        port,
        context,
        method="POST",
        path="/mcp",
        body=body,
        headers={**base, "Authorization": "Bearer invalid.invalid.invalid"},
    )
    probes["invalid_auth"] = status
    status, _ = https_probe(
        port, context, method="POST", path="/wrong", body=body, headers=auth
    )
    probes["wrong_path"] = status
    status, _ = https_probe(
        port,
        context,
        method="POST",
        path="/mcp",
        body=body,
        headers={**auth, "Host": "evil.example"},
    )
    probes["host_rebinding"] = status
    status, _ = https_probe(
        port,
        context,
        method="POST",
        path="/mcp",
        body=body,
        headers={**auth, "Origin": "https://evil.example"},
    )
    probes["hostile_origin"] = status
    status, _ = https_probe(
        port, context, method="PUT", path="/mcp", body=body, headers=auth
    )
    probes["wrong_method"] = status
    oversized = b'{"value":"' + (b"x" * 300_001) + b'"}'
    status, _ = https_probe(
        port, context, method="POST", path="/mcp", body=oversized, headers=auth
    )
    probes["oversized_body"] = status
    expected = {
        "missing_auth": 401,
        "invalid_auth": 401,
        "wrong_path": 404,
        "host_rebinding": 403,
        "hostile_origin": 403,
        "wrong_method": 405,
        "oversized_body": 413,
    }
    if probes != expected:
        raise AcceptanceError("one or more HTTPS boundary probes did not fail closed")
    plain = http.client.HTTPConnection("127.0.0.1", port=port, timeout=5)
    try:
        try:
            plain.request("GET", "/mcp")
            response = plain.getresponse()
            response.read(1024)
            probes["plaintext_http_rejected"] = False
        except (ConnectionError, http.client.HTTPException, TimeoutError, OSError):
            probes["plaintext_http_rejected"] = True
    finally:
        plain.close()
    if probes["plaintext_http_rejected"] is not True:
        raise AcceptanceError("plaintext HTTP was not rejected")
    return probes


def git_identity() -> tuple[str, bool]:
    commit = run_checked(["git", "rev-parse", "HEAD"]).strip()
    status = run_checked(["git", "status", "--porcelain", "--untracked-files=no"])
    return commit, status.strip() == ""


def write_receipt(output_root: Path, receipt: dict[str, Any], secrets_to_exclude: list[str]) -> Path:
    raw = canonical_bytes(receipt)
    for secret_value in secrets_to_exclude:
        if secret_value.encode("utf-8") in raw:
            raise AcceptanceError("receipt secret exclusion failed")
    if re.search(rb"[A-Za-z]:[\\/]", raw):
        raise AcceptanceError("receipt contains an absolute Windows path")
    run_directory = output_root / receipt["run_id"]
    run_directory.mkdir(parents=True, exist_ok=False)
    destination = run_directory / "receipt.json"
    temporary = run_directory / "receipt.json.partial"
    temporary.write_bytes(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    temporary.replace(destination)
    return destination


def run_acceptance(*, skip_build: bool, output_root: Path) -> Path:
    started = time.monotonic()
    if not skip_build:
        build_products()
    for required in [CATALOG_PATH, SERVER_ENTRY, DRIVER_PATH, PACKAGE_PATH]:
        if not required.is_file():
            raise AcceptanceError("a required staging product is missing")
    node = shutil.which("node")
    if node is None:
        raise AcceptanceError("Node.js is not available")
    inspector = inspector_entry()
    catalog_bytes = CATALOG_PATH.read_bytes()
    catalog_sha256 = sha256_bytes(catalog_bytes)
    catalog = json.loads(catalog_bytes.decode("utf-8"))
    secret = secrets.token_bytes(32)
    secret_text = base64url(secret)
    now = int(time.time())
    token = make_token(secret, now)
    source_commit, tracked_clean = git_identity()
    process: subprocess.Popen[bytes] | None = None
    receipt: dict[str, Any] | None = None
    with tempfile.TemporaryDirectory(prefix="hwpx-agent-p15-") as temporary_name:
        temporary = Path(temporary_name)
        try:
            process, ready = start_server(node, secret_text)
            url = ready.get("url")
            certificate_base64 = ready.get("certificate_pem_base64")
            if (
                not isinstance(url, str)
                or not re.fullmatch(r"https://127\.0\.0\.1:[0-9]{1,5}/mcp", url)
                or not isinstance(certificate_base64, str)
                or ready.get("catalog_sha256") != catalog_sha256
                or ready.get("tool_count") != EXPECTED_TOOL_COUNT
                or ready.get("driver_lifecycle") != "persistent_per_server_run"
            ):
                raise AcceptanceError("staging readiness contract mismatch")
            port = int(url.split(":")[2].split("/")[0])
            if not 1 <= port <= 65_535:
                raise AcceptanceError("staging port was invalid")
            try:
                certificate_pem = base64.b64decode(certificate_base64, validate=True)
            except ValueError as error:
                raise AcceptanceError("staging certificate was malformed") from error
            certificate_path = temporary / "staging-cert.pem"
            certificate_path.write_bytes(certificate_pem)
            config_path = temporary / "inspector-config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "hwpx-agent": {
                                "type": "streamable-http",
                                "url": url,
                                "headers": {"Authorization": f"Bearer {token}"},
                                "protocolEra": "modern",
                                "connectionTimeout": 15_000,
                                "requestTimeout": 15_000,
                            }
                        }
                    },
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            listed = inspector_call(
                node,
                inspector,
                config_path,
                certificate_path,
                "tools/list",
                strict=True,
            )
            tool_names = validate_tool_list(listed, catalog)
            results = []
            for index, descriptor in enumerate(catalog["tools"], start=1):
                arguments = synthesize(descriptor["inputSchema"])
                request_id = f"req_inspector_{index:02d}"
                arguments["request_id"] = request_id
                value = inspector_call(
                    node,
                    inspector,
                    config_path,
                    certificate_path,
                    "tools/call",
                    tool_name=descriptor["name"],
                    arguments=arguments,
                )
                results.append(
                    validate_call_result(value, descriptor["name"], request_id, catalog_sha256)
                )
            context = ssl.create_default_context(cafile=str(certificate_path))
            context.check_hostname = True
            probes = negative_probes(port, context, token)
            certificate_der = ssl.PEM_cert_to_DER_cert(certificate_pem.decode("ascii"))
            sdk_version, inspector_version = package_versions()
            receipt = {
                "schema_version": "hwpx-agent.p15-inspector-staging-receipt/v1",
                "run_id": uuid.uuid4().hex,
                "source_commit": source_commit,
                "tracked_clean": tracked_clean,
                "qualifying": tracked_clean,
                "decision": "PASS" if tracked_clean else "DEVELOPMENT_PASS",
                "scope": "current_pc_hancom_2020_local_inspector_staging",
                "transport": {
                    "scheme": "https",
                    "bind": "127.0.0.1",
                    "path": "/mcp",
                    "ephemeral_port": True,
                    "certificate_sha256": sha256_bytes(certificate_der),
                    "private_key_persisted": False,
                },
                "protocol": {
                    "selected_era": "modern",
                    "server_supported_eras": ready.get("protocol_eras"),
                    "server_sdk_version": sdk_version,
                    "inspector_version": inspector_version,
                },
                "driver_lifecycle": "persistent_per_server_run",
                "graceful_shutdown": True,
                "catalog_sha256": catalog_sha256,
                "tool_count": len(tool_names),
                "tool_order_sha256": sha256_bytes(canonical_bytes(tool_names)),
                "strict_schema_discovery": "PASS",
                "tool_results": results,
                "negative_probes": probes,
                "durable_secret_material_persisted": False,
                "hangul_process_started": False,
                "platform": {"system": platform.system(), "machine": platform.machine()},
                "duration_milliseconds": round((time.monotonic() - started) * 1_000),
            }
            stop_server(process)
            process = None
            receipt["duration_milliseconds"] = round((time.monotonic() - started) * 1_000)
        finally:
            if process is not None:
                stop_server(process)
    if receipt is None:
        raise AcceptanceError("staging acceptance did not produce a receipt")
    receipt["temporary_configuration_deleted_before_receipt"] = True
    return write_receipt(output_root, receipt, [token, secret_text])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "implementation/p15/evidence/staging-runs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = run_acceptance(skip_build=args.skip_build, output_root=args.output_root)
    except (AcceptanceError, OSError, subprocess.SubprocessError, KeyError, TypeError) as error:
        print(f"P15-09 Inspector staging: FAIL ({type(error).__name__})", file=sys.stderr)
        return 1
    print(f"P15-09 Inspector staging: PASS ({receipt.relative_to(ROOT)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
