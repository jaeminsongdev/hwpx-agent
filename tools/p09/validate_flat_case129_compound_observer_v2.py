"""Pure compound contract with the qualified full-source observer epoch.

새 권위 수용기의 입력 계약이다. 파일/프로세스/Native 실행이나 queue 변경은
하지 않는다. 원 v1 전체 source/body oracle을 유지하며 observer·이전1904
입력·고정 receipt 결속을 추가한다. 호출자가 현재 byte 결속을 수행해야 한다.
"""
import math

import validate_flat_case129_compound_v1 as prior

a, scope, source = prior.a, prior.scope, prior.source
SELF = "tools/p09/validate_flat_case129_compound_observer_v2.py"
TEST = "tools/p09/tests/test_validate_flat_case129_compound_observer_v2.py"
PASS = "PASS_PRESERVED129_OBSERVER_COMPOUND_CONTRACT_NOT_FRESH_BINDING_OR_QUEUE_ACCEPTANCE"
SOURCE_PIN = dict(path="implementation/p09/evidence/p09-361-case129-independent-full-source-run002.v1.json",
    bytes=2365041, sha256="b4684672cfdd81c01237098904070208198a063841f725eb7e7e987a3973514f")
CONNECTION_PIN = dict(path="implementation/p09/evidence/p09-361-whole-source-observer-connection-code-r317.v1.json",
    bytes=4518, sha256="2204d686e5e0fd122b8eb76ebcf16dd1e94895e7ae43c308c19ed66fed8d819a")
OBSERVER_PIN = dict(path="implementation/p09/evidence/p09-361-warning-only-observer-code15-r312.v1.json",
    bytes=3296, sha256="f178efd3f9fe39f1a83e2230f486f202a9255447a76232a088b5a8b782300d65")
REAL_PIN = dict(path="implementation/p09/evidence/p09-361-warning-only-observer-real-light-r313.v1.json",
    bytes=5796, sha256="baff2d0bcfc10746a16999f66262592010b5a4851b404abfdf623bf4f594d581")
PREVIOUS_PIN = dict(path="implementation/p09/evidence/p09-361-case129-independent-full-source-run001.v1.json",
    bytes=500493, sha256="5acd00d741b421a51f40e514d2b53a191d451716b8132f52dd012c661bcdd8ba")
CONNECTION_FILES = ("tools/p09/close_flat_case129_preserved_source_observer_v2.py",
    "tools/p09/tests/test_close_flat_case129_preserved_source_observer_v2.py")
OBSERVER_FILES = ("tools/p09/warning_only_serial_attribution_v1.py",
    "tools/p09/tests/test_warning_only_serial_attribution_v1.py")


def require(ok, code):
    if not ok:
        raise ValueError("OBSERVER_COMPOUND_" + code)


def integer(value, code):
    require(type(value) is int and value >= 0, code)
    return value


def number(value, code):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, code)
    return value


def covered(required, pins, checkpoint):
    """Bounded fixed pin lists only; no current filesystem freshness claim."""
    require(type(pins) is list and 0 < len(pins) <= 64, "BOUNDED_DEPENDENCY_PINS")
    selected = scope.pins(pins, len(pins))
    for name, pin in selected.items():
        checkpoint()
        a.exact(required.get(name), pin, "EVERY_QUALIFIED_DEPENDENCY_IN_NATIVE_SCOPE")
    return selected


