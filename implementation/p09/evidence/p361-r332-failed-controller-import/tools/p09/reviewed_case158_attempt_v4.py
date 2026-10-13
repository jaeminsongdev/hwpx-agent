"""Complete explicit158/run002 identity, without rewriting observations.

Keep v3's original single argument adapter. Clone the original root/task/public
run/identity functions with the same physical dependency as that adapter.
No product execution, automatic retry or source/body evidence is implied.
"""
from types import SimpleNamespace as NS
import reviewed_case158_attempt_v3 as prior

SELF="tools/p09/reviewed_case158_attempt_v4.py"
TEST="tools/p09/tests/test_reviewed_case158_attempt_v4.py"
INDEX=prior.INDEX
PHYSICAL_RUN=prior.PHYSICAL_RUN
TASK=prior.TASK
ROOT=prior.ROOT
FAILED=prior.FAILED
clone=prior.clone
require=prior.require
connect_worker=prior.connect_worker
reviewed_failure=prior.reviewed_failure


def identity(original):
    def physical(index):
        value=original.physical_run(index)
        return PHYSICAL_RUN if type(index) is int and index==INDEX else value
    root=clone(original.root_path,physical_run=physical)
    task=clone(original.task,physical_run=physical)
    public=clone(original.public_run,physical_run=physical)
    validate=clone(original.validate_actual,physical_run=physical,root_path=root,task=task)
    require(root(NS(index=INDEX))==ROOT and task(INDEX)==TASK and public(INDEX,2)==1,
        "ALL_RUN002_IDENTITIES_AGREE")
    return NS(**{**vars(original),"physical_run":physical,"root_path":root,
        "task":task,"public_run":public,"validate_actual":validate})


def connect_template(window18):
    template,proof=prior.connect_template(window18)
    actual_retry=template.__globals__["OLD17"].OLD16.OLD15.RETRY
    names=identity(actual_retry)
    require(names.physical_run(INDEX)==actual_retry.physical_run(INDEX),
        "IDENTITY_AND_SINGLE_ENGINE_ADAPTER_AGREE")
    return template,names,dict(proof,root_path=ROOT,task=TASK,
        original_root_task_public_and_identity_check_code_retained=True,
        actual_runtime_record_relabelled=False)
