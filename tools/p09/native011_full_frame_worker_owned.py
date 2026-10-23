"""Original owned three-live-epoch monitor for one whole no-GO diagnostic.

Default entry only prepares the exact connection. Explicit --whole-no-go runs
one fixed child, preserves failures and uses the new202/EOF/owned-rate checker.
No product intent, GO, automatic retry, new deadline or historical rewrite.
"""
import ast
import copy
import hashlib
from pathlib import Path
import sys
from types import CodeType, FunctionType, SimpleNamespace as NS

import native011_readonly_frame_owned as original
import native011_readonly_terminal_monitor as terminal_protocol
import native011_full_frame_worker_validation as validation
import native011_ready_scope_connection as control
import native011_product_worker_scope as qualification
import current_stored_runtime_scope as scope
import native011_product_worker_ready_probe as child_checker
import native011_product_worker_entry as worker_entry

SELF='tools/p09/native011_full_frame_worker_owned.py'
TEST='tools/p09/tests/test_native011_full_frame_worker_owned.py'
TARGET='tools/p09/native011_full_frame_worker_connection.py'
PREPARE='implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-owned-prepare005.v1.json'
OUTPUT_PREFIX='implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-owned'
PASS='PASS_OWNED_FULL_FRAME_WORKER202_READY_REAL_EOF_NOT_PRODUCT_OR_BATCH'
ADAPTER=dict(validation.SOURCE)
EPOCH=dict(path='tools/p09/native011_current_epoch_owned_audit.py',bytes=7577,
    sha256='9db0e5d0eec913904fcd2c6e783dfc33dea1b1b1738469e2208368627cd0d627')
TERMINAL=dict(path='tools/p09/native011_readonly_terminal_monitor.py',bytes=11791,
    sha256='141704be4569bb9e9d1cbe0319be9ed9617e8274da7678b0765788c7c9266fb4')
EXTRA=(TEST,ADAPTER['path'],EPOCH['path'],TERMINAL['path'],validation.SELF,validation.TEST,
    control.SELF,qualification.SELF,child_checker.SELF,worker_entry.SELF,
    'tools/p09/current_stored_runtime_scope.py','tools/p09/native011_full_frame_worker_ready.py',
    'tools/p09/tests/test_native011_full_frame_worker_connection.py',control.READY['path'],qualification.READY['path'])


def require(ok,code):
    if not ok:raise ValueError('FULL_FRAME_WORKER_OWNED_'+code)


def exact(raw,pin):
    require(type(raw) is bytes and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
        'EXACT_ORIGINAL_MONITOR_ADAPTER_AND_PROTOCOL_SOURCE')
    return raw


