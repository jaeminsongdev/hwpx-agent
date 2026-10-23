"""Approved preparation CPU connection; the original parent entry stays sealed.

No Native/product/worker/GO mode. Freshly close original policy witnesses
before selecting the already-qualified preparation-only Guard dependency.
"""
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_zlib_preparation.py'
TEST='tools/p09/tests/test_batch_zlib_preparation.py'
PARENT=dict(path='tools/p09/batch_zlib_engine.py',bytes=14940,
    sha256='fc2bc3e67e9352944916cc25a1c1863a888c1529913c20c9e9c9b29d31208772')
POLICY=dict(path='tools/p09/preparation_attributed_cpu_v1.py',bytes=9869,
    sha256='ddc1b48f17645337e65125373d9db822477ca6a94cc34e23992498e6c2c7d13d')
WITNESS=dict(path='tools/p09/preparation_attributed_entry_v1.py',bytes=28701,
    sha256='572c86f7c932e4e2e3fa85ad021372ffeabdea187ff7253e41ca02e3abca623f')
PREFIX='implementation/p09/evidence/p09-361-case165-'
DESIGN=dict(path=PREFIX+'preparation-attributed-CPU-design-code001.v1.json',bytes=5672,
    sha256='0bb7a4361e48b0b9de8000fc6e1f2808e4ed6a094821cb1b270f522075a1486c')
PROBE=dict(path=PREFIX+'preparation-attributed-CPU-probe001.v1.json',bytes=6604,
    sha256='43543a2be639dfd63fe7a0831403a85255e738e26b3b52b21b2b338c39b5e8be')
CONNECTION=dict(path=PREFIX+'preparation-attributed-connection-code010.v1.json',bytes=15307,
    sha256='1d7b2775d2b73e45c15c8b424a6cc73287dd33980475b17f6219ebf0246844c3')
GRAPH=PREFIX+'successor-run010-zlib-graph004.v1.json'
AUTHORIZATION='준비 단계에만 적용'
READERS=(
    dict(path='tools/p09/single_snapshot_source_guard_v1.py',bytes=4560,
        sha256='f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43'),
    dict(path='tools/p09/reusable_audit_chunk_v1.py',bytes=8088,
        sha256='1aa1db74585cbdf50df32ac0c9dc07dfd31557fc37647ca6e6ea3969fbb60e75'))
READER_SOURCE=dict(path='tools/p09/audit_evidence_io.py',bytes=5653,
    sha256='84b7dae287ac01c7ec308ca302762ec283406fca3fa43bc469882a3913578a8f')
EXTRA=(SELF,POLICY['path'],WITNESS['path'],DESIGN['path'],PROBE['path'],CONNECTION['path'])+tuple(p['path'] for p in READERS)+(READER_SOURCE['path'],)
GUARD_BOOTSTRAP=tuple('tools/p09/'+n+'.py' for n in
    ('prepared_run_closure_v1','owned_cpu_baseline_v1','terminal_metadata_pressure_v1','distinct_final_sample_guard_v1'))


def require(ok,code):
    if not ok:raise ValueError('ZLIB_PREPARATION_'+code)


def parent_module(root):
    path=root/PARENT['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_SEALED_PARENT')
    for ancestor in (path.parent,*path.parent.parents):
        require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),'DIRECT_SEALED_ANCESTORS')
        if ancestor==root:break
    with path.open('rb') as stream:raw=stream.read(PARENT['bytes']+1)
    require(len(raw)==PARENT['bytes'] and hashlib.sha256(raw).hexdigest()==PARENT['sha256'],'SEALED_PARENT_SOURCE')
    env=dict(__name__='p09_exact_zlib_preparation_parent',__file__=str(path))
    exec(compile(raw,PARENT['path'],'exec'),env)
    return NS(**env)


