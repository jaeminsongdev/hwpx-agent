"""Closed common-entry construction with the original owned metadata policy.

This verifies the real shared engine and independent checker before execution.
It never begins a whole batch, metadata body, Native Frame, worker, GO or intent.
"""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_engine_owned_metadata_entry.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_entry.py'
CONTROL='tools/p09/native011_engine_owned_metadata_validation.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-engine-owned-metadata-entry-construct001.v1.json'
CONTROLS=(SELF,TEST,CONTROL,'tools/p09/tests/test_native011_engine_owned_metadata_validation.py',
    'tools/p09/native011_engine_owned_metadata_connection.py','tools/p09/tests/test_native011_engine_owned_metadata_connection.py',
    'tools/p09/native011_engine_owned_metadata_adoption.py','tools/p09/tests/test_native011_engine_owned_metadata_adoption.py')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('ENGINE_OWNED_METADATA_ENTRY_'+code)


def driver_type(base,projection):
    class Driver(base):
        def __init__(self):super().__init__(8,construct_only=True);self.output=OUTPUT
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);original=control.admit;state=NS(calls=0)
            def declared(q,a,scope,**options):
                require(state.calls==0 and options==dict(exact_read=True,decoder_timing=True,chunk_join=True,metadata_tail=True),
                    'ONE_EXPLICIT_COMMON_OWNED_METADATA_DECLARATION')
                value=original(q,a,scope,**options);state.calls+=1
                require(len(value.control_names)==39 and not set(CONTROLS)&set(value.control_names)
                    and len(set(CONTROLS))==8,'EXACT47_NAMED_CONTROLS_NOT_OBSERVED_SOURCE_UNION')
                return NS(**{**vars(value),'control_names':value.control_names+CONTROLS})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            result=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            owner=data.planned.batch;proof=row['metadata_tail_connection']
            require(self.construct_only and self.stage=='construction' and self.native is None
                and owner.phase=='NEW' and owner.metadata_connection.readers==owner.metadata_connection.budgets==[]
                and owner.shared.metadata is owner.shared.frame is None
                and prepared.linked.state.attempts==prepared.linked.state.calls==0,
                'REAL_COMMON_PARENT_WITHOUT_ANY_BODY_OR_FRAME_OR_WORKER')
            require(proof['original_engine_owned_assignment_required'] is True
                and proof['original_engine_metadata_IO_rates']==dict(binary=1048576,other=2097152)
                and proof['metadata_factory_connection']['engine_assignment_stage']['original_engine_assignment_required_before_IO'] is True
                and proof['metadata_factory_connection']['entire_original_metadata_factory_and_Router_code_retained'] is True
                and proof['reader_allocations_during_connection']==0
                and row['actual_engine_and_checker_same_complete_model'] is True
                and q.final_fresh_hashes==len(q.snapshots),'COMMON_METADATA_SELECTOR_AND_ORIGINAL_CHECKER_CLOSURE')
            return dict(result,state='PASS_COMMON_ENTRY_OWNED_METADATA_AND_CHECKER_CONSTRUCTION_NOT_EXECUTION',
                engine_owned_common_entry_projection=projection,common_metadata_factory_connected_before_original_engine_assignment=True,
                actual_metadata_body_or_Native_or_worker_or_product_executed=False,GO_authorized=False)
    return Driver


def main():
    require(sys.argv[1:]==[],'CLOSED_NO_GO_CONSTRUCTION_ENTRY');sys.dont_write_bytecode=True
    root=Path(__file__).resolve().parents[2];require(not(root/OUTPUT).exists(),'EXCLUSIVE_NEW_CONSTRUCTION')
    def fresh(name,limit):
        path=root/name
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_BOOTSTRAP');return raw
    raw=fresh(LOADER['path'],LOADER['bytes'])
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_owned_metadata_entry_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    pins=[]
    for name in (CONTROL,'tools/p09/native011_readonly_frame_driver.py','tools/p09/native011_ready_native_construction.py'):
        raw=fresh(name,65536);pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=NS(**env).load(root,pins,{})
    adapter=libs.native011_engine_owned_metadata_validation;common=libs.native011_ready_native_construction
    raw=fresh(adapter.SOURCE['path'],adapter.SOURCE['bytes'])
    validator,projection=adapter.project(raw,common.validate)
    entry,entry_proof=adapter.bind_entry(raw,common.main,validator)
    return entry(driver=driver_type(libs.native011_readonly_frame_driver.Driver,
        dict(validator=projection,entry=entry_proof))())


if __name__=='__main__':raise SystemExit(main())
