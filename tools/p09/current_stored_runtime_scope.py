"""Current-generation runtime input composition and serial cost model only.

No file read, Native acquisition, child, GO, queue advance or Gate acceptance.
Historical logical pins are preserved at their exact archive paths; current
compiled inputs are added, never silently overlaid over a conflicting pin.
An actual runner must pin its own full imported closure/receipts, freshly check
the complete scope twice under live Native locks, and retain the original
resource/identity/cleanup oracles. This plan cannot authorize that runner.
"""
from pathlib import PurePosixPath
import re

SELF="tools/p09/current_stored_runtime_scope.py"
TEST="tools/p09/tests/test_current_stored_runtime_scope.py"
CASE112="actual_import::policy_product::fresh_policy_acl_revocation_and_source_aead_tamper_deny_cached_product"
LIST_PIN=dict(path="implementation/p09/evidence/p09-361-case112-current-stored-list-run001.v1.json",
    bytes=774020,sha256="06a9affc55cc5f9b1892a1be3649fa210822427be7020f865dccdac8acf4daf4")
EXE_PIN=dict(path="target/p09-361-case112-current-lib-check-r001/debug/deps/form_stored_provider-p361-case112-r003.exe",
    bytes=14216704,sha256="188144dfa1e758ae3a88d3d9c881df03037a6164cef1ef16de9901b2c1b4cff8")
CURRENT_LIBRARY=dict(path="crates/product-cli/src/lib.rs",bytes=26562,
    sha256="4811ee756dde8335a8ae70836dba8093684c2b7aa26c49af654e0a9c4d997323")
CURRENT_MODULE=dict(path="crates/product-cli/src/reference_validation_product.rs",bytes=6645,
    sha256="9943fe55690775ae58564c247324ae239d9218f571e804a553297be4672e28bd")
FROZEN=(
    dict(path="crates/product-cli/src/lib.rs",bytes=26524,
        sha256="0018013e7d6929533f8b072b2ee7702f195d9af4a568001935f3ee2e5e07c70d"),
    dict(path="tools/p09/resume_preserved106_queue_runtime.py",bytes=179934,
        sha256="417e8f7f1b736c07387324bb6829ed22d176ae8e8498f2977738101d32438c95"),
    dict(path="tools/p09/tests/test_preserved106_queue_runtime.py",bytes=137611,
        sha256="8ebe6bc796214808f8f67c49e59c51845af6e1c7173699f8af7f0f7241e425ac"),
)
ARCHIVES=tuple(dict(pin,path=("implementation/p09/evidence/p361-v24-product-source/" if i==0 else
    "implementation/p09/evidence/p361-v24-candidate-code/")+pin["path"]) for i,pin in enumerate(FROZEN))
FIXTURES=("fixtures/target-build/p09-42-product-form-values-01/output/five-kinds-source.hwpx",
          "fixtures/target-build/p09-42-product-form-values-01/output/five-kinds-output.hwpx")
LOCK_SECONDS=600
ORIGINAL_ACQUISITION_CEILING=14
BYTE_NATIVE_CEILING=20


def require(ok,code):
    if not ok:raise ValueError("CURRENT_STORED_RUNTIME_SCOPE_"+code)


def pins(rows,count=None):
    require(type(rows) is list and 0<len(rows)<=4096,"PIN_COUNT")
    result={}
    for row in rows:
        require(type(row) is dict and set(row)=={"path","bytes","sha256"},"PIN_SHAPE")
        name=row["path"]
        require(type(name) is str and name and not name.startswith("/")
            and not any(c in name for c in '\\:*?<>|"') and not any(ord(c)<32 for c in name)
            and all(p not in ("",".","..") and not p.endswith((" ",".")) for p in name.split("/")),"DIRECT_RELATIVE_PATH")
        require(type(row["bytes"]) is int and 0<row["bytes"]<=512*1048576
            and type(row["sha256"]) is str and re.fullmatch("[0-9a-f]{64}",row["sha256"]),"PIN_VALUE")
        require(name not in result,"DUPLICATE_PIN")
        result[name]=dict(row)
    require(count is None or (type(count) is int and len(result)==count),"EXACT_PIN_COUNT")
    return result


