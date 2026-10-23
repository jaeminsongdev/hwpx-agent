"""Original decoder cost with the actual unopened prepared parent retained.

No whole opening, Native Frame, metadata callback, worker, GO or product.
GC callbacks observe only; GC enablement, thresholds and clocks stay unchanged.
"""
import cProfile
import gc
import hashlib
import math
import pstats
import sys
import time
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_prepared_decoder_profile.py'
TEST='tools/p09/tests/test_native011_prepared_decoder_profile.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-prepared-decoder-profile001.v1.json'
CANDIDATE_OUTPUT='implementation/p09/evidence/p09-361-native011-current805-prepared-decoder-chunk-join002.v1.json'
CANDIDATE=('tools/p09/native011_decoder_chunk_join.py','tools/p09/tests/test_native011_decoder_chunk_join.py')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,label):
    if not ok:raise ValueError('PREPARED_DECODER_PROFILE_'+label)


class GCWindow:
    def __init__(self,budget,*,module=gc,clock=time.perf_counter):
        self.module,self.clock,self.budget=module,clock,budget
        self.previous=tuple(module.callbacks);self.enabled=module.isenabled();self.threshold=module.get_threshold()
        self.events=[];self.pending=None;self.failed=False;self.installed=False;self.closed=False
        self.callback=self.observe
    def observe(self,phase,info):
        # CPython suppresses exceptions from GC callbacks. Preserve a sticky
        # diagnostic failure instead of letting a callback fabricate success.
        try:
            require(phase in ('start','stop') and type(info.get('generation')) is int
                and 0<=info['generation']<=2,'DECLARED_GC_EVENT')
            now=self.clock();require(type(now) in (int,float) and math.isfinite(now),'FINITE_GC_CLOCK')
            if phase=='start':
                require(self.pending is None,'ONE_GC_EVENT')
                self.pending=(now,info['generation'],self.budget.active is not None)
            else:
                require(self.pending is not None and len(self.events)<1024,'BOUNDED_PAIRED_GC_EVENT')
                started,generation,inside=self.pending
                require(info['generation']==generation and now>=started,'MATCHED_MONOTONIC_GC_EVENT')
                self.events.append(dict(generation=generation,seconds=now-started,inside_original_decoder_budget=inside))
                self.pending=None
        except BaseException:self.failed=True
    def open(self):
        require(not self.installed and not self.closed,'ONE_GC_OBSERVATION_WINDOW')
        self.module.callbacks.append(self.callback);self.installed=True
    def close(self):
        if self.closed:return
        if self.installed:
            matches=[i for i,callback in enumerate(self.module.callbacks) if callback is self.callback]
            if len(matches)==1:del self.module.callbacks[matches[0]]
            else:self.failed=True
        current=tuple(self.module.callbacks)
        self.restored=len(current)==len(self.previous) and all(a is b for a,b in zip(current,self.previous))
        self.unchanged=self.module.isenabled()==self.enabled and self.module.get_threshold()==self.threshold
        self.failed|=not self.restored or not self.unchanged or self.pending is not None
        self.closed=True
    def evidence(self):
        require(self.closed,'TERMINAL_GC_OBSERVATION_ONLY')
        return dict(failed=self.failed,callbacks_restored=self.restored,enabled_and_thresholds_unchanged=self.unchanged,
            event_count=len(self.events),inside_decoder_seconds=sum(e['seconds'] for e in self.events if e['inside_original_decoder_budget']),
            outside_decoder_seconds=sum(e['seconds'] for e in self.events if not e['inside_original_decoder_budget']),
            events=list(self.events),GC_disabled_collected_frozen_or_threshold_changed=False)


