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
WIDGET = ROOT / "web/plugin-widget/dist/plan-review-widget-v1.html"
HARNESS = ROOT / "web/plugin-widget/dist/plan-review-e2e-host.html"
EVIDENCE_ROOT = ROOT / "artifacts/p16/evidence/plan-review-e2e-runs"
PASS_TEXT = "PASS calls=5 order=capability_check,document_edit(dry),capability_check,document_edit(dry),document_edit(execute)"
RESULT_PATTERN = re.compile(r'<p id="e2e-result" data-state="(?P<state>[a-z]+)">(?P<text>[^<]*)</p>')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def find_chrome() -> Path | None:
    override = os.environ.get("HWPX_AGENT_CHROME")
    candidates = [Path(override) if override else None, Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"), Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")]
    command = shutil.which("google-chrome") or shutil.which("chrome")
    if command:
        candidates.append(Path(command))
    return next((candidate for candidate in candidates if candidate and candidate.is_file()), None)

def run_e2e(chrome: Path) -> dict[str, object]:
    if not WIDGET.is_file() or not HARNESS.is_file():
        raise RuntimeError("PLAN_REVIEW_E2E_BUNDLE_MISSING")
    with tempfile.TemporaryDirectory(prefix="hwpx-p16-06-e2e-") as profile:
        command = [str(chrome), "--headless=new", "--disable-background-networking", "--disable-component-update", "--disable-default-apps", "--disable-gpu", "--disable-sync", "--metrics-recording-only", "--no-default-browser-check", "--no-first-run", "--allow-file-access-from-files", "--host-resolver-rules=MAP * ~NOTFOUND", "--virtual-time-budget=12000", f"--user-data-dir={profile}", "--dump-dom", HARNESS.as_uri()]
        completed = subprocess.run(command, cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    text = completed.stdout.decode("utf-8", errors="replace")
    match = RESULT_PATTERN.search(text)
    if completed.returncode != 0:
        raise RuntimeError(f"PLAN_REVIEW_E2E_CHROME_EXIT:{completed.returncode}")
    if match is None:
        raise RuntimeError("PLAN_REVIEW_E2E_RESULT_MISSING")
    if match.group("state") != "pass" or match.group("text") != PASS_TEXT:
        raise RuntimeError(f"PLAN_REVIEW_E2E_FAILED:{match.group('text')[:120]}")
    return {
        "schema_version": "hwpx-agent.p16-plan-review-e2e-receipt/v1", "state": "pass",
        "scope": "local_headless_browser_mcp_apps_bridge_component", "browser_executable": chrome.name,
        "resource": {"path": WIDGET.relative_to(ROOT).as_posix(), "bytes": WIDGET.stat().st_size, "sha256": sha256(WIDGET)},
        "harness": {"path": HARNESS.relative_to(ROOT).as_posix(), "bytes": HARNESS.stat().st_size, "sha256": sha256(HARNESS)},
        "assertions": {"bridge": "real_ext_apps_appbridge_postmessage_iframe", "call_count": 5, "call_order": ["capability_check", "document_edit_dry", "capability_check", "document_edit_dry", "document_edit_execute"], "execution_requires_review_acknowledgement_and_second_click": True, "route_and_base_identity_checked": True, "distinct_idempotency_keys": True, "server_reauthorization_required": True},
        "claims": {"actual_chatgpt_or_codex_host_tested": False, "developer_mode_tested": False, "registered_plugin_tested": False, "remote_mcp_tested": False, "hangul_or_com_invoked": False},
    }

def publish(receipt: dict[str, object]) -> Path:
    run_id = uuid.uuid4().hex
    directory = EVIDENCE_ROOT / run_id
    directory.mkdir(parents=True, exist_ok=False)
    destination = directory / "receipt.json"
    payload = (json.dumps(receipt | {"run_id": run_id}, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = directory / "receipt.json.partial"
    temporary.write_bytes(payload)
    temporary.replace(destination)
    return destination

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local MCP Apps iframe plan-review E2E.")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    chrome = find_chrome()
    if chrome is None:
        raise RuntimeError("PLAN_REVIEW_E2E_CHROME_NOT_FOUND")
    receipt = run_e2e(chrome)
    evidence = publish(receipt) if args.publish else None
    print(f"P16_PLAN_REVIEW_E2E_PASS calls={receipt['assertions']['call_count']} widget_bytes={receipt['resource']['bytes']} evidence={evidence.relative_to(ROOT).as_posix() if evidence else 'not_published'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
