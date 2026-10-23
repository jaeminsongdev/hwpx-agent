from pathlib import Path
from contextlib import contextmanager
import json
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import native011_full_frame_worker_ready as m
import native011_readonly_frame_probe as original
import native011_product_worker_ready_probe as probe
import native011_product_worker_entry as worker
import native011_inherited_worker_ready_inspection as ready_original
import test_native011_readonly_frame_probe as phase_fixture
import test_native011_product_parent_handoff as transfer_fixture


class Tests(unittest.TestCase):
    def phase(self,callback=None,*,saved_parent=False):
        phase,args,owner,events,clock,mode=phase_fixture.ReadonlyFrameContracts().fixture()
        extra=dict(path='tools/p09/model201.py',bytes=1,sha256='0'*64)
        owner.current[extra['path']]=extra;owner.whole[extra['path']]=extra
        owner.initial=dict(owner.whole);owner.initial_reader.snapshots=dict(owner.whole)
        owner.initial_reader.read_passes=owner.initial_reader.bytes_read=202
        args=list(args);old=args[-2].SourceInheritance
        class Loan(old):
            def arm(self):events.append('flags_arm');self.state='ARMED';return tuple(range(1,203))
        args[-2]=NS(SourceInheritance=Loan)
        raw=(Path(__file__).resolve().parents[3]/m.SOURCE['path']).read_bytes()
        if callback is None:
            def callback(actual,frame):
                self.assertIs(actual,phase);self.assertIs(frame,phase.frame)
                self.assertEqual(frame.state,'BEFORE_READ');self.assertEqual(len(frame.boundaries),1)
                self.assertEqual(actual.state,'SOURCE_FLAGS');events.append('model-worker-ready-eof')
                return dict(model_only=True,product_GO_writes=0)
        saved=owner.parent_connection.parent.run_owned if saved_parent else None
        if saved_parent:
            def denied(run):raise AssertionError('INSTALLED_PRODUCT_ROUTE_MUST_STAY_DENIED')
            owner.parent_connection.parent.run_owned=denied
        adapted=m.FullFramePhase(original,raw,callback,original_parent_run=saved,phase=phase)
        return NS(phase=phase,adapted=adapted,args=args,owner=owner,events=events,clock=clock,mode=mode,raw=raw)

    def test_original_full_reads_surround_callback_and_201_default_is_not_mutated(self):
        before=original.NativePhase.run.__code__;f=self.phase();result=f.adapted.run(*f.args)
        self.assertIs(original.NativePhase.run.__code__,before);self.assertIn(201,before.co_consts)
        self.assertEqual(f.events.count('read'),2);self.assertEqual(f.events.count('model-worker-ready-eof'),1)
        self.assertLess(f.events.index('flags_restore'),f.events.index('model-worker-ready-eof'))
        self.assertLess(f.events.index('model-worker-ready-eof'),len(f.events)-1-f.events[::-1].index('read'))
        self.assertEqual(f.owner.phase,'BROKEN');self.assertEqual(f.phase.frame.state,'CLOSED')
        self.assertEqual(result['proof']['worker_source_count'],202)
        self.assertEqual(result['proof']['product_or_worker_processes_created'],1)
        self.assertFalse(result['proof']['original_Job_commit_supplied']);self.assertEqual(result['actual_accepted_count_delta'],0)
        self.assertTrue(f.adapted.projection['entire_original_run_code_inverse'])

    def test_restoration_failure_prevents_child_and_second_read(self):
        f=self.phase();f.mode.flag_fail=True
        with self.assertRaisesRegex(ValueError,'ORIGINAL_SOURCE_FLAGS_RESTORED'):f.adapted.run(*f.args)
        self.assertEqual(f.events.count('read'),1);self.assertNotIn('model-worker-ready-eof',f.events)
        self.assertEqual(f.adapted.callback_attempts,0);self.assertEqual(f.phase.frame.state,'CLOSED')

    def test_child_failure_is_preserved_and_original_frame_cleanup_runs(self):
        def fail(*args):raise ValueError('MODEL_CHILD_READY_FAILURE')
        f=self.phase(fail);f.mode.close_fail=True
        with self.assertRaisesRegex(ValueError,'MODEL_CHILD_READY_FAILURE'):f.adapted.run(*f.args)
        self.assertEqual(f.events.count('read'),1);self.assertTrue(f.phase.failed)
        self.assertIn('FRAME_CLOSE_UNCONFIRMED',f.phase.cleanup_errors);self.assertFalse(f.adapted.callback_completed)
        with self.assertRaises(ValueError):f.adapted.run(*f.args)

    def test_child_time_is_in_original600_and_must_not_start_second_read_when_expired(self):
        f=self.phase()
        def callback(*args):f.clock[0]=600;return dict(model_only=True)
        f.adapted.callback=callback
        with self.assertRaisesRegex(ValueError,'ORIGINAL600_INCLUDES_METADATA'):f.adapted.run(*f.args)
        self.assertEqual(f.events.count('read'),1);self.assertEqual(f.phase.frame.state,'CLOSED')
        self.assertEqual(f.phase.started,0);self.assertFalse(f.adapted.callback_completed)

    def test_saved_original_parent_runs_only_diagnostic_and_installed_route_remains_denied(self):
        f=self.phase(saved_parent=True);installed=f.owner.parent_connection.parent.run_owned
        result=f.adapted.run(*f.args)
        self.assertIs(f.owner.parent_connection.parent.run_owned,installed)
        self.assertTrue(result['proof']['explicit_no_product_delegate_only'])
        self.assertFalse(result['proof']['original_engine_body_called'])
        self.assertEqual(f.owner.parent_connection.state.attempts,1)

    def test_original_source_tamper_or_phase_method_tamper_is_rejected(self):
        f=self.phase()
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_READONLY_SOURCE'):m.projected_run(original,f.raw+b' ')
        with patch.object(original.NativePhase,'_read_frame',lambda *args:None):
            with self.assertRaisesRegex(ValueError,'EVERY_ORIGINAL_PHASE_METHOD_CODE_UNCHANGED'):
                m.projected_run(original,f.raw)

    def test_prepared_helpers_compile_once_and_create_one_phase_without_skipping_actual_reads(self):
        f=self.phase();callback=f.adapted.callback
        with patch.object(m,'projected_run',wraps=m.projected_run) as run,patch.object(m,'projected_read',wraps=m.projected_read) as read:
            prepared=m.prepare_phase(original,f.raw,callback)
            self.assertEqual(run.call_count,1);self.assertEqual(read.call_count,1)
            self.assertIsNone(f.phase.frame);self.assertFalse(prepared.preparation['source_byte_hash_JSON_AST_or_closing_credit_reused'])
            selected=prepared.create(phase=f.phase)
            self.assertEqual(run.call_count,1);self.assertEqual(read.call_count,1)
            result=selected.run(*f.args)
        self.assertEqual(f.events.count('read'),2);self.assertEqual(f.events.count('model-worker-ready-eof'),1)
        self.assertEqual(result['proof']['worker_source_count'],202);self.assertEqual(f.phase.frame.state,'CLOSED')
        with self.assertRaisesRegex(ValueError,'ONE_PREPARED_PHASE_CREATION_NO_RETRY'):prepared.create()

    def test_prepared_class_or_function_drift_is_rejected_and_failure_consumes_the_factory(self):
        for failure in ('method','code','global'):
            with self.subTest(failure=failure):
                f=self.phase();prepared=m.prepare_phase(original,f.raw,f.adapted.callback)
                target=original.NativePhase.check
                if failure=='method':change=patch.object(original.NativePhase,'check',lambda *args:None)
                elif failure=='code':
                    @contextmanager
                    def changed_code():
                        before=target.__code__
                        try:
                            target.__code__=before.replace(co_consts=(*before.co_consts,'changed'));yield
                        finally:target.__code__=before
                    change=changed_code()
                else:change=patch.dict(target.__globals__,{'_MODEL_NEW_PREPARED_GLOBAL':object()})
                with change:
                    with self.assertRaisesRegex(ValueError,'PREPARED_ORIGINAL_'):prepared.create(phase=f.phase)
                self.assertIsNone(f.phase.frame)
                with self.assertRaisesRegex(ValueError,'ONE_PREPARED_PHASE_CREATION_NO_RETRY'):prepared.create(phase=f.phase)

    def worker(self):
        f=transfer_fixture.Tests().fixture();journal=[];fault=NS(member=True,cleanup=False,child=False,guard=False)
        process=f.f.process;terminal=NS(done=False)
        process.poll=lambda:1 if terminal.done else None
        def wait(timeout):terminal.done=True;process.returncode=1;return 1
        process.wait=wait;process.returncode=None;process.stdout=object();process.stderr=object()
        windows=f.Windows()
        windows.k.AssignProcessToJobObject=lambda job,handle:(journal.append('assign') or True)
        def member(handle,job,value):value._obj.value=fault.member;return True
        windows.k.IsProcessInJob=member
        windows.k.CloseHandle=lambda job:not fault.cleanup
        windows.k.TerminateJobObject=lambda *args:True
        windows.accounting=lambda job:dict(active_processes=0)
        class Nested:
            def __init__(self,actual):self.windows=actual;journal.append('verified-parent')
            def parent_check(self):journal.append('same-parent')
            def create(self):journal.append('preparation-job');return 777
            def verify(self,job):return dict(model_only=True,maximum_system_CPU_percent=6.25,relative_parent_cpu_hard_cap_percent=100)
        class Capture:
            def __init__(self,output_only,**kwargs):journal.append('capture');self.output_only=output_only
            def communicate(self,timeout):
                terminal.done=True;process.returncode=1
                child=dict(state='COMPLETED_ORIGINAL_INHERITED_WORKER_NOT_PRODUCT_ACCEPTANCE',
                    original_worker_exit_code=1,error_code=None,cleanup_confirmed=True,
                    cleanup=dict(import_finder_restored=True,inherited_source_cleanup_confirmed=True),
                    source_count=202,final_fresh_hashes=202,inherited_sources_closed=202,
                    source_pin_sha256=worker.pin_digest(f.required),source_closing_before_original_READY=True,
                    every_declared_source_read_at_least_twice=True,original_GO_observed=False,original_input_reads=1,
                    product_creation_attempts=1 if fault.child else 0,GO_written_by_child=False,Native_or_product_acceptance_qualified=False)
                return json.dumps(child)+'\n',json.dumps(dict(terminal='WORKER_NOT_AUTHORIZED'))
            def close(self):journal.append('capture-close')
            def progress(self):pass
        def check():
            journal.append('native600-guard')
            if fault.guard:raise ValueError('MODEL_NATIVE_GUARD_STOP')
        phase=NS(frame=f.frame,check=check)
        api=NS(**{**vars(f.api),'nested':NS(InnerPreparationJob=Nested),'coverage':f.f.handoff.coverage,
            'probe':probe,'worker':worker,'original':ready_original})
        selected=m.WorkerProbe(f.f.handoff.root,windows,f.required,type(f.frame),api,Capture,factory=f.f.factory)
        return NS(f=f,selected=selected,phase=phase,journal=journal,fault=fault)

    def test_worker_probe_constructor_is_inert_and_does_not_take_frame_or_guard_ownership(self):
        f=self.worker();self.assertEqual(f.journal,[]);self.assertEqual(f.f.f.events,[])
        self.assertEqual(f.selected.proof['state'],'NOT_RUN_WHOLE_FRAME_WORKER_READY')
        self.assertFalse(f.selected.proof['GO_authorized']);self.assertEqual(f.selected.attempts,0)

    def test_original_ready_real_eof_and_cleanup_leave_full_frame_open_for_second_read(self):
        f=self.worker();before=dict(f.f.frame.held.stream_read_counts);result=f.selected(f.phase,f.f.frame)
        self.assertTrue(result['cleanup_confirmed']);self.assertEqual(result['product_GO_writes'],0)
        self.assertTrue(result['readiness']['readiness_confirmed']);self.assertFalse(result['readiness']['actual_original_GO_written'])
        observation=result['gate_cost_observation'];self.assertEqual(observation['original_gate_seconds'],15)
        self.assertFalse(observation['observation_used_for_admission_or_budget'])
        self.assertGreater(observation['observations']['original_owned_check']['calls'],0)
        self.assertGreater(observation['observations']['original_gate_checkpoint']['calls'],0)
        self.assertEqual(observation['observations']['original_gate_checkpoint']['failed_calls'],0)
        self.assertEqual(f.f.pipe.saved,f.f.api.bridge.START);self.assertEqual(f.f.frame.held.stream_read_counts,before)
        self.assertFalse(f.f.frame.held.closed);self.assertEqual(f.f.frame.state,'BEFORE_READ')
        self.assertTrue(result['preparation_only_nested_Job_not_product_Job'])
        self.assertFalse(result['original_product_Job_or_commit_qualified'])
        self.assertIn('capture-close',f.journal);self.assertEqual(len(f.f.f.created),1)

    def test_wrong_job_cannot_send_start_or_go_and_cannot_retry(self):
        f=self.worker();f.fault.member=False
        with self.assertRaises(ValueError):f.selected(f.phase,f.f.frame)
        self.assertEqual(f.f.pipe.saved,b'');self.assertTrue(f.selected.proof['cleanup_confirmed'])
        with self.assertRaisesRegex(ValueError,'ONE_ACTUAL_PHASE_FRAME_AND_NO_CHILD_RETRY'):f.selected(f.phase,f.f.frame)

    def test_native_guard_failure_before_child_is_not_replaced_by_preparation_policy(self):
        f=self.worker();f.fault.guard=True
        with self.assertRaisesRegex(ValueError,'MODEL_NATIVE_GUARD_STOP'):f.selected(f.phase,f.f.frame)
        self.assertEqual(f.f.f.created,[]);self.assertNotIn('preparation-job',f.journal)
        self.assertTrue(f.selected.proof['cleanup_confirmed']);self.assertFalse(f.f.frame.held.closed)

    def test_gate_resource_error_is_preserved_without_a_new_eof_wait_or_guard_retry(self):
        f=self.worker();original_check=f.phase.check;calls=[]
        def check():
            if f.f.f.created:
                calls.append(1);raise ValueError('MODEL_FIRST_GATE_RESOURCE_ERROR')
            return original_check()
        f.phase.check=check
        with self.assertRaisesRegex(ValueError,'MODEL_FIRST_GATE_RESOURCE_ERROR'):f.selected(f.phase,f.f.frame)
        self.assertEqual(len(calls),1);self.assertTrue(f.selected.proof['cleanup_confirmed'])
        self.assertEqual(f.f.pipe.saved,b'')
        observation=f.selected.proof['gate_cost_observation']
        self.assertEqual(observation['observations']['original_owned_check']['failed_calls'],1)
        self.assertEqual(observation['observations']['original_gate_checkpoint']['calls'],0)

    def test_child_product_attempt_or_cleanup_failure_is_never_accepted(self):
        for failure in ('child','cleanup'):
            f=self.worker();setattr(f.fault,failure,True)
            with self.assertRaises(ValueError):f.selected(f.phase,f.f.frame)
            self.assertEqual(f.selected.proof['state'],'FAILED_WHOLE_FRAME_WORKER_READY_NOT_PRODUCT')
            self.assertFalse(f.f.frame.held.closed)

    def test_child_primary_error_survives_unexpected_cleanup_error(self):
        f=self.worker();f.fault.guard=True
        def cleanup(*args):raise OSError('MODEL_CLEANUP_ERROR')
        f.selected.api.probe=NS(**{**vars(probe),'cleanup':cleanup})
        with self.assertRaisesRegex(ValueError,'MODEL_NATIVE_GUARD_STOP'):f.selected(f.phase,f.f.frame)
        self.assertFalse(f.selected.proof['cleanup_confirmed'])


if __name__=='__main__':unittest.main()
