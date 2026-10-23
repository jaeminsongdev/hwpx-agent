"""Fresh real private factory, two semantic inputs with original closing.

No whole opening, full admission callback, Native Frame, worker, GO or product.
The unopened constructor is original. A separate component reader closes all
code inputs; the real Routed metadata reader performs its own fresh IO/closing.
"""
import hashlib
import sys
import time
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_metadata_tail_probe.py'
TEST='tools/p09/tests/test_native011_metadata_tail_probe.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-metadata-tail-private-probe001.v1.json'
OWNED_OUTPUT='implementation/p09/evidence/p09-361-native011-current805-engine-owned-metadata-private-probe002.v1.json'
CONTROLS=('tools/p09/native011_metadata_tail_candidate.py','tools/p09/tests/test_native011_metadata_tail_candidate.py',
    'tools/p09/native011_metadata_tail_connection.py','tools/p09/tests/test_native011_metadata_tail_connection.py',SELF,TEST)
OWNED_CONTROLS=('tools/p09/native011_engine_owned_metadata_adoption.py',
    'tools/p09/tests/test_native011_engine_owned_metadata_adoption.py',
    'tools/p09/native011_engine_owned_metadata_connection.py','tools/p09/tests/test_native011_engine_owned_metadata_connection.py')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('METADATA_TAIL_PRIVATE_PROBE_'+code)


def component(root,q,a,owner,prepared,checkpoint,*,engine_owned=False):
    require(type(engine_owned) is bool,'EXPLICIT_ENGINE_OWNED_COMPONENT_MODE')
    require(q.read_passes==0 and not q.snapshots and q.final_fresh_hashes==0,'SEPARATE_UNUSED_COMPONENT_SOURCE_READER')
    def source(name):
        expected=dict(owner.whole[name]);actual,raw=q._read(name,parse=True);q._bind(name,actual)
        a.exact(actual,expected,'FRESH_DECLARED_COMPONENT_CODE_BYTES');return bytes(raw)
    def private(name):
        raw=source(name);env=dict(__name__='p09_private_'+name.rsplit('/',1)[-1][:-3],__file__=name)
        exec(compile(raw,name,'exec'),env);return NS(**env)
    candidate=private(CONTROLS[0]);connection=private(CONTROLS[2])
    for name in CONTROLS+(OWNED_CONTROLS if engine_owned else ()):q.pin(name)
    exact=private('tools/p09/native011_exact_read_budget.py')
    codes=private('tools/p09/native011_chunk_join_connection.py')
    old=owner.metadata_connection.original_reader
    leaves=[cls for cls in old.__mro__ if cls.__name__=='ChunkLeaf' and '_read' in vars(cls)]
    require(len(leaves)==1,'ACTUAL_EXISTING_METADATA_WORKSPACE')
    chunk=NS(**leaves[0]._read.__globals__['_workspace_for'].__globals__)
    require(chunk.SELF=='tools/p09/reusable_audit_chunk_v1.py','EXACT_ACTUAL_WORKSPACE_NAMESPACE')
    pressure=prepared.linked.engine.run_owned.__globals__['byte_policy']
    if engine_owned:
        adoption=private(OWNED_CONTROLS[0]);owned_connection=private(OWNED_CONTROLS[2])
        linked,proof=owned_connection.connect(prepared.linked,owner,{name:dict(pin) for name,pin in owner.whole.items()},
            connection,candidate,adoption,exact,pressure,chunk,source(exact.ORIGINAL['path']),
            source(connection.METADATA['path']),source(connection.BUILD['path']),codes)
    else:
        linked,proof=connection.connect(prepared.linked,owner,{name:dict(pin) for name,pin in owner.whole.items()},
            candidate,exact,pressure,chunk,source(exact.ORIGINAL['path']),source(connection.METADATA['path']),
            source(connection.BUILD['path']),codes)
    rows=prepared.entry.graph.binding.descriptors()
    require(type(rows) is list and len(rows)==162,'ACTUAL162_DECLARED_PAIRS')
    selected=sorted(rows,key=lambda row:(row['physical_envelope_pin']['bytes'],row['physical_envelope_pin']['path']))[:2]
    require(len(selected)==2,'TWO_ACTUAL_DECLARED_SEMANTIC_INPUTS')
    prefix=None
    if engine_owned:
        reader,prefix=owned_connection.allocate_original_prefix(source(owned_connection.ENGINE['path']),
            prepared.linked.engine.run_owned.__globals__['build'],root,checkpoint,pressure)
        require(adoption.summary(reader)['original_engine_owned_assignment_adopted'] is True,
            'ACTUAL_ORIGINAL_ENGINE_ALLOCATION_AND_OWNED_ASSIGNMENT')
    else:reader=prepared.linked.engine.run_owned.__globals__['build'].BuildReader(root,checkpoint)
    require(isinstance(reader,linked.selected_reader) and owner.metadata_connection.readers==[reader]
        and len(owner.metadata_connection.budgets)==1,'ONE_ORIGINAL_ROUTED_METADATA_ALLOCATION')
    started=time.perf_counter()
    for row in selected:
        a.exact(reader.fresh_pin(row['semantic_original_pin']['path']),row['semantic_original_pin'],
            'FRESH_REAL_SEMANTIC_HASH_NOT_PHYSICAL_PIN_SUBSTITUTION')
    reader.finish();checkpoint(force=True)
    require(reader.final_fresh_hashes==len(reader.snapshots)==2 and reader.read_passes==4
        and reader.bytes_read==reader.pacer.bytes_paced==2*sum(row['physical_envelope_pin']['bytes'] for row in selected)
        and reader.open_pacer.requests==4 and reader.lossless_metadata_attempts==reader.lossless_metadata_completed==4
        and reader.pacer.reserved_bytes-reader.pacer.refunded_bytes==reader.bytes_read
        and reader.pacer.pending is reader.pacer.request is None and not reader.pacer.failed,
        'ALL_REAL_PHYSICAL_BYTES_SEMANTIC_DECODES_OPEN_GUARDS_AND_CLOSING')
    elapsed=time.perf_counter()-started
    q.finish();checkpoint(force=True)
    require(q.final_fresh_hashes==len(q.snapshots) and owner.shared.frame is None
        and prepared.linked.state.attempts==prepared.linked.state.calls==0,'COMPLETE_COMPONENT_CLOSING_NO_WORKER')
    return dict(connection=proof,actual_private_factory_reader_created=True,selected_pairs=selected,
        actual_physical_read_passes=reader.read_passes,actual_physical_bytes=reader.bytes_read,
        actual_semantic_fresh_inputs=len(reader.snapshots),actual_semantic_final_fresh_hashes=reader.final_fresh_hashes,
        actual_semantic_decodes=reader.lossless_metadata_completed,query_requests=reader.open_pacer.requests,
        actual_byte_policy='original_engine_owned_binary1_other2_MiB' if engine_owned else 'original_metadata_binary2p5_other4_MiB',
        actual_query_policy='original20_per_second',original_allocation_assignment_prefix=prefix,
        engine_owned_adoption=None if not engine_owned else adoption.summary(reader),
        actual_final_selected_rate=reader.pacer.rate,actual_paced_bytes_by_kind=dict(reader.pacer.bytes_by_kind),
        exact_reserved_bytes=reader.pacer.reserved_bytes,exact_refunded_bytes=reader.pacer.refunded_bytes,
        actual_source_snapshot=reader.source_snapshot_diagnostics(),actual_workspace=chunk.summary(reader),
        actual_shared_decoder=owner.shared.evidence(),elapsed_seconds=elapsed,
        component_source_fresh_inputs=len(q.snapshots),component_source_final_fresh_hashes=q.final_fresh_hashes,
        component_source_pins=list(q.snapshots.values()),constructor_reader_reused=False,
        complete_metadata_callback_or_Native_Frame_or_worker_or_product_executed=False,GO_authorized=False,
        complete_metadata_or_shared5_or_Native_or_product_qualified=False)


