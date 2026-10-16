"""Two fixed P149 stopped-validation carriers plus complete75 physical checks.

Preserve different stop reasons, unknown child execution and every original
byte. Reuse unchanged73 reader/codec layers; all150 fresh decodes share the
original5-second budget. No Binding, worker, Native or product authorization.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/legacy149_full75_carriers_v1.py'
TEST='tools/p09/tests/test_legacy149_full75_carriers_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
FULL73=dict(path=PREFIX+'legacy154-full73-physical-g001-attempt001.v1.json',bytes=94286,
    sha256='c24cea0dd8baf0e71158550df29e237cc3a4be0706858c0318bff4865191e805')
MANIFEST=dict(path=PREFIX+'successor-native009-full73-manifest001.v1.json',bytes=54021,
    sha256='5f10883d89c5e3d7b44e345e16ac5100bef46a57dc45709400cff1181e646ee5')
OLD=dict(path='tools/p09/legacy154_full73_carrier_v1.py',bytes=17579,
    sha256='c141083b7b08702f3243d2a25ba12edf31e9a194b8e7a1b485099e833d3b68eb')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
ROLE='historical_validation_worker_writer_started_stopped_not_accepted_product_execution_unknown'
RECORDS=[
 dict(key='run01',stop_reason='OWNED_RUNNER_FAILURE',failure_tag='runner',original=dict(
    path='implementation/p09/evidence/p09-149-compression-full-stored.actual-run01.v1.json',bytes=3607741,
    sha256='677ef24e932a3f48690a6b4818e41f2753b977206b904f649fa22df3b89fd774')),
 dict(key='run02',stop_reason='STOP_LOW_AVAILABLE_RAM',failure_tag='ram',original=dict(
    path='implementation/p09/evidence/p09-149-compression-full-stored.actual-run02.v1.json',bytes=3322888,
    sha256='103c85ed2b7bad5885c37e7cc22f8f55ba46c4a2c6435b4f8110e34687940557'))]


def require(ok,label):
    if not ok:raise ValueError('LEGACY149_CARRIER_'+label)


def identifier(value):
    require(type(value) is int and 1<=value<=8,'FINITE_IDENTIFIER');return value


def original(key):
    found=[record for record in RECORDS if record['key']==key]
    require(type(key) is str and len(found)==1,'TWO_EXACT_FIXED_KEYS');return found[0]


def destination(key,generation):
    spec=original(key)
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/'+\
        f'legacy-p149-compression-full-stored.actual-{key}.failed.{spec["failure_tag"]}.xz8m-g{identifier(generation):03}.envelope.v1.json'


def exact_original(key,pin,raw):
    expected=original(key)['original']
    require(type(pin) is dict and pin==expected,'EXACT_FIXED_ORIGINAL_PIN')
    require(type(raw) is bytes and len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest()==expected['sha256'],'ALL_ORIGINAL_BYTES')


def failure(key,row):
    expected=dict(schema_version='hwpx-agent.p09-conservative-maintenance/v1',state='STOPPED_NOT_ACCEPTED',
        stop_reason=original(key)['stop_reason'],operation_phase='running',worker_created=True,job_assigned=True,
        writer_authorized=True,heavy_work_started=True,product_complete=False,cleanup_confirmed=True,
        owned_tree_empty=True,native_or_SQL_run=False,P09_gate='OPEN')
    require(type(row) is dict and all(type(row.get(n)) is type(value) and row[n]==value for n,value in expected.items()),
        'EXACT_DISTINCT_POST_WRITER_FAILURE_NOT_PREBODY_OR_PASS')
    require(row.get('actual_product_child_executed') is None and row.get('product_body_observed') is None,
        'UNKNOWN_EXECUTION_NOT_FALSE_OR_TRUE')
    return dict(expected,actual_product_child_executed=None,product_body_observed=None,
        original_product_execution_field_present='actual_product_child_executed' in row,
        original_product_body_field_present='product_body_observed' in row)


def physical_pin(key,pin):
    original(key)
    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'}
        and type(pin['path']) is str and pin['path'] in {destination(key,n) for n in range(1,9)}
        and type(pin['bytes']) is int and 0<pin['bytes']<=16*1024*1024
        and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None,'ONE_EXPLICIT_PHYSICAL_PIN')


def reusable(row,generation,attempt):
    require(type(row) is dict and type(row.get('generation')) is int and row['generation']==generation
        and type(row.get('attempt')) is int and 1<=row['attempt']<attempt<=8,'EXACT_EARLIER_GENERATION')
    expected=dict(state='FAILED_LEGACY149_FULL75_PHYSICAL_NOT_ADOPTED',cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        original_overwritten_or_deleted=False,full75_binding_worker_or_Native_qualified=False)
    require(all(type(row.get(n)) is type(value) and row[n]==value for n,value in expected.items()),'FAILED_CLEANED_PUBLICATION_ONLY')
    records=row.get('records');require(type(records) is list and len(records)==2,'BOTH_FIXED_RECORDS')
    for spec,record in zip(RECORDS,records):
        require(type(record) is dict and record.get('key')==spec['key'] and record.get('original')==spec['original']
            and record.get('source_role')==ROLE and record.get('original_stop_reason')==spec['stop_reason']
            and record.get('original_failure_promoted') is False and record.get('actual_failed_product_child_executed') is None,
            'EXACT_UNPROMOTED_UNKNOWN_EXECUTION_ROLES')
        physical_pin(spec['key'],record['physical'])
        require(record['physical']['path']==destination(spec['key'],generation),'SAME_PHYSICAL_GENERATION')
    return copy.deepcopy(records)


def reader_type(base,records,budget,xz,counts):
    require(type(records) is list and len(records)==2,'TWO_FIXED_READER_RECORDS')
    selected={}
    for spec,record in zip(RECORDS,records):
        require(record['key']==spec['key'] and record['original']==spec['original'],'EXACT_READER_PAIR')
        physical_pin(spec['key'],record['physical']);selected[record['physical']['path']]=record
    require(len(selected)==2,'DISTINCT_PHYSICAL_PATHS')
    class Reader(base):
        def _read(self,name,parse=False):
            pin,buffer=super()._read(name,parse=parse or name in selected)
            if name in selected:
                record=selected[name];require(pin==record['physical'],'ACTUAL_FRESH_PHYSICAL_PIN')
                raw=budget.run(lambda check:xz.decode(bytes(buffer),check))
                exact_original(record['key'],record['original'],raw)
                counts[name]=counts.get(name,0)+1
                if not parse:buffer=None
            return pin,buffer
    return Reader


def prior_legacy_pairs(specifications,prior72,exact):
    require(type(specifications) is list and len(specifications)==2 and type(prior72) is list and len(prior72)==72,
        'COMPLETE_PRIOR_TWO_ROLE_INTERFACE')
    pairs=[]
    for spec,descriptor in zip(specifications,prior72[70:72]):
        exact(descriptor['semantic_original_pin'],spec['original'],'UNCHANGED_PRIOR_KEY_AND_ORIGINAL_ROLE')
        pairs.append(dict(key=spec['key'],original=descriptor['semantic_original_pin'],physical=descriptor['physical_envelope_pin']))
    return pairs


def main():
    import argparse,importlib.util,io,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('CARRIER_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    selected={'prepared_run_closure_v1','terminal_metadata_pressure_v1','distinct_final_sample_guard_v1',
        'owned_cpu_baseline_v1','ast_clone_namespace_v1','ast_copy_namespace_connection_v1',
        'receipt_xz_envelope_v1','successor_preparation_workspace_v1'}
    initial=[pin for pin in bootstrap.native009_full72_construction_v1.PINS if pin['path'].rsplit('/',1)[-1][:-3] in selected]
    require(len(initial)==8,'CLOSED_BOOTSTRAP8')
    libs,_=envelope.namespace_bundle.load(c.ROOT,initial,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    old_namespace,_=loader.load(c.ROOT,[OLD],{});old=old_namespace.legacy154_full73_carrier_v1
    components,_=loader.load(c.ROOT,old.PINS,{'current_stored_runtime_scope':scope,'owned_source_read_pressure':bytes_policy})
    physical=components.runtime_envelope_physical_io_v1;xz=libs.receipt_xz_envelope_v1
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,required=True);parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--reuse-publication-attempt',type=int);parser.add_argument('--publication-bytes',type=int);parser.add_argument('--publication-sha256')
    args=parser.parse_args();generation=identifier(args.generation);attempt=identifier(args.attempt)
    reuse=args.reuse_publication_attempt is not None
    require(reuse==(args.publication_bytes is not None)==(args.publication_sha256 is not None),'EXPLICIT_ALL_REUSE_PIN_ARGUMENTS')
    output=PREFIX+f'legacy149-full75-physical-g{generation:03}-attempt{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    if not reuse:
        for spec in RECORDS:require(not(c.ROOT/destination(spec['key'],generation)).exists(),'EXCLUSIVE_CARRIERS')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='ADMISSION';budget=None;counts68={};counts8=[];counts7=[];counts2={};counts154=[];counts149={}
    row=dict(state='FAILED_LEGACY149_FULL75_PHYSICAL_NOT_ADOPTED',generation=generation,attempt=attempt,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,original_overwritten_or_deleted=False,
        prior73_mapping_or_descriptor_policy_changed=False,full75_binding_worker_or_Native_qualified=False,
        original_failure_promoted=False,automatic_retry=False)
    try:
        guard.acquire();seed=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST):seed.pin(name)
        for pin in [CONSTRUCTION,OLD]+initial+old.PINS:a.exact(seed.pin(pin['path']),pin,'UNCHANGED_OLD73_READERS_CODECS_AND_GUARDS')
        prior=a.read_exact(seed,FULL73)
        a.fields(prior,dict(state='PASS_LEGACY154_COMPLETE73_PHYSICAL10_NOT_BINDING_WORKER_OR_NATIVE',
            pair_count=73,decode_count=146,fresh_inputs=175,final_fresh_hashes=175,cleanup_confirmed=True,
            accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),'EXACT_COMPLETE73_PROOF')
        manifest=a.read_exact(seed,MANIFEST);prior73=manifest['descriptors'];prior72=prior['full72_descriptors']
        expected=prior72+[dict(schema_version=prior72[0]['schema_version'],next_case=165,
            semantic_original_pin=prior['record']['original'],physical_envelope_pin=prior['record']['physical'])]
        a.exact(prior73,expected,'ENTIRE_UNCHANGED73_TABLE');require(len(prior73)==73,'EXACT_PRIOR73_COUNT')
        raw_by_key={};rows_by_key={};encoded_by_key={};records=[]
        phase='BOTH_EXACT_ORIGINAL_FAILURES'
        for spec in RECORDS:
            key=spec['key'];pin,buffer=seed._read(spec['original']['path'],parse=True);seed._bind(pin['path'],pin)
            raw=bytes(buffer);del buffer;exact_original(key,pin,raw);raw_by_key[key]=raw;rows_by_key[key]=json.loads(raw)
        row['original_failure_classifications']={spec['key']:failure(spec['key'],rows_by_key[spec['key']]) for spec in RECORDS}
        if reuse:
            old_pin=dict(path=PREFIX+f'legacy149-full75-physical-g{generation:03}-attempt{identifier(args.reuse_publication_attempt):03}.v1.json',
                bytes=args.publication_bytes,sha256=args.publication_sha256)
            records=reusable(a.read_exact(seed,old_pin),generation,attempt)
            for record in records:a.exact(seed.pin(record['physical']['path']),record['physical'],'FRESH_EXISTING_PHYSICAL_PUBLICATION')
            row.update(reused_failed_publication_pin=old_pin,prior_failed_decoder_counts_or_verification_reused=False)
        else:
            phase='TWO_OPAQUE_LOSSLESS_ENCODINGS'
            for spec in RECORDS:
                key=spec['key'];encoded=xz.encode(raw_by_key[key],guard.check)
                exact_original(key,spec['original'],xz.decode(encoded,guard.check))
                pin=dict(path=destination(key,generation),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
                records.append(dict(key=key,original=dict(spec['original']),physical=pin,source_role=ROLE,
                    original_stop_reason=spec['stop_reason'],original_failure_promoted=False,actual_failed_product_child_executed=None))
                encoded_by_key[key]=encoded
        phase='FIXED_ROLE_AND_READER_CONTRACTS'
        spec=importlib.util.spec_from_file_location('legacy149_carrier_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.RAW=raw_by_key;tests.ROWS=rows_by_key;tests.CHECKPOINT=guard.check
        tests.PRIOR_SPECS=components.legacy_validation_carriers_v1.RECORDS;tests.PRIOR72=prior72;tests.EXACT=a.exact
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=test.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for test,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=13,errors=0,failures=0,skipped=0),'ALL_FIXED_P149_13')
        tests.RAW=tests.ROWS=None;del tests,raw_by_key,rows_by_key
        row['records']=records
        if not reuse:
            for record in records:physical.publish_exclusive(c.ROOT,encoded_by_key[record['key']],record['physical'],guard.check)
        del encoded_by_key
        phase='ALL75_TWO_FRESH_PHYSICAL_BOUNDARIES'
        budget=physical.DecoderBudget(guard.check)
        Base=components.xz_corpus_delivery_v1.reader_type(a.AcceptanceReader,prior72[:68],budget,xz,
            components.runtime_record_envelope_v2,counts68,a.exact)
        Prior8=components.prepare_native008_carrier_v1.decoder_reader(Base,prior72[68]['physical_envelope_pin']['path'],budget,xz,counts8)
        Prior7=components.prepare_native007_carrier_v1.reader_type(Prior8,prior72[69]['physical_envelope_pin'],budget,xz,counts7)
        legacy_pairs=prior_legacy_pairs(components.legacy_validation_carriers_v1.RECORDS,prior72,a.exact)
        Prior72=components.legacy_validation_carriers_v1.reader_type(Prior7,legacy_pairs,budget,xz,counts2)
        Prior73=old.reader_type(Prior72,prior['record']['physical'],budget,xz,counts154)
        Reader=reader_type(Prior73,records,budget,xz,counts149);q=Reader(c.ROOT,guard.check)
        for pin in seed.snapshots.values():a.exact(q.pin(pin['path']),pin,'REOPEN_ALL_CURRENT_SEED_INPUTS')
        for pin in prior['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'CURRENT_WHOLE73_VERIFIER_CODE')
        physicals=[r['physical_envelope_pin'] for r in prior73]+[r['physical'] for r in records]
        require(len(physicals)==len({pin['path'] for pin in physicals})==75,'ALL75_DISTINCT_PHYSICAL_FILES')
        for pin in physicals:a.exact(q.pin(pin['path']),pin,'FIRST_FRESH_FULL75_PHYSICAL_HASH_AND_DECODE')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        phase='FINAL_FRESH_FULL75_PHYSICAL_HASH_AND_DECODE';q.finish();guard.check(force=True)
        require(len(counts68)==68 and all(type(n) is int and n==2 for n in counts68.values())
            and counts8==[prior72[68]['physical_envelope_pin']]*2 and counts7==[prior72[69]['physical_envelope_pin']]*2
            and len(counts2)==2 and all(type(n) is int and n==2 for n in counts2.values())
            and counts154==[prior['record']['physical']]*2 and len(counts149)==2
            and all(type(n) is int and n==2 for n in counts149.values()) and budget.attempts==budget.completed==150,
            'ALL150_CURRENT_DECODES_SHARE_ORIGINAL5')
        require(not denied,'NO_SUBPROCESS_ATTEMPTS')
        reduced=sum(spec['original']['bytes'] for spec in RECORDS)-sum(record['physical']['bytes'] for record in records)
        row.update(state='PASS_LEGACY149_COMPLETE75_PHYSICAL13_NOT_BINDING_WORKER_OR_NATIVE',pair_count=75,decode_count=150,
            prior_verification_pin=FULL73,prior_manifest_pin=MANIFEST,full73_descriptors=prior73,
            prior68_decode_counts=counts68,failed008_decode_count=len(counts8),failed007_decode_count=len(counts7),
            legacy2_decode_counts=counts2,legacy154_decode_count=len(counts154),legacy149_decode_counts=counts149,
            physical_corpus_bytes=sum(pin['bytes'] for pin in physicals),reduced_physical_bytes=reduced,
            two_other_byte_pass_nominal_saved_seconds=reduced/1048576,source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            old73_reader_functions_and_codecs_retained=True,shared_current_decoder5_not_prior_timing_sum=True,
            semantic_input_scope_reduced=False,byte_hash_JSON_cache=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            decoder_budget=None if budget is None else budget.evidence(),CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'OWNER_CLEANUP');libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ('state','contracts','contract_failures','records','pair_count','decode_count','reduced_physical_bytes',
        'two_other_byte_pass_nominal_saved_seconds','fresh_inputs','final_fresh_hashes','decoder_budget','elapsed_seconds','CPU_max',
        'owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