def attest(raw,pin,module,names):
    exact(raw,pin);filename=getattr(module,names[0]).__code__.co_filename
    require(filename.replace('\\','/').endswith(pin['path']),'EXPECTED_ORIGINAL_FUNCTION_SOURCE')
    def matches(code):
        functions={value.co_name:value for value in code.co_consts if type(value) is CodeType}
        return all(type(getattr(module,name)) is FunctionType and getattr(module,name).__code__==functions.get(name) for name in names)
    matched=matches(compile(raw,filename,'exec'))
    if not matched:
        tree=ast.parse(raw)
        matched=matches(compile(ast.fix_missing_locations(ast.Module(body=[node for node in tree.body
            if not isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[])),filename,'exec'))
    require(matched,'WHOLE_ORIGINAL_DEPENDENCY_FUNCTION_CODES')


def project(raw):
    before,base=original.project(raw,terminal_protocol=True);node=copy.deepcopy(before);counts=[]
    labels={'implementation/p09/evidence/p09-361-native011-current805-readonly-frame-owned':OUTPUT_PREFIX,
        'FAILED_OWNED_READONLY_NATIVE_FRAME_NOT_ACCEPTED':'FAILED_OWNED_FULL_FRAME_WORKER_READY_NOT_ACCEPTED',
        original.OWNED_PASS:PASS}
    def changed(after,before):
        after=ast.copy_location(after,before);after._no_go_before=copy.deepcopy(before);return after
    class Select(ast.NodeTransformer):
        def visit_Constant(self,value):
            if type(value.value) is str and value.value in labels:
                counts.append(value.value);return changed(ast.Constant(labels[value.value]),value)
            return value
        def visit_Assign(self,value):
            if len(value.targets)==1 and isinstance(value.targets[0],ast.Name) and value.targets[0].id=='command':
                counts.append('command')
                return changed(ast.parse("command=[sys.executable,'-B',str(c.ROOT/TARGET),'--whole-no-go']").body[0],value)
            return self.generic_visit(value)
        def visit_Tuple(self,value):
            if len(value.elts)>2 and isinstance(value.elts[0],ast.Name) and value.elts[0].id=='SELF' and isinstance(value.elts[1],ast.Name) and value.elts[1].id=='TARGET':
                after=copy.deepcopy(value);present={part.value for part in after.elts if isinstance(part,ast.Constant)}
                after.elts.extend(ast.Constant(name) for name in EXTRA if name not in present)
                counts.append('sources');return changed(after,value)
            return self.generic_visit(value)
    node=Select().visit(node)
    loops=[(index,value) for index,value in enumerate(node.body) if isinstance(value,ast.Try)]
    require(len(loops)==1,'ONE_ORIGINAL_OWNED_TRY')
    body=loops[0][1].body
    source_positions=[index for index,value in enumerate(body) if isinstance(value,ast.For)
        and isinstance(value.iter,ast.Tuple) and len(value.iter.elts)>2
        and isinstance(value.iter.elts[0],ast.Name) and value.iter.elts[0].id=='SELF']
    require(len(source_positions)==1,'ONE_EXPLICIT_SOURCE_LOOP_BEFORE_CHILD')
    hook=ast.parse("row['monitor_preparation']=_verify_preparation(q,a)").body[0];hook._no_go_added=True
    body.insert(source_positions[0]+1,hook);counts.append('preparation')
    require(sorted(counts)==sorted([*labels,'command','sources','preparation']),'EXACT_SIX_MONITOR_CONNECTION_EDITS')
    class Undo(ast.NodeTransformer):
        def visit(self,value):
            if hasattr(value,'_no_go_before'):return copy.deepcopy(value._no_go_before)
            if hasattr(value,'_no_go_added'):return None
            return super().visit(value)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'ENTIRE_ORIGINAL_READONLY_MONITOR_AST_INVERSE')
    return node,dict(original_readonly_projection=base,entire_original_monitor_connection_AST_inverse=True,
        same_original_Job_capture_cleanup_failure_and2400_retained=True,
        three_live_epochs_and_empty_Job_before_audit_retained=True,exact_no_GO_child_only=True,
        product_or_Native_GO_authorized=False)


def verify_preparation(q,a):
    require(not getattr(q,'_p09_monitor_preflight_used',False) and q.final_fresh_hashes==0,
        'ONE_PRELAUNCH_READER_NOT_CLOSED_OR_REUSED')
    q._p09_monitor_preflight_used=True
    proof=q.json(PREPARE)
    require(proof['state']=='PASS_WHOLE_NO_GO_MONITOR_CONNECTION_PREPARED_NOT_EXECUTION'
        and proof['cleanup_confirmed'] is True and proof['fresh_inputs']==proof['final_fresh_hashes']>0
        and proof['actual_diagnostic_child_or_Native_or_product_executed'] is False,
        'CLOSED_CURRENT_PREPARATION_REQUIRED_BEFORE_LONG_NO_GO')
    require(0<len(proof['source_pins'])<=96 and any(pin['path']==SELF for pin in proof['source_pins']),
        'BOUNDED_COMPLETE_PREPARATION_SOURCE_CLOSURE')
    compared=0;fresh=0
    for pin in proof['source_pins']:
        actual=q.snapshots.get(pin['path'])
        if actual is None:actual=q.pin(pin['path']);fresh+=1
        else:compared+=1
        a.exact(actual,pin,'CURRENT_PREPARED_MONITOR_SOURCE_NOT_OLD_BYTE_CREDIT')
    return dict(same_invocation_first_reads_compared=compared,additional_first_reads=fresh,
        original_final_fresh_hashes_required=True,Native_byte_or_prior_run_credit_reused=False)


