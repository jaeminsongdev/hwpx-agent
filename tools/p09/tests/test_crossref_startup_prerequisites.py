"""Pure modeled observation contracts only; no actual native launch/session evidence."""
from contextlib import ExitStack
import unittest
from unittest.mock import patch
import crossref_startup_prerequisites as subject


class StartupPrerequisitesContracts(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.plan=self.stack.enter_context(patch.object(subject.startup.limits,'validate_plan',return_value={'affinity':4,'priority':0x4000}))
        self.registration=self.stack.enter_context(patch.object(subject.startup,'read_registered_command',return_value=[subject.startup.limits.EXECUTABLE,'-Automation']))
        self.processes=self.stack.enter_context(patch.object(subject.startup,'hwp_pids',return_value=set()))
        self.parent=self.stack.enter_context(patch.object(subject.startup,'parent_without_prompt_kill',return_value={'job_present':False}))
        self.pin=lambda:{'bytes':subject.startup.limits.EXECUTABLE_BYTES,'sha256':subject.startup.limits.EXECUTABLE_SHA}
    def run_inspection(self,check=lambda:None):return subject.inspect(object(),check,self.pin)
    def test_01_all_modeled_prerequisites_still_never_grant_native_readiness(self):
        result=self.run_inspection();self.assertTrue(result['all_observed_prerequisites_passed']);self.assertEqual(result['failed_prerequisites'],[])
        for field in('process_created','COM_activated','document_opened','permission_dialog_requested','native_startup_qualified','fixed_eight_executed','P09_complete'):self.assertIs(result[field],False)
    def test_02_original_parent_job_denial_is_preserved_without_fallback(self):
        self.parent.side_effect=ValueError('XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE');result=self.run_inspection()
        self.assertEqual(result['failed_prerequisites'],['caller_lifecycle_native_safe']);self.assertEqual(result['closed_errors']['caller_lifecycle_native_safe'],'XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
    def test_03_existing_hwp_is_reported_but_never_closed_or_terminated(self):
        self.processes.return_value={123,456};result=self.run_inspection();self.assertEqual(result['preexisting_hwp_processes'],2)
        self.assertFalse(result['checks']['no_preexisting_hwp_process']);self.assertFalse(result['process_created'])
    def test_04_registration_and_pin_mismatch_cannot_be_ignored(self):
        self.registration.side_effect=ValueError('XREF_NATIVE_STARTUP_FIXED_REGISTERED_SERVER');self.pin=lambda:{'bytes':True,'sha256':subject.startup.limits.EXECUTABLE_SHA}
        result=self.run_inspection();self.assertFalse(result['checks']['fixed_registered_server']);self.assertFalse(result['checks']['fixed_current_executable'])
    def test_05_private_registry_or_os_error_values_are_not_returned(self):
        self.registration.side_effect=OSError('PRIVATE-REGISTRY-VALUE');result=self.run_inspection()
        self.assertNotIn('PRIVATE-REGISTRY-VALUE',str(result));self.assertFalse(result['checks']['fixed_registered_server'])
    def test_06_resource_stop_propagates_before_any_observation(self):
        def stop():raise ValueError('STOP_SYSTEM_CPU')
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_CPU'):self.run_inspection(stop)
        self.plan.assert_not_called();self.registration.assert_not_called();self.processes.assert_not_called();self.parent.assert_not_called()
    def test_07_resource_stop_inside_process_snapshot_does_not_continue_to_parent(self):
        self.processes.side_effect=ValueError('STOP_SYSTEM_COMMIT')
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_COMMIT'):self.run_inspection()
        self.parent.assert_not_called()
    def test_08_unknown_or_malformed_snapshot_fails_closed_without_authority(self):
        self.processes.return_value={True};result=self.run_inspection();self.assertFalse(result['checks']['no_preexisting_hwp_process']);self.assertIsNone(result['preexisting_hwp_processes'])
        self.plan.side_effect=ValueError('UNKNOWN_CALLBACK_FAILURE')
        with self.assertRaisesRegex(ValueError,'UNKNOWN_CALLBACK_FAILURE'):self.run_inspection()


if __name__=='__main__':unittest.main()
