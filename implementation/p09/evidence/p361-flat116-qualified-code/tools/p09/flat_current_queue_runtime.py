"""Flat current queue connection, not an import chain of per-case controllers.

Immutable per-step DATA selects the next exact case. The already-qualified115
controller/113 entry/112 engine and same-owner closing guards remain. Every
inherited input and fresh pin still joins the new whole Native frame. No body
replay, scope reduction, altered guard/rate/deadline, new sampler or Gate PASS.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace as NS

import run_case115_current_queue as stable
import accept_case115_current_epoch as accepted115

c=stable.c
scope=stable.scope
native=stable.native
SELF='tools/p09/flat_current_queue_runtime.py'
TEST='tools/p09/tests/test_flat_current_queue.py'
ENTRY_WRAPPER_PIN=dict(path=stable.SELF,bytes=9524,
    sha256='ab791cf03ecd0c1cf3c1d0aca4a3d1335a9fe3189ba394235d3d1d8d1f370d62')
ENTRY_PIN=stable.ENTRY_PIN
SCHEMA=stable.SCHEMA
PASS=stable.PASS
TARGET=stable.TARGET
CONFIG=None


def require(ok,code):
    if not ok:raise ValueError('FLAT_QUEUE_'+code)


def config_path(index):
    require(type(index) is int and 116<=index<=249,'INDEX_RANGE')
    return f'implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json'


def unique(pairs):
    result={}
    for name,value in pairs:
        require(name not in result,'DUPLICATE_CONFIG_KEY');result[name]=value
    return result


def validate_config(row,index):
    a=accepted115.a
    require(type(row) is dict and set(row)=={'schema_version','index','before','case','prior_queue_pin','prior_candidate_pin'},'CONFIG_SHAPE')
    a.fields(row,dict(schema_version='hwpx-agent.p09-flat-current-queue-step/v1',index=index,before=index-7),'CONFIG_CURSOR')
    require(type(row['case']) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_:]*',row['case']),'EXACT_TEST_NAME')
    pins=scope.pins([row['prior_queue_pin'],row['prior_candidate_pin']],2)
    prior=index-1
    queue=f'implementation/p09/evidence/p09-361-case{prior}-current-epoch-accept001.v1.json'
    require(row['prior_queue_pin']['path']==queue,'PRIOR_QUEUE_PATH')
    require(re.fullmatch(f'implementation/p09/evidence/p09-361-case{prior}-current-runtime-run[0-9]{{3}}\\.v1\\.json',
        row['prior_candidate_pin']['path']) is not None,'PRIOR_CANDIDATE_PATH')
    if index==116:
        a.exact(row['prior_candidate_pin'],accepted115.ROOT_PIN,'ACTUAL115_ANCHOR')
        a.exact(row['prior_queue_pin'],dict(path=accepted115.OUTPUT,bytes=279082,
            sha256='c9323cb101a91b4b2f407e9b65c54b67e288f8e8fc3bd8e89da14c1edf8c0499'),'ACTUAL109_ANCHOR')
    return dict(row)


def load_config(index):
    name=config_path(index);path=c.ROOT/name
    stable.stable.prior.build.direct_path(path,file_required=True)
    with path.open('rb') as stream:raw=stream.read(16385)
    require(0<len(raw)<=16384,'BOUNDED_CONFIG')
    row=validate_config(json.loads(raw.decode('utf-8'),object_pairs_hook=unique),index)
    return NS(**row,path=name,pin=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))


def configure(index):
    global CONFIG
    require(CONFIG is None,'ONE_IMMUTABLE_STEP_PER_PROCESS')
    CONFIG=load_config(index);return CONFIG


def context(step,index=None,name=None,before=None,parent=None):
    index=step.index if index is None else index
    name=step.case if name is None else name
    before=step.before if before is None else before
    parent=step.prior_queue_pin if parent is None else parent
    return NS(**{**vars(stable),'SELF':SELF,'TEST':TEST,'INDEX':index,'BEFORE':before,
        'CASE':name,'PRIOR_ACCEPT_PIN':parent,'MARKER_ARGS':[f'current-queue-case{index}-runtime-only'],
        'arguments':lambda:[name,'--exact','--test-threads=1','--format=pretty','--color=never'],
        'attribution':stable.stable.attribution})


def task_for(run):
    require(CONFIG is not None and type(run) is int and 1<=run<=999,'CONFIG_AND_RUN')
    return f'case{CONFIG.index}-current-r{run:03}-tests'


def task_index(task):
    require(type(task) is str and re.fullmatch('case[0-9]{3}-current-r[0-9]{3}-tests',task),'TASK_SHAPE')
    index=int(task[4:7]);config_path(index);return index


def run_for(task):
    require(CONFIG is not None and task_index(task)==CONFIG.index,'EXACT_CONFIG_TASK')
    run=int(task[-9:-6]);require(task_for(run)==task,'TASK_RUN');return run


def arguments():return context(CONFIG).arguments()


def entry_wrapper(raw):
    require(type(raw) is bytes and len(raw)==ENTRY_WRAPPER_PIN['bytes']
        and hashlib.sha256(raw).hexdigest()==ENTRY_WRAPPER_PIN['sha256'],'QUALIFIED115_WRAPPER')
    nodes=[n for n in ast.parse(raw.decode('utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='entry_projection']
    require(len(nodes)==1,'ONE_QUALIFIED_ENTRY_PROJECTION')
    node=copy.deepcopy(nodes[0]);before=ast.dump(node,include_attributes=False)
    old='implementation/p09/evidence/p09-361-case115-current-runtime-run';changes=0
    class Project(ast.NodeTransformer):
        def visit_Constant(self,n):
            nonlocal changes
            if n.value==old:
                changes+=1;new=ast.parse("f'implementation/p09/evidence/p09-361-case{INDEX}-current-runtime-run'",mode='eval').body
                new._old_path=copy.deepcopy(n);return new
            return n
    node=Project().visit(node);require(changes==1,'ONE_RECEIPT_METADATA_PARAMETER')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_old_path'):return copy.deepcopy(n._old_path)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_QUALIFIED_ENTRY_STATEMENTS_RETAINED')
    namespace=dict(stable.__dict__);ctx=context(CONFIG)
    namespace.update(vars(ctx));namespace.update(entry=entry,template=template,binding=binding,
        binding_attempt=binding_attempt,task_for=task_for,run_for=run_for,arguments=arguments,
        require=require,runtime_budget=stable.runtime_budget)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),ENTRY_WRAPPER_PIN['path'],'exec'),namespace)
    return namespace['entry_projection'],dict(original115_wrapper_AST_restored_exactly=True,
        receipt_metadata_literals_parameterized=1,extra_sampler_or_control_flow_replacement=False)


def entry():
    require(CONFIG is not None,'CONFIG_REQUIRED')
    stable.stable.prior.build.direct_path(c.ROOT/ENTRY_WRAPPER_PIN['path'],file_required=True)
    with (c.ROOT/ENTRY_WRAPPER_PIN['path']).open('rb') as stream:raw=stream.read(ENTRY_WRAPPER_PIN['bytes']+1)
    project,proof=entry_wrapper(raw)
    stable.stable.prior.build.direct_path(c.ROOT/ENTRY_PIN['path'],file_required=True)
    with (c.ROOT/ENTRY_PIN['path']).open('rb') as stream:raw=stream.read(ENTRY_PIN['bytes']+1)
    api,inner=project(raw);proof.update(qualified113_entry=inner)
    return api,proof


def template():
    api,_=entry();pin=stable.stable.TEMPLATE_PIN
    stable.stable.prior.build.direct_path(c.ROOT/pin['path'],file_required=True)
    with (c.ROOT/pin['path']).open('rb') as stream:raw=stream.read(pin['bytes']+1)
    engine,proof=api.projection(raw);original=engine.run_owned
    fixed,h=stable.handoff.project(raw,original,CONFIG.index,CONFIG.before)
    complete,f=stable.final_sample.project(raw,original,fixed,CONFIG.index,CONFIG.before)
    engine.run_owned=complete;proof.update(same_owner_handoff=h,final_actual_sample=f)
    return engine,proof


def binding(q):
    # Import ONE fixed validator, not the previous per-case controller. It is
    # pinned with its test before the whole Native frame; no recursive imports.
    import flat_current_queue_acceptance as acceptance
    a=accepted115.a
    a.exact(q.pin(CONFIG.path),CONFIG.pin,'UNCHANGED_STEP_DATA')
    queue=a.read_exact(q,CONFIG.prior_queue_pin)
    expected_state=accepted115.PASS if CONFIG.index==116 else acceptance.PASS
    a.fields(queue,dict(state=expected_state,accepted_count_after=CONFIG.before,next_runtime_index=CONFIG.index,
        accepted_count_delta=1,accepted_test_indices=[CONFIG.index-1],resource_cleanup_confirmed=True,
        full249_current_qualified=False,signed16_current_qualified=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN'),
        'EXACT_PRIOR_QUEUE_NOT_REBASE')
    a.exact(queue['runtime_candidate_pin'],CONFIG.prior_candidate_pin,'PRIOR_ACCEPTED_NATIVE_ROOT')
    row=a.read_exact(q,CONFIG.prior_candidate_pin)
    listing=a.read_exact(q,scope.LIST_PIN);oldbody=a.read_exact(q,a.BODY_PIN)
    fresh=a.packed.unpack(a.read_exact(q,a.FRESH_PIN),q.checkpoint)
    names=listing['source_test_names']
    require(names[CONFIG.index-1]==CONFIG.case and names[CONFIG.index-2]==queue['accepted_test_names'][0],'COMPILED_NEXT_EXACT_CASE')
    previous=context(CONFIG,index=CONFIG.index-1,name=names[CONFIG.index-2],before=CONFIG.before-1,
        parent=row['prior_queue_fresh_pin'])
    acceptance.validate_candidate(q,row,listing,oldbody,fresh,previous,flat=CONFIG.index>116)
    a.resource_history(queue['resource_samples'])
    required=scope.pins(row['source_freeze'])
    prior_fresh=scope.pins(queue['fresh_input_pins'])
    n=len(prior_fresh)
    require(type(queue['fresh_read_passes']) is int and queue['fresh_read_passes']>=2*n
        and type(queue['fresh_bytes_read']) is int and queue['fresh_bytes_read']>=2*sum(p['bytes'] for p in prior_fresh.values()),
        'PRIOR_COMPLETE_FRESH_READS')
    a.exact(queue['final_fresh_hashes'],n,'ALL_PRIOR_FINAL_HASHES')
    required=scope.extend(required,prior_fresh)
    for pin in row['bootstrap_metadata']['input_pins']:a.exact(q.pin(pin['path']),pin,'ALL_INHERITED_BOOTSTRAP')
    for name in (stable.SELF,stable.TEST,stable.handoff.SELF,stable.handoff.TEST,stable.final_sample.SELF,
            accepted115.SELF,accepted115.TEST):
        a.exact(q.pin(name),required[name],'QUALIFIED115_CODE')
        archive='implementation/p09/evidence/p361-case115-qualified-code/'+name
        a.exact(q.pin(archive),dict(required[name],path=archive),'QUALIFIED115_ARCHIVE')
    q.pin(acceptance.SELF);q.pin(acceptance.TEST)
    current=scope.listing_inputs(listing)
    rust={n for n in current if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==787 and required[scope.EXE_PIN['path']]==scope.EXE_PIN,'CURRENT_RUST787_EXE')
    return required,rust


def binding_attempt(q,run):
    require(run==1,'NO_AUTOMATIC_RETRY_WITHOUT_RECEIPT_AND_CODE_REVIEW')
    return binding(q)


def worker(task):
    api,_=template();return api.worker(task)


def run_owned(run):
    api,_=entry();return api.run_owned(run)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:
            configure(task_index(sys.argv[3]));raise SystemExit(worker(sys.argv[3]))
        parser=argparse.ArgumentParser();parser.add_argument('--case',type=int,required=True);parser.add_argument('--run',type=int,required=True)
        args=parser.parse_args();configure(args.case);raise SystemExit(run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,256}',str(error)) else 'REDACTED_FLAT_QUEUE_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
