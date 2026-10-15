"""Exact P154 duration failure carrier plus fresh complete73 physical checks.

Original bytes, worker/writer creation and unknown product execution survive.
Old complete72 readers and both codecs remain; all146 boundary decodes share
one original5-second budget. No Binding/worker/Native or acceptance adoption.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/legacy154_full73_carrier_v1.py'
TEST='tools/p09/tests/test_legacy154_full73_carrier_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
ORIGINAL=dict(path='implementation/p09/evidence/p09-154-observed-full.actual-run01.v1.json',bytes=3917483,
    sha256='c81b34d53215da2bee70709358963db5f1de5db6fbd17caa629673011c67754a')
FULL72=dict(path=PREFIX+'legacy2-full72-physical-g001-attempt002.v1.json',bytes=92822,
    sha256='476b5a8efdc79d0e629e2c2d35d7ccc79a10eddeeb20a6ab8afbf1d649c69787')
MANIFEST=dict(path=PREFIX+'successor-native009-full72-manifest001.v1.json',bytes=52166,
    sha256='7c8ef123f31954986a9ddec60bda2f247cbaa7efb4a4d530f1e794e2798ffb70')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
PINS=[
 dict(path='tools/p09/runtime_record_envelope_v1.py',bytes=3596,sha256='59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5'),
 dict(path='tools/p09/runtime_record_envelope_v2.py',bytes=2891,sha256='9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f'),
 dict(path='tools/p09/runtime_envelope_source_projection_v1.py',bytes=6401,sha256='728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b'),
 dict(path='tools/p09/runtime_envelope_physical_io_v1.py',bytes=7214,sha256='b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c'),
 dict(path='tools/p09/xz_corpus_delivery_v1.py',bytes=20913,sha256='6602c1afa08140ab7b5f4b1e6b873329f7a00544a17c4d836b2f2ee24258d255'),
 dict(path='tools/p09/prepare_native008_carrier_v1.py',bytes=8895,sha256='a60cf611d93686d176e4ae3988f72f98f44040566b4fa18b4c89a922adfa6a78'),
 dict(path='tools/p09/prepare_native007_carrier_v1.py',bytes=9043,sha256='ef885936084f42ba0c99e84535b22384594949d6d46ac459947ca4c1495fb930'),
 dict(path='tools/p09/legacy_validation_carriers_v1.py',bytes=15701,sha256='9647510cc51b6d93212cb8528ee20bba87f19a46ca0eade01ed4caf649145e75')]
ROLE='historical_validation_worker_writer_started_duration_stop_product_execution_unknown'


def require(ok,label):
    if not ok:raise ValueError('LEGACY154_CARRIER_'+label)


def identifier(value):
    require(type(value) is int and 1<=value<=8,'FINITE_IDENTIFIER');return value


def destination(generation):
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/'+\
        f'legacy-p154-observed-full.actual-run01.failed.duration.xz8m-g{identifier(generation):03}.envelope.v1.json'


def exact_original(pin,raw):
    require(type(pin) is dict and pin==ORIGINAL,'EXACT_FIXED_ORIGINAL_PIN')
    require(type(raw) is bytes and len(raw)==ORIGINAL['bytes'] and hashlib.sha256(raw).hexdigest()==ORIGINAL['sha256'],'ALL_ORIGINAL_BYTES')


def failure(row):
    expected=dict(schema_version='hwpx-agent.p09-observed-current-full249/v1',state='STOPPED_NOT_ACCEPTED',
        stop_reason='STOP_DURATION_LIMIT',operation_phase='running',worker_created=True,job_assigned=True,
        writer_authorized=True,heavy_work_started=True,product_complete=False,cleanup_confirmed=True,
        owned_tree_empty=True,native_or_SQL_run=False,P09_gate='OPEN')
    require(type(row) is dict and all(type(row.get(k)) is type(v) and row[k]==v for k,v in expected.items()),
        'ORIGINAL_POST_WRITER_FAILURE_NOT_PREBODY_OR_PASS')
    require(row.get('actual_product_child_executed') is None and row.get('product_body_observed') is None
        and row.get('passed_test_names',[])==[],'UNKNOWN_PRODUCT_EXECUTION_NOT_FALSE_OR_TRUE')
    return dict(expected,actual_product_child_executed=None,product_body_observed=None,
        original_product_execution_field_present='actual_product_child_executed' in row,
        original_product_body_field_present='product_body_observed' in row)


def physical_pin(pin):
    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'}
        and type(pin['path']) is str and pin['path'] in {destination(n) for n in range(1,9)}
        and type(pin['bytes']) is int and 0<pin['bytes']<=16*1024*1024
        and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None,'ONE_EXPLICIT_PHYSICAL_PIN')


def reusable(row,generation,attempt):
    require(type(row) is dict and type(row.get('generation')) is int and row['generation']==generation
        and type(row.get('attempt')) is int and 1<=row['attempt']<attempt<=8,'EXACT_EARLIER_GENERATION')
    expected=dict(state='FAILED_LEGACY154_FULL73_PHYSICAL_NOT_ADOPTED',cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        original_overwritten_or_deleted=False,full73_binding_worker_or_Native_qualified=False)
    require(all(type(row.get(k)) is type(v) and row[k]==v for k,v in expected.items()),'ONLY_FAILED_CLEANED_PUBLICATION_NOT_PASS')
    record=row.get('record')
    require(type(record) is dict and record.get('original')==ORIGINAL and record.get('source_role')==ROLE
        and record.get('original_failure_promoted') is False and record.get('actual_failed_product_child_executed') is None,
        'EXACT_UNPROMOTED_UNKNOWN_PRODUCT_ROLE')
    physical_pin(record['physical']);require(record['physical']['path']==destination(generation),'SAME_PHYSICAL_GENERATION')
    return copy.deepcopy(record)


def reader_type(original,carrier,budget,xz,counts):
    physical_pin(carrier)
    class Reader(original):
        def _read(self,name,parse=False):
            pin,buffer=super()._read(name,parse=parse or name==carrier['path'])
            if name==carrier['path']:
                require(pin==carrier,'ACTUAL_FRESH_PHYSICAL_PIN')
                raw=budget.run(lambda check:xz.decode(bytes(buffer),check));exact_original(ORIGINAL,raw)
                counts.append(dict(pin))
                if not parse:buffer=None
            return pin,buffer
    return Reader


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
    initial=[p for p in bootstrap.native009_full72_construction_v1.PINS if p['path'].rsplit('/',1)[-1][:-3] in selected]
    require(len(initial)==8,'CLOSED_BOOTSTRAP8')
    libs,_=envelope.namespace_bundle.load(c.ROOT,initial,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    components,_=loader.load(c.ROOT,PINS,{'current_stored_runtime_scope':scope,'owned_source_read_pressure':bytes_policy})
    physical=components.runtime_envelope_physical_io_v1;xz=libs.receipt_xz_envelope_v1
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,required=True);parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--reuse-publication-attempt',type=int);parser.add_argument('--publication-bytes',type=int);parser.add_argument('--publication-sha256')
    args=parser.parse_args();generation=identifier(args.generation);attempt=identifier(args.attempt)
    reuse=args.reuse_publication_attempt is not None
    require(reuse==(args.publication_bytes is not None)==(args.publication_sha256 is not None),'ALL_EXPLICIT_REUSE_PIN_ARGUMENTS')
    output=PREFIX+f'legacy154-full73-physical-g{generation:03}-attempt{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    if not reuse:require(not(c.ROOT/destination(generation)).exists(),'EXCLUSIVE_CARRIER')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='ADMISSION';budget=None;counts68={};counts8=[];counts7=[];counts2={};counts154=[]
    row=dict(state='FAILED_LEGACY154_FULL73_PHYSICAL_NOT_ADOPTED',generation=generation,attempt=attempt,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,original_overwritten_or_deleted=False,
        prior72_mapping_or_descriptor_policy_changed=False,full73_binding_worker_or_Native_qualified=False,
        original_failure_promoted=False,automatic_retry=False)
    try:
        guard.acquire();seed=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST):seed.pin(name)
        for pin in [CONSTRUCTION]+initial+PINS:a.exact(seed.pin(pin['path']),pin,'EXACT_EXISTING_READER_AND_CODEC_SOURCES')
        prior=a.read_exact(seed,FULL72)
        a.fields(prior,dict(state='PASS_LEGACY2_FULL72_PHYSICAL_NOT_BINDING_WORKER_OR_NATIVE',
            pair_count=72,decode_count=144,fresh_inputs=173,final_fresh_hashes=173,cleanup_confirmed=True,
            accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),'ORIGINAL_COMPLETE72_PROOF')
        manifest=a.read_exact(seed,MANIFEST);prior72=manifest['descriptors']
        expected=prior['full70_descriptors']+[dict(schema_version=prior['full70_descriptors'][0]['schema_version'],next_case=165,
            semantic_original_pin=r['original'],physical_envelope_pin=r['physical']) for r in prior['records']]
        a.exact(prior72,expected,'ENTIRE_UNCHANGED72_TABLE')
        require(len(prior72)==72,'EXACT_PRIOR72_COUNT')
        phase='EXACT_ORIGINAL_FAILURE_AND_OPAQUE_CARRIER'
        pin,buffer=seed._read(ORIGINAL['path'],parse=True);seed._bind(pin['path'],pin);raw=bytes(buffer);del buffer
        exact_original(pin,raw);flags=failure(json.loads(raw));row['original_failure_classification']=flags
        if reuse:
            old_attempt=identifier(args.reuse_publication_attempt)
            old_pin=dict(path=PREFIX+f'legacy154-full73-physical-g{generation:03}-attempt{old_attempt:03}.v1.json',
                bytes=args.publication_bytes,sha256=args.publication_sha256)
            record=reusable(a.read_exact(seed,old_pin),generation,attempt);carrier=record['physical'];encoded=None
            row['reused_failed_publication_pin']=old_pin;row['prior_failed_decoder_counts_or_verification_reused']=False
            a.exact(seed.pin(carrier['path']),carrier,'FRESH_EXACT_EXISTING_CARRIER')
        else:
            encoded=xz.encode(raw,guard.check);exact_original(pin,xz.decode(encoded,guard.check))
            carrier=dict(path=destination(generation),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            record=dict(original=dict(ORIGINAL),physical=carrier,source_role=ROLE,
                original_failure_promoted=False,actual_failed_product_child_executed=None)
        phase='EXACT_ROLE_AND_READER_CONTRACTS'
        spec=importlib.util.spec_from_file_location('legacy154_carrier_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.RAW=raw;tests.ROW=json.loads(raw)
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=10,errors=0,failures=0,skipped=0),'ALL_EXACT_LEGACY154_10')
        tests.RAW=tests.ROW=None;del tests,raw
        if not reuse:physical.publish_exclusive(c.ROOT,encoded,carrier,guard.check)
        del encoded;row['record']=record
        phase='ALL73_TWO_FRESH_PHYSICAL_BOUNDARIES'
        budget=physical.DecoderBudget(guard.check)
        Base=components.xz_corpus_delivery_v1.reader_type(a.AcceptanceReader,prior72[:68],budget,xz,
            components.runtime_record_envelope_v2,counts68,a.exact)
        Prior8=components.prepare_native008_carrier_v1.decoder_reader(Base,prior72[68]['physical_envelope_pin']['path'],budget,xz,counts8)
        Prior7=components.prepare_native007_carrier_v1.reader_type(Prior8,prior72[69]['physical_envelope_pin'],budget,xz,counts7)
        Prior72=components.legacy_validation_carriers_v1.reader_type(Prior7,prior['records'],budget,xz,counts2)
        Reader=reader_type(Prior72,carrier,budget,xz,counts154);q=Reader(c.ROOT,guard.check)
        for old in seed.snapshots.values():a.exact(q.pin(old['path']),old,'REOPEN_ALL_SEED_INPUTS')
        for old in prior['source_pins']:
            if old['path'].startswith('tools/p09/') and old['path'].endswith('.py'):
                a.exact(q.pin(old['path']),old,'CURRENT_ORIGINAL_FULL72_VERIFIER_PROGRAMS')
        physicals=[r['physical_envelope_pin'] for r in prior72]+[carrier]
        require(len({p['path'] for p in physicals})==73,'ALL73_DISTINCT_PHYSICAL_FILES')
        for old in physicals:a.exact(q.pin(old['path']),old,'FIRST_FULL73_PHYSICAL_HASH_AND_DECODE')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        phase='FINAL_FULL73_PHYSICAL_HASH_AND_DECODE';q.finish();guard.check(force=True)
        require(len(counts68)==68 and all(type(v) is int and v==2 for v in counts68.values())
            and counts8==[prior72[68]['physical_envelope_pin']]*2 and counts7==[prior72[69]['physical_envelope_pin']]*2
            and len(counts2)==2 and all(type(v) is int and v==2 for v in counts2.values())
            and counts154==[carrier,carrier] and budget.attempts==budget.completed==146,'ALL146_CURRENT_DECODES_ONE_BUDGET5')
        require(not denied,'NO_SUBPROCESS_ATTEMPTS')
        row.update(state='PASS_LEGACY154_COMPLETE73_PHYSICAL10_NOT_BINDING_WORKER_OR_NATIVE',pair_count=73,decode_count=146,
            prior_verification_pin=FULL72,prior_manifest_pin=MANIFEST,full72_descriptors=prior72,
            prior68_decode_counts=counts68,failed008_decode_count=len(counts8),failed007_decode_count=len(counts7),
            legacy2_decode_counts=counts2,legacy154_decode_count=len(counts154),physical_corpus_bytes=sum(p['bytes'] for p in physicals),
            reduced_physical_bytes=ORIGINAL['bytes']-carrier['bytes'],
            two_other_byte_pass_nominal_saved_seconds=(ORIGINAL['bytes']-carrier['bytes'])/1048576,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            old72_reader_functions_and_codecs_retained=True,shared_current_decoder5_not_prior_timing_sum=True,
            semantic_input_scope_reduced=False,byte_hash_JSON_cache=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            decoder_budget=None if budget is None else budget.evidence(),
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','record','pair_count','decode_count','reduced_physical_bytes',
        'two_other_byte_pass_nominal_saved_seconds','fresh_inputs','final_fresh_hashes','decoder_budget','elapsed_seconds','CPU_max',
        'owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
