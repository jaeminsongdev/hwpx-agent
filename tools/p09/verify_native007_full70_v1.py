"""Fresh complete70 physical corpus qualification, not Native or acceptance.

Keep the fixed prior68 reader, add the distinct failed008 and failed007 readers,
and charge all140 physical decodes to one original five-second DecoderBudget.
No original receipt, descriptor policy, product code or resource cap is edited.
"""
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/verify_native007_full70_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
PUBLICATION=dict(path=PREFIX+'native007-carrier-g001-attempt001.v1.json',bytes=7268,
    sha256='c03c5547826db4d1e3a68fee18afc15c57c77c9fde503fdfef7d60929272217e')
PHYSICAL=dict(path='implementation/p09/evidence/p361-lossless-runtime-inputs/'+
    'case165-runtime-run007.failed.final-source.xz8m-g001.envelope.v1.json',bytes=287658,
    sha256='176d807b620e24f69be9a98fb717ba493b8a3ef77526ac31172d5115dffacb11')


def require(ok,label):
    if not ok:raise ValueError('FULL70_PHYSICAL_'+label)


def main():
    import argparse,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import runtime_envelope_physical_io_v1 as physical
    import receipt_xz_envelope_v1 as xz
    import runtime_record_envelope_v2 as old
    import xz_corpus_delivery_v1 as delivery
    import prepare_native008_carrier_v1 as producer8
    import native008_failure_binding_v1 as failed8
    import prepare_native007_carrier_v1 as producer7
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer7.identifier(parser.parse_args().attempt)
    output=PREFIX+f'native007-full70-physical-attempt{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic();budget=None;counts68={};counts8=[];counts7=[]
    row=dict(state='FAILED_FULL70_PHYSICAL_NOT_ADOPTED',accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,automatic_retry=False,
        original_full69_mapping_or_descriptor_policy_changed=False,
        Native_binding_worker_or_complete_current_scope_qualified=False)
    try:
        guard.acquire();budget=physical.DecoderBudget(guard.check)
        seed=a.AcceptanceReader(c.ROOT,guard.check)
        pub=a.read_exact(seed,PUBLICATION);prior69=a.read_exact(seed,failed8.FULL69)
        a.fields(pub,dict(state='PASS_NATIVE007_LOSSLESS_TWO_FRESH_READS_NOT_FULL70_OR_RUNTIME_BINDING',
            contracts=dict(run=9,errors=0,failures=0,skipped=0),fresh_inputs=28,final_fresh_hashes=28,
            cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
            original_overwritten_or_deleted=False,current_runtime_profile_changed=False), 'EXACT_NEW_CARRIER_PROOF')
        a.exact(pub['original_pin'],producer7.ORIGINAL,'EXACT_FAILED007_ORIGINAL')
        a.exact(pub['published_carrier_pin'],PHYSICAL,'EXACT_FAILED007_CARRIER')
        a.fields(prior69,dict(state='PASS_FULL69_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_NATIVE_BINDING_OR_ACCEPTANCE',
            pair_count=69,decode_count=138,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False),'PRIOR_FULL69')
        a.exact(prior69['new_failed_semantic_pin'],failed8.ORIGINAL,'EXACT_FAILED008_ORIGINAL')
        a.exact(prior69['new_failed_physical_pin'],failed8.PHYSICAL,'EXACT_FAILED008_CARRIER')
        prior68=a.read_exact(seed,prior69['prior_verification_pin'])
        a.fields(prior68,dict(state=delivery.VERIFICATION,pair_count=68,ordinary_pair_count=61,
            preserved_special_count=7,cleanup_confirmed=True),'PRIOR_FULL68')
        manifest=a.read_exact(seed,prior68['publication_manifest_pin']);pairs=manifest['descriptors']
        require(type(pairs) is list and len(pairs)==68 and delivery.digest(pairs)==failed8.TABLE,'ENTIRE_FIXED_PRIOR68')
        originals=[p['semantic_original_pin']['path'] for p in pairs]+[failed8.ORIGINAL['path'],producer7.ORIGINAL['path']]
        carriers=[p['physical_envelope_pin']['path'] for p in pairs]+[failed8.PHYSICAL['path'],PHYSICAL['path']]
        require(len(set(originals))==len(set(carriers))==70 and not set(originals)&set(carriers),'WHOLE70_BIJECTIVE_NO_COLLISION')
        Base=delivery.reader_type(a.AcceptanceReader,pairs,budget,xz,old,counts68,a.exact)
        Prior=producer8.decoder_reader(Base,failed8.PHYSICAL['path'],budget,xz,counts8)
        Reader=producer7.reader_type(Prior,PHYSICAL,budget,xz,counts7)
        q=Reader(c.ROOT,guard.check)
        for pin in seed.snapshots.values():a.exact(q.pin(pin['path']),pin,'REOPEN_ALL_SEED_METADATA')
        for proof in (pub,prior69):
            for pin in proof['source_pins']:
                if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                    a.exact(q.pin(pin['path']),pin,'UNCHANGED_REVIEWED_CODE')
        q.pin(SELF)
        for pair in pairs:a.exact(q.pin(pair['physical_envelope_pin']['path']),pair['physical_envelope_pin'],'FIRST_REAL_PRIOR68_DECODE')
        a.exact(q.pin(failed8.PHYSICAL['path']),failed8.PHYSICAL,'FIRST_REAL_FAILED008_DECODE')
        a.exact(q.pin(PHYSICAL['path']),PHYSICAL,'FIRST_REAL_FAILED007_DECODE')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        require(len(counts68)==68 and all(type(v) is int and v==2 for v in counts68.values())
            and counts8==[failed8.PHYSICAL,failed8.PHYSICAL] and counts7==[PHYSICAL,PHYSICAL]
            and budget.attempts==budget.completed==140,'ALL70_TWO_REAL_DECODES_ONE_BUDGET')
        row.update(state='PASS_FULL70_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_NATIVE_BINDING_OR_ACCEPTANCE',
            prior_verification_pin=failed8.FULL69,publication_pin=PUBLICATION,full68_descriptor_digest=failed8.TABLE,
            new_failed_semantic_pin=producer7.ORIGINAL,new_failed_physical_pin=PHYSICAL,
            pair_count=70,decode_count=140,prior_decode_counts=counts68,
            failed008_decode_count=len(counts8),failed007_decode_count=len(counts7),
            physical_corpus_bytes=sum(p['physical_envelope_pin']['bytes'] for p in pairs)+failed8.PHYSICAL['bytes']+PHYSICAL['bytes'],
            semantic_corpus_bytes=sum(p['semantic_original_pin']['bytes'] for p in pairs)+failed8.ORIGINAL['bytes']+producer7.ORIGINAL['bytes'],
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            every_semantic_original_and_physical_pin_hash_checked=True,
            failed007_execution_true_and_failed008_execution_unknown_preserved=True,
            ordinary_prior_descriptor_policy_unchanged=True,all70_share_original_decoder5_seconds=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            decoder_budget=None if budget is None else budget.evidence(),
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','pair_count','decode_count','physical_corpus_bytes','fresh_inputs',
        'final_fresh_hashes','decoder_budget','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
