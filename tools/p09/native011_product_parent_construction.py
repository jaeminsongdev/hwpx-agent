"""Qualified worker202 in the real unopened common metadata/checker parent.

Only construction: no whole opening, reader/budget, Native Frame, worker, GO,
intent or product. The original source201 path and earlier receipts remain.
"""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_product_parent_construction.py'
TEST='tools/p09/tests/test_native011_product_parent_construction.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-product-worker202-parent-construct001.v1.json'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_PARENT_CONSTRUCTION_'+code)


def fresh(root,name,limit):
    path=root/name
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP')
        if member==root:break
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(0<len(raw)<=limit,'BOUNDED_FRESH_BOOTSTRAP');return raw


def driver_type(base,scope_api):
    class Driver(base):
        def __init__(self):
            super().__init__();self.output=OUTPUT;self.scope_state=None;self.scope_projection=None
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control)
            self.scope_state,self.scope_projection=scope_api.bind(control,fresh(root,scope_api.SOURCE['path'],scope_api.SOURCE['bytes']))
            before=control.admit;state=NS(calls=0)
            def declared(q,a,scope,**options):
                require(state.calls==0,'ONE_PARENT202_DECLARATION');state.calls+=1
                value=before(q,a,scope,**options)
                require(len(value.control_names)==57 and SELF not in value.control_names and TEST not in value.control_names,
                    'EXACT59_EXPLICIT_PARENT202_CONTROL_ROLES')
                return NS(**{**vars(value),'control_names':value.control_names+(SELF,TEST)})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            qualified=self.scope_state.admission;observed=row['exact_current_worker201_scope']
            require(self.scope_state.calls==1 and qualified is not None and qualified['worker_sources']==202
                and qualified['source_declaration_only'] is True and qualified['GO_authorized'] is False
                and observed['required_worker_sources']==observed['direct_current_worker_sources']==202
                and observed['missing_sources']==observed['conflicting_sources']==[]
                and observed['history_inputs']==419 and observed['original_base_reference_same'] is True
                and observed['actual_live_Frame_coverage_qualified'] is False,'ACTUAL_WORKER202_DIRECT_CURRENT_AND_ORIGINAL_FRAME_BASE')
            return dict(value,state='PASS_WORKER202_COMMON_PARENT_METADATA_CHECKER_CONSTRUCTION_NOT_NATIVE',
                qualified_worker202_admission=qualified,worker202_scope_inspector_projection=self.scope_projection,
                exact_current_worker202_scope=observed,legacy_worker201_field_label_is_compatibility_only=True,
                actual_product_launch_handoff_installed=False,actual_worker202_GO_or_Native_qualified=False)
    return Driver


def main():
    require(sys.argv[1:]==[],'CLOSED_NO_GO_PARENT_CONSTRUCTION');sys.dont_write_bytecode=True
    root=Path(__file__).resolve().parents[2];require(not(root/OUTPUT).exists(),'EXCLUSIVE_NEW_PARENT_CONSTRUCTION')
    raw=fresh(root,LOADER['path'],LOADER['bytes'])
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_worker202_parent_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    pins=[]
    for name in ('tools/p09/native011_engine_owned_metadata_validation.py','tools/p09/native011_engine_owned_metadata_entry.py',
        'tools/p09/native011_product_worker_scope.py','tools/p09/native011_readonly_frame_driver.py',
        'tools/p09/native011_ready_native_construction.py'):
        raw=fresh(root,name,65536);pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=NS(**env).load(root,pins,{})
    adapter=libs.native011_engine_owned_metadata_validation;common=libs.native011_ready_native_construction
    raw=fresh(root,adapter.SOURCE['path'],adapter.SOURCE['bytes']);validator,projection=adapter.project(raw,common.validate)
    execute,entry_projection=adapter.bind_entry(raw,common.main,validator)
    Base=libs.native011_engine_owned_metadata_entry.driver_type(libs.native011_readonly_frame_driver.Driver,
        dict(validator=projection,entry=entry_projection))
    return execute(driver=driver_type(Base,libs.native011_product_worker_scope)())


if __name__=='__main__':raise SystemExit(main())
