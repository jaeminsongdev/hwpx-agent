"""First-error and owned-cleanup models only; no process is created."""
from types import SimpleNamespace as NS
import unittest
import native011_owned_preparation as runner


class OwnedPreparationContracts(unittest.TestCase):
    def test_original_memory_failure_not_masked_by_cleanup_failure(self):
        primary=ValueError('ORIGINAL_RAM_STOP');cleanup=ValueError('OWNED_CLEANUP_FAILED');calls=[]
        def close():calls.append('close');raise cleanup
        owned=NS(kill=lambda:calls.append('kill'),wait=lambda timeout:calls.append('wait'),close=close,
            profile={'cleanup_confirmed':False})
        result={'constructor_entered':True}
        with self.assertRaises(ValueError) as caught:
            try:raise primary
            finally:runner.cleanup_owned(owned,None,result,primary)
        self.assertIs(caught.exception,primary);self.assertEqual(calls,['kill','wait','close'])
        self.assertFalse(result['cleanup']);self.assertEqual(len(result['cleanup_errors']),1)

    def test_cleanup_failure_is_not_lost_without_a_primary_failure(self):
        cleanup=ValueError('OWNED_CLOSE_FAILED')
        def close():raise cleanup
        owned=NS(kill=lambda:None,wait=lambda timeout:None,close=close,profile={'cleanup_confirmed':False})
        with self.assertRaises(ValueError) as caught:runner.cleanup_owned(owned,None,{'constructor_entered':True},None)
        self.assertIs(caught.exception,cleanup)

    def test_before_constructor_stop_is_clean_but_partial_constructor_is_unknown(self):
        for entered in (False,True):
            result={'constructor_entered':entered}
            runner.cleanup_owned(None,None,result,ValueError('BEFORE_OR_PARTIAL_CONSTRUCTION_STOP'))
            self.assertEqual(result['cleanup'],not entered)
            self.assertNotIn('owned_job',result)

    def test_memory_condition_does_not_become_a_cpu_incident(self):
        result=runner.failure_record(ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP'),[
            dict(available_ram_percent=4.99,commit_used_percent=52.7,system_cpu_percent=11.93)])
        self.assertEqual(result['first_error_code'],'CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP')
        self.assertEqual(result['observed_resource_condition'],'SYSTEM_MEMORY_PRESSURE')
        self.assertTrue(result['resource_condition_not_process_attribution'])

    def test_error_values_are_not_printed_as_secret_or_full_log(self):
        result=runner.failure_record(ValueError('private value=not printed'),[])
        self.assertEqual(result['first_error_code'],'CLOSED_READONLY_FAILURE')

    def test_fresh_guard_failure_never_enters_a_process_constructor(self):
        original=ValueError('ORIGINAL_RAM_STOP');checks=[]
        def check(force=False):checks.append(force);raise original
        guard=NS(check=check,samples=[dict(available_ram_percent=4.8,commit_used_percent=52,system_cpu_percent=5)])
        result={}
        with self.assertRaises(ValueError) as caught:runner.run_once([],guard,{},83.47,result)
        self.assertIs(caught.exception,original);self.assertEqual(checks,[True])
        self.assertFalse(result['constructor_entered']);self.assertTrue(result['cleanup'])
        self.assertTrue(result['stop_before_process_creation'])


if __name__=='__main__':unittest.main()
