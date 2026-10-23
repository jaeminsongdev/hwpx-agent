import copy
import unittest
import native011_readonly_terminal_audit as m


def fixture():
    parent=dict(state='FAILED_OWNED_READONLY_NATIVE_FRAME_NOT_ACCEPTED',failure=dict(first_error_code=m.RACE),
        cleanup=True,automatic_retry=False,accepted_count_delta=0,GO_authorized=False,
        epochs=[dict(stage=s,cleanup_confirmed=True,elapsed_seconds=1) for s in ('construction','opening','native_readonly')],
        owned=dict(constructor_entered=True,cleanup=True,cleanup_errors=[],owned_job=dict(worker_created=True,
            job_assigned=True,target_authorized=True,owned_tree_empty=True,cleanup_confirmed=True,job_handle_closed=True,
            last_job_accounting=dict(active_processes=0,owned_processes=[]),limits_readback=dict(verified=True,
                kill_on_close=True,breakaway_disabled=True,cpu_hard_cap_machine_percent=6.25,affinity_mask=1,priority_class=16384))))
    child={'original':'unchanged'};calls=[]
    def validator(c,read):
        calls.append((c,read));return dict(accepted_count_delta=0,product_executed=False,batch_phase='BROKEN')
    return child,parent,validator,calls


class Tests(unittest.TestCase):
    def test_original_validator_once_and_failed_monitor_never_relabelled(self):
        child,parent,validator,calls=fixture();before=copy.deepcopy(parent)
        row=m.inspect(child,parent,validator,object())
        self.assertEqual(parent,before);self.assertEqual(len(calls),1);self.assertIs(calls[0][0],child)
        self.assertFalse(row['original_owned_monitor_pass']);self.assertTrue(row['original_child_OS_exit_code_not_directly_recorded'])
        self.assertFalse(row['unobserved_live_phase_or_exit_code_inferred'])
        self.assertFalse(row['actual_owned_Native_or_product_acceptance_qualified'])

    def test_different_failure_successful_parent_or_retry_is_refused(self):
        for kind in ('failure','state','retry','go'):
            child,parent,validator,calls=fixture()
            if kind=='failure':parent['failure']['first_error_code']='CPU_STOP'
            if kind=='state':parent['state']='PASS_OWNED_FRAME'
            if kind=='retry':parent['automatic_retry']=True
            if kind=='go':parent['GO_authorized']=True
            with self.assertRaises(ValueError):m.inspect(child,parent,validator,None)
            self.assertEqual(calls,[])

    def test_missing_cleanup_process_or_original_limit_is_refused(self):
        for kind in ('cleanup','active','cap','priority','handles'):
            child,parent,validator,calls=fixture();job=parent['owned']['owned_job']
            if kind=='cleanup':job['cleanup_confirmed']=False
            if kind=='active':job['last_job_accounting']['active_processes']=1
            if kind=='cap':job['limits_readback']['cpu_hard_cap_machine_percent']=100
            if kind=='priority':job['limits_readback']['priority_class']=0
            if kind=='handles':job['job_handle_closed']=False
            with self.assertRaises(ValueError):m.inspect(child,parent,validator,None)
            self.assertEqual(calls,[])

    def test_missing_late_or_expired_phase_cannot_be_fabricated(self):
        for kind in ('missing','late','expired'):
            child,parent,validator,calls=fixture()
            if kind=='missing':parent['epochs'].pop()
            if kind=='late':parent['epochs'].append(dict(stage='terminal_evidence',elapsed_seconds=1,cleanup_confirmed=True))
            if kind=='expired':parent['epochs'][2]['elapsed_seconds']=600
            with self.assertRaises(ValueError):m.inspect(child,parent,validator,None)
            self.assertEqual(calls,[])

    def test_original_validation_failure_or_product_credit_propagates(self):
        child,parent,validator,calls=fixture();error=ValueError('ORIGINAL_FULL_FRAME_OR_SOURCE_MISMATCH')
        def failed(*args):raise error
        with self.assertRaises(ValueError) as caught:m.inspect(child,parent,failed,None)
        self.assertIs(caught.exception,error)
        with self.assertRaises(ValueError):m.inspect(child,parent,lambda *args:dict(
            accepted_count_delta=1,product_executed=True,batch_phase='READY'),None)
