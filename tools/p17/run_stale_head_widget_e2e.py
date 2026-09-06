from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
WIDGET = ROOT / "web/plugin-widget/dist/continuity-widget-v2.html"
HARNESS = ROOT / "web/plugin-widget/dist/continuity-v2-e2e-host.html"
EVIDENCE_ROOT = ROOT / "artifacts/p17/stale-head-widget-runs"
PASS_TEXT = (
    "PASS calls=3 "
    "order=project_conflict_resolve,project_open,project_history"
)
RESULT_PATTERN = re.compile(
    r'<p id="e2e-result" data-state="(?P<state>[a-z]+)">(?P<text>[^<]*)</p>'
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_chrome() -> Path | None:
    override = os.environ.get("HWPX_AGENT_CHROME")
    candidates = [
        Path(override) if override else None,
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    command = shutil.which("google-chrome") or shutil.which("chrome")
    if command:
        candidates.append(Path(command))
    return next(
        (candidate for candidate in candidates if candidate and candidate.is_file()),
        None,
    )


def run_e2e(chrome: Path) -> dict[str, object]:
    if not WIDGET.is_file() or not HARNESS.is_file():
        raise RuntimeError("STALE_HEAD_E2E_BUNDLE_MISSING")
    with tempfile.TemporaryDirectory(prefix="hwpx-p17-07-widget-e2e-") as profile:
        command = [
            str(chrome),
            "--headless=new",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-gpu",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-default-browser-check",
            "--no-first-run",
            "--allow-file-access-from-files",
            "--host-resolver-rules=MAP * ~NOTFOUND",
            "--virtual-time-budget=10000",
            f"--user-data-dir={profile}",
            "--dump-dom",
            HARNESS.as_uri(),
        ]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            creationflags=creationflags,
        )
    text = completed.stdout.decode("utf-8", errors="replace")
    match = RESULT_PATTERN.search(text)
    if completed.returncode != 0:
        raise RuntimeError(f"STALE_HEAD_E2E_CHROME_EXIT:{completed.returncode}")
    if match is None:
        raise RuntimeError("STALE_HEAD_E2E_RESULT_MISSING")
    if match.group("state") != "pass" or match.group("text") != PASS_TEXT:
        raise RuntimeError(f"STALE_HEAD_E2E_FAILED:{match.group('text')[:120]}")
    return {
        "schema_version": "hwpx-agent.p17-stale-head-widget-e2e-receipt/v1",
        "state": "pass",
        "scope": "local_headless_browser_mcp_apps_bridge_component",
        "browser_executable": chrome.name,
        "resource": {
            "path": WIDGET.relative_to(ROOT).as_posix(),
            "bytes": WIDGET.stat().st_size,
            "sha256": sha256(WIDGET),
        },
        "harness": {
            "path": HARNESS.relative_to(ROOT).as_posix(),
            "bytes": HARNESS.stat().st_size,
            "sha256": sha256(HARNESS),
        },
        "assertions": {
            "bridge": "real_ext_apps_appbridge_postmessage_iframe",
            "selection_call_count": 0,
            "confirmed_call_count": 3,
            "call_order": [
                "project_conflict_resolve",
                "project_open",
                "project_history",
            ],
            "request_and_response_revision_generation_checked": True,
            "three_request_ids_distinct": True,
            "idempotency_key_present": True,
            "post_resolution_refresh_required": True,
        },
        "claims": {
            "actual_chatgpt_or_codex_host_tested": False,
            "project_conflict_resolve_registered": False,
            "actual_remote_transport_tested": False,
            "actual_concurrent_web_codex_tested": False,
            "hangul_or_com_invoked": False,
            "p17_07_pass": False,
        },
    }


def publish(receipt: dict[str, object]) -> Path:
    run_id = uuid.uuid4().hex
    directory = EVIDENCE_ROOT / run_id
    directory.mkdir(parents=True, exist_ok=False)
    destination = directory / "receipt.json"
    payload = (
        json.dumps(
            receipt | {"run_id": run_id},
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    temporary = directory / "receipt.json.partial"
    temporary.write_bytes(payload)
    temporary.replace(destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the local MCP Apps stale-head widget E2E."
    )
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    chrome = find_chrome()
    if chrome is None:
        raise RuntimeError("STALE_HEAD_E2E_CHROME_NOT_FOUND")
    receipt = run_e2e(chrome)
    evidence = publish(receipt) if args.publish else None
    print(
        "P17_STALE_HEAD_WIDGET_E2E_PASS "
        f"calls={receipt['assertions']['confirmed_call_count']} "
        f"widget_bytes={receipt['resource']['bytes']} "
        f"evidence={evidence.relative_to(ROOT).as_posix() if evidence else 'not_published'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
