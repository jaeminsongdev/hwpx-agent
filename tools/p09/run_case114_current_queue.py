"""Exact114 using preserved113 engine and qualified retained-stream mechanics.

Closed metadata projection only in engine/original GO/Job/worker. A separately
qualified Native stream implementation removes second REAL duplicate openings,
not byte passes or resource/identity guards. Immutable candidate is not a queue
advance. Completed111/112/113 must never be replayed.
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
import accept_current_queue_epoch as accepted113
import retained_read_streams as native

c=stable.c
scope=stable.scope
SELF='tools/p09/run_case114_current_queue.py'
TEST='tools/p09/tests/test_case114_current_queue.py'
INDEX=114
BEFORE=107
CASE='actual_import::policy_product::repository_revocation_mid_verification_denies_after_original_compiler_reads'
MARKER_ARGS=['current-queue-case114-runtime-only']
SCHEMA=stable.SCHEMA
PASS=stable.PASS
TARGET=stable.TARGET
PRIOR_ACCEPT_PIN=dict(path=accepted113.OUTPUT,bytes=274684,
    sha256='5c3493c8b903b7aca288f90499e60fa3038046fd8ccfc68d75d602d0f4cea289')
ENTRY_PIN=dict(path=stable.SELF,bytes=13838,
    sha256='b7eee285198222bcb80b150498bf69de9b34619510ebc7400546c43eeb3adad9')
PROBE_PIN=dict(path='implementation/p09/evidence/p09-361-retained-read-streams-probe001.v1.json',bytes=50036,
    sha256='49e12c5626b4baa271eb9372368bd80ca63f2578d77069c82e6f9643b27b4195')


def require(ok,code):
    if not ok:raise ValueError('CURRENT114_'+code)


def task_for(run):
    require(type(run) is int and 1<=run<=999,'RUN_RANGE')
    return f'case114-current-r{run:03}-tests'


def run_for(task):
    require(type(task) is str and re.fullmatch('case114-current-r[0-9]{3}-tests',task),'EXACT_TASK')
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
    new='implementation/p09/evidence/p09-361-case114-current-runtime-run'
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
    return api.projection(raw)


def binding(q):
    a=stable.accepted112
    parent=a.read_exact(q,PRIOR_ACCEPT_PIN)
    a.fields(parent,dict(state=accepted113.PASS,accepted_count_before=106,accepted_count_delta=1,
        accepted_count_after=107,runtime_remaining_individual_cases=142,next_runtime_index=114,
        runtime_candidate_pin=accepted113.ROOT_PIN,accepted_test_indices=[113],accepted_test_names=[stable.CASE],
        accepted_current_generation_case_count=2,prior_epochs_rebased_to_new_runtime=False,
        resource_cleanup_confirmed=True,product_child_executed=False,Native_frame_reexecuted=False,
        full249_current_qualified=False,signed16_current_qualified=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN'),
        'IMMUTABLE_PRIOR107')
    row,listing,_,_=accepted113.prepare(q)
    required=scope.pins(row['source_freeze'],1731)
    require(listing['source_test_names'][113]==CASE and CASE not in (stable.CASE,scope.CASE112),'EXACT114_NOT_REPLAY')
    fresh=scope.pins(parent['fresh_input_pins'],829)
    a.fields(parent,dict(final_fresh_hashes=829,fresh_read_passes=1658),'PRIOR_TWO_FRESH_PASSES')
    require(parent['fresh_bytes_read']==2*sum(p['bytes'] for p in fresh.values()),'PRIOR_FULL_FRESH_BYTES')
    # Keep every inherited bootstrap/failed-history pin, so the new complete
    # scope remains reconstructible, not a shortcut limited to114 fixtures.
    for pin in row['bootstrap_metadata']['input_pins']:
        a.exact(q.pin(pin['path']),pin,'PRESERVED113_BOOTSTRAP')
    for name in (accepted113.SELF,accepted113.TEST):a.exact(q.pin(name),fresh[name],'PRESERVED_ACCEPT113_CODE')
    # Source/preimage copies are checked before use; no original paths are rebased.
    for name in (stable.SELF,stable.TEST,stable.acquisition.SELF,stable.acquisition.TEST,
            stable.attribution.SELF,stable.attribution.TEST,stable.attribution.p.SELF,stable.attribution.p.TEST,
            accepted113.SELF,accepted113.TEST):
        expected=required.get(name,fresh.get(name))
        a.exact(q.pin(name),expected,'UNCHANGED_QUALIFIED113_SOURCE')
        archive='implementation/p09/evidence/p361-case113-qualified-code/'+name
        a.exact(q.pin(archive),dict(expected,path=archive),'QUALIFIED113_EXACT_ARCHIVE')
    probe=a.read_exact(q,PROBE_PIN)
    a.fields(probe,dict(state='PASS_SMALL_REAL_RETAINED_STREAMS_NOT_WHOLE_CURRENT_RUNTIME_OR_PRODUCT',
        ready_for_separate_current_queue_integration=True,actual_product_or_Job_executed=False,
        whole_current_scope_qualified=False,queue_delta=0,cleanup_confirmed=True),'REAL_RETAINED_PROBE')
    probe_pins=scope.pins(probe['fresh_input_pins'])
    for name in (native.SELF,native.TEST):a.exact(q.pin(name),probe_pins[name],'QUALIFIED_RETAINED_SOURCE')
    a.exact(q.pin(native.LOCK_PIN['path']),native.LOCK_PIN,'UNCHANGED_ORIGINAL_READER_BINDING')
    current=scope.listing_inputs(listing)
    rust={n for n in current if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==787,'WHOLE_CURRENT_RUST787')
    return required,rust


def binding_attempt(q,run):
    require(run==1,'NO_AUTOMATIC_RETRY_WITHOUT_RECEIPT_AND_CODE_REVIEW')
    return binding(q)


def runtime_budget(required,requests):return native.model(required,requests)


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
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,256}',str(error)) else 'REDACTED_CURRENT114_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