def build(root,read):
    raw=exact(read(original.SOURCE),original.SOURCE)
    adapter=exact(read(ADAPTER),ADAPTER);epoch=exact(read(EPOCH),EPOCH);terminal=exact(read(TERMINAL),TERMINAL)
    attest(epoch,EPOCH,original.original,('project','preserve_terminal_failure','observe_markers'))
    attest(terminal,TERMINAL,terminal_protocol,('monitor_type','cleanup_and_audit'))
    # One source compile profile attests all four functions. The validator still
    # makes its complete three-function inverse; no source/code cache is added.
    selected=validation.build(adapter,original,child_checker.validate_child,worker_entry.pin_digest,extra_functions=('project',))
    node,projection=project(raw)
    env=dict(__name__='p09_full_frame_source_worker_owned',__file__=original.SOURCE['path'])
    exec(compile(raw,original.SOURCE['path'],'exec'),env)
    def failure(owned,capture,row,stdout,stderr,monitor):
        return original.original.preserve_terminal_failure(owned,capture,row,stdout,stderr,NS(seen=monitor.seen,MARKERS=env['MARKERS']))
    def observe(monitor,markers,owned,capture,row):
        return original.original.observe_markers(monitor,markers,owned,capture,row,failure)
    def cleanup(owned,capture,result,monitor):
        return terminal_protocol.cleanup_and_audit(owned,capture,result,monitor,env['cleanup_owned'])
    def validate(proof,read):
        required=validation.declared_worker(read,control,qualification,scope)
        return selected.validate(proof,read,required)
    Monitor=terminal_protocol.monitor_type(env['Monitor'],env['MARKERS'],('construction','opening','native_readonly'))
    env.update(SELF=SELF,TARGET=TARGET,STAGES=('construction','opening','native_readonly','terminal_evidence'),
        _preserve_terminal_failure=failure,_observe_markers=observe,_validate_readonly=validate,Monitor=Monitor,
        _cleanup_terminal=cleanup,_terminal_complete=lambda monitor,result:monitor.terminal_complete(result),
        _verify_preparation=verify_preparation)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),original.SOURCE['path'],'exec'),env)
    return NS(main=env['main'],environment=env,projection=projection,validator_projection=selected.projection)


def direct(root,pin):
    path=root/pin['path']
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP_SOURCES')
        if member==root:break
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    return exact(raw,pin)


def prepare():
    import accept_case112_current_epoch as a,conservative_maintenance as c,prepared_run_closure_v1 as host
    import owned_cpu_baseline_v1 as baseline,preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;connection=None
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);require(not(c.ROOT/PREPARE).exists(),'EXCLUSIVE_NEW_PREPARATION')
        names={SELF,TEST,TARGET,*EXTRA}
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if type(path) is str and path.endswith('.py'):
                actual=Path(path).absolute()
                if actual.is_relative_to(c.ROOT):names.add(actual.relative_to(c.ROOT).as_posix())
        require(0<len(names)<=96,'BOUNDED_OBSERVED_CODE_WITNESS_NOT_NATIVE_HELPER_SCOPE')
        for name in sorted(names):q.pin(name)
        def raw(pin):
            actual,data=q._read(pin['path'],parse=True);q._bind(actual['path'],actual)
            a.exact(actual,pin,'FRESH_EXACT_ORIGINAL_MONITOR_DEPENDENCY');return bytes(data)
        connection=build(c.ROOT,raw);q.finish();guard.check(force=True)
    finally:guard.close()
    require(guard.cleanup and connection is not None,'PREPARATION_GUARD_CLEANUP')
    result=dict(state='PASS_WHOLE_NO_GO_MONITOR_CONNECTION_PREPARED_NOT_EXECUTION',cleanup_confirmed=guard.cleanup,
        fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_pins=list(q.snapshots.values()),
        monitor_projection=connection.projection,validator_projection=connection.validator_projection,
        actual_diagnostic_child_or_Native_or_product_executed=False,GO_authorized=False,accepted_count_delta=0)
    pin=publisher.publish(c.ROOT,PREPARE,result,NS(require=c.require,exact=a.exact))
    print(__import__('json').dumps(dict(state=result['state'],fresh=result['fresh_inputs'],final=result['final_fresh_hashes'],
        cleanup=guard.cleanup,receipt=pin)),flush=True)
    return 0


def main():
    require(sys.argv[1:] in ([],['--whole-no-go']),'CLOSED_PREPARE_OR_SINGLE_WHOLE_NO_GO_ONLY')
    sys.dont_write_bytecode=True
    if not sys.argv[1:]:return prepare()
    root=Path(__file__).resolve().parents[2];connection=build(root,lambda pin:direct(root,pin))
    before=sys.argv;sys.argv=[before[0],'--attempt','5','--generation','3']
    try:return connection.main()
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
