"""Two exact historical failed-validation receipts, fresh complete72 corpus.

Opaque bytes only; no product replay, source/executable/fixture transformation,
Native launcher or acceptance. Historical worker/writer creation stays true.
All144 real physical decodes share the original five-second budget.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/legacy_validation_carriers_v1.py'
TEST='tools/p09/tests/test_legacy_validation_carriers_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
RECORDS=[
 dict(key='p159-full249',original=dict(path='implementation/p09/evidence/p09-159-current-graph-full.actual-run01.v1.json',
    bytes=3959557,sha256='70d755fb99fa2ae5f2776d613d52123cdc9fed4e63860e5ed71d593ba6b9784e'),
    schema='hwpx-agent.p09-current-immutable-graph-full249/v1'),
 dict(key='p165-adaptive-full249',original=dict(path='implementation/p09/evidence/p09-165-adaptive-source-xml-full.actual-run01.v1.json',
    bytes=3939320,sha256='cdeb4115b293a61d17948700471c4cc4c137d887e260353c8c4ee73a19c3e9a9'),
    schema='hwpx-agent.p09-adaptive-source-xml-current-full249/v1')]


def require(ok,label):
    if not ok:raise ValueError('LEGACY_VALIDATION_CARRIERS_'+label)


def identifier(value):
    require(type(value) is int and 1<=value<=8,'FINITE_IDENTIFIER');return value


def record(key):
    require(type(key) is str,'EXACT_KEY_TYPE')
    matches=[r for r in RECORDS if r['key']==key];require(len(matches)==1,'TWO_EXACT_LEGACY_RECORDS_ONLY')
    return copy.deepcopy(matches[0])


def destination(key,generation):
    record(key)
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/'+\
        f'legacy-{key}.actual-run01.failed.duration.xz8m-g{identifier(generation):03}.envelope.v1.json'


def exact_original(key,pin,raw):
    expected=record(key)['original']
    require(type(pin) is dict and pin==expected,'EXACT_ORIGINAL_PIN')
    require(type(raw) is bytes and len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest()==expected['sha256'],'ALL_ORIGINAL_BYTES')


def failed_state(key,row):
    expected=dict(schema_version=record(key)['schema'],state='STOPPED_NOT_ACCEPTED',product_complete=False,
        P09_gate='OPEN',native_or_SQL_run=False,cleanup_confirmed=True,worker_created=True,
        job_assigned=True,writer_authorized=True,operation_phase='running',stop_reason='STOP_DURATION_LIMIT')
    require(type(row) is dict and all(type(row.get(k)) is type(v) and row[k]==v for k,v in expected.items()),
        'ORIGINAL_DURATION_FAILURE_WITH_WORKER_AND_WRITER_NOT_PREBODY_OR_PASS')


def reusable_publication(row,generation,attempt):
    require(type(row) is dict and type(row.get('attempt')) is int and 1<=row['attempt']<attempt<=8
        and type(row.get('generation')) is int and row['generation']==generation,'EARLIER_EXACT_GENERATION')
    expected=dict(state='FAILED_LEGACY2_FULL72_PHYSICAL_NOT_ADOPTED',cleanup_confirmed=True,
        product_or_Native_executed=False,GO_authorized=False,accepted_count_delta=0,
        original_overwritten_or_deleted=False,prior70_mapping_or_descriptor_policy_changed=False,
        full72_binding_worker_or_Native_scope_qualified=False,automatic_retry=False)
    require(all(type(row.get(k)) is type(v) and row[k]==v for k,v in expected.items()),'FAILED_CLEANED_PUBLICATION_ONLY_NOT_PASS_REUSE')
    rows=row.get('records');require(type(rows) is list and len(rows)==2,'BOTH_PUBLISHED_RECORDS')
    for value,item in zip(rows,RECORDS):
        require(type(value) is dict and set(value)=={'key','original','physical','source_role','original_failure_promoted','product_child_execution_asserted'}
            and value['key']==item['key'] and value['original']==item['original']
            and value['source_role']=='historical_validation_worker_and_writer_started_duration_stop_not_accepted'
            and value['original_failure_promoted'] is False and value['product_child_execution_asserted'] is False,'EXACT_UNPROMOTED_METADATA')
        pin=value['physical']
        require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and pin['path']==destination(item['key'],generation)
            and type(pin['bytes']) is int and 0<pin['bytes']<=16*1024*1024
            and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None,'BOUNDED_EXACT_PHYSICAL_DECLARATION')
    return copy.deepcopy(rows)


def reader_type(original,pairs,budget,xz,counts):
    require(type(pairs) is list and len(pairs)==2,'EXACT_TWO_PAIRS')
    table={p['physical']['path']:p for p in pairs};require(len(table)==2,'BIJECTIVE_PHYSICAL_PATHS')
    require({p['key'] for p in pairs}=={r['key'] for r in RECORDS},'BOTH_KEYS')
    for p in pairs:require(p['original']==record(p['key'])['original'],'CLOSED_ORIGINAL_TABLE')
    class Reader(original):
        def _read(self,name,parse=False):
            pin,buffer=super()._read(name,parse=parse or name in table)
            if name in table:
                pair=table[name];require(pin==pair['physical'],'FRESH_EXACT_PHYSICAL_PIN')
                raw=budget.run(lambda check:xz.decode(bytes(buffer),check))
                exact_original(pair['key'],pair['original'],raw)
                counts[name]=counts.get(name,0)+1
                if not parse:buffer=None
            return pin,buffer
    return Reader


def main():
    import argparse,importlib.util,io,time,unittest
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
    import native007_failure_binding_v1 as failed7
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--reuse-failed-publication',type=int)
    parser.add_argument('--publication-bytes',type=int);parser.add_argument('--publication-sha256')
    args=parser.parse_args()
    generation=identifier(args.generation);attempt=identifier(args.attempt)
    output=PREFIX+f'legacy2-full72-physical-g{generation:03}-attempt{attempt:03}.v1.json'
    reuse=args.reuse_failed_publication is not None
    require(reuse==(args.publication_bytes is not None)==(args.publication_sha256 is not None),'COMPLETE_EXPLICIT_PUBLICATION_PIN_FLAGS')
    for name in [output]+([] if reuse else [destination(r['key'],generation) for r in RECORDS]):
        path=c.ROOT/name;require(not path.exists() and not path.is_symlink() and not path.is_junction(),'EXCLUSIVE_OUTPUTS')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic()
    budget=None;counts68={};counts8=[];counts7=[];counts2={};published=[]
    row=dict(state='FAILED_LEGACY2_FULL72_PHYSICAL_NOT_ADOPTED',generation=generation,attempt=attempt,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,automatic_retry=False,
        original_overwritten_or_deleted=False,prior70_mapping_or_descriptor_policy_changed=False,
        full72_binding_worker_or_Native_scope_qualified=False)
    try:
        guard.acquire();budget=physical.DecoderBudget(guard.check);seed=a.AcceptanceReader(c.ROOT,guard.check)
        for pin in (producer8.CODEC,producer8.PHYSICAL):a.exact(seed.pin(pin['path']),pin,'UNCHANGED_CODEC_PUBLISHER')
        seed.pin(SELF);seed.pin(TEST)
        prior70=a.read_exact(seed,failed7.FULL70)
        a.fields(prior70,dict(state='PASS_FULL70_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_NATIVE_BINDING_OR_ACCEPTANCE',
            pair_count=70,decode_count=140,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False),'EXACT_FULL70')
        prior69=a.read_exact(seed,prior70['prior_verification_pin'])
        a.exact(prior70['prior_verification_pin'],failed8.FULL69,'UNCHANGED_PRIOR69_PROOF')
        prior68=a.read_exact(seed,prior69['prior_verification_pin'])
        manifest=a.read_exact(seed,prior68['publication_manifest_pin']);pairs68=manifest['descriptors']
        require(type(pairs68) is list and len(pairs68)==68 and delivery.digest(pairs68)==failed8.TABLE,'ENTIRE_FIXED68')
        reused=None
        if reuse:
            previous=identifier(args.reuse_failed_publication)
            old_pin=dict(path=PREFIX+f'legacy2-full72-physical-g{generation:03}-attempt{previous:03}.v1.json',
                bytes=args.publication_bytes,sha256=args.publication_sha256)
            reused=reusable_publication(a.read_exact(seed,old_pin),generation,attempt)
            row['reused_physical_publication_pin']=old_pin
            row['prior_partial_decoder_counts_or_failed_verification_reused']=False
        for index,item in enumerate(RECORDS):
            key=item['key'];pin,buffer=seed._read(item['original']['path'],parse=True);seed._bind(pin['path'],pin)
            raw=bytes(buffer);del buffer;exact_original(key,pin,raw);failed_state(key,json.loads(raw))
            if index==0:
                spec=importlib.util.spec_from_file_location('legacy_carrier_contracts',c.ROOT/TEST)
                tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
                tests.MODULE=sys.modules[__name__];tests.RAW=raw
                result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
                row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
                row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
                a.exact(row['contracts'],dict(run=10,errors=0,failures=0,skipped=0),'ALL_LEGACY10')
                tests.RAW=None;del tests
            if reused is not None:
                del raw;carrier=reused[index]['physical']
                a.exact(seed.pin(carrier['path']),carrier,'ONLY_EXACT_EXISTING_PUBLICATION_BYTES')
                published.append(copy.deepcopy(reused[index]));continue
            encoded=xz.encode(raw,guard.check);exact_original(key,pin,xz.decode(encoded,guard.check));del raw
            carrier=dict(path=destination(key,generation),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            physical.publish_exclusive(c.ROOT,encoded,carrier,guard.check);del encoded
            published.append(dict(key=key,original=dict(pin),physical=carrier,
                source_role='historical_validation_worker_and_writer_started_duration_stop_not_accepted',
                original_failure_promoted=False,product_child_execution_asserted=False))
        row['records']=published
        Base=delivery.reader_type(a.AcceptanceReader,pairs68,budget,xz,old,counts68,a.exact)
        Prior8=producer8.decoder_reader(Base,failed8.PHYSICAL['path'],budget,xz,counts8)
        Prior7=producer7.reader_type(Prior8,failed7.PHYSICAL,budget,xz,counts7)
        Reader=reader_type(Prior7,published,budget,xz,counts2);q=Reader(c.ROOT,guard.check)
        for pin in seed.snapshots.values():a.exact(q.pin(pin['path']),pin,'REOPEN_SEED_INPUTS')
        for pin in prior70['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'CURRENT_PRIOR_PHYSICAL_PROOF_PROGRAMS')
        physicals=[p['physical_envelope_pin'] for p in pairs68]+[failed8.PHYSICAL,failed7.PHYSICAL]+[p['physical'] for p in published]
        require(len({p['path'] for p in physicals})==72,'ALL72_DISTINCT_PHYSICAL_FILES')
        for pin in physicals:a.exact(q.pin(pin['path']),pin,'FIRST_COMPLETE72_REAL_PHYSICAL_DECODE')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        require(len(counts68)==68 and all(type(v) is int and v==2 for v in counts68.values())
            and counts8==[failed8.PHYSICAL,failed8.PHYSICAL] and counts7==[failed7.PHYSICAL,failed7.PHYSICAL]
            and len(counts2)==2 and all(type(v) is int and v==2 for v in counts2.values())
            and budget.attempts==budget.completed==144,'ALL72_TWO_FRESH_DECODES_SHARED5')
        saved=sum(p['original']['bytes']-p['physical']['bytes'] for p in published)
        row.update(state='PASS_LEGACY2_FULL72_PHYSICAL_NOT_BINDING_WORKER_OR_NATIVE',pair_count=72,decode_count=144,
            prior_verification_pin=failed7.FULL70,full68_descriptor_digest=failed8.TABLE,
            full70_descriptors=pairs68+[dict(schema_version=pairs68[0]['schema_version'],next_case=165,
                semantic_original_pin=o,physical_envelope_pin=p) for o,p in ((failed8.ORIGINAL,failed8.PHYSICAL),(failed7.ORIGINAL,failed7.PHYSICAL))],
            prior_decode_counts=counts68,failed008_decode_count=len(counts8),failed007_decode_count=len(counts7),legacy_decode_counts=counts2,
            physical_corpus_bytes=sum(p['bytes'] for p in physicals),reduced_physical_bytes=saved,
            two_other_byte_pass_nominal_saved_seconds=saved/1048576,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            historical_failures_not_prebody_or_acceptance=True,all72_share_original_decoder5_seconds=True,
            byte_hash_JSON_cache=False)
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
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','records','pair_count','decode_count',
        'physical_corpus_bytes','reduced_physical_bytes','two_other_byte_pass_nominal_saved_seconds','fresh_inputs','final_fresh_hashes',
        'decoder_budget','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
