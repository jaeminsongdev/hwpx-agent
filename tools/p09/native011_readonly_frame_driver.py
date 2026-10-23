"""New whole opening then one original600 metadata/Native-frame diagnostic.

No product, worker, GO, synthetic commit or successful batch closure. Child
guards never rotate after a Frame starts. Full terminal Frame JSON is preserved
losslessly in bounded exclusive/fsynced parts while the external owned monitor
continues supervising the same process, after the Native handles are closed.
"""
import base64
import hashlib
import json
import os
import re
import threading
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_readonly_frame_driver.py'
TEST='tools/p09/tests/test_native011_readonly_frame_driver.py'
MARKERS=('source_begin','connect_first_begin','consumer_begin','connect_second_begin')
PART_BYTES=180000
MAX_FRAME_BYTES=16*1048576


def require(ok,label):
    if not ok:raise ValueError('READONLY_FRAME_DRIVER_'+label)


def frame_parts(raw):
    require(type(raw) is bytes and 0<len(raw)<=MAX_FRAME_BYTES,'BOUNDED_COMPLETE_FRAME_BYTES')
    return [dict(index=i//PART_BYTES,bytes=len(raw[i:i+PART_BYTES]),
        sha256=hashlib.sha256(raw[i:i+PART_BYTES]).hexdigest(),
        base64=base64.b64encode(raw[i:i+PART_BYTES]).decode('ascii')) for i in range(0,len(raw),PART_BYTES)]


def precise_opening(reader,pressure,precise):
    # Same approved byte algorithm/rates/workspace/checkpoints; no opened or
    # partially used reader is eligible. OpenPacer and all Guard clocks stay.
    proof=precise.connect(reader,pressure)
    return dict(proof,scope='new_whole_opening_only',original_open_pacer_and_stage_deadline_retained=True)


def terminal_readers(frame):
    """Existing terminal counters only; partial bytes never become a boundary."""
    require(frame.state=='CLOSED' and frame.held.closed and not frame.registered,
        'PARTIAL_READER_DIAGNOSTIC_AFTER_ORIGINAL_CLOSE_ONLY')
    rows=[]
    for index,reader in enumerate(frame.readers):
        p=reader.pacer
        rows.append(dict(role='before' if index==0 else 'after',read_passes=reader.read_passes,
            actual_bytes_read=reader.bytes_read,recorded_complete_boundary=index<len(frame.boundaries),
            paced_bytes=p.bytes_paced,requested_sleep_seconds=p.requested_sleep_seconds,
            reservations=getattr(p,'reservations',None),reserved_bytes=getattr(p,'reserved_bytes',None),
            refunded_bytes=getattr(p,'refunded_bytes',None),pending_request=getattr(p,'pending',None) is not None,
            pacer_failed=getattr(p,'failed',None),
            completed_semantic_decodes=sum(getattr(reader,'semantic_decode_counts',{}).values())))
    return dict(declared_input_count=len(frame.inputs),declared_input_bytes=sum(pin['bytes'] for pin in frame.inputs.values()),
        recorded_complete_boundaries=len(frame.boundaries),readers=rows,diagnostic_only=True,
        actual_whole_Native_or_product_qualified=False,extra_guard_sampler_native_query_or_IO=False)


def timing_summary(observation):
    require(type(observation) is dict and type(observation['roles']) is dict,'TIMING_OBSERVATION_OBJECT')
    roles={}
    for role,timing in observation['roles'].items():
        require(role in ('metadata','frame') and type(timing) is dict and type(timing['rows']) is list
            and len(timing['rows'])<=649,'BOUNDED_ORIGINAL_ROLE_ROWS')
        roles[role]=dict((key,value) for key,value in timing.items() if key!='rows')
        roles[role]['recorded_row_count']=len(timing['rows'])
    return dict(observation,roles=roles)


