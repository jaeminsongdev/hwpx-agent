"""Accept ONLY the already-recorded legacy146 root through its original oracle.

The failed NO_PDH controller remains FAILED. No Native/product replay, relabel,
generic legacy fallback, resource relaxation, queue arithmetic change or patch
to any published controller/oracle. New code is an acceptance witness, not a
retroactive Native input or successful native-backend qualification.
"""
from types import FunctionType, SimpleNamespace as NS

SELF = "tools/p09/recorded_legacy146_acceptance_v1.py"
TEST = "tools/p09/tests/test_recorded_legacy146_acceptance_v1.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case146-legacy-migration-code8-r450.v1.json"
QUAL_STATE = "PASS_PINNED146_LEGACY_MIGRATION_CODE8_NOT_ACCEPTANCE_OR_NATIVE_BACKEND"
ROOT_PIN = dict(path="implementation/p09/evidence/p09-361-case146-current-runtime-run001.v1.json",
                bytes=2714708, sha256="4cd6e3e67e157521b7353af62a3d09503813acd80cbb614d3189ac3ef1dd3234")
FAILURE_PIN = {"path":"implementation/p09/evidence/p09-361-case146-controller-connection-failure-r447.v1.json","bytes":2698,"sha256":"abe5b9b8177d6c8b891e6601bbc2d4b1c6cbb0f1fc4cf7f84025b6b72c7c6985"}


def require(ok, code):
    if not ok:
        raise ValueError("RECORDED_LEGACY146_" + code)


def checked_record(q, runtime, pin):
    step = runtime.base.CONFIG
    require(type(step.index) is int and step.index == 146 and type(step.before) is int
            and step.before == 139, "ONLY_RECORDED146_BEFORE139")
    runtime.a.exact(pin, ROOT_PIN, "ONLY_IMMUTABLE_RECORDED_ROOT")
    failure = runtime.a.read_exact(q, FAILURE_PIN)
    runtime.a.fields(failure, dict(
        state="FAILED_NATIVE_V6_CONNECTION_AFTER_REAL_PRODUCT_PASS_NOT_ACCEPTED",
        command_exit_code=2, error_code="NATIVE_CONTROLLER_V6_REAL_NATIVE_LOCAL_CONNECTION",
        official_accepted_count=139, accepted_count_delta=0,
        successful_product_replay_authorized=False, PC_freeze_resolved=False),
        "FAILED_OPTIMIZER_REMAINS_FAILED")
    runtime.a.exact(failure["root_inspection"]["root_pin"], ROOT_PIN, "SAME_FAILED_CONNECTION_ROOT")
    row = runtime.a.read_exact(q, pin)
    runtime.a.fields(row, dict(
        state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
        selected_test_index=146, stop_reason=None, closing_error_code=None,
        actual_product_child_executed=True, Native_source_frame_qualified=True,
        cleanup_confirmed=True, owned_tree_empty=True), "RECORDED_PRODUCT_NOT_NEW_BACKEND")
    info = row["serial_CPU_attribution"]
    require(info.get("backend") is None and "native_backend_connection" not in info,
            "LEGACY_DIAGNOSTIC_NOT_RELABELLED")
    runtime.a.fields(info, dict(existing_observer_instances=1, additional_PDH_queries_explicit=True,
                               second_sampler_thread_or_process=False), "ORIGINAL_PDH_FORMAT")
    return row


def qualify(q, runtime):
    pin = q.pin(QUAL_PATH)
    row = runtime.a.read_exact(q, pin)
    runtime.a.fields(row, dict(state=QUAL_STATE,
        contracts=dict(run=8, errors=0, failures=0, skipped=0),
        accepted_count_delta=0, cleanup_confirmed=True,
        Native_product_or_acceptance_executed=False), "MIGRATION_CODE_NOT_PRODUCT")
    pins = runtime.base.scope.pins(row["new_code_pins"], 2)
    require(set(pins) == {SELF, TEST}, "EXACT_TESTED_CODE2")
    for name, expected in pins.items():
        runtime.a.exact(q.pin(name), expected, "CURRENT_QUALIFIED_MIGRATION_CODE")
    runtime.a.exact(row["recorded_root_pin"], ROOT_PIN, "QUALIFIED_EXACT_ROOT")
    runtime.a.exact(row["preserved_failure_pin"], FAILURE_PIN, "PRESERVED_OPTIMIZER_FAILURE")
    return pin


def preparation(v6):
    """ONE source dependency changes back to the actual record's original oracle."""
    original = v6.API.prepare
    legacy = v6.M.API.prepare.__globals__["source"]
    connected = original.__globals__["source"]
    require(legacy.validate_candidate.__code__ is connected.validate_candidate.__code__,
            "SAME_WHOLE_CANDIDATE_BODY")
    env = dict(original.__globals__, source=legacy)
    require(set(env) == set(original.__globals__) and all(
        env[name] is value for name, value in original.__globals__.items() if name != "source"),
        "ONLY_FORMAT_DEPENDENCY_CHANGED")
    fn = FunctionType(original.__code__, env, argdefs=original.__defaults__, closure=original.__closure__)
    require(fn.__code__ is original.__code__ and fn.__defaults__ is original.__defaults__
            and fn.__closure__ is original.__closure__, "FULL_PREPARE_CODE_UNCHANGED")
    return fn


def runtime(v6):
    require(v6.SELF == "tools/p09/flat_current_queue_native_diagnostic_runtime_v6.py",
            "EXACT_RECORDED_CONTROLLER")
    full = preparation(v6)
    def prepare(q, root_pin):
        recorded = checked_record(q, v6.M, root_pin)
        qualification = qualify(q, v6.M)
        row, listing, evidence, proof = full(q, root_pin)
        v6.M.a.exact(row, recorded, "FULL_ORACLE_VALIDATED_THE_SAME_PINNED_RECORD")
        return row, listing, evidence, dict(proof, recorded_legacy146_format_route=dict(
            recorded_root_pin=ROOT_PIN, preserved_failure_pin=FAILURE_PIN,
            qualification_pin=qualification, actual_backend="ORIGINAL_PDH",
            full_original_legacy_product_source_resource_oracle_retained=True,
            failed_native_optimizer_promoted_to_success=False,
            Native_or_product_reexecuted=False, new_code_not_retroactive_Native_input=True))
    api = NS(**{**vars(v6.API), "prepare": prepare})
    return NS(**{**vars(v6.M), "SELF":v6.SELF, "TEST":v6.TEST, "API":api,
                 "own_inputs":v6.own_inputs, "data_path":v6.data_path,
                 "validate_data":v6.validate_data, "template":v6.template,
                 "context":v6.context, "validator":v6.validator})

