"""P206: 전체 기존 runtime와 명시 fixture의 native 읽기 전용 handle 자격 확인.

새 제품 body/공유 frame은 실행하지 않는다. 원 입력을 제외하지 않고 실제 byte와
handle/path identity를 확인한다. 권한 probe는 이번에 만든 작은 파일에서만 한다.
"""
import argparse
import hashlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_minimal_runtime_r07_case as prior
import runtime_fixture_inputs as fixtures
import locked_runtime_inputs as locks
import owned_source_read_pressure as owned_rate

c=prior.c;b=prior.b;r=prior.r;v=prior.v
SELF='tools/p09/qualify_locked_runtime_inputs.py'
TEST='tools/p09/tests/test_locked_runtime_input_qualification.py'
PROBE='tools/p09/tests/fixtures/p206-input-lock-probe.txt'
SCHEMA='hwpx-agent.p09-locked-runtime-input-qualification/v1'
PASS='PASS_FULL_RUNTIME_AND_KNOWN_FIXTURE_READ_LOCKS_NOT_SHARED_FRAME_PRODUCT_OR_GATE'
PROBE_PASS='PASS_SMALL_OWN_FIXTURE_READ_LOCK_NOT_FULL_RUNTIME_SHARED_FRAME_PRODUCT_OR_GATE'
CONTRACT_PASS='PASS_LOCK_CODE_CONTRACTS_AND_FULL_SCOPE_COST_AUDIT_NOT_NATIVE_FULL_RUNTIME_OR_GATE'
FAILED_FULL=dict(path='implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run01.v1.json',
    bytes=344819,sha256='a71f78acdeb3a0d86a5c9798415be2c374fa4cf97142f9e011de749094e2a43a')
BODY=dict(path='implementation/p09/evidence/runtime-r07/cases/p190-case-011-attempt-001.json',
    bytes=933704,sha256='6d8ad0af9c5e12bd178b94cb28735200b611ca6b288165fcc7eaa7052c02877d')
CLOSING=dict(path='implementation/p09/evidence/runtime-r07/p198-case-011-attempt-001-close-07.v1.json',
    bytes=1145043,sha256='23f0505522ea72495377986ed944bf9adc2c967d195ef56a291fb79829f4c5ae')
HELPERS=(locks.SELF,locks.TEST,SELF,TEST,fixtures.SELF,fixtures.TEST,PROBE)
REFERENCES=['https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew',
    'https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle',
    'https://docs.python.org/3/library/msvcrt.html#msvcrt.get_osfhandle']


def require(ok,code):c.require(ok,'P206_QUALIFY_'+code)


def combine(runtime,manifests,fixture_inputs,helpers):
    result={}
    for group in (runtime,manifests,fixture_inputs,helpers):
        for name,pin in group.items():
            require(name not in result or result[name]==pin,'CONFLICTING_SCOPE_PIN')
            result[name]=dict(pin)
    require(set(runtime)<=set(result) and all(result[name]==pin for name,pin in runtime.items()),'EVERY_ORIGINAL_RUNTIME_INPUT_RETAINED')
    return locks.input_pins(result)


def lower_read_rate(reader):
    require(reader.read_passes==reader.bytes_read==0,'RATE_BEFORE_ANY_READER_IO')
    reader.pacer=owned_rate.OwnedPacer()