class Driver:
    def __init__(self,attempt,*,construct_only=False):
        require(type(attempt) is int and attempt in (1,2,3,4,5,6,7,8) and type(construct_only) is bool,'CLOSED_READONLY_ATTEMPT')
        self.exact_read=attempt in (5,6,7,8);self.exact_factory=None
        self.observe_decoder=attempt in (6,7,8);self.decoder_timing=None
        self.chunk_join=attempt in (7,8);self.chunk_link=None
        self.metadata_tail=attempt==8;self.metadata_tail_link=None
        self.attempt=attempt;self.construct_only=construct_only;self.guard=None;self.records=[];self.closed=False
        self.stage=None;self.native=None;self.last_samples=[];self.bound=False;self.case_context=None;self.started=None
        kind='construct' if construct_only else 'probe'
        self.output=f'implementation/p09/evidence/p09-361-native011-current805-readonly-frame-{kind}{attempt:03}.v1.json'
        self.result={};self.writer_started=False;self.owner=(os.getpid(),threading.get_ident())
    def exact_evidence(self,frame):
        state=self.exact_factory.state
        require(state.attempts==state.completed==2 and not state.failed and len(state.proofs)==2,
            'EXACT_TWO_ORIGINAL_FACTORY_CALLS_COMPLETED')
        sizes={name:pin['bytes'] for name,pin in frame.inputs.items()};rows=[]
        require(len(frame.readers)==2,'EXACT_TWO_REAL_READER_OBJECTS')
        for reader in frame.readers:
            p=reader.pacer
            require(dict(reader._exact_input_sizes)==sizes and reader.read_passes==len(sizes)
                and reader.bytes_read==p.bytes_paced==sum(sizes.values()) and p.pending is p.request is None
                and not p.failed and p.reserved_bytes-p.refunded_bytes==p.bytes_paced
                and p.reservations>=2*len(sizes) and p.refunded_bytes>=len(sizes) and 0<=p.tokens<=65536,
                'COMPLETE_EXACT_BYTES_REAL_EOF_AND_RESERVATION_ACCOUNTING')
            rows.append(dict(read_passes=reader.read_passes,bytes_read=reader.bytes_read,
                bytes_paced=p.bytes_paced,reservations=p.reservations,reserved_bytes=p.reserved_bytes,
                refunded_bytes=p.refunded_bytes,requested_sleep_seconds=p.requested_sleep_seconds,
                pending_request=False,failed=p.failed,actual_declared_scope_count=len(sizes)))
        return dict(attempts=state.attempts,completed=state.completed,failed=state.failed,
            original_factory_and_workspace_retained=True,readers=rows,
            product_or_worker_executed=False)
    def bind(self,root,a,c,guards,loader,control):
        require(not self.bound,'ONE_PRIVATE_DRIVER_BINDING')
        self.root=root;self.a=a;self.c=c;self.guards=guards;self.loader=loader;self.control=control;self.bound=True
    def codec_evidence(self,frame):
        link=self.chunk_link;projection=frame.explicit_projection
        require(type(projection) is link.projection_type
            and projection.decode_fresh.__func__ is link.metadata_projection.decode_fresh.__func__ is link.method,
            'ACTUAL_FRAME_AND_METADATA_USE_SAME_PRIVATE_CODEC_DEPENDENCY')
        return dict(actual_Frame_and_metadata_projection_class_same=True,actual_original_projection_method_code_same=True,
            candidate_codec_namespace_used_by_both=True,installed_in_product=False,actual_Native_or_product_qualified=False)
    def metadata_evidence(self,owner):
        require(self.metadata_tail_link is not None and len(owner.metadata_connection.readers)==1,'ONE_REAL_METADATA_READER')
        reader=owner.metadata_connection.readers[0];p=reader.pacer
        require(isinstance(reader,self.metadata_tail_link.selected_reader)
            and dict(reader._exact_input_sizes)=={name:pin['bytes'] for name,pin in owner.whole.items()}
            and reader.final_fresh_hashes==len(reader.snapshots)>0
            and reader.bytes_read==p.bytes_paced==p.reserved_bytes-p.refunded_bytes
            and p.pending is p.request is None and not p.failed and reader.open_pacer.requests==reader.read_passes,
            'ACTUAL_COMPLETE_METADATA_CLOSING_BYTES_AND_ALL_ORIGINAL_OPEN_REQUESTS')
        return dict(fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
            physical_read_passes=reader.read_passes,physical_bytes_read=reader.bytes_read,bytes_paced=p.bytes_paced,
            query_requests=reader.open_pacer.requests,reservations=p.reservations,reserved_bytes=p.reserved_bytes,
            refunded_bytes=p.refunded_bytes,pending_request=False,failed=p.failed,
            actual_declared_whole_inputs=len(owner.whole),actual_factory_selected_reader=True,
            original_metadata_binary2p5_other4_MiB_policy_retained=True,original_open20_policy_retained=True,
            hash_JSON_source_or_closing_cache=False,actual_Native_or_product_qualified=False)
    def factory(self,stage):
        final=self.guards.distinct_final_sample_guard_v1.guard_type(self.a.Guard)
        if stage!='native':
            final=self.guards.preparation_attributed_cpu_v1.guard_type(final,role='whole_metadata_preflight')
        return self.guards.owned_cpu_baseline_v1.guard_type(final)()
    def _marker(self,index):print('P146_STAGE:'+MARKERS[index],file=__import__('sys').stderr,flush=True)
    def acquire(self):
        require(self.bound and self.guard is None and not self.records,'ONE_CONSTRUCTION_ADMISSION')
        self.stage='construction';self.started=time.monotonic();self.guard=self.factory(self.stage)
        self.guard.acquire();self._marker(0)
    def check(self,*args,**kwargs):
        require(not self.closed and self.guard is not None and (os.getpid(),threading.get_ident())==self.owner,
            'LIVE_ORIGINAL_STAGE_GUARD')
        return self.guard.check(*args,**kwargs)
    @property
    def samples(self):return self.last_samples if self.guard is None else self.guard.samples
    @property
    def cleanup(self):return bool(self.records) and all(r['cleanup_confirmed'] for r in self.records)
    def _release(self):
        if self.guard is None:return
        guard=self.guard;self.last_samples=guard.samples;self.guard=None
        try:guard.close()
        finally:
            self.records.append(dict(stage=self.stage,elapsed_seconds=time.monotonic()-self.started,
                cleanup_confirmed=guard.cleanup,resource_samples=len(guard.samples),
                system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),
                guard_kind='original_Native_no_preparation_relaxation' if self.stage=='native' else 'approved_preparation'))
        require(guard.cleanup,'STAGE_MUTEX_RELEASED')
    def advance(self,stage):
        require(self.native is None and not self.closed and (os.getpid(),threading.get_ident())==self.owner,
            'NO_ROTATION_AFTER_NATIVE_FRAME_PHASE_START')
        require((self.stage,stage) in (('construction','opening'),('opening','native')),'EXACT_READONLY_STAGE_ORDER')
        self.check(force=True);self._release();self.stage=stage;self.started=time.monotonic()
        self.guard=self.factory(stage);self.guard.acquire();self._marker(1 if stage=='opening' else 2)
    def close(self):
        if self.closed:return
        self.closed=True;self._release()
    def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
        require(self.stage=='construction' and not self.result,'ONE_REAL_DRIVER_INVOCATION')
        if self.construct_only:
            return dict(state='PASS_READONLY_FRAME_DRIVER_CONSTRUCTION_ONLY_NOT_EXECUTION',
                readonly_driver_bound=True,actual_Native_Frame_created=False,actual_product_executed=False)
        context=NS(data=data,batch=batch,prepared=prepared,bound=bound,shared=resources,oracle_result=checked,row=row)
        self.case_context=context
        helpers,_=private_load(loader,root,q,a,('native011_metadata_audit','native011_metadata_epochs',
            'native011_readonly_frame_probe','native011_source_coverage','native011_worker_source_inheritance',
            'native011_precise_boundary_pacer'),
            {'runtime_input_frame':a.native.frames,'current_stored_runtime_scope':batch.scope})
        self.components=helpers
        planning,_=entry.planning_libraries(root,q,a,loader)
        optimized=planning.batch_scope_admission.optimized_reader(root,q,checked.known,checked.loader,a.AcceptanceReader,a)
        # Preparation only; no first source verification is reused as a close.
        require(q.final_fresh_hashes==len(q.snapshots),'CONSTRUCTION_CLOSING_BEFORE_NEW_WHOLE_OPENING')
        self.advance('opening');opening=optimized.Reader(root,self.check)
        self.result['whole_opening_pacer']=precise_opening(opening,a.pressure,helpers.native011_precise_boundary_pacer)
        data.planned.batch.begin(opening)
        self.result['whole_opening']=dict(fresh_inputs=opening.read_passes,bytes_read=opening.bytes_read,
            full_pin_sha256=helpers.native011_metadata_audit.digest(opening.snapshots),actual_complete=True)
        publisher.publish(root,self.output.replace('.v1.json','.opening.v1.json'),
            dict(state='COMPLETED_NEW_OPENING_ONLY_NOT_NATIVE_OR_PRODUCT',evidence=self.result['whole_opening']),
            NS(require=require,exact=a.exact))
        self.advance('native');self.native=helpers.native011_readonly_frame_probe.NativePhase()
        native_resources=NS(lock=threading.Lock(),samples=self.samples)
        def metadata_once(check):
            captured=[]
            original=bound.attached.callback
            def observe(reader):
                required,rust=original(reader)
                api=prepared.linked.engine.run_owned.__globals__['native'].load(reader,14,self.c)
                captured.append((required,api));return required,rust
            attached=NS(**{**vars(bound.attached),'callback':observe})
            observed=NS(**{**vars(context),'bound':NS(**{**vars(bound),'attached':attached})})
            epochs=NS(check=check,validator=helpers.native011_metadata_epochs.idle_context)
            proof=helpers.native011_metadata_audit.metadata(root,epochs,observed,a)
            if self.metadata_tail:self.result['metadata_tail_reader']=self.metadata_evidence(data.planned.batch)
            require(len(captured)==1,'ONE_ORIGINAL_METADATA_CALLBACK_AND_NATIVE_API')
            return NS(required=captured[0][0],api=captured[0][1],proof=proof,
                native_type=a.native.borrowed.locks.Native,pacer_type=a.native.borrowed.locks.OpenPacer)
        def reader_factory(check,api):
            return prepared.linked.engine.run_owned.__globals__['BoundaryReader'](root,check,owner=native_resources,api=api)
        record=a.read_exact(q,self.control.READY)
        required=self.control.declarations(record,batch.scope)
        result=self.native.run(context,root,metadata_once,reader_factory,native_resources,self.check,
            helpers.native011_source_coverage,helpers.native011_worker_source_inheritance,required)
        if self.exact_read:self.result['exact_read_factory']=self.exact_evidence(self.native.frame)
        if self.chunk_join:self.result['chunk_join_actual_Frame']=self.codec_evidence(self.native.frame)
        self.full_frame=result['frame'];self.result.update(result['proof'])
        return dict(state='PASS_READONLY_NATIVE_FRAME_BOUNDARIES_NOT_PRODUCT_OR_BATCH',Frame_instances=1,
            readonly_frame_result=self.result,actual_Native_Frame_created=True,actual_product_executed=False,
            actual_owned_Native_acceptance_qualified=False,parent_attempts=1,
            batch_phase_after_readonly_abort=result['batch_phase_after_readonly_abort'])
    def finish(self,root,row,publisher,a):
        try:self._finish(root,row,publisher,a)
        except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
            value=error.args[0] if error.args else None
            code=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'TERMINAL_EVIDENCE_PUBLICATION_FAILED'
            row['terminal_evidence_publication_error']=code
            if row.get('state','').startswith('PASS_'):
                row.update(state='FAILED_READONLY_FRAME_EVIDENCE_NOT_ACCEPTED',error_code=code)
    def _finish(self,root,row,publisher,a):
        require(self.closed,'ORIGINAL_GUARD_CLOSED_BEFORE_TERMINAL_PUBLICATION')
        row.update(readonly_stage_records=self.records,readonly_driver_bound=True,Native_clock_reset_or_extended=False,
            exact_read_mode=self.exact_read,decoder_timing_mode=self.observe_decoder,chunk_join_mode=self.chunk_join,
            metadata_tail_mode=self.metadata_tail)
        if self.decoder_timing is not None:row['shared_decoder_timing_observation']=self.decoder_timing.evidence()
        if self.construct_only:return
        frame=None if self.native is None else self.native.frame
        if self.native is not None:self.result.update(self.native.proof)
        if 'readonly_frame_result' not in row:row['readonly_frame_result']=self.result
        row['actual_Native_Frame_created']=frame is not None
        if self.case_context is not None:
            row['parent_attempts']=self.case_context.data.planned.batch.parent_connection.state.attempts
        row['Frame_instances']=int(frame is not None)
        row['actual_product_executed']=False;row['actual_owned_Native_acceptance_qualified']=False
        if frame is not None:
            require(frame.state=='CLOSED' and frame.held.closed and not frame.registered,'NO_PUBLICATION_WITH_LIVE_HANDLES')
            row['terminal_actual_reader_counters']=terminal_readers(frame)
            if self.chunk_join:row['terminal_chunk_join_binding']=self.codec_evidence(frame)
            # Original publisher is bounded/exclusive/fsynced for EVERY part.
            # The already-owned external monitor remains active. No fresh child
            # guard, Native operation or retry is introduced after this point.
            self._marker(3);raw=(json.dumps(getattr(self,'full_frame',None) or frame.summary(),
                ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('utf-8')
            parts=[]
            for part in frame_parts(raw):
                name=self.output.replace('.v1.json',f'.frame-part{part["index"]:03}.v1.json')
                parts.append(publisher.publish(root,name,dict(schema_version='hwpx-agent.p09-terminal-frame-part/v1',
                    Native_execution_finished=True,Native_or_product_acceptance_qualified=False,**part),
                    NS(require=require,exact=a.exact)))
            row['full_frame_artifact']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=parts,
                Native_handles_closed_before_output=True,Native_execution_resumed=False)
        elif len(self.records)>=3:self._marker(3)
        if self.decoder_timing is not None:
            observation=row['shared_decoder_timing_observation']
            row['shared_decoder_timing_observation_artifact']=publisher.publish(root,
                self.output.replace('.v1.json','.timing.v1.json'),observation,NS(require=require,exact=a.exact))
            row['shared_decoder_timing_observation']=timing_summary(observation)
