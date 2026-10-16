"""Measure original fixed162 decoder components, never relax its five seconds.

Only private namespace dependencies are timed. Every original operation still
runs with its original arguments/result/errors; Python's default modules stay
untouched. A stopped profile remains a stopped profile, never qualification.
"""
from contextlib import contextmanager
import sys
import time
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/profile_fixed162_decoder_v1.py'
TEST='tools/p09/tests/test_profile_fixed162_decoder_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
BUILDER=dict(path='tools/p09/qualify_native009_failure_binding_v1.py',bytes=15143,
    sha256='2643f3b0966ed170c74435fa6f69ecaf26547805bbe42fbdce45ee9e35ccf038')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')


def require(ok,label):
    if not ok: raise ValueError('FIXED162_PROFILE_'+label)


class Meter:
    def __init__(self,active): self.active=active; self.stats={}; self.swaps=[]
    def add(self,label,wall,cpu,size=0):
        row=self.stats.setdefault(label,dict(calls=0,wall_seconds=0.0,thread_CPU_seconds=0.0,input_bytes=0))
        row['calls']+=1; row['wall_seconds']+=wall; row['thread_CPU_seconds']+=cpu; row['input_bytes']+=size
    def call(self,label,fn,*args,**kwargs):
        active=self.active()
        if not active: return fn(*args,**kwargs)
        wall,cpu=time.perf_counter(),time.thread_time()
        try: return fn(*args,**kwargs)
        finally:
            size=len(args[0]) if args and type(args[0]) in (bytes,bytearray,str) else 0
            self.add(label,time.perf_counter()-wall,time.thread_time()-cpu,size)
    def wrapper(self,label,fn):
        def call(*args,**kwargs): return self.call(label,fn,*args,**kwargs)
        return call
    def decoder_factory(self,original):
        meter=self
        class Decoder:
            def __init__(self,actual): self.actual=actual
            def __getattr__(self,key): return getattr(self.actual,key)
            def decompress(self,*args,**kwargs): return meter.call('lzma_decompress',self.actual.decompress,*args,**kwargs)
        def make(*args,**kwargs): return Decoder(meter.call('lzma_constructor',original,*args,**kwargs))
        return make
    def restore(self):
        for env,name,old in reversed(self.swaps): env[name]=old
        self.swaps.clear()
    @contextmanager
    def patched(self,functions):
        envs={id(fn.__globals__):fn.__globals__ for fn in functions}
        require(all(e.get('__name__','').startswith('p09_exact_') for e in envs.values()),'PRIVATE_NAMESPACES_ONLY')
        try:
            for env in envs.values():
                for name,operation,label in (('hashlib','sha256','sha256'),('json','loads','json_loads'),('base64','b64decode','base64_decode'),('lzma','LZMADecompressor','lzma_constructor')):
                    old=env.get(name)
                    if old is None or not callable(getattr(old,operation,None)): continue
                    original=getattr(old,operation)
                    call=self.decoder_factory(original) if name=='lzma' else self.wrapper(label,original)
                    env[name]=NS(**{**vars(old),operation:call}); self.swaps.append((env,name,old))
            yield len(envs)
        finally: self.restore()


def decoder_functions(projection,codec):
    pending=[projection.decode_fresh.__func__,codec.decode]; found={}
    while pending:
        fn=pending.pop()
        if type(fn) is not FunctionType or id(fn) in found: continue
        found[id(fn)]=fn
        for cell in fn.__closure__ or ():
            value=cell.cell_contents
            if type(value) is FunctionType: pending.append(value)
            elif type(value) is NS and type(getattr(value,'decode',None)) is FunctionType: pending.append(value.decode)
    return list(found.values())