def validate_epoch(row, pin, previous, connection, observed, real, checkpoint):
    require(callable(checkpoint), "ORIGINAL_CHECKPOINT_REQUIRED")
    prior.source_header(row)  # 실패 header는 전체 입력 순회 전에 거절한다.
    a.exact(pin, SOURCE_PIN, "EXACT_SOURCE002_RECEIPT")
    require(row.get("synthetic_fixture_only_not_evidence") is not True, "NO_SYNTHETIC_SOURCE")
    epoch = row["source_observer_epoch"]
    a.fields(epoch, dict(schema_version="hwpx-agent.p09-full-source-warning-only-observer/v2",
        qualification_pin=CONNECTION_PIN, observer_qualification_pin=OBSERVER_PIN,
        real_light_observer_pin=REAL_PIN, prior_failed_source_pin=PREVIOUS_PIN,
        original_run_and_guard_init_bytecode=True, default_module_classes_mutated=False,
        previous1904_source_inputs_retained=True, PDH_cleanup_confirmed=True,
        original_PDH_allowance_seconds=2.05, old_failed_root_promoted=False,
        product_body_replayed=False, causal_trigger_or_freeze_fix_established=False), "EXACT_OBSERVER_EPOCH")
    a.fields(connection, dict(state="PASS_WHOLE_SOURCE_OBSERVER_CONNECTION_CODE_NOT_ACTUAL_SOURCE_OR_QUEUE",
        accepted_count_after=122, accepted_count_delta=0, cleanup_confirmed=True,
        previous_failed_source_pin=PREVIOUS_PIN, source_qualification_pin=prior.QUAL_PIN,
        observer_code_qualification_pin=OBSERVER_PIN, real_light_observer_pin=REAL_PIN), "CONNECTION_QUALIFICATION")
    a.exact(connection["contracts"], dict(run=10, errors=0, failures=0, skipped=0), "CONNECTION10")
    a.exact(observed["contracts"], dict(run=15, errors=0, failures=0, skipped=0), "OBSERVER15")
    a.fields(observed, dict(cleanup_confirmed=True, accepted_count_after=122,
        accepted_count_delta=0), "OBSERVER_CODE_CLEANUP")
    a.fields(real, dict(state="PASS_REAL_WARNING_ONLY_OBSERVER_LIGHT_CONNECTION_NOT_FULL_SOURCE_OR_QUEUE",
        exact_original_Guard_init_code=True, default_Windows_and_Guard_classes_mutated=False,
        preparation_cleanup_confirmed=True, real_guard_cleanup_confirmed=True,
        PDH_cleanup_confirmed=True, actual_Native_source_executed=False), "REAL_LIGHT_QUALIFICATION")
    a.fields(previous, dict(state="FAILED_NOT_QUALIFIED",
        error_code="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", accepted_count_after=122,
        accepted_count_delta=0, independent_source_frame_qualified=False,
        original_product_body_replayed=False, resource_cleanup_confirmed=True,
        source_frame_cleanup_confirmed=True), "PREVIOUS_FAILURE_PRESERVED")
    a.fields(previous["source_frame"], dict(frame_state="CLOSED", registered_live_frame=False,
        actual_byte_boundaries=[]), "PREVIOUS_FRAME_CLOSED")
    a.fields(previous["source_frame"]["handles"], dict(input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
        active_reader_bindings=0, active_byte_streams=0), "PREVIOUS_HANDLES_CLOSED")
    checkpoint()
    required = scope.pins(row["required_source_pins"])
    old = scope.pins(previous["required_source_pins"])
    require(len(old) == 1904 and len(required) == 1913, "COMPLETE1904_TO1913_SCOPE")
    for index, (name, expected) in enumerate(old.items()):
        if index % 64 == 0:
            checkpoint()
        a.exact(required.get(name), expected, "EVERY_PREVIOUS_INPUT_RETAINED")
    for expected in (CONNECTION_PIN, OBSERVER_PIN, REAL_PIN, PREVIOUS_PIN):
        a.exact(required.get(expected["path"]), expected, "ALL_OBSERVER_RECEIPTS_IN_NATIVE_SCOPE")
    connected = covered(required, connection["new_code_pins"], checkpoint)
    require(set(connected) == set(CONNECTION_FILES), "EXACT_CONNECTION_CODE2")
    observers = covered(required, observed["new_code_pins"], checkpoint)
    require(set(observers) == set(OBSERVER_FILES), "EXACT_OBSERVER_CODE2")
    covered(required, observed["unchanged_dependency_pins"], checkpoint)
    covered(required, real["bound_source_pins"], checkpoint)
    observer = epoch["observer"]
    a.fields(observer, dict(existing_observer_instances=1, original_warning_percent=75,
        no_cold_PDH_collect_or_formatted_read=True,
        same_original_Probe_constructor_baseline_required=True,
        original_seven_counter_PID_binding_and_cost_budget_retained=True,
        original_K32_CPU_RAM_decisions_replaced=False, second_sampler_thread_or_process=False,
        runtime_connection_qualified=False, measured_Native_CPU_or_PC_freeze_improvement_proven=False),
        "SOLE_UNCHANGED_OBSERVER")
    require(type(observer["probes"]) is list and len(observer["probes"]) == 1, "EXACT_SINGLE_PROBE")
    probe = observer["probes"][0]
    a.fields(probe, dict(fixed_counter_count=7, wildcard_or_process_inventory=False,
        maximum_sample_budget_seconds=.05, total_added_sample_budget_seconds=2.0,
        query_remaining=False, cleanup_confirmed=True, close_attempts=1,
        original_K32_CPU_RAM_decisions_replaced=False, second_sampler_thread_or_process=False,
        cost_checked_before_formatted_reads=True,
        original_seven_counter_PID_status_and_final_cost_checks_retained=True,
        original_CPU_RAM_guards_replaced=False, runtime_connection_qualified=False,
        PC_freeze_resolved=False, security_sandbox_or_CPU_freeze_improvement_claimed=False),
        "ORIGINAL_PDH_BUDGET_AND_CLEANUP")
    checks, cold, warnings, hard = [integer(probe[key], "TYPED_OBSERVER_COUNTERS")
        for key in ("warning_only_checks", "cold_skips", "warning_only_reads", "hard_resource_skips")]
    samples = row["resource_samples"]
    require(type(samples) is list and 0 < len(samples) <= 4096, "BOUNDED_ALL_ORIGINAL_SAMPLES")
    a.exact(checks, len(samples), "EVERY_SAMPLE_ACCOUNTED")
    a.exact(cold + warnings + hard, checks, "NO_SKIPPED_OR_DUPLICATE_SAMPLE")
    # 실제002는 모두 cold다. warning 표본을 cold로 바꾼 위조는 허용하지 않는다.
    require(warnings == hard == 0 and cold == checks, "ACTUAL_SOURCE002_COLD_ONLY")
    for index, sample in enumerate(samples):
        if index % 64 == 0:
            checkpoint()
        cpu = number(sample["system_cpu_percent"], "FINITE_ORIGINAL_CPU")
        require(cpu < 75, "NO_WARNING_RELABELED_AS_COLD")
        _, stop = source.c.decision(sample, 0)
        require(stop is None, "NO_HARD_STOP_RELABELED_AS_COLD")
    a.fields(probe, dict(collect_calls=1, samples=0, early_budget_checks=0,
        early_budget_stops=0, maximum_added_sample_seconds=0.0,
        total_added_sample_seconds=0.0, disabled_reason=None), "BASELINE_ONLY_NO_COLD_PDH_READ")
    number(probe["setup_seconds"], "FINITE_SETUP_COST")
    checkpoint()
    return dict(full_source_pin=SOURCE_PIN, previous_failed_source_pin=PREVIOUS_PIN,
        connection_qualification_pin=CONNECTION_PIN, observer_qualification_pin=OBSERVER_PIN,
        real_light_observer_pin=REAL_PIN, all_previous1904_inputs_retained=True,
        sole_observer_samples=checks, cold_PDH_queries_skipped=cold,
        original_constructor_baseline_collects=1, PDH_cleanup_confirmed=True)


def validate(original, original_pin, row, pin, authority, authority_pin, listing,
             qualification, qualification_pin, previous, connection, observed, real, checkpoint):
    epoch = validate_epoch(row, pin, previous, connection, observed, real, checkpoint)
    result = prior.validate(original, original_pin, row, pin, authority, authority_pin,
        listing, qualification, qualification_pin, checkpoint)
    a.exact(result["state"], prior.PASS, "UNCHANGED_FULL_BODY_AND_NATIVE_ORACLE")
    return dict(result, state=PASS, source_observer_epoch_validation=epoch,
        original_full_compound_oracle_retained=True,
        fresh_receipt_binding_still_required=True, qualified_next130_branch_still_required=True,
        authoritative_counter_or_queue_write_performed=False)
