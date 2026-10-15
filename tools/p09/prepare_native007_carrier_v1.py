"""Lossless Native007 failure carrier; never replay or accept its product.

The exact raw receipt, including its observed product body and closing failure,
is preserved. Two new physical reads share the original five-second decoder
budget. This pair alone does not qualify the complete70 corpus or Native009.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/prepare_native007_carrier_v1.py'
TEST='tools/p09/tests/test_prepare_native007_carrier_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
ORIGINAL=dict(path=PREFIX+'current-runtime-run007.v1.json',bytes=4199057,
    sha256='3271eb9b07cd0eb1462630bb0f61e7ca7894545ec67f0c516ea8d898391a0f6c')


def require(ok,label):
    if not ok:raise ValueError('NATIVE007_CARRIER_'+label)


def identifier(value):
    require(type(value) is int and 1<=value<=8,'FINITE_IDENTIFIER');return value


def destination(generation):
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/'+\
        f'case165-runtime-run007.failed.final-source.xz8m-g{identifier(generation):03}.envelope.v1.json'


def exact_original(pin,raw):
    require(type(pin) is dict and pin==ORIGINAL,'EXACT_ORIGINAL_PIN')
    require(type(raw) is bytes and len(raw)==ORIGINAL['bytes']
        and hashlib.sha256(raw).hexdigest()==ORIGINAL['sha256'],'ALL_ORIGINAL_BYTES')


def failed_state(row):
    require(type(row) is dict and type(row.get('selected_test_index')) is int
        and row['selected_test_index']==165 and row.get('state')=='STOPPED_NOT_ACCEPTED'
        and row.get('stop_reason')=='STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING'
        and row.get('operation_phase')=='final_source_freeze','EXACT_CLOSING_FAILURE')
    require(row.get('product_complete') is False
        and row.get('current_generation_runtime_candidate_qualified') is False
        and row.get('actual_product_child_executed') is True,'EXECUTED_PRODUCT_NOT_ACCEPTED_OR_PREBODY')


def reader_type(original,carrier,budget,codec,counts):
    class Reader(original):
        def _read(self,name,parse=False):
            pin,buffer=super()._read(name,parse=parse or name==carrier['path'])
            if name==carrier['path']:
                require(pin==carrier,'FRESH_EXACT_PHYSICAL_PIN')
                decoded=budget.run(lambda check:codec.decode(bytes(buffer),check))
                exact_original(ORIGINAL,decoded);counts.append(dict(pin))
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
    import receipt_xz_envelope_v1 as codec
    import prepare_native008_carrier_v1 as previous
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--attempt',type=int,required=True);args=parser.parse_args()
    generation=identifier(args.generation);attempt=identifier(args.attempt)
    output=PREFIX+f'native007-carrier-g{generation:03}-attempt{attempt:03}.v1.json'
    name=destination(generation)
    for target in (output,name):
        path=c.ROOT/target
        require(not path.exists() and not path.is_symlink() and not path.is_junction(),'EXCLUSIVE_OUTPUTS')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic();budget=None;counts=[]
    row=dict(state='FAILED_NATIVE007_CARRIER_NOT_ADOPTED',generation=generation,attempt=attempt,
        product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False,
        automatic_retry=False,original_overwritten_or_deleted=False,current_runtime_profile_changed=False,
        source_role='same_case_executed_product_final_input_failure_not_accepted',
        full70_shared_decoder_or_Native_binding_qualified=False)
    try:
        guard.acquire();budget=physical.DecoderBudget(guard.check)
        q=a.AcceptanceReader(c.ROOT,guard.check)
        for pin in (previous.CODEC,previous.PHYSICAL):a.exact(q.pin(pin['path']),pin,'UNCHANGED_CODEC_AND_PUBLISHER')
        q.pin(SELF);q.pin(TEST)
        pin,buffer=q._read(ORIGINAL['path'],parse=True);q._bind(ORIGINAL['path'],pin)
        raw=bytes(buffer);del buffer;exact_original(pin,raw);failed_state(json.loads(raw))
        spec=importlib.util.spec_from_file_location('native007_carrier_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.RAW=raw;tests.CODEC=codec;tests.CHECK=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=9,errors=0,failures=0,skipped=0),'ALL_CARRIER9')
        encoded=codec.encode(raw,guard.check)
        exact_original(ORIGINAL,codec.decode(encoded,guard.check))
        carrier=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        tests.RAW=None;del raw;del tests
        physical.publish_exclusive(c.ROOT,encoded,carrier,guard.check);del encoded
        row['published_carrier_pin']=carrier
        # Reuse the existing reader's pin map, not its already-read contents.
        Reader=reader_type(a.AcceptanceReader,carrier,budget,codec,counts)
        fresh=Reader(c.ROOT,guard.check)
        for pin in q.snapshots.values():a.exact(fresh.pin(pin['path']),pin,'REOPEN_ALL_PROGRAM_AND_RAW_INPUTS')
        del q
        a.exact(fresh.pin(name),carrier,'FIRST_FRESH_CARRIER_READ')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':fresh.pin(path.relative_to(c.ROOT).as_posix())
        fresh.finish();guard.check(force=True)
        require(counts==[carrier,carrier] and budget.attempts==budget.completed==2,'TWO_REAL_CARRIER_DECODES')
        row.update(state='PASS_NATIVE007_LOSSLESS_TWO_FRESH_READS_NOT_FULL70_OR_RUNTIME_BINDING',
            original_pin=ORIGINAL,source_pins=list(fresh.snapshots.values()),fresh_inputs=len(fresh.snapshots),
            final_fresh_hashes=fresh.final_fresh_hashes,physical_decode_boundaries=2,
            original_bytes=ORIGINAL['bytes'],carrier_bytes=carrier['bytes'],
            reduced_physical_bytes=ORIGINAL['bytes']-carrier['bytes'],
            two_other_byte_pass_nominal_saved_seconds=(ORIGINAL['bytes']-carrier['bytes'])/1048576,
            original_product_execution_true_preserved=True,failed_product_NOT_accepted=True,
            parsed_JSON_hash_or_byte_cache=False,independent_full_successor_model_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            decoder_budget_for_this_pair_only=None if budget is None else budget.evidence(),
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNED_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','original_bytes','carrier_bytes',
        'reduced_physical_bytes','two_other_byte_pass_nominal_saved_seconds','physical_decode_boundaries','fresh_inputs',
        'final_fresh_hashes','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