def listing_inputs(row):
    require(row.get("schema_version")=="hwpx-agent.p09-case112-current-stored-listing/v1"
        and row.get("state")=="PASS_CURRENT_COMPILED_STORED249_LIST_ONLY_NOT_TEST_RUNTIME_OR_GATE"
        and row.get("compiled_test_executable_pin")==EXE_PIN
        and type(row.get("exit_code")) is int and row["exit_code"]==0
        and row.get("compiled249_listing_qualified") is True and row.get("current_compiled249_qualified") is True
        and row.get("actual_EXE_list_executed") is True and row.get("source_input_bytes_checked_before_after") is True
        and row.get("cleanup_confirmed") is True and row.get("owned_tree_empty") is True
        and row.get("Native_source_frame_qualified") is False and row.get("runtime_tests_executed") is False
        and row.get("product_test_bodies_executed") is False and row.get("full249_current_qualified") is False
        and row.get("signed16_current_qualified") is False,"ACTUAL_LIST_ONLY_PARENT")
    require(all(type(row.get(k)) is int and row[k]==v for k,v in
        (("prior_queue_cases",105),("next_case",112),("accepted_count_delta",0),("whole_workspace_Rust_input_count",787))),
        "LIST_ONLY_QUEUE_UNCHANGED")
    names=row.get("source_test_names")
    require(type(names) is list and len(names)==249 and all(type(n) is str for n in names)
        and names==sorted(set(names)) and names[111]==CASE112,"EXACT_CASE112_FROM_FULL249")
    modules=row.get("source_module_instances")
    require(type(modules) is list and len(modules)==59,"FULL59_MODULE_INSTANCES")
    observed=row.get("listing_observation",{})
    require(observed.get("full_names_validated") is True and type(observed.get("test_count")) is int
        and observed["test_count"]==249 and type(observed.get("stderr_bytes")) is int
        and observed["stderr_bytes"]==0,"ACTUAL_FULL_LIST_VALIDATED")
    expected=pins(row["source_freeze"],826)
    require(expected.get(EXE_PIN["path"])==EXE_PIN,"CURRENT_BINARY_INSIDE_SOURCE_SCOPE")
    phases=row.get("input_phase_observations")
    require(type(phases) is list and len(phases)==2,"TWO_COMPLETE_LIST_PHASES")
    for phase in phases:
        require(phase.get("phase")=="completed" and phase.get("whole_source_completed") is True
            and pins(phase["completed_input_pins"],826)==expected
            and type(phase.get("reader_passes")) is int and phase["reader_passes"]==826
            and type(phase.get("bytes_read")) is int and phase["bytes_read"]==sum(p["bytes"] for p in expected.values()),
            "FULL_BYTE_SCOPE_NOT_PARTIAL_AFTER")
    return expected


def extend(required,added):
    require(type(required) is dict and type(added) is dict
        and all(type(p) is dict and p.get("path")==n for rows in (required,added) for n,p in rows.items()),
        "MAPPING_KEY_PIN_BINDING")
    left=pins(list(required.values()));right=pins(list(added.values()))
    require(all(left[n]==right[n] for n in left.keys()&right.keys()),"CONFLICT_NOT_SILENT_REBASE")
    return pins(list({**left,**right}.values()))