def admission(root,loader,entry,a,c):
    guards,_=loader.load(root,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    guard=guards.owned_cpu_baseline_v1.guard_type(guards.terminal_metadata_pressure_v1.guard_type(
        guards.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    row=None
    try:
        guard.acquire();q=a.AcceptanceReader(root,guard.check)
        for n in (SELF,TEST):q.pin(n)
        for p in (*entry.BOOTSTRAP,PARENT,POLICY,WITNESS,DESIGN,PROBE,CONNECTION):
            a.exact(q.pin(p['path']),p,'ORIGINAL_POLICY_AND_SEALED_PARENT')
        record=a.read_exact(q,CONNECTION)
        a.fields(record,dict(state='PASS_PREPARATION_ATTRIBUTED_CONNECTION_CODE_NOT_NATIVE_OR_STAGE_EXECUTION',
            contracts=dict(run=30,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            GO_authorized=False,accepted_count_delta=0),'QUALIFIED_WITNESS_SOURCE_NOT_NATIVE_AUTHORITY')
        source={p['path']:p for p in record['source_pins']}
        a.exact(source[WITNESS['path']],WITNESS,'EXACT_WITNESS_FUNCTION_SOURCE')
        libraries,_=loader.load(root,[POLICY,WITNESS],{})
        policy=libraries.preparation_attributed_cpu_v1
        libraries.preparation_attributed_entry_v1.policy_witnesses(q,a,policy)
        import audit_evidence_io as original_reader
        for p in READERS:a.exact(q.pin(p['path']),p,'QUALIFIED_FRESH_STAT_AND_WORKSPACE_SOURCE')
        optimized,_=loader.load(root,list(READERS),{'audit_evidence_io':original_reader})
        actual,raw=q._read(READER_SOURCE['path'],parse=True);q._bind(actual['path'],actual)
        a.exact(actual,READER_SOURCE,'EXACT_ORIGINAL_READER_NOT_REWRITTEN')
        Source,source_proof=optimized.single_snapshot_source_guard_v1.reader_type(a.AcceptanceReader,bytes(raw))
        Reader,chunk_proof=optimized.reusable_audit_chunk_v1.reader_type(Source,bytes(raw))
        q.finish();guard.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots),'FULL_POLICY_WITNESS_CLOSING')
        row=dict(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            policy_source=dict(POLICY),design_and_controlled_probe_closed=True,
            reader_source_proof=source_proof,reader_chunk_proof=chunk_proof,
            connection30_reused_only_to_identify_witness_source=True,whole_connection77_or_Native_requalified=False)
    finally:guard.close()
    require(guard.cleanup is True,'ORIGINAL_ADMISSION_OWNER_CLOSED')
    row['cleanup_confirmed']=guard.cleanup
    return policy,row,Reader,optimized.reusable_audit_chunk_v1


def policy_loader(loader,policy,instances):
    """Replace only a private preparation dependency, not any Native module."""
    armed=True
    def load(root,pins,reuse):
        nonlocal armed
        names,proof=loader.load(root,pins,reuse)
        if armed and tuple(p['path'] for p in pins)==GUARD_BOOTSTRAP:
            armed=False
            require(hasattr(names,'terminal_metadata_pressure_v1'),'EXACT_PREPARATION_GUARD_BUNDLE')
            # The selector is only a bootstrap hook. Later AST namespace
            # connections must receive the exact original load function.
            facade.load=loader.load
            ordinary=names.terminal_metadata_pressure_v1
            def preparation_type(original):
                selected=policy.guard_type(original,role='dispatch_construction')
                initialize=selected.__init__
                def initialize_once(self):initialize(self);instances.append(self)
                selected.__init__=initialize_once
                return selected
            names=NS(**{**vars(names),'terminal_metadata_pressure_v1':
                NS(**{**vars(ordinary),'guard_type':preparation_type})})
        return names,proof
    facade=NS(**{**vars(loader),'load':load})
    return facade


def connect(parent,policy,witness,*,reader=None,chunk=None):
    instances=[];readers=[];original_bootstrap=parent.bootstrap;original_table=parent.source_table
    def bootstrap(root):
        loader,entry,profile=original_bootstrap(root)
        return policy_loader(loader,policy,instances),entry,profile
    def source_table(data,q,entry,profile,scope):
        sources=original_table(data,q,entry,profile,scope)
        extra={n:dict(q.pin(n)) for n in EXTRA}
        for p in (POLICY,WITNESS,DESIGN,PROBE,CONNECTION,*READERS,READER_SOURCE):
            require(extra[p['path']]==p,'EXACT_POLICY_DECLARATION_IN_CURRENT_SCOPE')
        return scope.extend(sources,extra)
    def measured_json(row,**options):
        require(type(row) is dict and len(instances)==1,'ONE_ACTUAL_PREPARATION_GUARD')
        guard=instances[0]
        if reader is not None:
            require(len(readers)==1,'ONE_ACTUAL_OPTIMIZED_PREPARATION_READER')
            row=dict(row,reader_optimization=dict(source=readers[0].source_snapshot_diagnostics(),
                chunk=chunk.summary(readers[0]),default_reader_changed=False))
        return json.dumps(dict(row,preparation_policy=guard.preparation_CPU.summary(),
            preparation_owned_limits=guard.preparation_limits,policy_admission=witness,
            preparation_only_authorization=AUTHORIZATION,Native_policy_changed=False,
            original_parent_main_code_unchanged=True),**options)
    original=parent.main
    builtins=dict(original.__builtins__)
    if reader is not None:
        import accept_case112_current_epoch as original_a
        original_import=builtins['__import__']
        class CurrentReader(reader):
            def __init__(self,*args,**options):
                super().__init__(*args,**options);readers.append(self)
        api=NS(**{**vars(original_a),'AcceptanceReader':CurrentReader})
        def imports(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='accept_case112_current_epoch' and level==0:return api
            return original_import(name,globals,locals,fromlist,level)
        builtins['__import__']=imports
    env=dict(original.__globals__,bootstrap=bootstrap,source_table=source_table,GRAPH=GRAPH,
        __builtins__=builtins,
        json=NS(**{**vars(json),'dumps':measured_json}))
    selected=FunctionType(original.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
    selected.__kwdefaults__=original.__kwdefaults__
    require(selected.__code__ is original.__code__ and selected.__closure__ is original.__closure__,'ENTIRE_PARENT_MAIN_BODY')
    return selected


def main():
    require(sys.argv[1:] in (['--prepare-graph'],['--connect']),'PREPARATION_ONLY_NO_NATIVE_OR_PRODUCT_MODE')
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'));sys.dont_write_bytecode=True
    import accept_case112_current_epoch as a,conservative_maintenance as c
    parent=parent_module(root);loader,entry,_=parent.bootstrap(root)
    policy,witness,Reader,chunk=admission(root,loader,entry,a,c)
    return connect(parent,policy,witness,reader=Reader,chunk=chunk)()


if __name__=='__main__':raise SystemExit(main())