def main():
    import argparse,importlib.util,io,json,re,traceback,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('FIXED162_PROFILE_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    original,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=original.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,_=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser(); parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt; require(type(attempt) is int and 1<=attempt<=8,'FINITE_PROFILE_ATTEMPT')
    output=PREFIX+f'fixed162-decoder-profile{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_PROFILE')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=meter=None; operations=[]; phase='ADMISSION'; stopped=False
    row=dict(state='FAILED_FIXED162_COMPONENT_PROFILE_NOT_QUALIFICATION',accepted_count_delta=0,
        product_or_Native_or_Job_Frame_executed=False,original_decoder5_changed=False,original_guard_calls_skipped=False,
        default_modules_mutated=False,diagnostic_instrumentation_only=True,Native009_replayed=False)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST): q.pin(path)
        a.exact(q.pin(BUILDER['path']),BUILDER,'FAILED_ATTEMPT_BUILDER_UNCHANGED')
        builder_ns,_=loader.load(c.ROOT,[BUILDER],{}); builder=builder_ns.qualify_native009_failure_binding_v1
        value=builder.build(c,a,q,loader,libs,construction,scope,bytes_policy,envelope)
        failure_path=PREFIX+'native009-failure-binding-code001.v1.json'; failure=q.json(failure_path)
        a.fields(failure,dict(state='FAILED_NATIVE009_FAILURE162_BINDING_NOT_ADOPTED',error_code='STOP_AGGREGATE_ENVELOPE_DECODER5',
            contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True),'PRESERVED_REAL_DECODER_STOP')
        manifest_pin=q.pin(PREFIX+'native009-failure-binding-manifest001.v1.json')
        bound=value.module.Binding(value.proof.rows,manifest_pin,next_case=165)
        required,_=bound.semantic_union(scope.extend(value.prior_scope,q.snapshots),guard.check)
        projection,_=bound.project(required,guard.check)
        spec=importlib.util.spec_from_file_location('fixed162_profile_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests); tests.MODULE=sys.modules[__name__]
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        a.exact(row['contracts'],dict(run=5,errors=0,failures=0,skipped=0),'TRANSPARENT_PROFILE_CONTRACTS5')
        physical=envelope._namespaces.runtime_envelope_physical_io_v1
        meter=Meter(lambda:budget is not None and budget.active is not None)
        def checkpoint(): return meter.call('original_resource_checkpoint',guard.check)
        budget=physical.DecoderBudget(checkpoint)
        functions=decoder_functions(projection,value.module.source.codec)
        row['profiled_decoder_functions']=[dict(file=Path(f.__code__.co_filename).name,function=f.__name__) for f in functions]
        phase='ORIGINAL_TWO_PASS_DECODER_COMPONENT_PROFILE'
        with meter.patched(functions) as count:
            row['private_namespace_count']=count
            for boundary in ('before','after'):
                for ordinal,r in enumerate(value.proof.rows):
                    old,new=r['semantic_original_pin'],r['physical_envelope_pin']
                    pin,buffer=q._read(new['path'],parse=True); q._bind(pin['path'],pin); a.exact(pin,new,'PROFILE_FRESH_PHYSICAL_PIN')
                    wall,cpu=time.perf_counter(),time.thread_time(); status='DECODED'
                    try: decoded=budget.run(lambda check:projection.decode_fresh(old['path'],pin,bytes(buffer),check)); del decoded
                    except ValueError as error:
                        status='STOPPED'; stopped=True
                        if error.args!=('STOP_AGGREGATE_ENVELOPE_DECODER5',): raise
                    finally:
                        operations.append(dict(boundary=boundary,ordinal=ordinal,semantic_path=old['path'],
                            physical_bytes=new['bytes'],restored_bytes=old['bytes'],status=status,
                            wall_seconds=time.perf_counter()-wall,thread_CPU_seconds=time.thread_time()-cpu))
                        del buffer
                    if stopped: break
                if stopped: break
        require(not meter.swaps,'ALL_PRIVATE_DEPENDENCIES_RESTORED')
        row.update(state=('PROFILE_ORIGINAL_DECODER5_STOP_RETAINED_NOT_QUALIFICATION' if stopped else 'PROFILE_FULL162_COMPLETED_NOT_RUNTIME_QUALIFICATION'),
            original_decoder_budget=budget.evidence(),component_timings=meter.stats,operations=operations,
            all324_completed=budget.completed==324,profiling_overhead_not_subtracted_from_original_budget=True,
            extra_native_queries_sampler_or_thread_started=False,source_bodies_or_hash_computations_replaced=False,
            original_guard_calls_replaced_by_pass_through_timer_only=True)
        phase='FINAL_PROFILE_SOURCE_HASHES'; q.finish(); guard.check(force=True)
        row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-7:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        if meter is not None: meter.restore(); row['component_timings']=meter.stats
        if budget is not None: row['original_decoder_budget']=budget.evidence()
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes)
        row['operations']=operations
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'PROFILE_OWNER_CLEANUP'); libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','original_decoder_budget','component_timings','all324_completed',
        'fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min',
        'cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row.get('all324_completed') else 1


if __name__=='__main__': raise SystemExit(main())