def measured_profile(q,a,entry,batch,data,prepared,checkpoint,*,candidate=None):
    graph=prepared.entry.graph;binding=graph.binding
    current=entry.current_logical(data,binding,checkpoint,batch.scope,a.exact)
    projection,_=binding.project(current,checkpoint);descriptors=binding.descriptors()
    require(type(descriptors) is list and len(descriptors)==162,'ORIGINAL162_DESCRIPTOR_DECLARATIONS')
    decode=projection.decode_fresh;codec_proof=None
    if candidate is not None:
        original_decode=decode.__func__
        selected,codec_proof=candidate.api.connect(candidate.original_raw,original_decode.__globals__['codec'])
        fn=FunctionType(original_decode.__code__,dict(original_decode.__globals__,codec=selected),
            argdefs=original_decode.__defaults__,closure=original_decode.__closure__)
        fn.__kwdefaults__=original_decode.__kwdefaults__
        require(fn.__code__ is original_decode.__code__,'ENTIRE_ORIGINAL_PHYSICAL_AND_SEMANTIC_HASH_PROJECTION')
        decode=lambda *args:fn(projection,*args)
    checkpoint_stats=NS(calls=0,wall=0.)
    def counted():
        begin=time.perf_counter()
        try:checkpoint()
        finally:
            checkpoint_stats.calls+=1;checkpoint_stats.wall+=time.perf_counter()-begin
    budget=graph.frames.connection.original.DecoderBudget(counted)
    window=GCWindow(budget);profile=cProfile.Profile();profile_started=False
    count=physical=expanded=0;wall=cpu=0.;original_error=None
    window.open()
    try:
        for descriptor in descriptors:
            pin=descriptor['physical_envelope_pin'];logical=descriptor['semantic_original_pin']['path']
            actual,raw=q._read(pin['path'],parse=True);q._bind(pin['path'],actual)
            a.exact(actual,pin,'EVERY_FRESH_PHYSICAL_PREPARED_PROFILE_INPUT')
            encoded=bytes(raw);started=time.perf_counter();started_cpu=time.process_time()
            profile.enable();profile_started=True
            try:
                decoded=budget.run(lambda check:decode(logical,actual,encoded,check))
            finally:
                profile.disable();wall+=time.perf_counter()-started;cpu+=time.process_time()-started_cpu
            physical+=len(raw);expanded+=len(decoded);count+=1;del decoded,raw,encoded
    except ValueError as error:
        if error.args!=('STOP_AGGREGATE_ENVELOPE_DECODER5',):raise
        original_error=error.args[0]
    finally:
        profile.disable();window.close()
    gc_record=window.evidence();require(not gc_record['failed'],'GC_OBSERVATION_RESTORATION')
    metrics=[]
    if profile_started:
        for (file,line,name),(primitive,calls,self_time,total_time,callers) in pstats.Stats(profile).stats.items():
            metrics.append(dict(file=file.replace('\\','/').rsplit('/',1)[-1],line=line,name=name,
                calls=calls,self_seconds=self_time,cumulative_seconds=total_time))
    metrics.sort(key=lambda row:row['cumulative_seconds'],reverse=True)
    self_metrics=sorted(metrics,key=lambda row:row['self_seconds'],reverse=True)
    return dict(completed_decodes=count,physical_bytes=physical,expanded_bytes=expanded,decoder=budget.evidence(),
        original_decoder_error=original_error,observed_wall_seconds=wall,observed_CPU_seconds=cpu,
        original_checkpoint_calls=checkpoint_stats.calls,checkpoint_wall_seconds=checkpoint_stats.wall,
        GC_observation=gc_record,top_cumulative=metrics[:24],top_self=self_metrics[:24],
        codec_variant='original' if candidate is None else 'chunk_join',codec_connection_proof=codec_proof,
        profiler_overhead_included=True,actual_prepared_parent_retained=True,
        metadata_or_whole_opening_or_Frame_or_worker_or_product_executed=False,
        combined_metadata_Frame5_or_Native_qualified=False)


