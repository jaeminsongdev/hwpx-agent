"""Reviewed158/run003 after the independently verified pre-product run002 stop.

Original root/task/public/checker and sole engine argument adapter code remain.
No current attempt may overwrite001/002 or relabel a receipt. The owner must
still qualify the whole current source scope and preserve every resource guard.
"""
from types import SimpleNamespace as NS
import reviewed_case158_attempt_v4 as original

SELF="tools/p09/reviewed_case158_attempt_v5.py"
TEST="tools/p09/tests/test_reviewed_case158_attempt_v5.py"
INDEX=158
PHYSICAL_RUN=3
TASK="case158-current-r003-tests"
ROOT="implementation/p09/evidence/p09-361-case158-current-runtime-run003.v1.json"
FAILED=original.FAILED
STOPPED=dict(path=original.ROOT,bytes=21201,
    sha256="956dbb5fb6723eeaac4b59ad6d4ffa7965583c17adcee318385f462d96b36dd4")
REVIEW_PATH="implementation/p09/evidence/p09-361-case158-run002-metadata-stop-review-code7-r675.v1.json"
clone=original.clone
require=original.require


def identity(prior):
    def physical(index):
        value=prior.physical_run(index)
        return PHYSICAL_RUN if type(index) is int and index==INDEX else value
    root=clone(prior.root_path,physical_run=physical)
    task=clone(prior.task,physical_run=physical)
    public=clone(prior.public_run,physical_run=physical)
    validate=clone(prior.validate_actual,physical_run=physical,root_path=root,task=task)
    require(root(NS(index=INDEX))==ROOT and task(INDEX)==TASK and public(INDEX,PHYSICAL_RUN)==1,
        "ALL_REVIEWED_RUN003_IDENTITIES_AGREE")
    return NS(**{**vars(prior),"physical_run":physical,"root_path":root,"task":task,
        "public_run":public,"validate_actual":validate})


def connect_template(window18):
    old17=window18.OLD17;old16=old17.OLD16;old15=old16.OLD15
    retry=identity(old15.RETRY)
    retry.connect_engine=clone(old15.RETRY.connect_engine,physical_run=retry.physical_run)
    next15=NS(**{**vars(old15),"template":clone(old15.template,RETRY=retry)})
    next16=NS(**{**vars(old16),"template":clone(old16.template,OLD15=next15)})
    next17=NS(**{**vars(old17),"template":clone(old17.template,OLD16=next16)})
    template=clone(window18.template,OLD17=next17)
    return template,retry,dict(index=158,qualification_run=1,physical_product_run=3,task=TASK,root_path=ROOT,
        original_template_chain_code_defaults_and_closures_retained=True,
        original_default_namespaces_or_sys_modules_mutated=False,
        original_single_argument_adapter_not_stacked=True,
        actual_runtime_record_relabelled=False,GO_authorized=False)


def connect_worker(connector,worker,policy):
    return clone(connector,TASK=TASK)(worker,policy)


def reviewed_failure(q,a,review_pin):
    first=original.prior.reviewed_failure(q,a)
    stopped=a.read_exact(q,STOPPED)
    a.fields(stopped,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r002-tests",selected_test_index=158,
        stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",product_body_observed=False,
        actual_product_child_executed=False,worker_created=False,job_assigned=False,source_frame=None,
        source_freeze=[],cleanup_confirmed=True,owned_tree_empty=True,Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False,accepted_count_delta=0),"EXACT_STOPPED002_NOT_PRODUCT")
    a.exact(review_pin["path"],REVIEW_PATH,"EXACT_STOP002_INDEPENDENT_REVIEW_PATH")
    reviewed=a.read_exact(q,review_pin)
    a.fields(reviewed,dict(state="PASS_EXACT158_RUN002_METADATA_STOP_REVIEW_NOT_PRODUCT_OR_GO",
        contracts=dict(run=7,errors=0,failures=0,skipped=0),original_runtime_pin=STOPPED,
        failed_root_preserved=True,actual_product_or_Native_executed=False,
        accepted_count_delta=0,cleanup_confirmed=True),"INDEPENDENT_STOP_REVIEW_NOT_GO")
    for p in reviewed["new_code_pins"]:a.exact(q.pin(p["path"]),p,"ORIGINAL_CURRENT_STOP_REVIEW_SOURCE")
    return first
