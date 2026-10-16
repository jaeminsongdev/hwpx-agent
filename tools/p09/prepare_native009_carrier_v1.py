"""Preserve the complete Native009 post-body shared720 failure as opaque XZ.

No product replay, source exclusion, status promotion or runtime connection.
Small test projections avoid copying the five-megabyte receipt per negative
test; the real original and both fresh physical decodes still hash all bytes.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SELF='tools/p09/prepare_native009_carrier_v1.py'
TEST='tools/p09/tests/test_prepare_native009_carrier_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
ORIGINAL=dict(path=PREFIX+'current-runtime-run009.v1.json',bytes=5046802,
    sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753')
CODEC=dict(path='tools/p09/receipt_xz_envelope_v1.py',bytes=4012,
    sha256='21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09')
PHYSICAL=dict(path='tools/p09/runtime_envelope_physical_io_v1.py',bytes=7214,
    sha256='b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c')
CASE='actual_import::source_review_locations::actual_original_stored_locations_match_direct_graph_without_state_defaults_or_writes'
SOURCE_ROLE='same_case_actual_body_PASS_final_source_shared720_failure_not_accepted_or_prebody'


def require(ok,label):
    if not ok: raise ValueError('NATIVE009_CARRIER_'+label)


def destination(generation):
    require(type(generation) is int and 1<=generation<=8,'FINITE_GENERATION')
    return 'implementation/p09/evidence/p361-lossless-runtime-inputs/'+f'case165-runtime-run009.failed.shared720.xz8m-g{generation:03}.envelope.v1.json'


def exact_original(pin,raw):
    require(type(pin) is dict and pin==ORIGINAL and type(pin['bytes']) is int,'EXACT_FIXED_ORIGINAL_PIN')
    require(type(raw) is bytes and len(raw)==ORIGINAL['bytes'] and hashlib.sha256(raw).hexdigest()==ORIGINAL['sha256'],'WHOLE_ORIGINAL_BYTES_AND_HASH')


def projection(row):
    frame=row['source_frame']; window=row['strict_product_window']; handles=frame['handles']; budget=frame['shared_metadata_frame_decoder']
    return dict(schema=row['schema_version'],state=row['state'],stop=row['stop_reason'],phase=row['operation_phase'],
        index=row['selected_test_index'],selected=row['selected_test_names'],passed=row['passed_test_names'],arguments=row['test_arguments'],
        product_complete=row['product_complete'],body=row['product_body_observed'],actual_child=row['actual_product_child_executed'],
        worker=row['worker_created'],assigned=row['job_assigned'],writer=row['writer_authorized'],cleanup=row['cleanup_confirmed'],
        tree_empty=row['owned_tree_empty'],Native_qualified=row['Native_source_frame_qualified'],candidate_qualified=row['current_generation_runtime_candidate_qualified'],
        accepted_delta=row['accepted_count_delta'],gates=[row['P09_gate'],row['A12_gate'],row['A13_gate']],terminal=dict(row['terminal_summary']),
        frame_state=frame['frame_state'],registered=frame['registered_live_frame'],input_count=frame['input_count'],input_bytes=frame['input_bytes'],
        completed_boundaries=len(frame['actual_byte_boundaries']),first_boundary_role=frame['actual_byte_boundaries'][0]['role'],
        handles_opened=handles['input_lock_handles_opened'],handles_closed=handles['input_lock_handles_closed'],handles_remaining=handles['input_lock_handles_remaining'],
        readers=handles['active_reader_bindings'],streams=handles['active_byte_streams'],close_errors=handles['handle_close_failed_attempts'],
        GO=window['actual_GO_writes'],captures=window['actual_capture_count'],capture_complete=window['actual_complete_capture_within_window'],
        product_window=window['maximum_GO_to_complete_capture_seconds'],GO_seconds=window['GO_to_complete_capture_elapsed_seconds'],
        ready_limit=window['worker_readiness']['readiness_limit_seconds'],ready_seconds=window['worker_readiness']['readiness_elapsed_seconds'],
        ready=window['worker_readiness']['readiness_confirmed'],decoder_limit=budget['shared_limit_seconds'],
        decoder_work=budget['total_decoder_work_seconds'],decoder_error=budget['terminal_error_seen'],
        metadata_decodes=budget['metadata_completed'],Frame_decodes=budget['Frame_completed'])


def validate_projection(p):
    expected=dict(schema='hwpx-agent.p09-current-queue-native-runtime-candidate/v1',state='STOPPED_NOT_ACCEPTED',
        stop='FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE',phase='final_source_freeze',index=165,
        selected=[CASE],passed=[CASE],arguments=[CASE,'--exact','--test-threads=1','--format=pretty','--color=never'],
        product_complete=False,body=True,actual_child=True,worker=True,assigned=True,writer=True,cleanup=True,tree_empty=True,
        Native_qualified=False,candidate_qualified=False,accepted_delta=0,gates=['OPEN','OPEN','OPEN'],
        terminal=dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248),frame_state='CLOSED',registered=False,
        input_count=3268,input_bytes=199890681,completed_boundaries=1,first_boundary_role='before',
        handles_opened=3642,handles_closed=3642,handles_remaining=0,readers=0,streams=0,close_errors=0,
        GO=1,captures=1,capture_complete=True,product_window=10,ready_limit=15,ready=True,
        decoder_limit=5.0,decoder_error=False,metadata_decodes=78,Frame_decodes=75)
    require(type(p) is dict and set(p)==set(expected)|{'GO_seconds','ready_seconds','decoder_work'},'EXACT_SMALL_FAILURE_PROJECTION')
    def same(a,b):
        if type(a) is not type(b): return False
        if type(b) is dict: return set(a)==set(b) and all(same(a[k],b[k]) for k in b)
        if type(b) is list: return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        return a==b
    require(all(same(p[k],v) for k,v in expected.items()),'EXACT_POST_BODY_FAILURE_NOT_PREBODY_OR_ACCEPTANCE')
    for key,limit in (('GO_seconds',10),('ready_seconds',15),('decoder_work',5)):
        require(type(p[key]) in (int,float) and math.isfinite(p[key]) and 0<=p[key]<=limit,'ACTUAL_BOUNDED_CAPTURE_READY_AND_PARTIAL_DECODER')
    return dict(p)


def main():
    import argparse,importlib.util,io,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('NATIVE009_CARRIER_ALL_SUBPROCESS_DENIED')
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
    parser=argparse.ArgumentParser(); parser.add_argument('--generation',type=int,required=True); parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args(); name=destination(args.generation); require(type(args.attempt) is int and 1<=args.attempt<=8,'FINITE_ATTEMPT')
    output=PREFIX+f'native009-carrier-g{args.generation:03}-attempt{args.attempt:03}.v1.json'
    for target in (output,name): require(not(c.ROOT/target).exists(),'EXCLUSIVE_OUTPUT_NO_ORIGINAL_OVERWRITE')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=None; phase='ADMISSION'
    row=dict(state='FAILED_NATIVE009_CARRIER_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        product_or_Native_executed=False,Native009_replayed=False,original_overwritten_or_deleted=False,
        source_role=SOURCE_ROLE,full162_Binding_worker_or_Native_qualified=False,actual_metadata_Frame_shared_decoder5_qualified=False,
        generation=args.generation,attempt=args.attempt)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST): q.pin(path)
        for pin in (CODEC,PHYSICAL): a.exact(q.pin(pin['path']),pin,'ORIGINAL_CODEC_AND_BOUNDED_PUBLISHER')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.suffix=='.py' and path.is_relative_to(c.ROOT/'tools/p09'): q.pin(path.relative_to(c.ROOT).as_posix())
        pin,buffer=q._read(ORIGINAL['path'],parse=True); q._bind(pin['path'],pin); raw=bytes(buffer); del buffer
        exact_original(pin,raw); failure=validate_projection(projection(json.loads(raw.decode('utf-8'),object_pairs_hook=codec.unique)))
        spec=importlib.util.spec_from_file_location('native009_carrier_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__]; tests.FAILURE=failure; tests.RAW=raw
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=10,errors=0,failures=0,skipped=0),'CARRIER10')
        # Only bounded credential shapes, never matched values, reach output.
        patterns=(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,256}\b',rb'\b(?:ghp_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{30,255})\b',
            rb'\bAKIA[0-9A-Z]{16}\b',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            rb'(?:postgres(?:ql)?|mysql|redis)://[^\s:/\x22\x27]{1,128}:[^\s@\x22\x27]{1,256}@')
        hits=0
        for pattern in patterns:
            guard.check(); hits+=bool(re.search(pattern,raw))
        require(hits==0,'CREDENTIAL_PATTERN_REQUIRES_PRIVATE_REVIEW_NO_PUBLICATION')
        phase='OPAQUE_ENCODING_AND_TWO_FRESH_PHYSICAL_DECODES'
        encoded=codec.encode(raw,guard.check); carrier=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        physical.publish_exclusive(c.ROOT,encoded,carrier,guard.check); del encoded
        row['published_carrier_pin']=carrier; budget=physical.DecoderBudget(guard.check)
        for boundary in ('before','after'):
            pin,buffer=q._read(name,parse=True); q._bind(name,pin); a.exact(pin,carrier,'NEW_FRESH_PHYSICAL_BYTES')
            restored=budget.run(lambda check:codec.decode(bytes(buffer),check)); del buffer
            exact_original(ORIGINAL,restored); require(restored==raw,'OPAQUE_ALL_BYTES_IDENTICAL')
            a.exact(validate_projection(projection(json.loads(restored.decode('utf-8'),object_pairs_hook=codec.unique))),failure,'FAILED_BODY_AND_CLEANUP_STATES_UNCHANGED')
            del restored
        del raw; tests.RAW=None
        require(budget.attempts==budget.completed==2,'TWO_COMPLETE_REAL_FRESH_DECODES')
        row.update(original_pin=ORIGINAL,reported_original_failure=failure,original_product_execution_true_preserved=True,
            failed_product_not_accepted=True,not_reclassified_as_prebody=True,physical_decode_boundaries=2,
            original_bytes=ORIGINAL['bytes'],carrier_bytes=carrier['bytes'],reduced_physical_bytes=ORIGINAL['bytes']-carrier['bytes'],
            two_other_byte_pass_nominal_saved_seconds=(ORIGINAL['bytes']-carrier['bytes'])/1048576,
            credential_pattern_categories_checked=5,credential_pattern_findings=0,not_all_secret_classes_guaranteed=True)
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_NATIVE009_POST_BODY_SHARED720_FAILURE_CARRIER10_NOT_BINDING_OR_ACCEPTANCE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        if budget is not None: row['decoder_budget_for_this_pair_only']=budget.evidence()
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes)
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'CARRIER_OWNER_CLEANUP'); publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','original_bytes','carrier_bytes','reduced_physical_bytes',
        'two_other_byte_pass_nominal_saved_seconds','decoder_budget_for_this_pair_only','fresh_inputs','final_fresh_hashes','elapsed_seconds',
        'CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