def driver_type(base,*,chunk_join=False):
    require(type(chunk_join) is bool,'EXPLICIT_CLOSED_CODEC_PROFILE_VARIANT')
    class Driver(base):
        def __init__(self):
            super().__init__(6,construct_only=True)
            self.output=CANDIDATE_OUTPUT if chunk_join else OUTPUT;self.component=None
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control)
            previous=control.admit;state=NS(calls=0)
            def declared(q,a,scope,**options):
                require(state.calls==0 and options==dict(exact_read=True,decoder_timing=True,chunk_join=False),
                    'ONE_EXPLICIT_CONSTRUCTION_ONLY_DECLARATION')
                declaration=previous(q,a,scope,**options);state.calls+=1
                additions=(SELF,TEST)+CANDIDATE if chunk_join else (SELF,TEST)
                require(len(declaration.control_names)==31 and not set(additions)&set(declaration.control_names),
                    'TWO_NAMED_PROFILE_SOURCES_NOT_OBSERVED_NATIVE_UNION')
                return NS(**{**vars(declaration),'control_names':declaration.control_names+additions})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            result=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            require(result['actual_Native_Frame_created'] is False and self.stage=='construction'
                and self.native is None and data.planned.batch.phase=='NEW','ACTUAL_UNOPENED_PREPARED_PARENT')
            # The constructor reader is already freshly closed. Never reset
            # its counters or reuse it for new inputs after that closing.
            component_reader=a.AcceptanceReader(root,self.check)
            candidate=None
            if chunk_join:
                def fresh_source(name):
                    actual,raw=component_reader._read(name,parse=True);component_reader._bind(name,actual)
                    a.exact(actual,dict(data.planned.current[name]),'FRESH_COMPLETE_PROFILE_CODEC_SOURCE');return bytes(raw)
                namespace=dict(__name__='p09_profile_private_chunk_codec',__file__=CANDIDATE[0])
                exec(compile(fresh_source(CANDIDATE[0]),CANDIDATE[0],'exec'),namespace)
                api=NS(**namespace);component_reader.pin(CANDIDATE[1])
                original_raw=fresh_source(api.SOURCE['path'])
                a.exact(component_reader.snapshots[api.SOURCE['path']],api.SOURCE,'EXACT_ORIGINAL_CANDIDATE_CODEC_SOURCE')
                candidate=NS(api=api,original_raw=original_raw)
            self.component=measured_profile(component_reader,a,entry,batch,data,prepared,self.check,candidate=candidate)
            component_reader.finish();self.check(force=True)
            require(component_reader.final_fresh_hashes==len(component_reader.snapshots),
                'SEPARATE_COMPONENT_READER_COMPLETE_FRESH_CLOSING')
            self.component['actual_component_reader']=dict(fresh_inputs=len(component_reader.snapshots),
                final_fresh_hashes=component_reader.final_fresh_hashes,physical_read_passes=component_reader.read_passes,
                physical_bytes_read=component_reader.bytes_read,source_pins=list(component_reader.snapshots.values()),
                constructor_reader_reused_or_counters_reset=False)
            state=('PASS_PREPARED_HEAP_ORIGINAL_DECODER_PROFILE_NOT_NATIVE_OR_PRODUCT'
                if self.component['original_decoder_error'] is None else
                'RECORDED_ORIGINAL_DECODER_STOP_IN_PREPARED_PROFILE_NOT_QUALIFIED')
            return dict(result,state=state,prepared_decoder_profile=self.component)

    return Driver


def main():
    require(sys.argv[1:] in ([],['--chunk-join']),'CLOSED_NO_PRODUCT_NO_GO_ENTRY')
    chunk_join=bool(sys.argv[1:])
    root=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
    require(not(root/(CANDIDATE_OUTPUT if chunk_join else OUTPUT)).exists(),'EXCLUSIVE_NEW_PROFILE_RECEIPT')
    def fresh(name,limit):
        path=root/name
        for parent in (path,*path.parents):
            require(not parent.is_symlink() and not parent.is_junction(),'DIRECT_SOURCE_ANCESTORS')
            if parent==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_SOURCE_READ');return raw
    raw=fresh(LOADER['path'],LOADER['bytes'])
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_prepared_profile_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    pins=[]
    for name in ('tools/p09/native011_readonly_frame_driver.py','tools/p09/native011_ready_native_construction.py'):
        raw=fresh(name,65536);pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=NS(**env).load(root,pins,{})
    before=sys.argv;sys.argv=[before[0]]
    try:return libs.native011_ready_native_construction.main(driver=driver_type(
        libs.native011_readonly_frame_driver.Driver,chunk_join=chunk_join)())
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