class Reader(r.Reader):
    def __init__(self,owner,context):
        super().__init__(owner,context);lower_read_rate(self.reader)
    def summary(self):
        out=super().summary();out.update(read_rate_policy='P206_binary1_other2_MiB_per_second',
            read_rates_by_kind=dict(binary=owned_rate.BINARY_RATE,other=owned_rate.OTHER_RATE))
        return out


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
        ('test_locked_runtime_inputs','test_locked_runtime_input_qualification'))
    with patch('subprocess.Popen',side_effect=AssertionError('P206_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P206_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P206_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==35 and not checked.skipped,'CONTRACT35')
    return 35


def current_inputs(q):
    expected,names,exe=b.baseline(q)
    require(q.pin(BODY['path'])==BODY and q.pin(CLOSING['path'])==CLOSING,'QUALIFIED_CASE011_RECEIPTS')
    case=q.json(BODY['path']);closed=q.json(CLOSING['path'])
    controller={name:q.pin(name) for name in prior.CONTROLLERS};engine={name:q.pin(name) for name in (b.SELF,b.TEST)}
    prior.validate_bridge(case,controller)
    runtime,historical=r.case_scope(case,expected,names,exe,engine,controller)
    r.validate(closed,case,BODY,expected,names,exe,engine,controller)
    require(len(runtime)==1421 and len(historical)==67,'EXACT_PRIOR_RUNTIME_WITHOUT_NEW_EXCLUSIONS')
    metadata={}
    for name,pin in fixtures.MANIFEST_PINS.items():
        require(q.pin(name)==pin,'KNOWN_FIXTURE_MANIFEST');metadata[name]=q.json(name)
    groups,fixture_inputs=fixtures.families(metadata[fixtures.P77],metadata[fixtures.FORM],metadata[fixtures.NOTE],
        metadata[fixtures.NATIVE],expected[fixtures.HEADER])
    require(len(fixture_inputs)==38,'KNOWN_FIXTURE38');helpers={name:q.pin(name) for name in HELPERS}
    require(0<helpers[PROBE]['bytes']<=128,'SMALL_OWN_PROBE_FILE')
    inputs=combine(runtime,fixtures.MANIFEST_PINS,fixture_inputs,helpers)
    require(not set(inputs)&historical and len(inputs)==1467,'FULL_PRIOR_PLUS_KNOWN_INPUTS')
    return expected,names,exe,runtime,fixture_inputs,helpers,inputs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--scope',choices=('contracts-only','probe-only','full-runtime'),default='contracts-only');args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT and 1<=args.run<=99,'CWD_RUN')
    target=b.s.scoped_path(f'implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run{args.run:02}.v1.json',fresh=True)
    context=r.observation.Context();owner=r.observation.Resources(context);q=held=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**r.flags(),
        actual_product_test_body_or_shared_frame_executed=False,existing_actual_runner_input_scope_changed=False,
        new_input_exclusions=[],content_or_attributes_written_or_deleted=False,qualification_scope=args.scope)
    try:
        owner.admit();q=Reader(owner,context);out['input_lock_contract_tests_passed']=contracts()
        if args.scope=='contracts-only':
            helpers={name:q.pin(name) for name in (locks.SELF,locks.TEST,SELF,TEST)}
            require(q.pin(FAILED_FULL['path'])==FAILED_FULL,'ORIGINAL_FAILED_FULL_SCOPE_RECEIPT')
            failed=q.json(FAILED_FULL['path']);before=failed['locked_identity_before']
            require(failed['state']=='FAILED_NOT_ACCEPTED' and failed['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and failed['input_locks']['input_lock_cleanup_confirmed']
                and failed['input_locks']['input_lock_handles_remaining']==0 and failed['IO']['finished'] is False,
                'ORIGINAL_FAILURE_AND_CLEANUP_NOT_RECLASSIFIED')
            budget=locks.open_budget(before['regular_file_count'],before['directory_count'])
            require(budget['input_files']==1467 and budget['ancestor_directories']==306,'OBSERVED_FULL_SCOPE_COUNTS')
            q.finish();out.update(state=CONTRACT_PASS,qualification_helper_pins=list(helpers.values()),
                preserved_failed_full_scope_receipt_pin=FAILED_FULL,full_scope_open_request_budget=budget,
                actual_native_input_lock_created_in_this_run=False,latest_full_runtime_lock_qualification='NOT_RUN',
                shared_open_pacer_for_native_handles_and_actual_byte_streams=True,
                required_full_byte_hash_before_and_final_passes_retained=True,
                original_hard_CPU_RAM_deadline_and_cleanup_unchanged=True)
        else:
            if args.scope=='full-runtime':expected,names,exe,runtime,fixture_inputs,helpers,inputs=current_inputs(q)
            else:
                helpers={name:q.pin(name) for name in (locks.SELF,locks.TEST,SELF,TEST,PROBE)}
                inputs=locks.input_pins(helpers);runtime=fixture_inputs={}
                require(0<helpers[PROBE]['bytes']<=128,'SMALL_OWN_PROBE_FILE')
            held=locks.InputLocks(c.ROOT,owner.checkpoint_io);held.acquire(inputs)
            out['planned_input_count']=len(inputs);out['planned_input_bytes']=sum(pin['bytes'] for pin in inputs.values())
            out['locked_identity_before']=held.acquisition_witness()
            probe=c.ROOT/PROBE;native=held.api
            with held.reader_sources(q.reader):
                for name,pin in inputs.items():require(q.pin(name)==pin,'EVERY_LOCKED_INPUT_ACTUAL_BYTE_HASH')
                inside=dict(read=native.access_probe(probe,locks.READ),write=native.access_probe(probe,locks.WRITE),
                    delete=native.access_probe(probe,locks.DELETE))
                require(inside['read']['opened'] and all(inside[key]==dict(opened=False,win32_error=32)
                    for key in ('write','delete')),'ACTUAL_READ_ALLOWED_WRITE_DELETE_SHARING_DENIED')
                q.finish();out['byte_stream_identity_passes']=held.verify_two_byte_passes(inputs)
            out['locked_identity_after']=held.verify_held_identities()
            require(held.close(),'ALL_OWN_INPUT_HANDLES_CLOSED')
            after=dict(write=native.access_probe(probe,locks.WRITE),delete=native.access_probe(probe,locks.DELETE))
            require(all(item==dict(opened=True,win32_error=0) for item in after.values()),'ACCESS_RESTORED_AFTER_RELEASE')
            owner.checkpoint_io();native.pacer.reserve()
            with probe.open('rb') as stream:probe_bytes=stream.read(129)
            require(len(probe_bytes)==helpers[PROBE]['bytes'] and hashlib.sha256(probe_bytes).hexdigest()==helpers[PROBE]['sha256'],
                'OWN_PROBE_BYTES_UNCHANGED_AFTER_ACCESS_ATTEMPTS')
            owner.checkpoint_io()
            out.update(state=PASS if args.scope=='full-runtime' else PROBE_PASS,
                binding=v.identity(names,expected,exe) if args.scope=='full-runtime' else None,
                qualified_input_pins=list(inputs.values()),qualified_inputs=len(inputs),
                qualified_input_bytes=sum(pin['bytes'] for pin in inputs.values()),prior_runtime_inputs=len(runtime),
                all_prior_runtime_inputs_retained=args.scope=='full-runtime',known_fixture_input_count=len(fixture_inputs),
                qualification_helper_pins=list(helpers.values()),
                sharing_probe_file_pin=helpers[PROBE],access_during_held_locks=inside,access_after_release=after,
                probe_access_open_only_no_write_truncate_delete_or_rename=True,
                own_probe_after_release_read_bytes=len(probe_bytes),
                actual_file_and_ancestor_handles_noninheritable=True,
                file_and_path_identities_checked_before_and_after_fresh_reads=True,
                verification_IO_reduction_already_applied=False)
        out['official_references']=REFERENCES
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        if held is not None:
            if not held.close():out['state']='FAILED_NOT_ACCEPTED'
            out['input_locks']=held.summary()
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=r.observation.summary(owner)
        with target.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','input_lock_contract_tests_passed','qualified_inputs','error_code','resource_stop_reason')}),flush=True)
    return 0 if out['state'] in (PASS,PROBE_PASS,CONTRACT_PASS) else 2


if __name__=='__main__':raise SystemExit(main())
