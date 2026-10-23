"""Current private parent, four real preparation epochs and owned metadata.

Reuses the original whole begin/end audit. No Native Frame, worker or GO path.
Every construction/component reader is independent and closes freshly.
"""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_engine_owned_metadata_preparation.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_preparation.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-engine-owned-metadata-preparation001.v1.json'
AUDIT=dict(path='tools/p09/native011_current_epoch_audit.py',bytes=10853,
    sha256='bd14968dee6e2648018bcb6af3356df085180234a9ecda3ce7606d84eeae80ed')
EPOCH=dict(path='tools/p09/native011_metadata_epochs.py',bytes=5696,
    sha256='4afc83d1ec7af136081a2314ae92cce1f63f14398a7cc6982ece9d3692275eb1')
EXTRA=(SELF,TEST,'tools/p09/native011_engine_owned_metadata_callback.py',
    'tools/p09/tests/test_native011_engine_owned_metadata_callback.py',
    'tools/p09/native011_current_epoch_audit.py','tools/p09/tests/test_native011_current_epoch_audit.py')


def require(ok,code):
    if not ok:raise ValueError('ENGINE_OWNED_METADATA_PREPARATION_'+code)


def driver_type(base,probe,audit_module,epoch_module):
    class Driver(base):
        def __init__(self):
            super().__init__(7,construct_only=True);self.output=OUTPUT;self.audit=None;self.source_evidence=None
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control)
            self.audit=audit_module.PreparationAudit(epoch_module,lambda role:self.factory(role),run_id=3)
            self.audit.checkpoint_path=lambda phase:OUTPUT.replace('.v1.json','.'+phase+'-checkpoint.v1.json')
            original=control.admit;state=NS(calls=0)
            def declared(q,a,scope,**options):
                require(state.calls==0 and options==dict(exact_read=True,decoder_timing=True,chunk_join=True),
                    'ONE_ORIGINAL_DECLARATION')
                value=original(q,a,scope,**options);state.calls+=1
                additions=probe.CONTROLS+probe.OWNED_CONTROLS+EXTRA
                require(len(value.control_names)==35 and len(set(additions))==len(additions)
                    and not set(additions)&set(value.control_names),'EXACT_NAMED_PREPARATION_SOURCES')
                return NS(**{**vars(value),'control_names':value.control_names+additions})
            control.admit=declared
        def acquire(self):
            require(self.bound and self.audit is not None,'BOUND_REAL_PREPARATION_AUDIT');self.audit.acquire()
        def check(self,*args,**kwargs):return self.audit.check(*args,**kwargs)
        @property
        def samples(self):return [] if self.audit is None else self.audit.samples
        @property
        def cleanup(self):return self.audit is not None and self.audit.cleanup
        def close(self):
            self.closed=True
            if self.audit is not None:self.audit.close()
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            require(self.audit.epochs.stage=='construction' and self.native is None
                and q.final_fresh_hashes==len(q.snapshots),'NEW_PREPARATION_AFTER_CONSTRUCTOR_CLOSING')
            context=NS(data=data,batch=batch,prepared=prepared,bound=bound,shared=resources,oracle_result=checked,row=row)
            self.case_context=context;source_reader=a.AcceptanceReader(root,self.check)
            owner=data.planned.batch
            def source(name):
                expected=dict(owner.whole[name]);actual,raw=source_reader._read(name,parse=True)
                source_reader._bind(name,actual);a.exact(actual,expected,'FRESH_DECLARED_PREPARATION_SOURCE')
                return bytes(raw)
            def private(name):
                env=dict(__name__='p09_preparation_'+name.rsplit('/',1)[-1][:-3],__file__=name)
                exec(compile(source(name),name,'exec'),env);return NS(**env)
            candidate=private(probe.CONTROLS[0]);connection=private(probe.CONTROLS[2])
            adoption=private(probe.OWNED_CONTROLS[0]);owned=private(probe.OWNED_CONTROLS[2])
            exact=private('tools/p09/native011_exact_read_budget.py')
            codes=private('tools/p09/native011_chunk_join_connection.py')
            bridge=private('tools/p09/native011_engine_owned_metadata_callback.py')
            leaves=[cls for cls in owner.metadata_connection.original_reader.__mro__
                if cls.__name__=='ChunkLeaf' and '_read' in vars(cls)]
            require(len(leaves)==1,'ACTUAL_EXISTING_WORKSPACE')
            chunk=NS(**leaves[0]._read.__globals__['_workspace_for'].__globals__)
            require(chunk.SELF=='tools/p09/reusable_audit_chunk_v1.py','EXACT_ACTUAL_WORKSPACE')
            pressure=prepared.linked.engine.run_owned.__globals__['byte_policy']
            link,proof=owned.connect(prepared.linked,owner,{n:dict(p) for n,p in owner.whole.items()},
                connection,candidate,adoption,exact,pressure,chunk,source(exact.ORIGINAL['path']),
                source(connection.METADATA['path']),source(connection.BUILD['path']),codes)
            self.audit.prepare(root,source_reader,a,loader,entry,context,private_load,publisher)
            selected,body_proof=bridge.project(source(bridge.SOURCE['path']),self.audit.original.metadata,
                source(owned.ENGINE['path']),owned)
            # The original audit instance receives a private function dependency;
            # its whole boundaries, four epochs and closing body stay unchanged.
            self.audit.original=NS(**{**vars(self.audit.original),'metadata':selected.callback})
            for name in probe.CONTROLS+probe.OWNED_CONTROLS+EXTRA:source_reader.pin(name)
            source_reader.finish();self.check(force=True)
            require(source_reader.final_fresh_hashes==len(source_reader.snapshots),'ALL_PREPARATION_SOURCE_CLOSING')
            self.source_evidence=dict(fresh_inputs=len(source_reader.snapshots),
                final_fresh_hashes=source_reader.final_fresh_hashes,source_pins=list(source_reader.snapshots.values()),
                constructor_reader_reused=False,connection=proof,callback_projection=body_proof)
            result=self.audit.run(root,q,context,a);reader=owner.metadata_connection.readers[0]
            require(isinstance(reader,link.selected_reader) and selected.state.attempts==selected.state.completed==1
                and not selected.state.failed and owner.shared.frame is None
                and prepared.linked.state.attempts==prepared.linked.state.calls==0,'ONE_COMPLETE_CALLBACK_NO_NATIVE_OR_WORKER')
            result['actual_owned_metadata_adoption']=adoption.summary(reader)
            result['actual_paced_bytes_by_kind']=dict(reader.pacer.bytes_by_kind)
            result['original_query_requests']=reader.open_pacer.requests
            self.result=result
            return dict(state='PASS_PREPARATION_FULL_OWNED_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE',
                actual_metadata_body_qualified=True,actual_whole_corpus_bytes_qualified=True,
                actual_Native_Frame_created=False,actual_product_executed=False,GO_authorized=False)
        def finish(self,root,row,publisher,a):
            require(self.closed,'PREPARATION_GUARDS_CLOSED_BEFORE_PUBLICATION')
            row.update(owned_metadata_preparation=self.audit.report(self.case_context),
                preparation_source_evidence=self.source_evidence,original_four600_preparation_epochs=True,
                Native_clock_reset_or_extended=False,actual_Native_Frame_created=False,
                actual_product_executed=False,GO_authorized=False)
            if self.decoder_timing is not None:
                observation=self.decoder_timing.evidence()
                row['shared_decoder_timing_observation_artifact']=publisher.publish(root,
                    OUTPUT.replace('.v1.json','.timing.v1.json'),observation,NS(require=require,exact=a.exact))
    return Driver


