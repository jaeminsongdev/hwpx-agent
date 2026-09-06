"""Disposable full-stack acceptance for the dedicated P16 plan-review MCP host."""
from __future__ import annotations

import base64
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import ssl
import subprocess
import tempfile
import threading
import time
import uuid
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LABEL = "hwpx-agent.p16-plan-review-staging-test"
MIGRATIONS = tuple(
    f"{number:04d}_{name}"
    for number, name in (
        (1, "p14_metadata"),
        (2, "p14_artifact_service"),
        (3, "p14_revision_cas"),
        (4, "p14_history_checkpoints"),
        (5, "p14_job_state_machine"),
        (6, "p14_worker_lease_fencing"),
        (7, "p14_idempotency_reconciliation"),
        (8, "p14_cancel_cleanup"),
        (9, "p14_retention_local_mirror"),
        (10, "p16_artifact_repository"),
        (11, "p16_plan_source"),
        (12, "p16_durable_plan_store"),
        (13, "p16_plan_review_evidence"),
    )
)
NOW = 2_000_000_000
TENANT = "00000000-0000-0000-0000-000000000001"
FOREIGN_TENANT = "00000000-0000-0000-0000-000000000002"
PROJECT_UUID = "00000000-0000-0000-0000-000000000101"
PROJECT = "prj_00000000000000000000000000000101"
BRANCH = "00000000-0000-0000-0000-000000000102"
REVISION_UUID = "00000000-0000-0000-0000-000000000201"
REVISION = "rev_00000000000000000000000000000201"
COMMIT = "00000000-0000-0000-0000-000000000202"
SOURCE_ARTIFACT = "00000000-0000-0000-0000-000000000301"
RESULT_ARTIFACT = "00000000-0000-0000-0000-000000000302"
PLAN = "plan_00000000000000000000000000000301"
SUBJECT = "private-owner"
TOKEN_KEY = b"0123456789abcdef0123456789abcdef"
RESOURCE = "https://mcp.hwpx-agent.example"
SERVER_ENTRY = ROOT / "web/plan-review-staging/dist/server.js"
DRIVER = ROOT / "target/debug" / (
    "plan-review-staging-driver.exe" if os.name == "nt" else "plan-review-staging-driver"
)
PROBE = ROOT / "target/debug/examples" / (
    "postgres_plan_review_evidence_probe.exe"
    if os.name == "nt"
    else "postgres_plan_review_evidence_probe"
)
WIDGET = ROOT / "web/plugin-widget/dist/plan-review-widget-v1.html"
MAX_CAPTURE_BYTES = 1_000_000
P15_CATALOG = ROOT / "protocol/mcp/p15-public-tools-v1.json"
P15_CATALOG_SHA256 = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"


class CheckFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def invoke(
    command: list[str],
    *,
    data: str | None = None,
    env: dict[str, str] | None = None,
    expected: bool = True,
    timeout: int = 90,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        input=data,
        env=env,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if expected and result.returncode != 0:
        raise CheckFailure(f"child_failed exit={result.returncode}")
    return result


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def token() -> str:
    header = base64url(
        json.dumps(
            {"alg": "HS256", "kid": "local-key-01", "typ": "at+jwt"},
            separators=(",", ":"),
        ).encode()
    )
    claims = base64url(
        json.dumps(
            {
                "iss": "https://identity.hwpx-agent.example",
                "sub": SUBJECT,
                "aud": RESOURCE,
                "exp": NOW + 3_540,
                "nbf": NOW - 60,
                "iat": NOW - 60,
                "jti": "plan-review-staging-owner",
                "scope": "project.read",
                "token_kind": "user",
                "tenant_id": TENANT,
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{claims}"
    signature = base64url(
        hmac.new(TOKEN_KEY, signing_input.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{signing_input}.{signature}"


def pnpm(command: str) -> None:
    if os.name == "nt":
        shell = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        invoke([shell, "/d", "/s", "/c", command], timeout=180)
    else:
        invoke(["sh", "-c", command], timeout=180)


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
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        environment.pop(name, None)
    return environment


def read_ready_line(process: subprocess.Popen[bytes]) -> dict[str, Any]:
    require(process.stdout is not None, "server_stdout_missing")
    output: queue.Queue[bytes | BaseException] = queue.Queue(maxsize=1)

    def reader() -> None:
        try:
            stream = process.stdout
            if stream is None:
                raise CheckFailure("server_stdout_missing")
            output.put(stream.readline())
        except BaseException as error:  # pragma: no cover - pipe failure
            output.put(error)

    threading.Thread(target=reader, name="p16-ready-reader", daemon=True).start()
    try:
        item = output.get(timeout=30)
    except queue.Empty as error:
        raise CheckFailure("server_ready_timeout") from error
    if isinstance(item, BaseException) or not item or len(item) > 200_000:
        raise CheckFailure("server_ready_record_invalid")
    try:
        value = json.loads(item.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CheckFailure("server_ready_record_malformed") from error
    require(isinstance(value, dict) and value.get("state") == "ready", "server_not_ready")
    return value


def stop_server(process: subprocess.Popen[bytes], *, expected_success: bool = True) -> None:
    if process.poll() is None:
        require(process.stdin is not None, "server_stdin_missing")
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired as error:
            process.terminate()
            process.wait(timeout=5)
            raise CheckFailure("server_shutdown_timeout") from error
    if expected_success:
        require(process.returncode == 0, "server_exit_failure")
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            content = stream.read(MAX_CAPTURE_BYTES + 1)
            stream.close()
            require(len(content) <= MAX_CAPTURE_BYTES, "server_output_unbounded")


def start_server(node: str, environment: dict[str, str]) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    process = subprocess.Popen(
        [node, str(SERVER_ENTRY)],
        cwd=ROOT,
        env=minimal_environment(environment),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        return process, read_ready_line(process)
    except Exception:
        stop_server(process, expected_success=False)
        raise


def inspector_entry() -> Path:
    package_root = ROOT / "web/mcp-staging/node_modules/@modelcontextprotocol/inspector"
    package = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
    relative = package.get("bin", {}).get("mcp-inspector")
    require(isinstance(relative, str), "inspector_entry_missing")
    entry = (package_root / relative).resolve()
    require(entry.is_file(), "inspector_not_installed")
    return entry


def inspector_call(
    node: str,
    inspector: Path,
    config_path: Path,
    certificate_path: Path,
    method: str,
    *,
    uri: str | None = None,
    arguments: dict[str, Any] | None = None,
    expected: bool = True,
) -> Any:
    command = [
        node,
        str(inspector),
        "--cli",
        "--config",
        str(config_path),
        "--server",
        "hwpx-agent-plan-review",
        "--method",
        method,
        "--format",
        "json",
        "--connect-timeout",
        "15000",
    ]
    if method == "tools/list":
        command.append("--strict")
    if uri is not None:
        command.extend(["--uri", uri])
    if arguments is not None:
        command.extend(
            [
                "--tool-name",
                "render_plan_review_widget",
                "--tool-args-json",
                json.dumps(arguments, separators=(",", ":")),
            ]
        )
    result = invoke(
        command,
        env=minimal_environment(
            {
                "NODE_EXTRA_CA_CERTS": str(certificate_path),
                "MCP_CLIENT_CONFIG_PATH": str(config_path.parent / "client.json"),
            }
        ),
        expected=False,
        timeout=45,
    )
    if not expected:
        return result
    require(result.returncode == 0 and result.stdout.strip(), f"inspector_{method}_failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CheckFailure(f"inspector_{method}_malformed") from error


def payload(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "inspector_result_not_object")
    nested = value.get("result")
    return nested if isinstance(nested, dict) else value


def call_arguments() -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.plan-review-render-request/v1",
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "project_id": PROJECT,
        "source_revision_id": REVISION,
        "plan_id": PLAN,
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
        response.read(MAX_CAPTURE_BYTES)
        return response.status, {
            name.lower(): value for name, value in response.getheaders()
        }
    finally:
        connection.close()


def negative_network_probes(
    port: int, context: ssl.SSLContext, bearer_token: str
) -> dict[str, int]:
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        separators=(",", ":"),
    ).encode()
    base = {"Content-Type": "application/json", "Accept": "application/json"}
    auth = {**base, "Authorization": f"Bearer {bearer_token}"}
    results: dict[str, int] = {}
    results["missing_auth"], headers = https_probe(
        port, context, method="POST", path="/mcp", body=body, headers=base
    )
    require("www-authenticate" in headers, "missing_auth_challenge_absent")
    results["invalid_auth"], _ = https_probe(
        port,
        context,
        method="POST",
        path="/mcp",
        body=body,
        headers={**base, "Authorization": "Bearer invalid.invalid.invalid"},
    )
    results["wrong_path"], _ = https_probe(
        port, context, method="POST", path="/wrong", body=body, headers=auth
    )
    results["host_rebinding"], _ = https_probe(
        port,
        context,
        method="POST",
        path="/mcp",
        body=body,
        headers={**auth, "Host": "evil.example"},
    )
    results["hostile_origin"], _ = https_probe(
        port,
        context,
        method="POST",
        path="/mcp",
        body=body,
        headers={**auth, "Origin": "https://evil.example"},
    )
    results["wrong_method"], _ = https_probe(
        port, context, method="PUT", path="/mcp", body=body, headers=auth
    )
    oversized = b'{"value":"' + b"x" * 300_001 + b'"}'
    results["oversized_body"], _ = https_probe(
        port, context, method="POST", path="/mcp", body=oversized, headers=auth
    )
    require(
        results
        == {
            "missing_auth": 401,
            "invalid_auth": 401,
            "wrong_path": 404,
            "host_rebinding": 403,
            "hostile_origin": 403,
            "wrong_method": 405,
            "oversized_body": 413,
        },
        "network_boundary_probe_mismatch",
    )
    return results


def validate_tool_list(value: Any) -> None:
    tools = payload(value).get("tools")
    require(isinstance(tools, list) and len(tools) == 1, "tool_count_mismatch")
    descriptor = tools[0]
    require(isinstance(descriptor, dict), "tool_descriptor_invalid")
    require(descriptor.get("name") == "render_plan_review_widget", "tool_name_mismatch")
    require(
        descriptor.get("annotations")
        == {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "tool_annotations_mismatch",
    )
    metadata = descriptor.get("_meta")
    require(
        isinstance(metadata, dict)
        and metadata.get("ui", {}).get("resourceUri")
        == "ui://hwpx-agent/plan-review/v1.html",
        "tool_resource_binding_mismatch",
    )


def validate_resource_list(value: Any) -> None:
    resources = payload(value).get("resources")
    require(isinstance(resources, list) and len(resources) == 1, "resource_count_mismatch")
    require(
        resources[0].get("uri") == "ui://hwpx-agent/plan-review/v1.html"
        and resources[0].get("mimeType") == "text/html;profile=mcp-app",
        "resource_descriptor_mismatch",
    )


def validate_resource_read(value: Any, widget_sha256: str) -> None:
    contents = payload(value).get("contents")
    require(isinstance(contents, list) and len(contents) == 1, "resource_content_count_mismatch")
    content = contents[0]
    text = content.get("text") if isinstance(content, dict) else None
    require(isinstance(text, str), "resource_text_missing")
    require(hashlib.sha256(text.encode()).hexdigest() == widget_sha256, "resource_digest_mismatch")
    require("PRIVATE" not in text and "kms.review" not in text, "resource_private_data_leak")


def validate_render(value: Any) -> str:
    result = payload(value)
    require(result.get("isError") is False, "render_result_failed")
    snapshot = result.get("structuredContent")
    require(isinstance(snapshot, dict), "render_snapshot_missing")
    require(snapshot.get("schema_version") == "hwpx-agent.plan-review/v1", "snapshot_schema_mismatch")
    require(snapshot.get("project_id") == PROJECT, "snapshot_project_mismatch")
    require(snapshot.get("source_revision_id") == REVISION, "snapshot_revision_mismatch")
    require(snapshot.get("plan_id") == PLAN, "snapshot_plan_mismatch")
    require(snapshot.get("execution_allowed") is True, "snapshot_execution_unexpectedly_denied")
    serialized = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    for private in ("PRIVATE", "kms.review", "11.0.0.9136"):
        require(private not in serialized, "snapshot_private_data_leak")
    return hashlib.sha256(serialized.encode()).hexdigest()


def main() -> int:
    docker = shutil.which("docker")
    cargo = shutil.which("cargo")
    node = shutil.which("node")
    require(docker is not None, "docker_missing")
    require(cargo is not None, "cargo_missing")
    require(node is not None, "node_missing")
    run_id = uuid.uuid4().hex
    run_root = ROOT / "artifacts/p16/plan-review-staging/runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    container = f"hwpx-p16-review-host-{run_id}"
    volume = f"hwpx-p16-review-host-data-{run_id}"
    contract = json.loads(
        (ROOT / "implementation/p14/postgres/p14-artifact-service-v1.json").read_text(
            encoding="utf-8"
        )
    )
    image = contract["database"]["container_image"]
    require(
        re.fullmatch(r"postgres:18\.4-bookworm@sha256:[0-9a-f]{64}", image) is not None,
        "unpinned_image",
    )
    invoke([docker, "image", "inspect", image])
    invoke(
        [
            cargo,
            "build",
            "--locked",
            "-p",
            "mcp-control-plane",
            "--example",
            "postgres_plan_review_evidence_probe",
        ],
        timeout=180,
    )
    invoke([cargo, "build", "--locked", "-p", "plan-review-staging-driver"], timeout=180)
    pnpm("pnpm --filter @hwpx-agent/plugin-widget build")
    pnpm("pnpm --filter @hwpx-agent/plan-review-staging build")
    for required in (PROBE, DRIVER, SERVER_ENTRY, WIDGET):
        require(required.is_file(), "required_product_missing")
    inspector = inspector_entry()
    migration_paths = [ROOT / "migrations/postgres" / f"{name}.up.sql" for name in MIGRATIONS]
    checks: list[str] = []
    stage = "setup"
    failure: str | None = None
    cleaned = False
    admin_password = secrets.token_urlsafe(32)
    source_password = secrets.token_urlsafe(32)
    plan_password = secrets.token_urlsafe(32)
    review_password = secrets.token_urlsafe(32)
    plan_key = secrets.token_bytes(32)
    evidence_key = secrets.token_bytes(32)
    child_environment = dict(os.environ, POSTGRES_PASSWORD=admin_password)
    process: subprocess.Popen[bytes] | None = None

    def sql(statement: str, *, expected: bool = True) -> subprocess.CompletedProcess[str]:
        return invoke(
            [
                docker,
                "exec",
                "-i",
                container,
                "psql",
                "-X",
                "--no-align",
                "--tuples-only",
                "--quiet",
                "--set",
                "ON_ERROR_STOP=1",
                "--username",
                "postgres",
                "--dbname",
                "postgres",
            ],
            data=statement,
            expected=expected,
        )

    def database_ready() -> None:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            result = invoke(
                [docker, "exec", container, "pg_isready", "--username", "postgres"],
                expected=False,
                timeout=5,
            )
            if result.returncode == 0:
                return
            time.sleep(0.25)
        raise CheckFailure("postgres_ready_timeout")

    def port() -> str:
        state = json.loads(invoke([docker, "inspect", container]).stdout)[0]
        require(
            state.get("Config", {}).get("Labels", {}).get(LABEL) == run_id,
            "container_ownership_mismatch",
        )
        bindings = state.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
        require(isinstance(bindings, list) and len(bindings) == 1, "ambiguous_port")
        binding = bindings[0]
        require(binding.get("HostIp") == "127.0.0.1", "non_loopback_port")
        value = binding.get("HostPort")
        require(isinstance(value, str) and value.isdigit(), "invalid_port")
        return value

    def probe_environment(mode: str) -> dict[str, str]:
        return dict(
            os.environ,
            HWPX_P16_PLAN_REVIEW_MODE=mode,
            HWPX_P16_PG_PORT=port(),
            HWPX_P16_PG_DATABASE="postgres",
            HWPX_P16_PLAN_PG_USER="hwpx_p16_plan_store",
            HWPX_P16_PLAN_PG_PASSWORD=plan_password,
            HWPX_P16_REVIEW_PG_USER="hwpx_p16_review_store",
            HWPX_P16_REVIEW_PG_PASSWORD=review_password,
            HWPX_P16_PLAN_KEY=plan_key.hex(),
            HWPX_P16_EVIDENCE_KEY_V1=evidence_key.hex(),
            HWPX_P16_EVIDENCE_KEY_V2=secrets.token_hex(32),
        )

    def server_environment() -> dict[str, str]:
        return {
            "HWPX_AGENT_ROOT": str(ROOT),
            "HWPX_AGENT_PLAN_REVIEW_DRIVER": str(DRIVER),
            "HWPX_AGENT_PLAN_REVIEW_LIFETIME_SECONDS": "300",
            "HWPX_AGENT_PLAN_REVIEW_CLOCK_UNIX_SECONDS": str(NOW),
            "HWPX_AGENT_PLAN_REVIEW_HMAC_KEY_B64": base64url(TOKEN_KEY),
            "HWPX_AGENT_PLAN_REVIEW_TENANT_ID": TENANT,
            "HWPX_AGENT_PLAN_REVIEW_PROJECT_ID": PROJECT,
            "HWPX_AGENT_PLAN_REVIEW_SUBJECT": SUBJECT,
            "HWPX_AGENT_PLAN_REVIEW_PG_PORT": port(),
            "HWPX_AGENT_PLAN_REVIEW_PG_DATABASE": "postgres",
            "HWPX_AGENT_PLAN_REVIEW_SOURCE_PG_USER": "hwpx_p16_plan_reader",
            "HWPX_AGENT_PLAN_REVIEW_SOURCE_PG_PASSWORD": source_password,
            "HWPX_AGENT_PLAN_REVIEW_PLAN_PG_USER": "hwpx_p16_plan_store",
            "HWPX_AGENT_PLAN_REVIEW_PLAN_PG_PASSWORD": plan_password,
            "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PG_USER": "hwpx_p16_review_store",
            "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PG_PASSWORD": review_password,
            "HWPX_AGENT_PLAN_REVIEW_PLAN_ACTIVE_KEY_REF": "kms.plan-v1",
            "HWPX_AGENT_PLAN_REVIEW_PLAN_ACTIVE_KEY_B64": base64url(plan_key),
            "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_ACTIVE_KEY_REF": "kms.review-v1",
            "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_ACTIVE_KEY_B64": base64url(evidence_key),
        }

    def run_host_round(*, include_network_probes: bool) -> str:
        nonlocal process
        process, ready = start_server(node, server_environment())
        url = ready.get("url")
        certificate_text = ready.get("certificate_pem_base64")
        widget_sha256 = hashlib.sha256(WIDGET.read_bytes()).hexdigest()
        require(
            isinstance(url, str)
            and re.fullmatch(r"https://127\.0\.0\.1:[0-9]{1,5}/mcp", url) is not None
            and isinstance(certificate_text, str)
            and ready.get("tool_count") == 1
            and ready.get("resource_count") == 1
            and ready.get("resource_sha256") == widget_sha256
            and ready.get("clock_mode") == "server_fixture",
            "server_readiness_contract_mismatch",
        )
        with tempfile.TemporaryDirectory(prefix="hwpx-agent-p16-review-") as temporary_name:
            temporary = Path(temporary_name)
            certificate_path = temporary / "certificate.pem"
            certificate_path.write_bytes(base64.b64decode(certificate_text, validate=True))
            config_path = temporary / "inspector.json"
            config_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "hwpx-agent-plan-review": {
                                "type": "streamable-http",
                                "url": url,
                                "headers": {"Authorization": f"Bearer {token()}"},
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
            validate_tool_list(
                inspector_call(node, inspector, config_path, certificate_path, "tools/list")
            )
            validate_resource_list(
                inspector_call(node, inspector, config_path, certificate_path, "resources/list")
            )
            validate_resource_read(
                inspector_call(
                    node,
                    inspector,
                    config_path,
                    certificate_path,
                    "resources/read",
                    uri="ui://hwpx-agent/plan-review/v1.html",
                ),
                widget_sha256,
            )
            if include_network_probes:
                context = ssl.create_default_context(cafile=str(certificate_path))
                context.check_hostname = True
                server_port = int(url.split(":")[2].split("/")[0])
                negative_network_probes(server_port, context, token())
            snapshot_sha256 = validate_render(
                inspector_call(
                    node,
                    inspector,
                    config_path,
                    certificate_path,
                    "tools/call",
                    arguments=call_arguments(),
                )
            )
            invalid = call_arguments()
            invalid["project_id"] = "prj_00000000000000000000000000000999"
            rejected = inspector_call(
                node,
                inspector,
                config_path,
                certificate_path,
                "tools/call",
                arguments=invalid,
                expected=False,
            )
            require(
                rejected.returncode != 0 or '"isError":true' in rejected.stdout,
                "unauthorized_project_was_rendered",
            )
        stop_server(process)
        process = None
        return snapshot_sha256

    try:
        facts_result = invoke(
            [str(PROBE)], env=dict(os.environ, HWPX_P16_PLAN_REVIEW_MODE="facts")
        )
        facts = json.loads(facts_result.stdout)
        owner_sha256 = facts["owner_sha256"]
        graph_sha256 = facts["graph_sha256"]
        require(re.fullmatch(r"[0-9a-f]{64}", owner_sha256) is not None, "owner_digest_invalid")
        require(re.fullmatch(r"[0-9a-f]{64}", graph_sha256) is not None, "graph_digest_invalid")
        checks.append("product_identity_and_graph_derived")
        require(
            hashlib.sha256(P15_CATALOG.read_bytes()).hexdigest()
            == P15_CATALOG_SHA256,
            "immutable_p15_catalog_drift",
        )
        checks.append("immutable_p15_catalog_digest_preserved")
        invoke([docker, "volume", "create", "--label", f"{LABEL}={run_id}", volume])
        invoke(
            [
                docker,
                "run",
                "--detach",
                "--pull",
                "never",
                "--name",
                container,
                "--label",
                f"{LABEL}={run_id}",
                "--publish",
                "127.0.0.1::5432",
                "--memory",
                "512m",
                "--cpus",
                "2",
                "--pids-limit",
                "128",
                "--mount",
                f"type=volume,source={volume},target=/var/lib/postgresql",
                "--env",
                "POSTGRES_PASSWORD",
                image,
            ],
            env=child_environment,
        )
        database_ready()
        for path in migration_paths:
            stage = path.name
            sql(
                f"SELECT set_config('hwpx_agent.migration_sha256','{digest(path)}',false);\n"
                + path.read_text(encoding="utf-8")
            )
        checks.append("all_thirteen_migrations_applied")

        stage = "seed_authoritative_source"
        sql(
            f"""
BEGIN;
INSERT INTO hwpx_agent.tenants(tenant_id,slug) VALUES
 ('{TENANT}','plan-review-host-one'),('{FOREIGN_TENANT}','plan-review-host-two');
INSERT INTO hwpx_agent.projects(
 tenant_id,project_id,slug,display_name,target_profile_id,retention_policy_id
) VALUES ('{TENANT}','{PROJECT_UUID}','synthetic-plan-review-host','Synthetic Plan Review Host',
          'hancom-2020','retention.local');
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
 VALUES ('{TENANT}','{PROJECT_UUID}','{owner_sha256}','owner');
INSERT INTO hwpx_agent.branches(
 tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT_UUID}','{BRANCH}','main',true,'{owner_sha256}');
INSERT INTO hwpx_agent.artifacts(
 tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,storage_state,
 encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
 encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
 scanner_engine_ref,scanner_signature_version,authorization_generation
) VALUES
 ('{TENANT}','{SOURCE_ARTIFACT}',repeat('1',64),128,'application/octet-stream','source','available',
  'kms.synthetic',transaction_timestamp(),1,'source.hwpx',
  'artifacts/v1/00000000000000000000000000000001/source/available/'||repeat('1',64)||'.aes256gcm',
  'AES-256-GCM',decode(repeat('01',12),'hex'),repeat('8',64),repeat('9',64),'verified',
  'scanner.synthetic','probe-v1',1),
 ('{TENANT}','{RESULT_ARTIFACT}',repeat('2',64),128,'application/octet-stream','result','available',
  'kms.synthetic',transaction_timestamp(),1,'result.hwpx',
  'artifacts/v1/00000000000000000000000000000001/result/available/'||repeat('2',64)||'.aes256gcm',
  'AES-256-GCM',decode(repeat('02',12),'hex'),repeat('a',64),repeat('b',64),'verified',
  'scanner.synthetic','probe-v1',1);
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
 VALUES ('{TENANT}','{SOURCE_ARTIFACT}','{owner_sha256}',true,true),
        ('{TENANT}','{RESULT_ARTIFACT}','{owner_sha256}',true,true);
COMMIT;
BEGIN;
ALTER TABLE hwpx_agent.revision_commit_receipts
 DISABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;
SELECT set_config('hwpx_agent.tenant_id','{TENANT}',true);
SELECT set_config('hwpx_agent.subject_sha256','{owner_sha256}',true);
SELECT outcome FROM hwpx_agent.commit_revision_cas(
 '{TENANT}','{PROJECT_UUID}','{BRANCH}','{owner_sha256}','{COMMIT}',NULL,0,'{REVISION_UUID}',
 ARRAY[]::uuid[],'{SOURCE_ARTIFACT}','{RESULT_ARTIFACT}',NULL,repeat('3',64),'verified',
 repeat('4',64),repeat('6',64),repeat('5',64),repeat('7',64));
ALTER TABLE hwpx_agent.revision_commit_receipts
 ENABLE TRIGGER revision_commit_receipts_idempotency_v2_guard;
COMMIT;
INSERT INTO hwpx_agent.revision_graph_bindings(
 tenant_id,project_id,revision_id,source_artifact_id,graph_sha256,created_by_subject_sha256
) VALUES ('{TENANT}','{PROJECT_UUID}','{REVISION_UUID}','{SOURCE_ARTIFACT}',
          '{graph_sha256}','{owner_sha256}');
"""
        )
        checks.append("authoritative_source_seeded")

        stage = "least_privilege_roles"
        sql(
            f"""
CREATE ROLE hwpx_p16_plan_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
 NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8 PASSWORD '{source_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_plan_reader;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_plan_reader;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.projects,hwpx_agent.branches,
 hwpx_agent.tenants,hwpx_agent.project_acl,hwpx_agent.artifacts,hwpx_agent.revisions,
 hwpx_agent.revision_graph_seals,hwpx_agent.revision_commit_receipts,
 hwpx_agent.revision_graph_bindings TO hwpx_p16_plan_reader;
CREATE ROLE hwpx_p16_plan_store LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
 NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8 PASSWORD '{plan_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_plan_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_plan_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.purge_expired_compiled_plan_records()
 TO hwpx_p16_plan_store;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.projects,hwpx_agent.branches,
 hwpx_agent.tenants,hwpx_agent.project_acl,hwpx_agent.artifacts,hwpx_agent.revisions,
 hwpx_agent.revision_graph_seals,hwpx_agent.revision_commit_receipts,
 hwpx_agent.revision_graph_bindings TO hwpx_p16_plan_store;
GRANT SELECT,INSERT ON hwpx_agent.compiled_plan_records TO hwpx_p16_plan_store;
CREATE ROLE hwpx_p16_review_store LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
 NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8 PASSWORD '{review_password}';
GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_p16_review_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_p16_review_store;
GRANT EXECUTE ON FUNCTION hwpx_agent.purge_expired_plan_review_evidence_records()
 TO hwpx_p16_review_store;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.compiled_plan_records
 TO hwpx_p16_review_store;
GRANT SELECT,INSERT ON hwpx_agent.plan_review_evidence_records TO hwpx_p16_review_store;
"""
        )
        checks.append("three_least_privilege_roles_admitted")

        stage = "seed_encrypted_plan_and_evidence"
        seeded = invoke([str(PROBE)], env=probe_environment("seed"), timeout=45)
        require(
            seeded.stdout.strip()
            == "P16_POSTGRES_PLAN_REVIEW_EVIDENCE_PROBE_PASS mode=seed",
            "seed_probe_marker_mismatch",
        )
        checks.append("encrypted_plan_and_evidence_seeded")

        stage = "registered_host_first_round"
        first_snapshot = run_host_round(include_network_probes=True)
        checks.extend(
            [
                "dedicated_tool_discovered_strict",
                "immutable_resource_read_exact",
                "durable_renderer_call_passed",
                "foreign_project_call_rejected",
                "https_auth_origin_host_size_boundaries_rejected",
                "graceful_host_shutdown",
            ]
        )

        stage = "postgres_restart"
        invoke([docker, "restart", container])
        database_ready()
        second_snapshot = run_host_round(include_network_probes=False)
        require(first_snapshot == second_snapshot, "restart_snapshot_drift")
        checks.append("postgres_and_host_restart_restore_exact")

        stage = "evidence_tamper"
        sql(
            f"""ALTER TABLE hwpx_agent.plan_review_evidence_records
 DISABLE TRIGGER plan_review_evidence_records_immutable;
UPDATE hwpx_agent.plan_review_evidence_records
 SET ciphertext=set_byte(ciphertext,0,get_byte(ciphertext,0) # 1)
 WHERE tenant_id='{TENANT}' AND project_id='{PROJECT_UUID}' AND plan_id='{PLAN}';
ALTER TABLE hwpx_agent.plan_review_evidence_records
 ENABLE TRIGGER plan_review_evidence_records_immutable;"""
        )
        process, ready_record = start_server(node, server_environment())
        require(ready_record.get("state") == "ready", "tamper_host_not_ready")
        with tempfile.TemporaryDirectory(prefix="hwpx-agent-p16-tamper-") as temporary_name:
            temporary = Path(temporary_name)
            certificate_path = temporary / "certificate.pem"
            certificate_path.write_bytes(
                base64.b64decode(ready_record["certificate_pem_base64"], validate=True)
            )
            config_path = temporary / "inspector.json"
            config_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "hwpx-agent-plan-review": {
                                "type": "streamable-http",
                                "url": ready_record["url"],
                                "headers": {"Authorization": f"Bearer {token()}"},
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
            tampered = inspector_call(
                node,
                inspector,
                config_path,
                certificate_path,
                "tools/call",
                arguments=call_arguments(),
                expected=False,
            )
            require(
                tampered.returncode != 0 or '"isError":true' in tampered.stdout,
                "tampered_evidence_rendered",
            )
        stop_server(process)
        process = None
        checks.append("registered_path_rejects_ciphertext_tamper")
    except Exception as error:  # noqa: BLE001 - bounded receipt below
        failure = f"{type(error).__name__}:{error}"
    finally:
        if process is not None:
            try:
                stop_server(process, expected_success=False)
            except Exception:
                pass
        inspect = invoke([docker, "inspect", container], expected=False)
        if inspect.returncode == 0:
            values = json.loads(inspect.stdout)
            if (
                len(values) == 1
                and values[0].get("Config", {}).get("Labels", {}).get(LABEL) == run_id
            ):
                invoke([docker, "rm", "--force", container], expected=False)
        volume_inspect = invoke([docker, "volume", "inspect", volume], expected=False)
        if volume_inspect.returncode == 0:
            values = json.loads(volume_inspect.stdout)
            if len(values) == 1 and values[0].get("Labels", {}).get(LABEL) == run_id:
                invoke([docker, "volume", "rm", volume], expected=False)
        cleaned = (
            invoke([docker, "inspect", container], expected=False).returncode != 0
            and invoke([docker, "volume", "inspect", volume], expected=False).returncode != 0
        )

    commit = invoke(["git", "rev-parse", "HEAD"]).stdout.strip()
    tracked_clean = not invoke(
        ["git", "status", "--porcelain", "--untracked-files=no"]
    ).stdout.strip()
    receipt = {
        "schema_version": "hwpx-agent.p16-plan-review-staging-check/v1",
        "run_id": run_id,
        "source_commit": commit,
        "tracked_clean": tracked_clean,
        "qualifying": failure is None and cleaned and tracked_clean,
        "decision": (
            "PASS"
            if failure is None and cleaned and tracked_clean
            else "DEVELOPMENT_PASS"
            if failure is None and cleaned
            else "FAIL"
        ),
        "scope": "current_pc_disposable_postgres_dedicated_plan_review_mcp_host",
        "passed": failure is None and cleaned,
        "checks": checks,
        "check_count": len(checks),
        "failed_stage": stage if failure else None,
        "failure": failure,
        "resources_cleaned": cleaned,
        "actual_hangul": False,
        "p15_catalog_modified": (
            hashlib.sha256(P15_CATALOG.read_bytes()).hexdigest()
            != P15_CATALOG_SHA256
        ),
        "p15_catalog_sha256": hashlib.sha256(P15_CATALOG.read_bytes()).hexdigest(),
    }
    raw = json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n"
    for secret_value in (
        admin_password,
        source_password,
        plan_password,
        review_password,
        plan_key.hex(),
        evidence_key.hex(),
        token(),
    ):
        require(secret_value.encode() not in raw, "receipt_secret_leak")
    (run_root / "receipt.json").write_bytes(raw)
    if not receipt["passed"]:
        print(f"P16_PLAN_REVIEW_STAGING_CHECK_FAILED stage={stage}")
        return 1
    print(
        f"P16_PLAN_REVIEW_STAGING_CHECK_PASS run_id={run_id} "
        f"checks={len(checks)} decision={receipt['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
