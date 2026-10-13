"""Bounded local daemon identity and fixed-image removal events; never pull or prune."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone

import conservative_maintenance as c
from bounded_process_progress import bounded_observation_run
from owned_sql_job import OwnedSQLJobProcess
from qualify_sql_runtime_environment import SOURCES as READINESS_SOURCES
from run_formula_issuer_registry_sql_checks import IMAGE
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher, LOCAL_DOCKER_HOST, local_docker_environment
from live_sql_evidence_reader import LiveSQLReader

SOURCES = list(dict.fromkeys(READINESS_SOURCES+["tools/p09/observe_fixed_sql_image_store.py",
    "implementation/p09/source-archive/p09-149-pre-image-store-query-diagnostic/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-image-store-gone-filter/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-image-store-query-phase-reset/source-preimages.v1.json"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-fixed-SQL-image-store.run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists()
        and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "SQL_STORE_FRESH_RECEIPT_REQUIRED")
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    until = int(time.time())
    row = {"schema_version": "hwpx-agent.p09-fixed-SQL-image-store/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "daemon_ID_sha256": None, "fixed_image_present": None, "image_id": None,
        "image_removal_events": [], "event_window_start_unix": until-3600, "event_window_end_unix": until,
        "event_history_may_be_truncated_or_lost_on_restart": True, "image_loss_cause_qualified": False,
        "owned_host_job_profiles": [], "last_query": None, "last_exit_code": None,
        "container_created_or_pulled_or_pruned": False, "system_or_WSL_or_Docker_settings_changed": False,
        "actual_SQL_product_executed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        docker = shutil.which("docker")
        c.require(docker and Path(docker).is_absolute() and Path(docker).is_file()
            and not Path(docker).is_symlink() and not Path(docker).is_junction(), "SQL_STORE_DOCKER_SCOPE")
        base = [docker, "--host", LOCAL_DOCKER_HOST]
        commands = [
            ("daemon", base+["info", "--format", "{{json .ID}}|{{json .SystemTime}}"]),
            ("image", base+["image", "inspect", IMAGE, "--format", "{{json .Id}}"]),
            ("removals", base+["events", "--since", str(until-3600), "--until", str(until),
                "--filter", "type=image", "--filter", "event=delete", "--filter", "event=untag",
                "--format", "{{json .Type}}|{{json .Action}}|{{json .Actor.ID}}|{{json .Time}}"]),
        ]
        resources.start()
        for kind, command in commands:
            row["last_query"] = kind
            row["last_exit_code"] = None
            row["query_error_categories"] = None
            holders = []
            def checkpoint():
                c.require(time.monotonic()-started <= 30, "STOP_SQL_STORE_SCOPE_TIME")
                resources.checkpoint_io()
            def factory(actual, **kwargs):
                c.require(actual == command and kwargs.get("cwd") == c.ROOT, "SQL_STORE_COMMAND_SCOPE")
                owned = OwnedSQLJobProcess(actual, windows=resources.windows, allowed_executables=[docker],
                    cwd=c.ROOT, env=local_docker_environment(), checkpoint=checkpoint)
                holders.append(owned)
                return owned
            try:
                result = bounded_observation_run(command, cwd=c.ROOT, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,
                    process_factory=factory)
            finally:
                row["owned_host_job_profiles"].extend(dict(owned.profile) for owned in holders)
            c.require(len(holders) == 1 and all(holders[0].profile.get(key) is True for key in
                ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed")), "SQL_STORE_CLEANUP_FAILED")
            row["last_exit_code"] = result.returncode
            if result.returncode != 0:
                categories = {"invalid_filter": r"invalid.*filter|filter.*invalid",
                    "unknown_flag": r"unknown flag|unknown shorthand flag",
                    "template_error": r"template parsing|template.*error",
                    "API_version_error": r"API version|client version.*new|client version.*old",
                    "daemon_connection_failed": r"cannot connect|error during connect|connection refused|pipe.*not find",
                    "not_supported": r"not supported|not implemented|unknown command",
                    "authorization_denied": r"unauthorized|access.*denied|permission.*denied",
                    "image_missing": r"no such image",
                    "unexpected_argument": r"requires.*argument|accepts.*argument|unknown.*argument",
                    "backend_unavailable": r"unavailable|internal server error|500 Internal",
                    "object_not_found": r"404|not found"}
                row["query_error_categories"] = [name for name, pattern in categories.items()
                    if re.search(pattern, result.stderr, re.I)] or ["unclassified_failure"]
            if kind == "image" and result.returncode != 0 and re.search(r"no such image", result.stderr, re.I):
                row["fixed_image_present"] = False
                continue
            c.require(result.returncode == 0, "SQL_STORE_READONLY_QUERY_FAILED")
            if kind == "daemon":
                parts = result.stdout.strip().split("|")
                c.require(len(parts) == 2, "SQL_STORE_DAEMON_METADATA_SCOPE")
                value, daemon_time = [json.loads(part) for part in parts]
                c.require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9:-]{8,128}", value),
                    "SQL_STORE_DAEMON_ID_SCOPE")
                row["daemon_ID_sha256"] = hashlib.sha256(value.encode()).hexdigest()
                c.require(isinstance(daemon_time, str) and len(daemon_time) <= 48,
                    "SQL_STORE_DAEMON_CLOCK_SCOPE")
                stamp = datetime.fromisoformat(daemon_time.replace("Z", "+00:00"))
                c.require(stamp.tzinfo is not None, "SQL_STORE_DAEMON_CLOCK_SCOPE")
                until = int(stamp.timestamp())-1
                row["daemon_time_UTC"] = stamp.astimezone(timezone.utc).isoformat()
                row["daemon_minus_client_seconds"] = round(stamp.timestamp()-time.time(), 3)
                row["event_window_start_unix"], row["event_window_end_unix"] = until-3600, until
                # PC/WSL 시각을 바꾸지 않고 조회 종료 시각만 엔진의 과거 시각에 결합한다.
                events = commands[2][1]
                events[events.index("--since")+1] = str(until-3600)
                events[events.index("--until")+1] = str(until)
            elif kind == "image":
                value = json.loads(result.stdout)
                c.require(isinstance(value, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value),
                    "SQL_STORE_IMAGE_ID_SCOPE")
                row["fixed_image_present"], row["image_id"] = True, value
            else:
                lines = result.stdout.splitlines()
                c.require(len(lines) <= 256, "SQL_STORE_EVENT_COUNT_SCOPE")
                for line in lines:
                    parts = line.split("|")
                    c.require(len(parts) == 4, "SQL_STORE_EVENT_FORMAT_SCOPE")
                    kind, action, actor, timestamp = [json.loads(part) for part in parts]
                    c.require(kind == "image" and action in {"delete", "untag"}
                        and isinstance(actor, str) and re.fullmatch(r"(?:sha256:)?[a-f0-9]{64}", actor)
                        and type(timestamp) is int and until-3600 <= timestamp <= until,
                        "SQL_STORE_EVENT_SCOPE")
                    # 이벤트 속성·라벨 원문은 저장하지 않고 허용된 최소 항목만 남긴다.
                    digest = IMAGE.split("@", 1)[1]
                    if actor in {digest, digest.split(":", 1)[1]}:
                        row["image_removal_events"].append({"action": action, "image_ID": actor, "time_unix": timestamp})
        row["state"] = "PASS_LOCAL_IMAGE_STORE_OBSERVATION_ONLY_NOT_CAUSE_SQL_PRODUCT_OR_GATE"
    except subprocess.TimeoutExpired:
        row["error_code"] = "SQL_STORE_QUERY_TIMEOUT"
        row["query_error_categories"] = ["bounded_query_timeout"]
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "SQL_STORE_OPERATION_FAILED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "SQL_STORE_REDACTED_FAILURE"
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_STORE_FINAL_FRESHNESS_FAILED"
        finish_watcher(resources, row)
        if resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in
            ("state", "fixed_image_present", "last_query", "last_exit_code", "elapsed_seconds")}))
        if "query_error_categories" in row:
            print(json.dumps({"query_error_categories": row["query_error_categories"]}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