def driver_type(base,*,engine_owned=False):
    require(type(engine_owned) is bool,'EXPLICIT_ENGINE_OWNED_DRIVER')
    class Driver(base):
        def __init__(self):super().__init__(7,construct_only=True);self.output=OWNED_OUTPUT if engine_owned else OUTPUT
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);previous=control.admit;state=NS(calls=0)
            def declared(q,a,scope,**options):
                require(state.calls==0 and options==dict(exact_read=True,decoder_timing=True,chunk_join=True),
                    'ONE_ORIGINAL_DECLARATION')
                value=previous(q,a,scope,**options);state.calls+=1
                additions=CONTROLS+(OWNED_CONTROLS if engine_owned else ())
                require(len(value.control_names)==35 and not set(additions)&set(value.control_names),
                    'EXACT_NAMED_COMPONENT_SOURCES')
                return NS(**{**vars(value),'control_names':value.control_names+additions})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            require(self.construct_only and self.stage=='construction' and self.native is None
                and value['actual_Native_Frame_created'] is False,'NO_NATIVE_OR_WHOLE_OPENING')
            component_reader=a.AcceptanceReader(root,self.check)
            evidence=component(root,component_reader,a,data.planned.batch,prepared,self.check,engine_owned=engine_owned)
            state='PASS_ACTUAL_ENGINE_OWNED_METADATA_COMPONENT_NOT_FULL_CALLBACK_OR_NATIVE' if engine_owned else \
                'PASS_ACTUAL_PRIVATE_METADATA_TAIL_COMPONENT_NOT_FULL_CALLBACK_OR_NATIVE'
            return dict(value,state=state,
                actual_private_metadata_tail_component=evidence)
    return Driver


def main():
    require(sys.argv[1:] in ([],['--engine-owned']),'CLOSED_NO_GO_ENTRY');root=Path(__file__).resolve().parents[2]
    engine_owned=bool(sys.argv[1:])
    sys.dont_write_bytecode=True;require(not(root/(OWNED_OUTPUT if engine_owned else OUTPUT)).exists(),'EXCLUSIVE_NEW_PROBE')
    def fresh(name,limit):
        path=root/name
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_BOOTSTRAP');return raw
    raw=fresh(LOADER['path'],LOADER['bytes'])
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_metadata_tail_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    pins=[]
    for name in ('tools/p09/native011_readonly_frame_driver.py','tools/p09/native011_ready_native_construction.py'):
        raw=fresh(name,65536);pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=NS(**env).load(root,pins,{})
    before=sys.argv;sys.argv=[before[0]]
    try:return libs.native011_ready_native_construction.main(driver=driver_type(
        libs.native011_readonly_frame_driver.Driver,engine_owned=engine_owned)())
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
