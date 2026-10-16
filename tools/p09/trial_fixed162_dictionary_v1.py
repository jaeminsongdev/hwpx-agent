"""Compare four fixed162 representatives, never change a runtime carrier.

Only the encoder's dictionary is reduced in a private function namespace.
Original decoder, all fresh hashes, byte pacing and the shared five seconds
remain unchanged. Measurements are diagnostic, not admission or causality.
"""
import hashlib
import sys
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/trial_fixed162_dictionary_v1.py'
TEST='tools/p09/tests/test_trial_fixed162_dictionary_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
MANIFEST=dict(path=PREFIX+'native009-failure-binding-manifest001.v1.json',bytes=117065,
    sha256='4af8d451da3bd31925423b26754bfa2a0e4eba3848479eb1af1d33ed3880cc89')
PROFILE=dict(path=PREFIX+'fixed162-decoder-profile001.v1.json',bytes=170886,
    sha256='9a4c92483776eb0a504f99c000de326d89317783148b4d7fced1da7d2d201965')
CODEC=dict(path='tools/p09/receipt_xz_envelope_v1.py',bytes=4012,
    sha256='21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09')
PHYSICAL=dict(path='tools/p09/runtime_envelope_physical_io_v1.py',bytes=7214,
    sha256='b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c')


def require(ok,label):
    if not ok: raise ValueError('FIXED162_DICTIONARY_'+label)


def encoder(codec,dictionary):
    require(type(dictionary) is int and dictionary==1024*1024,'EXACT_ONE_MIB_CANDIDATE_ONLY')
    require(type(codec.encode) is FunctionType and codec.DICTIONARY_BYTES==8*1024*1024,'ORIGINAL_EIGHT_MIB_ENCODER')
    env=dict(codec.encode.__globals__,__name__='p09_exact_dictionary_trial',DICTIONARY_BYTES=dictionary)
    fn=FunctionType(codec.encode.__code__,env,codec.encode.__name__,codec.encode.__defaults__,codec.encode.__closure__)
    require(fn.__code__ is codec.encode.__code__ and fn.__closure__ is codec.encode.__closure__,'ORIGINAL_BODY_AND_CLOSURE')
    require(all(env[k] is v for k,v in codec.encode.__globals__.items() if k not in ('__name__','DICTIONARY_BYTES')),'ONLY_PRIVATE_DICTIONARY_CHANGED')
    return fn


def representatives(rows):
    require(type(rows) is list and len(rows)==162,'WHOLE_FIXED162_SELECTION')
    # Include both old hot large receipts and the new post-body failure, not
    # just the smaller historical receipts that are easier to compress.
    indices=[max(range(75),key=lambda i:rows[i]['semantic_original_pin']['bytes']),
        max(range(75,161),key=lambda i:rows[i]['semantic_original_pin']['bytes']),161]
    zlib=[i for i in range(75) if '/legacy-zlib75/' in rows[i]['physical_envelope_pin']['path']]
    require(len(zlib)==7,'SEVEN_SEALED_PRIOR_REPACKS')
    indices.append(max(zlib,key=lambda i:rows[i]['semantic_original_pin']['bytes']))
    require(len(set(indices))==4,'FOUR_DISTINCT_FIXED_REPRESENTATIVES')
    return [(i,rows[i]) for i in indices]


