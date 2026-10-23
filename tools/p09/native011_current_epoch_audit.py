"""Actual current805 whole boundaries and metadata, never Frame/worker/GO.

Use the original four600 preparation epochs and unchanged metadata body.
These epochs neither start nor reset Native600, READY15 or product10 clocks.
"""
import hashlib
import copy
import json
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_audit.py'
TEST='tools/p09/tests/test_native011_current_epoch_audit.py'
SOURCE=dict(path='tools/p09/native011_metadata_audit.py',bytes=10082,
    sha256='b52d887dbd4330ab39d4e4a6ea13f45868c3e9eda0c2db9b5cf086271f50c0bd')
EPOCH=dict(path='tools/p09/native011_metadata_epochs.py',bytes=5696,
    sha256='4afc83d1ec7af136081a2314ae92cce1f63f14398a7cc6982ece9d3692275eb1')
PARENT=dict(path='tools/p09/native011_parent_plan.py',bytes=24332,
    sha256='b58c2658510f7af5824a4b54d64fe6858cd128a1ddef1e235b00bd46238c69b8')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_ACTUAL_AUDIT_'+code)


def checkpoint_payload(phase,result,source_pins):
    require(phase in ('opening','metadata','closing'),'NAMED_COMPLETED_PREPARATION_STAGE')
    opening=result.get('whole_opening',{})
    require(opening.get('actual_complete') is True
        and type(opening.get('fresh_inputs')) is int and opening['fresh_inputs']==result['declared_whole_inputs']
        and opening['bytes_read']==result['declared_whole_bytes']
        and opening['full_pin_sha256']==result['whole_pin_sha256'],'ACTUAL_COMPLETE_OPENING_NOT_PARTIAL')
    evidence=dict(whole_opening=copy.deepcopy(opening))
    if phase in ('metadata','closing'):
        metadata=result.get('metadata',{})
        require(metadata.get('state')=='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE'
            and type(metadata.get('fresh_inputs')) is int and metadata['fresh_inputs']>0
            and metadata['fresh_inputs']==metadata['final_fresh_hashes']
            and metadata['metadata_body_executed'] is True and metadata['Frame_created'] is False
            and metadata['worker_created'] is False and metadata['GO_authorized'] is False,
            'ACTUAL_METADATA_CLOSING_AND_NO_FRAME_OR_WORKER')
        evidence['metadata']=copy.deepcopy(metadata)
    if phase=='closing':
        closing=result.get('whole_closing',{})
        require(closing==opening,'EXACT_WHOLE_SECOND_BOUNDARY_NOT_FIRST_PASS_REUSE')
        evidence['whole_closing']=copy.deepcopy(closing)
    require(type(source_pins) is list and bool(source_pins),'CONSTRUCTION_SOURCE_DECLARATIONS')
    return dict(state='COMPLETED_PREPARATION_STAGE_ONLY_NOT_FULL_AUDIT_OR_NATIVE',phase=phase,
        execution_scope_whole_sha256=result['whole_pin_sha256'],execution_code_source_pins=copy.deepcopy(source_pins),
        evidence=evidence,actual_whole_closing_complete=phase=='closing',
        actual_Native_Frame_or_READY15_or_product_qualified=False,GO_authorized=False,accepted_count_delta=0,
        source_hash_or_freshness_cache=False,later_input_read_or_guard_may_be_skipped=False)