def compose(original,current):
    old=pins(original,1658);new=pins(current,826)
    require(all(old.get(p["path"])==p for p in FROZEN),"EXACT_THREE_FROZEN_PREIMAGES")
    require(new.get(EXE_PIN["path"])==EXE_PIN and new.get(CURRENT_LIBRARY["path"])==CURRENT_LIBRARY
        and new.get(CURRENT_MODULE["path"])==CURRENT_MODULE,"INTENTIONAL_CURRENT_BUILD_EPOCH")
    require(set(FIXTURES)<=set(old),"HISTORICAL_CASE_FIXTURES_RETAINED")
    archived=dict(old)
    for before,after in zip(FROZEN,ARCHIVES):
        require(after["path"] not in archived,"ARCHIVE_DISJOINT_FROM_ORIGINAL")
        archived.pop(before["path"]);archived[after["path"]]=dict(after)
    require(len(archived)==1658 and sum(p["bytes"] for p in archived.values())==sum(p["bytes"] for p in old.values()),
        "LOSSLESS_ORIGINAL_ARCHIVE_PROJECTION")
    result=extend(archived,new)
    require(all(result[n]==p for n,p in archived.items()) and all(result[n]==p for n,p in new.items()),
        "COMPLETE_ORIGINAL_AND_CURRENT_UNION")
    return result


def cost(required,acquisition_rate,*,extra_byte_open_reservations=0):
    rows=pins(list(required.values()))
    require(type(acquisition_rate) is int and 1<=acquisition_rate<=ORIGINAL_ACQUISITION_CEILING,"ORIGINAL_RATE_CEILING")
    require(type(extra_byte_open_reservations) is int and extra_byte_open_reservations>=0,"EXTRA_OPEN_ACCOUNTING")
    directories=len({parent.as_posix() for name in rows for parent in PurePosixPath(name).parents})
    require(len(rows)+directories<=8192,"ORIGINAL_HANDLE_CEILING")
    binary=sum(p["bytes"] for n,p in rows.items() if n.lower().endswith(".exe"))
    other=sum(p["bytes"] for n,p in rows.items() if not n.lower().endswith(".exe"))
    require(binary>0 and other>0,"ALL_BINARY_AND_OTHER_BYTES")
    acquire=(len(rows)+directories)/acquisition_rate
    byte=2*binary/1048576+2*other/2097152
    native=(2*len(rows)+extra_byte_open_reservations)/BYTE_NATIVE_CEILING
    total=acquire+byte+native+4+60
    return dict(inputs=len(rows),directories=directories,binary_bytes=binary,other_bytes=other,
        selected_acquisition_rate_per_second=acquisition_rate,
        original_acquisition_ceiling_per_second=ORIGINAL_ACQUISITION_CEILING,
        unchanged_byte_native_ceiling_per_second=BYTE_NATIVE_CEILING,
        acquisition_reservations=len(rows)+directories,native_acquisition_seconds=acquire,
        two_actual_byte_pass_native_reservations=2*len(rows),extra_byte_open_reservations=extra_byte_open_reservations,
        all_native_byte_open_pacing_seconds=native,two_actual_byte_pass_nominal_seconds=byte,
        nominal_early_yield_allowance_seconds=4,unallocated_margin_seconds=60,
        predicted_combined_seconds=total,unchanged_lock_deadline_seconds=LOCK_SECONDS,
        nominal_fits_unchanged_deadline=total<LOCK_SECONDS,byte_and_native_costs_assumed_overlapped=False,
        idle_pacer_credit_assumed=False,estimate_not_completion_guarantee=True,
        actual_runner_closure_qualified=False,Native_source_frame_qualified=False,
        GO_authorized=False,queue_advance_authorized=False,PC_freeze_improvement_claimed=False)


def select_cost(required,*,extra_byte_open_reservations=0):
    # 기존9/s부터 원14/s 이하만 검토한다. CPU/메모리/600s 상한을 올리지 않는다.
    for rate in range(9,ORIGINAL_ACQUISITION_CEILING+1):
        result=cost(required,rate,extra_byte_open_reservations=extra_byte_open_reservations)
        if result["nominal_fits_unchanged_deadline"]:return result
    raise ValueError("CURRENT_STORED_RUNTIME_SCOPE_NO_SAFE_ORIGINAL_BUDGET")
