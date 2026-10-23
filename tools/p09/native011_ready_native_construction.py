"""Current805 unopened real Native parent with exact worker201 source closure.

Original shared constructor/oracle/cost and metadata denial, no audit replay,
Frame instance, worker launch, GO, intent consumption or product execution.
"""
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_ready_native_construction.py'
TEST='tools/p09/tests/test_native011_ready_native_construction.py'
CONTROL='tools/p09/native011_ready_scope_connection.py'
ORIGINAL=dict(path='tools/p09/native011_current_epoch_shared.py',bytes=17131,
    sha256='db60bee1016ccab236a05363a618435c2d6c813ebe5359ef55e9cae5114d6dc2')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
PARENT=dict(path='tools/p09/native011_parent_plan.py',bytes=24332,
    sha256='b58c2658510f7af5824a4b54d64fe6858cd128a1ddef1e235b00bd46238c69b8')


def require(ok,label):
    if not ok:raise ValueError('READY_NATIVE_CONSTRUCTION_'+label)


def validate(control,q,a,scope,data,resources,actual,prepared,entry,row,declared,*,exact_owner=None):
    owner=data.planned.batch;connection=owner.parent_connection
    require(owner is resources.batch and owner.phase=='NEW' and connection.parent is actual
        and connection.state.attempts==0 and connection.state.frames==[]
        and prepared.linked.state.attempts==prepared.linked.state.calls==0
        and owner.shared.metadata is owner.shared.frame is None,'ONE_UNEXECUTED_NATIVE_SHARED_OWNER')
    proof=control.inspect_current(data,declared.required,scope,connection.frame_type,a.native.frames.Frame)
    require(row['actual_engine_and_checker_same_complete_model'] is True,
        'ORIGINAL_ENGINE_AND_INDEPENDENT_CHECKER_SAME_COST')
    model=control.complete_budget(row['complete_runtime_model'])
    # Load the original verifier against the exact Native base; do not alter
    # its implementation, class predicate, live guard or full byte accounting.
    source='tools/p09/native011_source_coverage.py';pin=q.pin(source)
    actual_pin,raw=q._read(source,parse=True);q._bind(source,actual_pin);a.exact(actual_pin,pin,'EXACT_COVERAGE_SOURCE')
    import ast
    tree=ast.parse(raw)
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('require','verify')]
    require(len(functions)==2,'WHOLE_ORIGINAL_COVERAGE_FUNCTION_PAIR')
    from types import MappingProxyType
    env=dict(frames=a.native.frames,scope=scope,MappingProxyType=MappingProxyType)
    exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),source,'exec'),env)
    require(issubclass(connection.frame_type,env['frames'].Frame),'ORIGINAL_COVERAGE_CLASS_PREDICATE_UNCHANGED')
    # Private explicit factory dependency only. Do not add default project
    # helpers to the already-full original Native helper64 inventory.
    def private_source(name):
        source_pin=q.pin(name);actual,data=q._read(name,parse=True);q._bind(name,actual)
        a.exact(actual,source_pin,'CURRENT_PRIVATE_PACER_FACTORY_SOURCE')
        private=dict(__name__='p09_private_'+name.rsplit('/',1)[-1][:-3],__file__=name)
        exec(compile(data,name,'exec'),private);return NS(**private)
    precise=private_source('tools/p09/native011_precise_boundary_pacer.py')
    clock_connection=private_source('tools/p09/native011_precise_boundary_connection.py')
    clocks,clock_proof=clock_connection.connect(prepared.linked,precise)
    require(clocks.state.attempts==clocks.state.completed==0 and not clocks.state.failed,
        'PRIVATE_FACTORY_CONNECTED_WITHOUT_READER_OR_IO')
    if exact_owner is not None:
        require(exact_owner.exact_read and exact_owner.exact_factory is None and declared.exact_read,
            'ONE_EXPLICIT_EXACT_READ_FACTORY_BEFORE_NATIVE')
        tail=private_source('tools/p09/native011_exact_read_budget.py')
        leaf_pin=q.pin(tail.ORIGINAL['path']);a.exact(leaf_pin,tail.ORIGINAL,'ORIGINAL_EXACT_READ_LEAF_SOURCE')
        actual_leaf,leaf=q._read(leaf_pin['path'],parse=True);q._bind(leaf_pin['path'],actual_leaf)
        a.exact(actual_leaf,leaf_pin,'FRESH_EXACT_READ_LEAF_BEFORE_PREPARATION')
        exact,exact_proof=tail.connect_private_factory(prepared.linked,clocks.original_reader,
            {name:dict(pin) for name,pin in data.planned.current.items()},bytes(leaf))
        require(exact.state.attempts==exact.state.completed==0 and not exact.state.failed,
            'EXACT_FACTORY_CONSTRUCTED_WITHOUT_IO_OR_CREDIT')
        exact_owner.exact_factory=exact;row['exact_read_factory_connection']=exact_proof
        if exact_owner.observe_decoder:
            require(declared.decoder_timing and exact_owner.decoder_timing is None,'EXPLICIT_READONLY_TIMING_DECLARATION')
            observer=private_source('tools/p09/native011_decoder_timing_observer.py')
            observed_pin=q.pin(observer.SHARED['path']);a.exact(observed_pin,observer.SHARED,'ORIGINAL_SHARED_TIMING_SOURCE')
            actual_shared,shared_raw=q._read(observed_pin['path'],parse=True);q._bind(observed_pin['path'],actual_shared)
            a.exact(actual_shared,observed_pin,'FRESH_ORIGINAL_SHARED_TIMING_SOURCE')
            budget_pin=q.pin(observer.BUDGET['path']);a.exact(budget_pin,observer.BUDGET,'ORIGINAL_TIMED_BUDGET_SOURCE')
            actual_budget,budget_raw=q._read(budget_pin['path'],parse=True);q._bind(budget_pin['path'],actual_budget)
            a.exact(actual_budget,budget_pin,'FRESH_ORIGINAL_TIMED_BUDGET_SOURCE')
            exact_owner.decoder_timing,timing_proof=observer.connect_shared(owner.shared,bytes(shared_raw),bytes(budget_raw))
            row['shared_decoder_timing_connection']=timing_proof
        if exact_owner.chunk_join:
            require(declared.chunk_join and exact_owner.chunk_link is None,'EXPLICIT_READONLY_SHARED_CODEC_DECLARATION')
            candidate=private_source('tools/p09/native011_decoder_chunk_join.py')
            codec_connection=private_source('tools/p09/native011_chunk_join_connection.py')
            def pinned_bytes(pin):
                a.exact(q.pin(pin['path']),pin,'ORIGINAL_SHARED_CODEC_CONNECTION_SOURCE')
                actual,data=q._read(pin['path'],parse=True);q._bind(pin['path'],actual)
                a.exact(actual,pin,'FRESH_SHARED_CODEC_CONNECTION_SOURCE');return bytes(data)
            graph=prepared.entry.graph
            logical=entry.current_logical(data,graph.binding,q.checkpoint,scope,a.exact)
            projected,_=graph.binding.project(logical,q.checkpoint)
            exact_owner.chunk_link,row['chunk_join_codec_connection']=codec_connection.connect(prepared.linked,owner,
                projected,candidate,pinned_bytes(codec_connection.SOURCE),pinned_bytes(codec_connection.METADATA),
                pinned_bytes(candidate.SOURCE))
            if getattr(exact_owner,'metadata_tail',False):
                require(declared.metadata_tail and exact_owner.metadata_tail_link is None,'EXPLICIT_READONLY_METADATA_TAIL')
                metadata_candidate=private_source('tools/p09/native011_metadata_tail_candidate.py')
                metadata_connection=private_source('tools/p09/native011_metadata_tail_connection.py')
                leaves=[cls for cls in owner.metadata_connection.original_reader.__mro__
                    if cls.__name__=='ChunkLeaf' and '_read' in vars(cls)]
                require(len(leaves)==1,'ACTUAL_METADATA_WORKSPACE_LEAF')
                chunk_api=NS(**leaves[0]._read.__globals__['_workspace_for'].__globals__)
                require(chunk_api.SELF=='tools/p09/reusable_audit_chunk_v1.py','ACTUAL_METADATA_WORKSPACE_NAMESPACE')
                exact_owner.metadata_tail_link,row['metadata_tail_connection']=metadata_connection.connect(prepared.linked,owner,
                    {name:dict(pin) for name,pin in owner.whole.items()},metadata_candidate,tail,
                    prepared.linked.engine.run_owned.__globals__['byte_policy'],chunk_api,bytes(leaf),
                    pinned_bytes(metadata_connection.METADATA),pinned_bytes(metadata_connection.BUILD),codec_connection)
    row.update(exact_current_worker201_scope=proof,complete_ready15_budget=model,
        precise_boundary_factory_connection=clock_proof,
        original_coverage_verifier_same_Native_base=True,coverage_function_source_pin=dict(pin),
        original_coverage_verifier_invoked_on_live_Frame=False,
        previous_full_audit_or_accepted_tests_replayed=False,
        actual_Native_or_source_Frame_qualified=False,actual_product_GO_received=False)