class PreparationAudit:
    def __init__(self,module,factory,*,run_id=1):
        require(type(run_id) is int and run_id in (1,2,3),'CLOSED_READONLY_AUDIT_ID')
        self.run_id=run_id
        self.module=module;self.epochs=module.Epochs(factory)
        self.result={};self.readers={};self.last_samples=[];self.prepared=False;self.checkpoints={}
    def acquire(self):self.advance('construction')
    def advance(self,stage):
        self.epochs.advance(stage)
        index=self.module.STAGES.index(stage)
        print('P146_STAGE:'+self.module.MARKERS[index],file=sys.stderr,flush=True)
        print(json.dumps(dict(phase=stage,Native_clock_started=False,original_limit_seconds=600)),flush=True)
    def check(self,*args,**kwargs):return self.epochs.check(*args,**kwargs)
    @property
    def samples(self):return self.epochs.guard.samples if self.epochs.guard is not None else self.last_samples
    @property
    def cleanup(self):
        return bool(self.epochs.records) and all(row['cleanup_confirmed'] for row in self.epochs.records)
    def fail(self):self.epochs.broken=True
    def close(self):
        if self.epochs.guard is not None:self.last_samples=self.epochs.guard.samples
        self.epochs.close()
    def prepare(self,root,q,a,loader,entry,context,private_load,publisher):
        require(not self.prepared,'ONE_ACTUAL_AUDIT_PREPARATION')
        for pin in (SOURCE,EPOCH):a.exact(q.pin(pin['path']),pin,'ENTIRE_ORIGINAL_METADATA_AND_EPOCH_SOURCE')
        libraries,_=private_load(loader,root,q,a,('native011_metadata_audit',),{})
        self.original=libraries.native011_metadata_audit
        libraries,_=entry.planning_libraries(root,q,a,loader)
        self.optimized=libraries.batch_scope_admission.optimized_reader(root,q,context.oracle_result.known,
            context.oracle_result.loader,a.AcceptanceReader,a)
        self.publisher=publisher;self.publisher_api=NS(require=require,exact=a.exact)
        for phase in ('opening','metadata','closing'):
            require(not(root/self.checkpoint_path(phase)).exists(),'EXCLUSIVE_STAGE_CHECKPOINTS')
        self.prepared=True
    def checkpoint_path(self,phase):
        require(phase in ('opening','metadata','closing'),'NAMED_CHECKPOINT_PATH')
        return f'implementation/p09/evidence/p09-361-native011-current805-audit{self.run_id:03}-{phase}-checkpoint.v1.json'
    def checkpoint(self,root,q,phase):
        require(phase not in self.checkpoints,'NO_CHECKPOINT_REPLAY_OR_OVERWRITE')
        self.check(force=True)
        payload=checkpoint_payload(phase,self.result,list(q.snapshots.values()))
        self.checkpoints[phase]=self.publisher.publish(root,self.checkpoint_path(phase),payload,self.publisher_api)
    def run(self,root,q,context,a):
        require(self.prepared and not self.readers,'ONE_PREPARED_ACTUAL_AUDIT')
        require(q.final_fresh_hashes==len(q.snapshots),'CONSTRUCTION_FRESH_CLOSING_BEFORE_WHOLE')
        self.epochs.bind(context)
        owner=context.data.planned.batch;whole=context.batch.plain(owner.whole)
        binary=sum(pin['bytes'] for name,pin in whole.items() if name.lower().endswith('.exe'))
        other=sum(pin['bytes'] for name,pin in whole.items() if not name.lower().endswith('.exe'))
        nominal=len(whole)/20+binary/1048576+other/2097152
        self.result.update(declared_whole_inputs=len(whole),declared_whole_bytes=binary+other,
            whole_pin_sha256=self.original.digest(whole),nominal_one_whole_read_seconds=nominal,
            construction_fresh_inputs=len(q.snapshots),construction_final_fresh_hashes=q.final_fresh_hashes,
            reader_optimization=dict(source=self.optimized.source_proof,chunk=self.optimized.chunk_proof))
        require(nominal<600,'WHOLE_BOUNDARY_NOMINAL_INSIDE_ORIGINAL600')
        self.advance('opening');opening=self.optimized.Reader(root,self.check);self.readers['opening']=opening
        owner.begin(opening)
        self.result['whole_opening']=dict(fresh_inputs=opening.read_passes,bytes_read=opening.bytes_read,
            full_pin_sha256=self.original.digest(opening.snapshots),actual_complete=True)
        self.checkpoint(root,q,'opening')
        self.advance('metadata')
        self.result['metadata']=self.original.metadata(root,self.epochs,context,a)
        self.checkpoint(root,q,'metadata')
        self.advance('closing');closing=self.optimized.Reader(root,self.check);self.readers['closing']=closing
        self.result['whole_batch']=owner.finish(closing)
        self.epochs.validator(context,closed=True);self.check(force=True)
        require(self.original.digest(closing.snapshots)==self.result['whole_pin_sha256'],
            'ACTUAL_WHOLE_OPEN_AND_CLOSE_EXACT_IDENTITIES')
        self.result['whole_closing']=dict(fresh_inputs=closing.read_passes,bytes_read=closing.bytes_read,
            full_pin_sha256=self.original.digest(closing.snapshots),actual_complete=True)
        self.checkpoint(root,q,'closing')
        self.result.update(actual_metadata_body_executed=True,actual_Native_Frame_created=False,
            actual_product_executed=False,actual_shared_Frame_or_readiness15_qualified=False)
        return self.result
    def report(self,context):
        row=dict(self.result,epochs=self.epochs.records,completed_stage_checkpoint_pins=dict(self.checkpoints))
        if context is not None:
            expected=context.data.planned.whole
            for stage,reader in self.readers.items():
                row[stage+'_progress']=dict(fresh_inputs=len(reader.snapshots),read_passes=reader.read_passes,
                    bytes_read=reader.bytes_read,disagreements=[dict(path=name,actual=pin,expected=expected.get(name))
                        for name,pin in reader.snapshots.items() if expected.get(name)!=pin][:8])
        return row


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    require(args.attempt in (1,2,3) and args.generation==3,'ONLY_CURRENT805_READONLY_AUDIT_REPORT003')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    raw=(c.ROOT/LOADER['path']).read_bytes()
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_BOOTSTRAP')
    env=dict(__name__='p09_current805_audit_bootstrap',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env);loader=NS(**env)
    modules,_=loader.load(c.ROOT,[PARENT,EPOCH],{});parent=modules.native011_parent_plan
    epoch=modules.native011_metadata_epochs;source_loader=parent.bootstrap_loader(c.ROOT)
    guards,_=source_loader.load(c.ROOT,list(parent.GUARDS),{})
    host,baseline,policy,final=(getattr(guards,name) for name in ('prepared_run_closure_v1',
        'owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))
    host.configure_host_policy(c)
    def factory(role):return baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role=role))()
    driver=PreparationAudit(epoch,factory,run_id=args.attempt)
    path='tools/p09/native011_current_epoch_shared.py';raw=(c.ROOT/path).read_bytes()
    pin=dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    libraries,_=loader.load(c.ROOT,[pin],{})
    # The wrapper already validated these closed identifiers. The shared entry
    # has no product/GO mode; its one private audit driver owns all epochs.
    previous=sys.argv;sys.argv=[previous[0]]
    try:return libraries.native011_current_epoch_shared.main(audit_driver=driver)
    finally:sys.argv=previous


if __name__=='__main__':raise SystemExit(main())
