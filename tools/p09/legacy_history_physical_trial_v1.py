"""Lossless physical trial for a fixed Native009 historical evidence corpus.

Never install generic metadata aliases. Select only the exact legacy JSON pins
already required by Native009, preserve their reported fields without filling
missing flags, and verify opaque whole-byte restoration twice. Runtime role
admission, Binding/worker/Frame integration and combined decoder5 stay external.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/legacy_history_physical_trial_v1.py'
TEST='tools/p09/tests/test_legacy_history_physical_trial_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
NATIVE=dict(path=PREFIX+'current-runtime-run009.v1.json',bytes=5046802,
    sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753')
MANIFEST=dict(path=PREFIX+'successor-native009-full75-manifest001.v1.json',bytes=57692,
    sha256='f19fb5603bc416d614d485995fbf71fa06da148b5204fcdc8b03f1511b91d615')
XZ=dict(path='tools/p09/receipt_xz_envelope_v1.py',bytes=4012,
    sha256='21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09')
PHYSICAL=dict(path='tools/p09/runtime_envelope_physical_io_v1.py',bytes=7214,
    sha256='b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c')
PATTERN=r'implementation/p09/evidence/p09-(?:14[0-9]|1[5-8][0-9])-[A-Za-z0-9_.-]+\.json'
FLAGS=('worker_created','job_assigned','writer_authorized','product_complete','product_body_observed',
    'actual_product_child_executed','cleanup_confirmed','owned_tree_empty','native_or_SQL_run','actual_Cargo_SQL_Hangul_run')


def require(ok,label):
    if not ok: raise ValueError('LEGACY_HISTORY_TRIAL_'+label)


def pin(value):
    require(type(value) is dict and set(value)=={'path','bytes','sha256'} and type(value['path']) is str
        and type(value['bytes']) is int and 0<value['bytes']<=16777216 and type(value['sha256']) is str
        and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'EXACT_BOUNDED_PIN')
    return dict(value)


def select(inputs,descriptors):
    require(type(inputs) is list and 0<len(inputs)<=4096 and type(descriptors) is list and len(descriptors)==75,'FIXED_NATIVE_AND_PRIOR75_SHAPE')
    physical={}; logical=set()
    for d in descriptors:
        old,new=pin(d['semantic_original_pin']),pin(d['physical_envelope_pin'])
        require(old['path'] not in logical and new['path'] not in physical,'BIJECTIVE_PRIOR75')
        logical.add(old['path']); physical[new['path']]=new
    seen=set(); result=[]
    for item in inputs:
        p=pin(item); name=p['path']; require(name not in seen,'UNIQUE_WHOLE_NATIVE_PHYSICAL_SCOPE'); seen.add(name)
        if re.fullmatch(PATTERN,name) and p['bytes']>=262144 and name not in logical and name not in physical: result.append(p)
    result.sort(key=lambda p:(-p['bytes'],p['path']))
    require(0<len(result)<=96 and sum(p['bytes'] for p in result)<=64*1024*1024,'BOUNDED_HISTORICAL_CORPUS')
    return result


def observation(row):
    require(type(row) is dict,'RECORD_OBJECT_NOT_SOURCE_REWRITE')
    values={}
    for name in FLAGS:
        present=name in row; value=row.get(name)
        require(not present or value is None or type(value) is bool,'REPORTED_FLAG_BOOL_NULL_OR_ABSENT')
        values[name]=dict(present=present,value=value)
    for name,pattern in (('schema_version',r'hwpx-agent\.[A-Za-z0-9_./-]{1,150}'),
            ('state',r'[A-Z][A-Z0-9_]{0,119}'),('stop_reason',r'[A-Z][A-Z0-9_]{0,119}'),('P09_gate',r'[A-Z][A-Z0-9_]{0,31}')):
        present=name in row; value=row.get(name)
        require(not present or value is None or type(value) is str and re.fullmatch(pattern,value) is not None,'CLOSED_REPORTED_STATE_METADATA')
        values[name]=dict(present=present,value=value)
    return values


def destination(original,generation):
    require(type(generation) is int and 1<=generation<=8 and re.fullmatch(PATTERN,original['path']) is not None,'EXPLICIT_LEGACY_DESTINATION')
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-p140-189/'+\
        original['path'].rsplit('/',1)[-1][:-5]+f'.xz8m-trial-g{generation:03}.envelope.v1.json'


def exact_bytes(raw,expected):
    pin(expected)
    require(type(raw) is bytes and len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest()==expected['sha256'],'ALL_RESTORED_ORIGINAL_BYTES')


def main():
    import argparse,importlib.util,io,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('LEGACY_HISTORY_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import prepared_run_closure_v1 as host
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import receipt_xz_envelope_v1 as xz
    import runtime_envelope_physical_io_v1 as physical
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    parser=argparse.ArgumentParser(); parser.add_argument('--generation',type=int,required=True); parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args(); require(type(args.generation) is int and 1<=args.generation<=8 and type(args.attempt) is int and 1<=args.attempt<=8,'FINITE_GENERATION_AND_ATTEMPT')
    output=PREFIX+f'legacy-history-physical-trial-g{args.generation:03}-attempt{args.attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_TRIAL_RESULT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=None; phase='ADMISSION'; records=[]
    row=dict(state='FAILED_LEGACY_HISTORY_PHYSICAL_TRIAL_NOT_RUNTIME_ALIASES',accepted_count_delta=0,
        Native_or_product_or_GO_executed=False,original_overwritten_or_deleted=False,generic_metadata_aliases_installed=False,
        Binding_worker_Frame_or_runtime_role_admission_qualified=False,combined_current_metadata_Frame_decoder5_qualified=False,
        generation=args.generation,attempt=args.attempt,automatic_retry=False)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST): q.pin(name)
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.suffix=='.py' and path.is_relative_to(c.ROOT/'tools/p09'): q.pin(path.relative_to(c.ROOT).as_posix())
        a.exact(q.pin(XZ['path']),XZ,'EXACT_ORIGINAL_XZ_CODEC'); a.exact(q.pin(PHYSICAL['path']),PHYSICAL,'EXACT_PHYSICAL_WRITER_AND_DECODER_BUDGET')
        native=a.read_exact(q,NATIVE); manifest=a.read_exact(q,MANIFEST)
        a.fields(native,dict(state='STOPPED_NOT_ACCEPTED',stop_reason='FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE',
            cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),'FIXED_NATIVE009_FAILURE_NOT_PROMOTED')
        chosen=select(native['source_freeze'],manifest['descriptors'])
        require(len(chosen)==86 and sum(p['bytes'] for p in chosen)==51637460,'EXACT_NATIVE009_LEGACY86_CORPUS')
        row.update(candidate_count=len(chosen),original_bytes=sum(p['bytes'] for p in chosen),native009_pin=NATIVE,prior75_manifest_pin=MANIFEST,
            candidate_selection_from_entire_fixed_Native_physical_scope=True)
        for original in chosen:
            path=c.ROOT/destination(original,args.generation)
            require(not path.exists() and not path.is_symlink() and not path.is_junction(),'NO_PREVIOUS_OR_PARTIAL_ENVELOPE_OVERWRITE')
        spec=importlib.util.spec_from_file_location('legacy_history_physical_trial_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests); tests.MODULE=sys.modules[__name__]
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=8,errors=0,failures=0,skipped=0),'PHYSICAL_TRIAL8')
        budget=physical.DecoderBudget(guard.check)
        phase='PRESERVE_EACH_ORIGINAL_AND_PUBLISH_FRESH_FIRST_DECODE'
        for original in chosen:
            actual,buffer=q._read(original['path'],parse=True); q._bind(actual['path'],actual)
            a.exact(actual,original,'FRESH_WHOLE_ORIGINAL_FROM_NATIVE009')
            raw=bytes(buffer); del buffer
            reported=observation(json.loads(raw.decode('utf-8'),object_pairs_hook=xz.unique))
            encoded=xz.encode(raw,guard.check); name=destination(original,args.generation)
            encoded_pin=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            physical.publish_exclusive(c.ROOT,encoded,encoded_pin,guard.check); del encoded
            # Preserve a published file even if a later read/decode/guard stops.
            item=dict(original=dict(original),physical=encoded_pin,reported_original_fields=reported,
                current_alias_role_qualified=False,original_status_promoted=False,first_decode_complete=False,second_decode_complete=False)
            records.append(item)
            actual,buffer=q._read(name,parse=True); q._bind(name,actual); a.exact(actual,encoded_pin,'FIRST_FRESH_PHYSICAL_BYTES')
            restored=budget.run(lambda check:xz.decode(bytes(buffer),check)); del buffer
            exact_bytes(restored,original); require(restored==raw,'OPAQUE_BYTE_FOR_BYTE_RESTORATION'); del restored,raw
            item['first_decode_complete']=True
        phase='SECOND_FRESH_PHYSICAL_READ_AND_DECODE'
        for item in records:
            actual,buffer=q._read(item['physical']['path'],parse=True); q._bind(actual['path'],actual)
            a.exact(actual,item['physical'],'SECOND_FRESH_PHYSICAL_PIN')
            restored=budget.run(lambda check:xz.decode(bytes(buffer),check)); del buffer
            exact_bytes(restored,item['original'])
            a.exact(observation(json.loads(restored.decode('utf-8'),object_pairs_hook=xz.unique)),item['reported_original_fields'],'MISSING_NULL_FALSE_AND_FAILURE_ROLES_UNCHANGED')
            del restored; item['second_decode_complete']=True
        physical_bytes=sum(r['physical']['bytes'] for r in records)
        row.update(records=records,physical_bytes=physical_bytes,bytes_saved=row['original_bytes']-physical_bytes,
            decoder_budget=budget.evidence(),expected_decode_count=2*len(records),all_reported_original_fields_preserved=True,
            Native_two_read_nominal_other_IO_savings_seconds=(row['original_bytes']-physical_bytes)/1048576,
            savings_estimate_excludes_new_sources_qualifications_roles_and_full_scope_recost=True)
        require(budget.completed==budget.attempts==172 and len(records)==86 and physical_bytes<row['original_bytes'],'ALL86_OPAQUE_TWO_PASS_RESTORATIONS')
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_LEGACY86_OPAQUE_PHYSICAL_TRIAL8_NOT_RUNTIME_ALIAS_OR_SHARED_NATIVE_DECODER',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_pins=list(q.snapshots.values()))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        row['records']=records
        if budget is not None: row['decoder_budget']=budget.evidence()
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes,
            actual_read_passes=q.read_passes,actual_physical_read_bytes=q.bytes_read)
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
        row['last_original_resource_samples']=[{k:s.get(k) for k in ('time_utc','system_cpu_percent','parent_cpu_machine_percent','available_ram_percent','commit_used_percent','parent_private_mib')} for s in guard.samples[-8:]]
    require(guard.cleanup,'TRIAL_OWNER_CLEANUP')
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','candidate_count','original_bytes','physical_bytes','bytes_saved',
        'decoder_budget','fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min',
        'cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