def main(*,driver=None):
    require(not sys.argv[1:],'CLOSED_NO_GO_CONSTRUCTION')
    sys.dont_write_bytecode=True
    import accept_case112_current_epoch as a,conservative_maintenance as c
    # Same small pinned private bootstrap as the original constructor. The
    # external owner already bounds this process; do not add default helpers.
    path=c.ROOT/LOADER['path']
    for parent_path in (path,*path.parents):
        require(not parent_path.is_symlink() and not parent_path.is_junction(),'DIRECT_BOOTSTRAP_ANCESTORS')
        if parent_path==c.ROOT:break
    with path.open('rb') as stream:bootstrap_raw=stream.read(LOADER['bytes']+1)
    require(len(bootstrap_raw)==LOADER['bytes']
        and hashlib.sha256(bootstrap_raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_SMALL_BOOTSTRAP')
    bootstrap_env=dict(__name__='p09_ready_native_private_bootstrap',__file__=LOADER['path'])
    exec(compile(bootstrap_raw,LOADER['path'],'exec'),bootstrap_env);bootstrap_loader=NS(**bootstrap_env)
    libraries,_=bootstrap_loader.load(c.ROOT,[PARENT],{})
    parent=libraries.native011_parent_plan;source_loader=parent.bootstrap_loader(c.ROOT)
    guards,_=source_loader.load(c.ROOT,list(parent.GUARDS),{})
    host,baseline,policy,final=(getattr(guards,name) for name in ('prepared_run_closure_v1',
        'owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        for name in (SELF,TEST,CONTROL):q.pin(name)
        def raw(pin):
            actual,data=q._read(pin['path'],parse=True);q._bind(pin['path'],actual)
            a.exact(actual,pin,'EXACT_SOURCE_BEFORE_PRIVATE_COMPILATION');return bytes(data)
        env=dict(__name__='p09_ready_native_original_loader',__file__=LOADER['path'])
        exec(compile(raw(LOADER),LOADER['path'],'exec'),env);loader=NS(**env)
        pins=[ORIGINAL,q.snapshots[CONTROL]];allowed={p['path']:p for p in pins}
        class Source:
            def __init__(self,name):self.name=name
            def __fspath__(self):return str(c.ROOT/self.name)
            def open(self,mode):
                require(mode=='rb' and self.name in allowed,'ONLY_EXPLICIT_BOOTSTRAP_SOURCES')
                return io.BytesIO(raw(allowed[self.name]))
        class Root:
            def __fspath__(self):return str(c.ROOT)
            def __truediv__(self,name):return Source(name)
        libs,_=loader.load(Root(),pins,{})
        control=libs.native011_ready_scope_connection;original=libs.native011_current_epoch_shared
        if driver is not None:driver.bind(c.ROOT,a,c,guards,source_loader,control)
        exact=driver is not None and driver.exact_read
        timing=driver is not None and driver.observe_decoder
        chunk_join=driver is not None and driver.chunk_join
        options=dict(exact_read=exact,decoder_timing=timing,chunk_join=chunk_join)
        if driver is not None and getattr(driver,'metadata_tail',False):options['metadata_tail']=True
        call,projection=control.project(raw(ORIGINAL),vars(original),
            lambda q,a,scope:control.admit(q,a,scope,**options),
            lambda *args:validate(control,*args,exact_owner=driver if exact else None),driver=driver)
        q.finish();g.check(force=True)
        bootstrap=dict(projection=projection,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,SyntaxError) as error:
        value=error.args[0] if error.args else None
        print(json.dumps(dict(state='FAILED_READY_NATIVE_BOOTSTRAP_NOT_NATIVE',error_type=type(error).__name__,
            error_code=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else
            'CLOSED_READY_NATIVE_BOOTSTRAP_FAILURE')),flush=True)
        return 2
    finally:g.close()
    require(g.cleanup,'BOOTSTRAP_GUARD_CLEANUP_BEFORE_ORIGINAL_CONSTRUCTOR')
    # The separate preparation guard neither starts nor resets Native600/15/10.
    before=sys.argv;sys.argv=[before[0],'--cost-oracle']
    try:return call()
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