def main():
    import argparse,importlib.util,io,json,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('DICTIONARY_TRIAL_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import prepared_run_closure_v1 as host
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import receipt_xz_envelope_v1 as codec
    import runtime_envelope_physical_io_v1 as physical
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    parser=argparse.ArgumentParser(); parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt; require(type(attempt) is int and 1<=attempt<=8,'FINITE_ATTEMPT')
    output=PREFIX+f'fixed162-dictionary-trial{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_TRIAL_ONLY')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=None; phase='ADMISSION'; records=[]
    row=dict(state='FAILED_DICTIONARY_TRIAL_NOT_ADOPTED',accepted_count_delta=0,
        runtime_carriers_published_or_replaced=0,Native009_replayed=False,GO_authorized=False,
        decoder_or_five_second_limit_changed=False,hashes_or_original_guard_calls_skipped=False,
        dictionary_candidate_bytes=1024*1024,dictionary_original_bytes=8*1024*1024,
        product_Native_worker_Job_Frame_executed=False,measured_performance_is_not_causal_proof=True)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST): q.pin(path)
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.suffix=='.py' and path.is_relative_to(c.ROOT/'tools/p09'): q.pin(path.relative_to(c.ROOT).as_posix())
        for pin in (CODEC,PHYSICAL): a.exact(q.pin(pin['path']),pin,'UNCHANGED_ORIGINAL_DECODER_AND_BUDGET')
        profile=a.read_exact(q,PROFILE)
        a.fields(profile,dict(state='PROFILE_FULL162_COMPLETED_NOT_RUNTIME_QUALIFICATION',all324_completed=True,
            fresh_inputs=239,final_fresh_hashes=239,cleanup_confirmed=True),'MEASURED_ORIGINAL_WHOLE_CORPUS_NOT_ADMISSION')
        manifest=a.read_exact(q,MANIFEST); rows=manifest['descriptors']; selected=representatives(rows)
        candidate=encoder(codec,1024*1024)
        spec=importlib.util.spec_from_file_location('dictionary_trial_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.M=sys.modules[__name__]; tests.CODEC=codec
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=tback.splitlines()[-1].split(':',1)[0]) for t,tback in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=8,errors=0,failures=0,skipped=0),'EIGHT_CONTRACTS')
        budget=physical.DecoderBudget(guard.check)
        phase='FOUR_FRESH_ORIGINALS_AND_CROSSED_8MIB_1MIB_DECODES'
        for ordinal,descriptor in selected:
            old,new=descriptor['semantic_original_pin'],descriptor['physical_envelope_pin']
            pin,buffer=q._read(old['path'],parse=True); q._bind(pin['path'],pin); a.exact(pin,old,'FRESH_WHOLE_ORIGINAL')
            raw=bytes(buffer); del buffer
            pin,buffer=q._read(new['path'],parse=True); q._bind(pin['path'],pin); a.exact(pin,new,'FRESH_CURRENT_EIGHT_MIB_CARRIER')
            old_encoded=bytes(buffer); del buffer
            wall,cpu=time.perf_counter(),time.thread_time(); encoded=candidate(raw,guard.check)
            record=dict(ordinal=ordinal,original_pin=old,old_physical_pin=new,candidate_bytes=len(encoded),
                candidate_sha256=hashlib.sha256(encoded).hexdigest(),
                encoding_wall_seconds=time.perf_counter()-wall,encoding_thread_CPU_seconds=time.thread_time()-cpu,decodes=[])
            for boundary,order in (('before',('old8m','candidate1m')),('after',('candidate1m','old8m'))):
                for variant in order:
                    # Fresh decompressor and complete semantic hash every time;
                    # no decoded-byte cache, changed decoder or time deduction.
                    data=old_encoded if variant=='old8m' else encoded
                    wall,cpu=time.perf_counter(),time.thread_time()
                    restored=budget.run(lambda check:codec.decode(data,check))
                    require(restored==raw and len(restored)==old['bytes'] and hashlib.sha256(restored).hexdigest()==old['sha256'],'ENTIRE_OPAQUE_ORIGINAL_BYTES')
                    record['decodes'].append(dict(boundary=boundary,variant=variant,
                        wall_seconds=time.perf_counter()-wall,thread_CPU_seconds=time.thread_time()-cpu))
                    del restored
            records.append(record); del raw,old_encoded,encoded
        require(budget.attempts==budget.completed==16,'ALL_SIXTEEN_FRESH_DECODES')
        row.update(representative_count=4,records=records,profile_pin=PROFILE,manifest_pin=MANIFEST,
            original_carrier_bytes=sum(r['old_physical_pin']['bytes'] for r in records),
            candidate_carrier_bytes=sum(r['candidate_bytes'] for r in records),
            original_decode_wall_seconds=sum(d['wall_seconds'] for r in records for d in r['decodes'] if d['variant']=='old8m'),
            candidate_decode_wall_seconds=sum(d['wall_seconds'] for r in records for d in r['decodes'] if d['variant']=='candidate1m'))
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_FOUR_DICTIONARY_REPRESENTATIVES8_NOT_WHOLE_CORPUS_OR_RUNTIME',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        if budget is not None: row['decoder_budget']=budget.evidence()
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes)
        row['records']=records; guard.close()
        row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'ORIGINAL_OWNER_CLEANUP'); publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','representative_count',
        'original_carrier_bytes','candidate_carrier_bytes','original_decode_wall_seconds','candidate_decode_wall_seconds',
        'decoder_budget','fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','owned_CPU_machine_max',
        'owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
