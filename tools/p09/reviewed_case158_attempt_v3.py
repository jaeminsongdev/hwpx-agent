"""Distinct158/run002 with the original single physical argument adapter.

No function body/source deadline/worker or historical namespace is rewritten.
Clone the explicit template dependency chain; never stack a second adapter or
change an actual recorded path/task to make it look like another attempt.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/reviewed_case158_attempt_v3.py"
TEST="tools/p09/tests/test_reviewed_case158_attempt_v3.py"
INDEX=158
PHYSICAL_RUN=2
TASK="case158-current-r002-tests"
ROOT="implementation/p09/evidence/p09-361-case158-current-runtime-run002.v1.json"
FAILED="implementation/p09/evidence/p09-361-case158-v19-actual-run001-failed-root-absent-r660.v1.json"


def require(ok,label):
    if not ok:raise ValueError("REVIEWED158_ATTEMPT_"+label)


def clone(fn,**deps):
    require(type(fn) is FunctionType,"EXACT_ORIGINAL_FUNCTION")
    new=FunctionType(fn.__code__,dict(fn.__globals__,**deps),argdefs=fn.__defaults__,closure=fn.__closure__)
    new.__kwdefaults__=fn.__kwdefaults__
    require(new.__code__ is fn.__code__ and new.__closure__ is fn.__closure__,"ORIGINAL_CODE_CLOSURE_DEFAULTS")
    return new


def connect_template(window18):
    old17=window18.OLD17;old16=old17.OLD16;old15=old16.OLD15
    original_retry=old15.RETRY
    def physical(index):
        original_retry.physical_run(index)
        return PHYSICAL_RUN if type(index) is int and index==INDEX else original_retry.physical_run(index)
    retry=NS(**{**vars(original_retry),"physical_run":physical,
        "connect_engine":clone(original_retry.connect_engine,physical_run=physical)})
    require(retry.physical_run(INDEX)==2,"EXPLICIT158_RUN002")
    next15=NS(**{**vars(old15),"template":clone(old15.template,RETRY=retry)})
    next16=NS(**{**vars(old16),"template":clone(old16.template,OLD15=next15)})
    next17=NS(**{**vars(old17),"template":clone(old17.template,OLD16=next16)})
    template=clone(window18.template,OLD17=next17)
    return template,dict(index=158,qualification_run=1,physical_product_run=2,
        original_template_chain_code_defaults_and_closures_retained=True,
        original_default_namespaces_or_sys_modules_mutated=False,
        original_single_argument_adapter_not_stacked=True,
        original_engine_source_path_task_and_worker_receipt_not_relabelled=True,
        actual_current158_template_or_product_qualified=False,GO_authorized=False)


def connect_worker(original_connector,original_worker,policy):
    # The nested execute resolves TASK in its own globals; an isolated clone
    # preserves the entire original connector and its once-only state logic.
    return clone(original_connector,TASK=TASK)(original_worker,policy)


def reviewed_failure(q,a):
    record=q.json(FAILED)
    a.fields(record,dict(state="FAILED_NOT_ACCEPTED_RUNTIME_ROOT_ABSENT",accepted_count_delta=0,
        terminal_exit_code=1,runtime_root_exists=False,
        actual_product_body_or_complete_capture_proven=False,
        actual_Native_frame_commit_or_handle_counters_proven=False),"REVIEWED_UNPROVEN_ATTEMPT001")
    require(not (q.root/"implementation/p09/evidence/p09-361-case158-current-runtime-run001.v1.json").exists(),
        "FAILED_ROOT_ABSENCE_STILL_EXACT")
    return record
