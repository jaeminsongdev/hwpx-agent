"""Fresh exact-identity parent fallback; no backend qualification from mocks."""
import json
from pathlib import Path
import re
import subprocess
import time

import conservative_maintenance as c
import sql_container_ownership as ownership
from bounded_process_progress import bounded_observation_run
from owned_sql_job import OwnedSQLJobProcess
from sql_call_supervisor import grace_resource_checkpoint, valid_clock
from sql_runtime_supervision import LOCAL_DOCKER_HOST, local_docker_environment

MAX_QUERY_BYTES, MAX_CLEANUP_SECONDS = 16384, 15


def absent(result):
    c.require(type(result.returncode) is int and isinstance(result.stderr, str)
        and len(result.stderr.encode("utf-8")) <= MAX_QUERY_BYTES, "SQL_OWNED_CLEANUP_ERROR_SCOPE")
    return result.returncode != 0 and re.search(r"no such (object|container)", result.stderr, re.I) is not None


def inspect_item(result):
    c.require(type(result.returncode) is int and result.returncode == 0 and isinstance(result.stdout, str)
        and len(result.stdout.encode("utf-8")) <= MAX_QUERY_BYTES, "SQL_OWNED_CLEANUP_INSPECT_SCOPE")
    try:
        rows = json.loads(result.stdout, object_pairs_hook=ownership.unique_object)
    except json.JSONDecodeError:
        raise ValueError("SQL_OWNED_CLEANUP_JSON_INVALID") from None
    c.require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), "SQL_OWNED_CLEANUP_AMBIGUOUS")
    return rows[0]


def owned_item(item, intent, expected_id=None):
    c.require(isinstance(item, dict) and isinstance(item.get("Id"), str)
        and re.fullmatch(r"[0-9a-f]{64}", item["Id"]), "SQL_OWNED_CLEANUP_ID_SCOPE")
    host = item["HostConfig"]
    c.require((expected_id is None or item["Id"] == expected_id)
        and item["Name"] == "/"+intent["container_name"]
        and item["Config"]["Labels"].get(intent["label_key"]) == intent["run_id"]
        and item["Config"]["Image"] == intent["image_pin"] and item["Image"] == intent["image_id"],
        "SQL_OWNED_CLEANUP_IDENTITY_MISMATCH")
    bindings = host["PortBindings"]
    c.require(host["NetworkMode"] == "bridge" and set(bindings) == {"5432/tcp"}
        and len(bindings["5432/tcp"]) == 1 and bindings["5432/tcp"][0]["HostIp"] == "127.0.0.1"
        and not item["Mounts"] and host["ReadonlyRootfs"] is True and host["NanoCpus"] == 1000000000
        and host["Memory"] == host["MemorySwap"] == 536870912 and host["PidsLimit"] == 64
        and set(host["Tmpfs"]) == {"/var/lib/postgresql", "/tmp", "/var/run/postgresql"},
        "SQL_OWNED_CLEANUP_ISOLATION_MISMATCH")
    return item["Id"]


def closed_error(error):
    value = str(error) if isinstance(error, ValueError) else "SQL_OWNED_CLEANUP_OPERATION_FAILED"
    return value if len(value) <= 160 and re.fullmatch(r"SQL_OWNED_[A-Z_]+|STOP_[A-Z_]+|OWNED_SQL_[A-Z_]+", value) \
        else "SQL_OWNED_CLEANUP_REDACTED_FAILURE"


