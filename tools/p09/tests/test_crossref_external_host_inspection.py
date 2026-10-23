"""Modeled external-root contracts; actual kernel denial is a separate driver observation."""
import ast
from contextlib import ExitStack
import io
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch

import crossref_external_host_inspection as subject
import inspect_external_crossref_host as entry


class ExternalHostContracts(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.identity=dict(process_id=123,session_id=1,creation_filetime_100ns='1234567',
            process_image=str(subject.fixed.PYTHON),affinity_mask=4,priority_class=0x4000,kernel_handle_observation=True)
        self.prereq=dict(all_observed_prerequisites_passed=True,failed_prerequisites=[],
            process_created=False,COM_activated=False,permission_dialog_requested=False)
        self.layout=dict(empty_jobs_closed=True,child_started_or_assigned=False,native_preassignment_or_COM_owner_qualified=False)
        self.kernel=self.stack.enter_context(patch.object(subject,'current_identity',return_value=self.identity))
        self.observe=self.stack.enter_context(patch.object(subject.prerequisites,'inspect',return_value=self.prereq))
        self.parent=self.stack.enter_context(patch.object(subject.prerequisites.startup,'parent_without_prompt_kill',return_value={'job_present':False}))
        self.jobs=self.stack.enter_context(patch.object(subject,'empty_resource_layout',return_value=self.layout))
        self.runtime=dict(path=subject.fixed.PYTHON.name,bytes=107312,
            sha256='dea78bb78043f0d53ef4a475f85fa0312b90fa93c136a0686d17946781c60e16')
    def inspect(self,check=lambda:None,pin=None):
        return subject.inspect(object(),check,lambda:{},pin or(lambda:self.runtime))
    def factories(self):
        # Use the unpatched module-level function stored before setUp mocking.
        windows=NS(memory_limit=800,mask=4,cpu_rate=625)
        windows.accounting=Mock(return_value={'active_processes':0})
        def make(memory):
            plan=dict(memory_limit=memory,affinity=4,cpu_rate=625)
            profile=dict(cleanup_confirmed=False)
            item=NS(plan=plan,job=object(),profile=profile)
            item.readback=Mock(return_value=dict(verified=True,kill_on_close=False,breakaway_disabled=True,time_limit_installed=False))
            item.close=Mock(side_effect=lambda:profile.update(cleanup_confirmed=True))
            return item
        owner,worker=make(700),make(100)
        a=self.stack.enter_context(patch.object(subject.native,'NativeOwnerJob',return_value=owner))
        b=self.stack.enter_context(patch.object(subject.host,'OwnedHostProcess',return_value=worker))
        return windows,owner,worker,a,b

    def test_01_jobless_model_still_has_no_native_or_future_execution_authority(self):
        out=self.inspect();self.assertTrue(out['external_jobless_prerequisites_observed'])
        for key in('process_created','COM_activated','document_opened','permission_dialog_requested',
                'fixed_eight_executed','native_startup_qualified','native_execution_authorized','P09_complete'):
            self.assertIs(out[key],False)
        self.assertTrue(out['future_invocation_must_revalidate_all_live_conditions']);self.assertEqual(out['accepted_count_delta'],0)
        self.assertEqual(self.parent.call_count,2);self.assertEqual(self.kernel.call_count,2)

    def test_02_current_job_denial_never_creates_even_empty_jobs(self):
        self.prereq.update(all_observed_prerequisites_passed=False,failed_prerequisites=['caller_lifecycle_native_safe'])
        out=self.inspect();self.assertFalse(out['external_jobless_prerequisites_observed']);self.assertIsNone(out['empty_resource_layout'])
        self.jobs.assert_not_called();self.parent.assert_not_called()

    def test_03_existing_hwp_denial_does_not_touch_that_process(self):
        self.prereq.update(all_observed_prerequisites_passed=False,failed_prerequisites=['no_preexisting_hwp_process'])
        self.assertFalse(self.inspect()['external_jobless_prerequisites_observed']);self.jobs.assert_not_called()

    def test_04_wrong_python_sha_rejects_before_prerequisite_or_job_operations(self):
        self.runtime['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'FIXED_PYTHON_RUNTIME_BYTES'):self.inspect()
        self.observe.assert_not_called();self.jobs.assert_not_called()

    def test_05_wrong_python_size_or_boolean_never_matches_numeric_identity(self):
        for size in(True,107311,0):
            with self.subTest(size=size):
                self.runtime['bytes']=size
                with self.assertRaisesRegex(ValueError,'FIXED_PYTHON_RUNTIME_BYTES'):self.inspect()
        self.observe.assert_not_called()

    def test_06_wrong_runtime_basename_has_no_path_or_executable_fallback(self):
        self.runtime['path']='other.exe'
        with self.assertRaisesRegex(ValueError,'FIXED_PYTHON_RUNTIME_BYTES'):self.inspect()
        self.jobs.assert_not_called()

    def test_07_kernel_birth_or_session_drift_fails_same_invocation(self):
        for field in('process_id','session_id','creation_filetime_100ns','process_image'):
            other=dict(self.identity);other[field]='changed'
            self.kernel.side_effect=[self.identity,other]
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,'CALLER_KERNEL_IDENTITY_CHANGED'):self.inspect()

    def test_08_original_resource_stop_prevents_first_kernel_observation(self):
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_CPU'):
            self.inspect(lambda:(_ for _ in ()).throw(ValueError('STOP_SYSTEM_CPU')))
        self.kernel.assert_not_called();self.observe.assert_not_called();self.jobs.assert_not_called()

    def test_09_stop_inside_original_prerequisites_propagates_without_more_work(self):
        self.observe.side_effect=ValueError('STOP_SYSTEM_COMMIT')
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_COMMIT'):self.inspect()
        self.parent.assert_not_called();self.jobs.assert_not_called();self.assertEqual(self.kernel.call_count,1)

    def test_10_empty_job_error_is_not_checkbox_or_native_success(self):
        self.jobs.side_effect=OSError('PRIVATE-OS-ERROR')
        with self.assertRaises(OSError):self.inspect()
        self.assertEqual(self.jobs.call_count,1);self.assertEqual(self.kernel.call_count,1)

    def test_11_parent_must_remain_jobless_after_empty_job_cleanup(self):
        self.parent.side_effect=[{'job_present':False},ValueError('XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')]
        with self.assertRaisesRegex(ValueError,'PARENT_LIFECYCLE_NOT_NATIVE_SAFE'):self.inspect()
        self.assertEqual(self.jobs.call_count,1)

    def test_12_final_runtime_bytes_drift_cannot_use_prior_pin_as_live_authority(self):
        wrong=dict(self.runtime,sha256='f'*64);pins=Mock(side_effect=[self.runtime,wrong])
        with self.assertRaisesRegex(ValueError,'FIXED_PYTHON_RUNTIME_BYTES'):self.inspect(pin=pins)
        self.assertEqual(pins.call_count,2)

    def test_13_empty_original_jobs_read_back_and_close_both_partitions(self):
        windows,owner,worker,_,_=self.factories()
        out=EMPTY_LAYOUT(windows,lambda:None,lambda:{})
        self.assertEqual(out['aggregate_private_limit_bytes'],800);self.assertTrue(out['empty_jobs_closed'])
        self.assertFalse(out['child_started_or_assigned']);self.assertFalse(out['native_preassignment_or_COM_owner_qualified'])
        owner.close.assert_called_once();worker.close.assert_called_once()

    def test_14_kill_time_or_breakaway_flag_mismatch_cannot_be_accepted(self):
        windows,owner,worker,_,_=self.factories()
        for field,value in(('kill_on_close',True),('breakaway_disabled',False),('time_limit_installed',True),('verified',False)):
            with self.subTest(field=field):
                owner.readback.return_value.update(verified=True,kill_on_close=False,breakaway_disabled=True,time_limit_installed=False)
                owner.readback.return_value[field]=value
                with self.assertRaisesRegex(ValueError,'NO_KILL_TIME_OR_BREAKAWAY_POLICY'):EMPTY_LAYOUT(windows,lambda:None,lambda:{})
        self.assertEqual(owner.close.call_count,4);self.assertEqual(worker.close.call_count,4)

    def test_15_combined_budget_or_affinity_mismatch_is_not_hidden_by_empty_jobs(self):
        windows,owner,worker,_,_=self.factories()
        for field,value in(('memory_limit',101),('affinity',8),('cpu_rate',626)):
            worker.plan.update(memory_limit=100,affinity=4,cpu_rate=625);worker.plan[field]=value
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,'UNCHANGED_SHARED_BUDGET'):EMPTY_LAYOUT(windows,lambda:None,lambda:{})

    def test_16_any_live_job_member_rejects_empty_only_claim(self):
        windows,owner,worker,_,_=self.factories();windows.accounting.return_value={'active_processes':1}
        with self.assertRaisesRegex(ValueError,'EMPTY_JOBS_ONLY'):EMPTY_LAYOUT(windows,lambda:None,lambda:{})
        owner.close.assert_called_once();worker.close.assert_called_once()

    def test_17_worker_constructor_failure_closes_already_created_empty_owner(self):
        windows,owner,_,_,factory=self.factories();factory.side_effect=ValueError('MODELED_WORKER_CREATE_FAILED')
        with self.assertRaisesRegex(ValueError,'MODELED_WORKER_CREATE_FAILED'):EMPTY_LAYOUT(windows,lambda:None,lambda:{})
        owner.close.assert_called_once()

    def test_18_owner_constructor_failure_never_enters_worker_factory(self):
        windows,_,_,factory,worker=self.factories();factory.side_effect=ValueError('MODELED_OWNER_CREATE_FAILED')
        with self.assertRaisesRegex(ValueError,'MODELED_OWNER_CREATE_FAILED'):EMPTY_LAYOUT(windows,lambda:None,lambda:{})
        worker.assert_not_called()

    def test_19_resource_stop_after_configuration_still_closes_empty_jobs(self):
        windows,owner,worker,_,_=self.factories();checkpoint=Mock(side_effect=[None,ValueError('STOP_SYSTEM_CPU')])
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_CPU'):EMPTY_LAYOUT(windows,checkpoint,lambda:{})
        self.assertEqual(checkpoint.call_count,2);owner.close.assert_called_once();worker.close.assert_called_once()

    def test_20_worker_cleanup_failure_still_attempts_owner_cleanup_once(self):
        windows,owner,worker,_,_=self.factories();worker.close.side_effect=ValueError('MODELED_EMPTY_CLOSE_FAILED')
        with self.assertRaisesRegex(ValueError,'MODELED_EMPTY_CLOSE_FAILED'):EMPTY_LAYOUT(windows,lambda:None,lambda:{})
        owner.close.assert_called_once();worker.close.assert_called_once()

    def test_21_inspection_cli_has_no_execute_subset_retry_or_arbitrary_path_mode(self):
        for args in([],['--inspect-only'],['--inspect-only','--inspection-run','0'],
                ['--inspect-only','--inspection-run','1','--execute'],['--inspect-only','--inspection-run','1','--output','PRIVATE']):
            with self.subTest(args=args),patch('sys.stderr',io.StringIO()):
                with self.assertRaises(SystemExit):entry.main(args)
        for value in(True,0,9,'1'):
            with self.assertRaises(ValueError):entry.receipt_name(value)
        self.assertEqual(entry.receipt_name(1),'implementation/p09/evidence/p09-361-external-crossref-host-inspection-run001.v1.json')
        self.assertEqual(entry.safe_code(OSError('PRIVATE-SYSTEM-VALUE')),'EXTERNAL_HOST_INSPECTION_FAILURE_NO_RAW_VALUES')

    def test_22_actual_source_has_no_launch_com_assignment_breakaway_or_force_kill_calls(self):
        root=Path(__file__).resolve().parents[3]
        forbidden={'CreateProcessW','ResumeThread','Popen','run','system','TerminateProcess','TerminateJobObject',
            'AssignProcessToJobObject','CoCreateInstance','create_suspended','resume','bind_owner','admit','start_waiting','kill'}
        for path in(entry.SELF,entry.MODULE):
            tree=ast.parse((root/path).read_text(encoding='utf-8'))
            calls={n.func.attr if isinstance(n.func,ast.Attribute)else n.func.id for n in ast.walk(tree)
                if isinstance(n,ast.Call)and isinstance(n.func,(ast.Name,ast.Attribute))}
            self.assertFalse(calls&forbidden)
        self.assertNotIn('preparation_CPU',subject.__doc__)


    def test_23_preserved_old_python_image_cannot_satisfy_new_runtime_pin(self):
        self.runtime['sha256']='7d938c92a08d6495421f2f1076ccd7198aec0b288471abc0a55e90b1150d96a1'
        with self.assertRaisesRegex(ValueError,'FIXED_PYTHON_RUNTIME_BYTES'):self.inspect()
        self.observe.assert_not_called();self.jobs.assert_not_called()


    def test_24_entry_requires_packed_proof_and_rejects_incomplete_or_failed_code(self):
        proof=dict(state=entry.CODE_STATE,cleanup=True,fresh_inputs=5,final_fresh_hashes=5,
            contracts=dict(run=1,errors=0,failures=0,skipped=0),current_distinct_contracts=24,retained_contracts=23)
        self.assertEqual(entry.load_code_proof(NS(json=lambda path:entry.r.compact.pack(proof))),proof)
        with self.assertRaisesRegex(ValueError,'COMPACT_RECEIPT_ENVELOPE'):
            entry.load_code_proof(NS(json=lambda path:proof))
        for field,value in(('cleanup',False),('final_fresh_hashes',4),('state','FAILED'),
                ('current_distinct_contracts',23),('retained_contracts',22)):
            with self.subTest(field=field):
                bad=dict(proof);bad[field]=value
                with self.assertRaises(ValueError):entry.load_code_proof(NS(json=lambda path:entry.r.compact.pack(bad)))


EMPTY_LAYOUT=subject.empty_resource_layout