def main():
    require(sys.argv[1:]==[],'CLOSED_NO_GO_ENTRY');sys.dont_write_bytecode=True
    root=Path(__file__).resolve().parents[2];require(not(root/OUTPUT).exists(),'EXCLUSIVE_NEW_PREPARATION')
    def fresh(name,limit):
        path=root/name
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_BOOTSTRAP');return raw
    loader_pin=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
        sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
    raw=fresh(loader_pin['path'],loader_pin['bytes'])
    require(len(raw)==loader_pin['bytes'] and hashlib.sha256(raw).hexdigest()==loader_pin['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_owned_metadata_preparation_bootstrap',__file__=loader_pin['path'])
    exec(compile(raw,loader_pin['path'],'exec'),env);pins=[]
    for name in ('tools/p09/native011_readonly_frame_driver.py','tools/p09/native011_ready_native_construction.py',
        'tools/p09/native011_metadata_tail_probe.py',AUDIT['path'],EPOCH['path']):
        raw=fresh(name,65536)
        pin=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if name in (AUDIT['path'],EPOCH['path']):require(pin==(AUDIT if name==AUDIT['path'] else EPOCH),'EXACT_ORIGINAL_PREPARATION_IMPLEMENTATION')
        pins.append(pin)
    libs,_=NS(**env).load(root,pins,{})
    return libs.native011_ready_native_construction.main(driver=driver_type(libs.native011_readonly_frame_driver.Driver,
        libs.native011_metadata_tail_probe,libs.native011_current_epoch_audit,libs.native011_metadata_epochs)())


if __name__=='__main__':raise SystemExit(main())
