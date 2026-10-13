"""Bounded parent-to-worker policy data; no historical receipt IO in worker.

The parent must qualify and hold the complete source scope before dispatch.
This module preserves the original worker function, GO/Job and subprocess body.
It is not OS-wide isolation and does not qualify a product or permit queue advance.
"""
import hashlib
import json
from types import FunctionType, SimpleNamespace as NS
import runtime_envelope_raw_access_policy_v1 as raw_policy

SELF = "tools/p09/runtime_envelope_worker_connection_v1.py"
TEST = "tools/p09/tests/test_runtime_envelope_worker_connection_v1.py"
SCHEMA = "hwpx-agent.p09-envelope-worker-policy-capsule/v1"
MAX_BYTES = 16384
TASK = "case158-current-r001-tests"
AUTHORITY = dict(path="implementation/p09/evidence/p09-361-case157-current-epoch-accept001.v1.json",
    bytes=471501, sha256="9233d5bab4e2986b0993b1700a8d5fac945a3e439e5b72b13aca45bed41ea04d")
ROOT = dict(path="implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json",
    bytes=2510393, sha256="b69f11fba45c67ba367e9226bf1df5e40f95b3bfd1135574f600ed125418812b")
source = raw_policy.source


def unique(pairs):
    result = {}
    for name, value in pairs:
        source.require(name not in result, "WORKER_CAPSULE_DUPLICATE_KEY")
        result[name] = value
    return result


def encode(binding, authority_pin, root_pin, checkpoint):
    checkpoint()
    source.require(type(binding) is source.Binding, "WORKER_CAPSULE_BINDING")
    source.exact(authority_pin, AUTHORITY, "WORKER_CAPSULE_AUTHORITY151")
    source.exact(root_pin, ROOT, "WORKER_CAPSULE_ROOT157")
    row = dict(schema_version=SCHEMA, next_case=158, accepted_count_before=151,
        manifest_pin=dict(binding.manifest_pin), descriptors=binding.descriptors(),
        authority151_pin=dict(AUTHORITY), actual157_pin=dict(ROOT))
    data = json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")
    source.require(0 < len(data) <= MAX_BYTES, "WORKER_CAPSULE_SIZE")
    checkpoint()
    return data, dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def decode(data, expected_pin, checkpoint):
    checkpoint()
    source.require(type(data) is bytes and 0 < len(data) <= MAX_BYTES,
        "WORKER_CAPSULE_BOUNDED_BYTES")
    source.exact(expected_pin, dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()),
        "WORKER_CAPSULE_EXACT_TRANSPORT_BYTES")
    row = json.loads(data.decode("ascii"), object_pairs_hook=unique)
    source.require(type(row) is dict and set(row) == {"schema_version", "next_case",
        "accepted_count_before", "manifest_pin", "descriptors", "authority151_pin",
        "actual157_pin"}, "WORKER_CAPSULE_CLOSED_SCHEMA")
    source.exact({k: row[k] for k in ("schema_version", "next_case", "accepted_count_before",
        "authority151_pin", "actual157_pin")}, dict(schema_version=SCHEMA, next_case=158,
        accepted_count_before=151, authority151_pin=AUTHORITY, actual157_pin=ROOT),
        "WORKER_CAPSULE_EXACT_CONTEXT")
    binding = source.Binding(row["descriptors"], row["manifest_pin"], next_case=158)
    checkpoint()
    return binding, dict(policy_capsule_bytes=len(data), exact_capsule_hash_checked=True,
        historical_receipt_files_read_by_capsule_decoder=0,
        worker_manifest_or_original_fresh_IO_not_claimed=True,
        parent_whole_source_admission_and_live_locks_still_required=True,
        current158_product_or_worker_dispatch_qualified=False, GO_authorized=False)


def connect_worker(original, policy):
    source.require(type(original) is FunctionType and type(policy) is raw_policy.Policy,
        "WORKER_CONNECTION_EXACT_TYPES")
    state = NS(attempts=0, calls=0, completed=False, original=original)

    def execute(task):
        source.exact(task, TASK, "WORKER_CONNECTION_EXACT158_TASK")
        source.require(state.attempts == 0, "WORKER_CONNECTION_NO_AUTOMATIC_RETRY")
        state.attempts += 1
        with policy.install():
            state.calls += 1
            result = original(task)
        state.completed = True
        return result

    return execute, state


def evidence(state, policy):
    return dict(original_worker_function_code_defaults_closure_and_globals_retained=True,
        worker_attempts=state.attempts, original_worker_calls=state.calls,
        original_worker_returned=state.completed, raw_access_policy=policy.evidence(),
        original_GO_Job_subprocess_and_resource_guard_body_not_replaced=True,
        no_new_sampler_retry_thread_or_history_reader=True,
        external_Rust_child_and_unwrapped_OS_APIs_not_guarded=True,
        current158_whole_worker_dispatch_qualified=False, product_or_Gate_qualified=False,
        GO_authorized=False)
