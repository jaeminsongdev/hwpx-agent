"""Exact115 after distinct108 authority, retaining all inherited source bytes.

Use the unchanged qualified113 controller/112 engine with closed metadata only.
Seed post-cleanup cadence from the SAME last successful observer timestamp.
The retained byte streams, full reads, GO/Job, guards and cleanup remain.
No accepted body replay, compilation, SQL/Hangul, retry or queue advance.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
from types import SimpleNamespace as NS

import run_current_queue_native as stable
import accept_case114_compound_epoch as accepted114
import retained_read_streams as native
import postcleanup_sampler_handoff as handoff
import postcleanup_final_sample as final_sample

c=stable.c
scope=stable.scope
SELF='tools/p09/run_case115_current_queue.py'
TEST='tools/p09/tests/test_case115_current_queue.py'
INDEX=115
BEFORE=108
CASE='actual_import::policy_product::same_values_new_policy_generation_invalidates_whole_cached_product_no_old_fallback'
MARKER_ARGS=['current-queue-case115-runtime-only']
SCHEMA=stable.SCHEMA
PASS=stable.PASS
TARGET=stable.TARGET
PRIOR_ACCEPT_PIN=dict(path=accepted114.OUTPUT,bytes=282941,
    sha256='f75547f91497c30625cabb68291152aba76900c2bb7bd78b1cdadbc136485e1f')
ENTRY_PIN=dict(path=stable.SELF,bytes=13838,
    sha256='b7eee285198222bcb80b150498bf69de9b34619510ebc7400546c43eeb3adad9')
HANDOFF_PINS=(dict(path=handoff.SELF,bytes=4775,
    sha256='26a23c539eaf38eae0c7560142afd53d67c02983ac8ece18cd84ef8d29b5abf9'),
    dict(path=handoff.TEST,bytes=3510,
    sha256='35fa0b5bdcda4f0e85148f89643f9e7e93aa31123781735f157cd26bb3adbc39'))


def require(ok,code):
    if not ok:raise ValueError('CURRENT115_'+code)


def task_for(run):
    require(type(run) is int and 1<=run<=999,'RUN_RANGE')
    return f'case115-current-r{run:03}-tests'


def run_for(task):
    require(type(task) is str and re.fullmatch('case115-current-r[0-9]{3}-tests',task),'EXACT_TASK')
    run=int(task[-9:-6]);require(task_for(run)==task,'TASK_RUN');return run


def arguments():return [CASE,'--exact','--test-threads=1','--format=pretty','--color=never']


def entry_projection(raw):
    require(type(raw) is bytes and len(raw)==ENTRY_PIN['bytes']
        and hashlib.sha256(raw).hexdigest()==ENTRY_PIN['sha256'],'QUALIFIED113_ENTRY_BYTES')
    tree=ast.parse(raw.decode('utf-8'))
    nodes=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('projection','run_owned')]
    require(len(nodes)==2 and {n.name for n in nodes}=={'projection','run_owned'},'TWO_QUALIFIED_DEFINITIONS')
    before=[ast.dump(n,include_attributes=False) for n in nodes];changes=0
    old='implementation/p09/evidence/p09-361-case113-current-runtime-run'
    new='implementation/p09/evidence/p09-361-case115-current-runtime-run'
    class Project(ast.NodeTransformer):
        def visit_Constant(self,n):
            nonlocal changes
            if n.value==old:
                changes+=1;n._old_path=copy.deepcopy(n);n.value=new
            return n
    projected=Project().visit(ast.Module(body=nodes,type_ignores=[]))
    require(changes==2,'ONLY_PROJECT_AND_UNDO_RECEIPT_PATHS')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_old_path'):return copy.deepcopy(n._old_path)
            return super().visit(n)
    require([ast.dump(n,include_attributes=False) for n in Undo().visit(copy.deepcopy(projected)).body]==before,
        'ALL_QUALIFIED113_ENTRY_STATEMENTS_RETAINED')
    namespace=dict(stable.__dict__)
    namespace.update(SELF=SELF,TEST=TEST,INDEX=INDEX,BEFORE=BEFORE,CASE=CASE,MARKER_ARGS=MARKER_ARGS,
        PRIOR_ACCEPT_PIN=PRIOR_ACCEPT_PIN,native=native,binding=binding,binding_attempt=binding_attempt,
        template=template,task_for=task_for,run_for=run_for,arguments=arguments,require=require,
        runtime_budget=runtime_budget)
    exec(compile(ast.fix_missing_locations(projected),ENTRY_PIN['path'],'exec'),namespace)
    return NS(**{n.name:namespace[n.name] for n in nodes}),dict(
        qualified113_entry_AST_restored_exactly=True,receipt_path_constants_projected=2,
        original_GO_Job_worker_resource_and_frame_statements_replaced=False,
        separate_qualified_retained_Native_mechanics=True,qualified_entry_pin=ENTRY_PIN)


def entry():
    stable.prior.build.direct_path(c.ROOT/ENTRY_PIN['path'],file_required=True)
    with (c.ROOT/ENTRY_PIN['path']).open('rb') as stream:raw=stream.read(ENTRY_PIN['bytes']+1)
    return entry_projection(raw)


def template():
    api,_=entry();pin=stable.TEMPLATE_PIN
    stable.prior.build.direct_path(c.ROOT/pin['path'],file_required=True)
    with (c.ROOT/pin['path']).open('rb') as stream:raw=stream.read(pin['bytes']+1)
    engine,proof=api.projection(raw)
    original_engine=engine.run_owned
    fixed,handoff_proof=handoff.project(raw,original_engine,INDEX,BEFORE)
    complete,final_proof=final_sample.project(raw,original_engine,fixed,INDEX,BEFORE)
    engine.run_owned=complete
    proof.update(postcleanup_same_owner_handoff=handoff_proof,
        original_engine_body_before_timestamp_change_code_exact=True,
        final_postcleanup_actual_resource_sample=final_proof)
    return engine,proof


def binding(q):
    a=accepted114.a
    parent=a.read_exact(q,PRIOR_ACCEPT_PIN)
    a.fields(parent,dict(schema_version='hwpx-agent.p09-case114-compound-epoch-acceptance/v1',
        state=accepted114.PASS,accepted_count_before=107,accepted_count_delta=1,accepted_count_after=108,
        runtime_remaining_individual_cases=141,next_runtime_index=115,
        preserved_failed_product_body_pin=accepted114.s.BODY_PIN,
        independent_source_recovery_pin=accepted114.SOURCE_PIN,accepted_test_indices=[114],
        accepted_test_names=[accepted114.s.r.CASE],accepted_current_generation_case_count=3,
        prior_epochs_rebased_to_new_runtime=False,product_and_source_epochs_distinct=True,
        Native_product_single_frame_qualified=False,resource_cleanup_confirmed=True,
        product_child_executed=False,Native_frame_reexecuted=False,successful_product_cases_reexecuted=False,
        original_failed_root_state_rewritten=False,original_missing_final_identity_retroactively_fabricated=False,
        full249_current_qualified=False,signed16_current_qualified=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN'),
        'IMMUTABLE_DISTINCT_PRIOR108')
    a.exact(parent['accepted_epoch_key'],accepted114.s.BODY_PIN['sha256']+':114:source:'+accepted114.SOURCE_PIN['sha256'],
        'UNIQUE_DISTINCT_BODY114_SOURCE_EPOCH')
    source,body,listing,required,_=accepted114.prepare(q)
    require(listing['source_test_names'][INDEX-1]==CASE
        and CASE not in (accepted114.s.r.CASE,stable.CASE,scope.CASE112),'EXACT115_NOT_REPLAY')
    a.exact(len(required),1758,'FULL_INDEPENDENT_SOURCE_SCOPE')
    fresh=scope.pins(parent['fresh_input_pins'],836)
    a.fields(parent,dict(final_fresh_hashes=836,fresh_read_passes=1673,fresh_bytes_read=74255433),'ACTUAL_PRIOR_FRESH_READS')
    a.resource_history(parent['resource_samples'])
    required=scope.extend(required,fresh)
    for pin in source['bootstrap_input_pins']:
        a.exact(q.pin(pin['path']),pin,'ALL_INHERITED_SOURCE_BOOTSTRAP')
    for name in (accepted114.s.SELF,accepted114.s.TEST,accepted114.SELF,accepted114.TEST):
        a.exact(q.pin(name),required[name],'QUALIFIED114_RECOVERY_ACCEPTOR')
        archive='implementation/p09/evidence/p361-case114-compound-qualified-code/'+name
        a.exact(q.pin(archive),dict(required[name],path=archive),'QUALIFIED114_EXACT_ARCHIVE')
    for pin in HANDOFF_PINS:a.exact(q.pin(pin['path']),pin,'REVIEWED_HANDOFF_SOURCE')
    current=scope.listing_inputs(listing)
    rust={n for n in current if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==787 and required[scope.EXE_PIN['path']]==scope.EXE_PIN,'WHOLE_CURRENT_RUST787_AND_EXE')
    return required,rust


def binding_attempt(q,run):
    require(run==1,'NO_AUTOMATIC_RETRY_WITHOUT_RECEIPT_AND_CODE_REVIEW')
    return binding(q)


def runtime_budget(required,requests):
    model=native.model(required,requests)
    model.update(final_postcleanup_distinct_sample_wait_allowance_seconds=final_sample.WAIT_ALLOWANCE,
        final_postcleanup_same_owner_actual_sample_required=True)
    model['predicted_runtime_combined_seconds']+=final_sample.WAIT_ALLOWANCE
    model['nominal_fits_unchanged_deadline']=model['predicted_runtime_combined_seconds']<600
    require(model['nominal_fits_unchanged_deadline'],'FINAL_RESOURCE_COST_INSIDE_ORIGINAL600')
    return model


def worker(task):
    api,_=template();return api.worker(task)


def run_owned(run):
    api,_=entry();return api.run_owned(run)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,required=True)
    return run_owned(parser.parse_args().run)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,256}',str(error)) else 'REDACTED_CURRENT115_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