def cleanup_from_intent(intent, command):
    row = {"state": "FAILED_NOT_ACCEPTED", "stage": "intent", "container_id": None,
        "command_response_removal_verified": False, "backend_container_cleanup_confirmed": None,
        "owned_host_job_profiles": [], "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "P09_gate": "OPEN", "product_complete": False}
    try:
        intent = ownership.validate_intent(intent, intent["parent_nonce"], intent["case"])
        c.require(callable(command), "SQL_OWNED_CLEANUP_COMMAND_REQUIRED")
        row["stage"] = "fresh_owned_lookup"
        observed = command(["inspect", intent["container_name"]])
        if observed.returncode != 0:
            c.require(absent(observed), "SQL_OWNED_CLEANUP_LOOKUP_UNVERIFIED")
            row["command_response_removal_verified"] = True
            row["state"] = "OWNED_TARGET_ABSENT_FROM_COMMAND_RESPONSE_NOT_SQL_OR_GATE"
        else:
            identifier = owned_item(inspect_item(observed), intent)
            row["container_id"], row["stage"] = identifier, "owned_id_remove"
            removed = command(["rm", "--force", identifier])
            c.require(type(removed.returncode) is int and removed.returncode == 0, "SQL_OWNED_CLEANUP_REMOVAL_FAILED")
            row["stage"] = "removed_id_absence"
            c.require(absent(command(["inspect", identifier])), "SQL_OWNED_CLEANUP_REMOVAL_UNVERIFIED")
            row["command_response_removal_verified"] = True
            row["state"] = "OWNED_TARGET_REMOVAL_FROM_COMMAND_RESPONSE_NOT_SQL_OR_GATE"
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", closed_error(error)
    finally:
        if isinstance(command, OwnedCleanupCommand):
            row["owned_host_job_profiles"] = [dict(profile) for profile in command.profiles]
            clean = bool(command.profiles) and all((profile.get("limits_readback") or {}).get("verified") is True
                and all(profile.get(key) is True for key in ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed"))
                and (profile.get("last_job_accounting") or {}).get("active_processes") == 0 for profile in command.profiles)
            if not clean:
                row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", "SQL_OWNED_CLEANUP_HOST_TEARDOWN_UNVERIFIED"
            elif row["command_response_removal_verified"]:
                row["backend_container_cleanup_confirmed"] = True
    return row


class OwnedCleanupCommand:
    """Only fresh admitted name/ID; fixed local npipe, three bounded owned CLI jobs."""
    def __init__(self, intent, parent_result, resources, docker):
        self.intent = ownership.validate_intent(intent, intent["parent_nonce"], intent["case"])
        c.require(isinstance(parent_result, dict), "SQL_OWNED_CLEANUP_PARENT_TREE_NOT_CLOSED")
        profile = parent_result.get("owned_job_profile") or {}
        final = profile.get("last_job_accounting") or {}
        c.require(all(profile.get(key) is True for key in ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed"))
            and type(final.get("active_processes")) is int
            and final["active_processes"] == 0, "SQL_OWNED_CLEANUP_PARENT_TREE_NOT_CLOSED")
        path = Path(docker)
        c.require(path.is_absolute() and path.is_file() and not path.is_symlink() and not path.is_junction(),
            "SQL_OWNED_CLEANUP_DOCKER_EXECUTABLE_SCOPE")
        self.docker, self.resources, self.admitted_id, self.profiles = docker, resources, None, []
        self.started = time.monotonic()
        self.calls = 0

    def __call__(self, arguments):
        c.require(isinstance(arguments, list) and all(isinstance(arg, str) for arg in arguments)
            and self.calls < 3, "SQL_OWNED_CLEANUP_COMMAND_BUDGET")
        name = self.intent["container_name"]
        allowed = [["inspect", name]]
        if self.admitted_id is not None:
            allowed += [["rm", "--force", self.admitted_id], ["inspect", self.admitted_id]]
        c.require(arguments in allowed, "SQL_OWNED_CLEANUP_TARGET_NOT_ADMITTED")
        actual = [self.docker, "--host", LOCAL_DOCKER_HOST, *arguments]
        holders = []
        self.calls += 1
        def checkpoint():
            now = valid_clock(time.monotonic, self.started)
            c.require(now-self.started <= MAX_CLEANUP_SECONDS, "STOP_SQL_OWNED_CLEANUP_WALL_TIME")
            grace_resource_checkpoint(self.resources, now)
        def factory(args, **kwargs):
            c.require(args == actual and kwargs.get("cwd") == c.ROOT
                and kwargs.get("stdin") == kwargs.get("stdout") == kwargs.get("stderr") == subprocess.PIPE
                and kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,
                "SQL_OWNED_CLEANUP_LAUNCH_SCOPE")
            owned = OwnedSQLJobProcess(actual, windows=self.resources.windows, allowed_executables=[self.docker],
                cwd=c.ROOT, checkpoint=checkpoint, env=local_docker_environment())
            holders.append(owned)
            return owned
        try:
            result = bounded_observation_run(actual, cwd=c.ROOT, timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS, process_factory=factory)
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            if hasattr(error, "owned_sql_job_profile") and not holders:
                self.profiles.append(dict(error.owned_sql_job_profile))
            raise
        finally:
            self.profiles.extend(dict(owned.profile) for owned in holders)
        c.require(len(holders) == 1 and all(holders[0].profile.get(key) is True
            for key in ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed")), "SQL_OWNED_CLEANUP_QUERY_TEARDOWN_FAILED")
        # 마지막 조회와 pipe/Job teardown 시간도 전체 budget과 host 정책에 포함한다.
        checkpoint()
        if arguments == ["inspect", name] and result.returncode == 0:
            identifier = owned_item(inspect_item(result), self.intent, self.admitted_id)
            self.admitted_id = identifier
        return result


def parent_fallback_cleanup(nonce, case, parent_result, resources, docker):
    checked = ownership.load_intent(nonce, case)
    command = OwnedCleanupCommand(checked["intent"], parent_result, resources, docker)
    row = cleanup_from_intent(checked["intent"], command)
    row["journal_pin"] = checked["journal_pin"]
    return row
