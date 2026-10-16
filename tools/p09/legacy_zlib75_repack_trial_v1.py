"""Repack seven exact already-aliased receipts; no alias policy extension.

Original raw files and old zlib carriers remain. Decode the original carrier,
verify its actual raw source pin, then publish separate XZ and restore it twice.
This physical trial does not install a new Binding or authorize another product.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/legacy_zlib75_repack_trial_v1.py'
TEST='tools/p09/tests/test_legacy_zlib75_repack_trial_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
TRIAL=dict(path=PREFIX+'legacy-history-physical-trial-g001-attempt001.v1.json',bytes=238781,
    sha256='a92f937bbfc518541d4800b88d4e0b6ada4ab7c0e09df9e7c278928040861f6e')
KEYS=((158,3),(158,4),(160,1),(160,2),(160,3),(165,2),(165,3))


def require(ok,label):
    if not ok: raise ValueError('LEGACY_ZLIB75_REPACK_'+label)


def choose(descriptors):
    require(type(descriptors) is list and len(descriptors)==75,'WHOLE_EXISTING75')
    expected=[f'implementation/p09/evidence/p09-361-case{index}-current-runtime-run{run:03}.v1.json' for index,run in KEYS]
    table={}
    for row in descriptors:
        name=row['semantic_original_pin']['path']; require(name not in table,'UNIQUE_EXISTING_ORIGINALS'); table[name]=row
    require(all(name in table for name in expected),'ALL_FIXED_SEVEN_ALREADY_ALIASED')
    return [copy.deepcopy(table[name]) for name in expected]


def destination(original,generation):
    require(type(generation) is int and 1<=generation<=8,'FINITE_GENERATION')
    allowed={f'implementation/p09/evidence/p09-361-case{index}-current-runtime-run{run:03}.v1.json' for index,run in KEYS}
    require(type(original) is dict and original['path'] in allowed,'NO_OTHER_SOURCE_OR_GENERIC_METADATA')
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-zlib75/'+\
        original['path'].rsplit('/',1)[-1][:-5]+f'.xz8m-repack-g{generation:03}.envelope.v1.json'


def main():
    import argparse,importlib.util,io,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('LEGACY_ZLIB75_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import prepared_run_closure_v1 as host
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import legacy_history_physical_trial_v1 as history
    import receipt_xz_envelope_v1 as xz
    import runtime_record_envelope_v2 as old_codec
    import runtime_envelope_physical_io_v1 as physical
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    parser=argparse.ArgumentParser(); parser.add_argument('--generation',type=int,required=True); parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args(); require(type(args.generation) is int and 1<=args.generation<=8 and type(args.attempt) is int and 1<=args.attempt<=8,'FINITE_ATTEMPT')
    output=PREFIX+f'legacy-zlib75-repack-g{args.generation:03}-attempt{args.attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=None; phase='ADMISSION'; records=[]
    row=dict(state='FAILED_LEGACY_ZLIB75_REPACK_NOT_INSTALLED',accepted_count_delta=0,
        Native_or_product_or_GO_executed=False,original_or_old_carrier_overwritten_or_deleted=False,
        current75_descriptor_policy_changed=False,generic_metadata_aliases_installed=False,
        Binding_worker_Frame_or_current_shared_decoder5_qualified=False,generation=args.generation,attempt=args.attempt,automatic_retry=False)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST): q.pin(name)
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.suffix=='.py' and path.is_relative_to(c.ROOT/'tools/p09'): q.pin(path.relative_to(c.ROOT).as_posix())
        previous=a.read_exact(q,TRIAL)
        a.fields(previous,dict(state='PASS_LEGACY86_OPAQUE_PHYSICAL_TRIAL8_NOT_RUNTIME_ALIAS_OR_SHARED_NATIVE_DECODER',
            contracts=dict(run=8,errors=0,failures=0,skipped=0),candidate_count=86,original_bytes=51637460,physical_bytes=8877309,
            bytes_saved=42760151,fresh_inputs=199,final_fresh_hashes=199,cleanup_confirmed=True,generic_metadata_aliases_installed=False),
            'ORIGINAL_INDEPENDENT86_PHYSICAL_PROOF_NOT_RUNTIME_ROLE')
        source_pins={p['path']:p for p in previous['source_pins']}
        a.exact(q.pin(history.SELF),source_pins[history.SELF],'EXACT_REUSED_BYTE_AND_REPORTED_FIELD_HELPER')
        for pin in (history.XZ,history.PHYSICAL): a.exact(q.pin(pin['path']),pin,'EXACT_ORIGINAL_CODECS_AND_PACING')
        manifest=a.read_exact(q,history.MANIFEST); selected=choose(manifest['descriptors'])
        for item in selected: require(not(c.ROOT/destination(item['semantic_original_pin'],args.generation)).exists(),'NO_PREVIOUS_CARRIER_OVERWRITE')
        spec=importlib.util.spec_from_file_location('legacy_zlib75_repack_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests); tests.MODULE=sys.modules[__name__]
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=6,errors=0,failures=0,skipped=0),'REPACK6')
        budget=physical.DecoderBudget(guard.check); phase='OLD_ZLIB_AND_FIRST_NEW_XZ_DECODE'
        for descriptor in selected:
            original,old=descriptor['semantic_original_pin'],descriptor['physical_envelope_pin']
            a.exact(q.pin(original['path']),original,'CURRENT_ORIGINAL_RAW_BYTES_STILL_REQUIRED')
            actual,buffer=q._read(old['path'],parse=True); q._bind(actual['path'],actual); a.exact(actual,old,'EXACT_EXISTING_ZLIB_CARRIER')
            raw=budget.run(lambda check:old_codec.decode(bytes(buffer),check)); del buffer
            history.exact_bytes(raw,original); reported=history.observation(json.loads(raw.decode('utf-8'),object_pairs_hook=xz.unique))
            encoded=xz.encode(raw,guard.check); name=destination(original,args.generation)
            new=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            physical.publish_exclusive(c.ROOT,encoded,new,guard.check); del encoded
            item=dict(original=dict(original),old_physical=dict(old),physical=new,reported_original_fields=reported,
                original_status_promoted=False,current_Binding_installed=False,first_new_decode_complete=False,second_new_decode_complete=False)
            records.append(item)
            actual,buffer=q._read(name,parse=True); q._bind(actual['path'],actual); a.exact(actual,new,'FIRST_NEW_FRESH_PHYSICAL_PIN')
            restored=budget.run(lambda check:xz.decode(bytes(buffer),check)); del buffer
            history.exact_bytes(restored,original); require(restored==raw,'OPAQUE_OLD_AND_NEW_RESTORATION_IDENTICAL'); del restored,raw
            item['first_new_decode_complete']=True
        phase='SECOND_FRESH_NEW_XZ_DECODE'
        for item in records:
            actual,buffer=q._read(item['physical']['path'],parse=True); q._bind(actual['path'],actual); a.exact(actual,item['physical'],'SECOND_NEW_FRESH_PHYSICAL_PIN')
            restored=budget.run(lambda check:xz.decode(bytes(buffer),check)); del buffer
            history.exact_bytes(restored,item['original'])
            a.exact(history.observation(json.loads(restored.decode('utf-8'),object_pairs_hook=xz.unique)),item['reported_original_fields'],'ORIGINAL_FAILURE_NULL_AND_ABSENCE_UNCHANGED')
            del restored; item['second_new_decode_complete']=True
        old_bytes=sum(p['old_physical']['bytes'] for p in records); new_bytes=sum(p['physical']['bytes'] for p in records)
        saved=old_bytes-new_bytes
        require(len(records)==7 and budget.attempts==budget.completed==21 and saved>0,'ALL_SEVEN_OLD_AND_TWO_NEW_PASSES')
        row.update(records=records,old_carrier_bytes=old_bytes,new_carrier_bytes=new_bytes,additional_bytes_saved=saved,
            original_raw_bytes=sum(p['original']['bytes'] for p in records),decoder_budget=budget.evidence(),
            old_codec_actual_decodes=7,new_codec_actual_decodes=14,prior86_physical_trial_pin=TRIAL,
            separate_trials_not_combined_current_metadata_Frame_budget=True,
            total_trial_bytes_saved_with_prior86=previous['bytes_saved']+saved,
            Native_two_read_nominal_other_IO_savings_seconds=(previous['bytes_saved']+saved)/1048576,
            new_roles_sources_proofs_and_actual_current_scope_not_yet_recosted=True)
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_SEVEN_ALREADY_ALIASED_RECEIPTS_REPACK6_NOT_CURRENT_BINDING_OR_NATIVE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
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
    require(guard.cleanup,'REPACK_OWNER_CLEANUP'); publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','old_carrier_bytes','new_carrier_bytes','additional_bytes_saved',
        'decoder_budget','total_trial_bytes_saved_with_prior86','Native_two_read_nominal_other_IO_savings_seconds','fresh_inputs','final_fresh_hashes',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
