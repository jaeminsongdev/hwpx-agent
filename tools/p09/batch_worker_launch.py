"""Run010 worker entry; original READY/GO/Job/worker bodies stay intact.

Only prepare() and explicit task/entry metadata differ. Preparation reads the
bounded published graph and four entry inputs, never raw historical receipts.
No new product permission or Native dispatcher is provided by this module.
"""
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_worker_launch.py'
TASK='case165-current-r010-tests'
GRAPH=dict(path='implementation/p09/evidence/p09-361-case165-successor-run010-graph002.v1.json',bytes=11673,
    sha256='104a632a894608e33f51e3ea98c9e0080dd226465b3efc92dc410e3e6a899363')
ENTRY=dict(path='tools/p09/native009_worker_entry_v1.py',bytes=5740,
    sha256='0124e1c8bd05363be0fe8194d4d67778d74ab0d494af7e69b3f621c8a138d602')
LAUNCH=dict(path='tools/p09/native009_worker_launch_v1.py',bytes=4057,
    sha256='30088c308a7294dec10c295bcaba1d396382a7194541e5e21bd599dc03762f4b')
PROTOCOL=dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45')
STEP=dict(path='implementation/p09/evidence/p09-361-case165-step-config001.v1.json',bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')


def require(ok,label):
    if not ok:raise ValueError('BATCH_WORKER_'+label)


def probe_invocation(argv):
    require(type(argv) is list,'EXPLICIT_ARGUMENT_LIST')
    probe=bool(argv and argv[0]=='--probe-no-go')
    return probe,argv[1:] if probe else argv


def preparation_profile(probe,argv):
    require(type(probe) is bool and type(argv) is list,'EXPLICIT_PROFILE_ARGUMENTS')
    selected=bool(argv and argv[0]=='--zlib')
    require(not selected or probe,'NEW_ZLIB_PROFILE_REQUIRES_NO_GO_PROBE')
    return selected,argv[1:] if selected else argv


def deny_probe_process(event,args):
    if event in ('subprocess.Popen','os.system','os.startfile'):
        raise ValueError('BATCH_WORKER_NO_GO_PROBE_PROCESS_DENIED')


class NoGoInput:
    """Diagnostic stdin: only actual EOF reaches the unchanged worker."""
    def __init__(self,original):self.original=original
    def __getattr__(self,name):return getattr(self.original,name)
    def readline(self,*args,**kwargs):
        value=self.original.readline(*args,**kwargs)
        require(type(value) is str and value=='','NO_GO_PROBE_REQUIRES_REAL_EOF')
        return value


def family(original,updates):
    functions=[v for v in vars(original).values() if type(v) is FunctionType]
    require(functions and len({id(fn.__globals__) for fn in functions})==1,'ONE_ORIGINAL_PRIVATE_FAMILY')
    before=functions[0].__globals__;env=dict(before,**updates)
    for name,fn in tuple(vars(original).items()):
        if type(fn) is FunctionType and fn.__globals__ is before:
            selected=FunctionType(fn.__code__,env,name=fn.__name__,argdefs=fn.__defaults__,closure=fn.__closure__)
            selected.__kwdefaults__=fn.__kwdefaults__
            require(selected.__code__ is fn.__code__ and selected.__defaults__ is fn.__defaults__
                and selected.__closure__ is fn.__closure__,'ORIGINAL_CODE_DEFAULTS_CLOSURE')
            env[name]=selected
    return NS(**env)


def launch_api(root,loader):
    libs,_=loader.load(root,[LAUNCH],{})
    original=libs.native009_worker_launch_v1
    require(original.ENTRY==ENTRY['path'] and original.TASK=='case165-current-r009-tests','ORIGINAL_LAUNCH_IDENTITY')
    return family(original,dict(ENTRY=SELF,TASK=TASK))


def prepare(root,*,checkpoint=lambda:None,package=None):
    """Actual child preparation; no parent ledger or failed Native body reads."""
    import ast,copy
    import conservative_maintenance as c
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import runtime_envelope_namespace_bundle_v1 as source_loader
    import batch_worker_entry as worker
    c.Windows();require(c.ROOT==root,'SAME_EXPLICIT_REPOSITORY')
    require(callable(checkpoint),'EXPLICIT_PREPARATION_CHECKPOINT')
    q=a.AcceptanceReader(root,checkpoint)
    report=a.read_exact(q,GRAPH)
    a.fields(report,dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
        index=165,cleanup_confirmed=True,GO_authorized=False,product_or_Native_executed=False),
        'PUBLISHED_NO_GO_PREPARATION_ONLY')
    known=scope.pins(report['source_pins'])
    require(len(known)==report['fresh_inputs']==report['final_fresh_hashes']==64,'CLOSED_PREPARATION64')
    if package is not None:
        require(getattr(package,'SELF',None)=='tools/p09/batch_zlib_runtime.py','EXACT_NEW_PACKAGE_PROFILE')
        report,known=package.admit(root,q,a,scope,report,known,SELF)
    a.exact(q.pin(source_loader.SELF),known[source_loader.SELF],'ORIGINAL_SOURCE_LOADER')
    # Reuse the original paced namespace adapter without importing the full
    # batch policy/Frame graph as default worker helpers.
    policy_pin=known['tools/p09/batch_verification.py']
    actual,raw=q._read(policy_pin['path'],parse=True);q._bind(actual['path'],actual)
    a.exact(actual,policy_pin,'WHOLE_PINNED_POLICY_SOURCE_NOT_REWRITTEN')
    tree=ast.parse(bytes(raw))
    requested=('require','_constant_shape','_code_shape','prepare_engine_builder')
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in requested]
    paced=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PacedNamespaceLoader')
    require(len(nodes)==len(requested),'EXACT_COMPLETE_PRODUCTION_DEFINITIONS')
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
        and n.targets[0].id in ('ENGINE','ENGINE_SHA','RUNTIME','RUNTIME_SHA')}
    import os,threading
    env=dict(ast=ast,copy=copy,hashlib=hashlib,os=os,threading=threading,FunctionType=FunctionType,NS=NS,scope=scope,**constants)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes+[paced],type_ignores=[])),policy_pin['path'],'exec'),env)
    loader=env['PacedNamespaceLoader'](source_loader,q,known).api
    names,_=loader.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')],{})
    optimized,_=names.ast_copy_namespace_connection_v1.connect(source_loader,names.ast_clone_namespace_v1)
    loader=env['PacedNamespaceLoader'](optimized,q,known).api
    construction,_=loader.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    construction=construction.native009_full72_construction_v1
    # These are the original constructor's explicit CODE pins, not recursively
    # discovered receipts or a union of whatever the worker happened to open.
    known=scope.extend(known,scope.pins(construction.PINS+[PROTOCOL]))
    loader=env['PacedNamespaceLoader'](optimized,q,known).api
    host_pin=next(p for p in construction.PINS if p['path']=='tools/p09/prepared_run_closure_v1.py')
    a.exact(q.pin(host_pin['path']),host_pin,'EXACT_ORIGINAL_HOST_POLICY_SOURCE')
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c)
    import flat_current_queue_envelope_runtime_v25 as envelope
    loader,_=construction.private_runtime_imports(loader)
    libs,_=loader.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('fixed162_worker_transport_v1','receipt_xz_envelope_v1','bounded_successor_capsule_wire_v2',
         'post_product_recovery_connection_v1','post_product_recovery_window_v1')],{})
    api=libs.fixed162_worker_transport_v1.connect(root,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
        libs.bounded_successor_capsule_wire_v2,q.checkpoint,a.exact)
    def read(pin,limit):
        require(limit==16384 and pin['bytes']<=limit,'ORIGINAL_BOUNDED_ENTRY_READ')
        before=q.maximum_parse_bytes
        try:
            q.maximum_parse_bytes=min(before,limit+1)
            actual,data=q._read(pin['path'],parse=True);q._bind(actual['path'],actual)
        finally:q.maximum_parse_bytes=before
        a.exact(actual,pin,'ACTUAL_ENTRY_METADATA_BYTES');return bytes(data)
    def transport(reference,step,check):
        return worker.transport_graph(root,loader,known,api,libs.bounded_successor_capsule_wire_v2,
            bytes_policy,reference,step,check)
    if package is None:
        entry=worker.reconstruct(TASK,report['bootstrap_pin'],read,api.reconstruct,transport,q.checkpoint)
    else:
        entry=package.reconstruct(root,q,a,scope,loader,known,api,libs.bounded_successor_capsule_wire_v2,
            bytes_policy,worker,report,read)
    a.exact(dict(entry.graph.binding.manifest_pin),report['manifest_pin'],'SAME_PUBLISHED_MANIFEST')
    # The original runtime declares its two template sources separately from
    # the compact graph's producer64. Admit that closed CODE list before build,
    # never whichever files a failed construction happened to open.
    require(len(entry.runtime.PINS)==2 and all(p['path'].endswith('.py') for p in entry.runtime.PINS),
        'ORIGINAL_CLOSED_TEMPLATE_SOURCE_PAIR')
    known=scope.extend(known,scope.pins(entry.runtime.PINS))
    loader=env['PacedNamespaceLoader'](optimized,q,known).api
    loader,_=construction.private_runtime_imports(loader)
    a.exact(q.pin(STEP['path']),STEP,'CURRENT_STEP_BEFORE_WORKER')
    actual,raw=q._read(known[constants['ENGINE']]['path'],parse=True);q._bind(actual['path'],actual)
    a.exact(actual,known[constants['ENGINE']],'ORIGINAL_WORKER_ENGINE_BUILDER')
    runtime_pin,runtime_raw=q._read(constants['RUNTIME'],parse=True);q._bind(runtime_pin['path'],runtime_pin)
    a.exact(runtime_pin,known[constants['RUNTIME']],'ORIGINAL_WORKER_FACTORY_SOURCE')
    builder=env['prepare_engine_builder'](bytes(raw),entry.runtime,bytes(runtime_raw))
    linked=builder.build(root,loader,NS(runtime=entry.runtime),entry.graph,envelope.prior,
        libs.post_product_recovery_connection_v1,libs.post_product_recovery_window_v1,q.checkpoint)
    protocol,_=loader.load(root,[PROTOCOL],{})
    require(linked.state.calls==linked.state.attempts==0 and linked.window.WINDOW.SECONDS==10
        and protocol.worker_readiness_v1.SECONDS==15,'UNEXECUTED_ORIGINAL_WORKER_AND_LIMITS')
    q.finish()
    require(q.final_fresh_hashes==len(q.snapshots),'ALL_CHILD_PREPARATION_CLOSING_HASHES')
    linked.preparation_evidence=dict(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
        physical_bytes_read=q.bytes_read,actual_worker_calls=linked.state.calls,
        actual_worker_attempts=linked.state.attempts,
        source_pins=[dict(q.snapshots[n]) for n in sorted(q.snapshots)])
    if package is not None:
        linked.preparation_evidence.update(zlib_profile=True,package_pins=list(package.PACKAGE),
            qualification_scope=report['reused_qualification_scope'],entry_proof=entry.proof)
    return linked,protocol.worker_readiness_v1


def worker_api(root,loader,*,package=None):
    libraries,_=loader.load(root,[ENTRY],{})
    original=libraries.native009_worker_entry_v1
    require(original.TASK=='case165-current-r009-tests','ORIGINAL_WORKER_IDENTITY')
    api=family(original,dict(__file__=str(root/SELF),SELF=SELF,TASK=TASK,STEP=STEP))
    prepared=[]
    def current_prepare(actual):
        require(actual==root,'ONE_EXACT_WORKER_ROOT')
        result=prepare(actual,package=package)
        if package is not None:prepared.append(result)
        return result
    api.main.__globals__['prepare']=current_prepare;api.prepare=current_prepare
    if package is not None:
        def measured_json(row,**options):
            require(len(prepared)==1,'ONE_MEASURED_CHILD_PREPARATION')
            return json.dumps(package.terminal_evidence(prepared[0][0],row),**options)
        # Only this private original main gets additive EOF identity evidence.
        # Original task/counts/worker/raw-policy/step fields remain untouched.
        api.main.__globals__['json']=NS(**{**vars(json),'dumps':measured_json})
    return api


def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'))
    sys.dont_write_bytecode=True
    # Validate the same original closed argument contract before importing the
    # expensive production envelope. No process or product is created here.
    probe,argv=probe_invocation(sys.argv[1:])
    zlib,argv=preparation_profile(probe,argv)
    if probe:sys.addaudithook(deny_probe_process)
    package=None
    if zlib:import batch_zlib_runtime as package
    import runtime_envelope_namespace_bundle_v1 as loader
    api=worker_api(root,loader,package=package)
    api.arguments(argv)
    if not probe:return api.main()
    original_argv,original_stdin=sys.argv,sys.stdin
    try:
        sys.argv=[original_argv[0],*argv];sys.stdin=NoGoInput(original_stdin)
        return api.main()
    finally:sys.argv,sys.stdin=original_argv,original_stdin


if __name__=='__main__':raise SystemExit(main())
