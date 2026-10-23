"""Nested quota models only; real parent and child OS readback is separate."""
import copy
import unittest
import native011_nested_preparation_job as nested


class NestedPreparationContracts(unittest.TestCase):
    def fixture(self):
        class Windows:
            cpu_rate=625;processors=16
            parent=dict(verified=True,job_private_limit_mib=2560,cpu_hard_cap_machine_percent=6.25,
                affinity_mask=1,priority_class=0x4000,active_process_limit=16,kill_on_close=True,breakaway_disabled=True)
            def verify_job_limits(self,job):
                return dict(self.parent) if job is None else dict(self.parent,cpu_hard_cap_machine_percent=self.cpu_rate/100)
            def job(self):return 42
        windows=Windows();windows.parent=copy.deepcopy(windows.parent);return windows
    def test_relative_100_retains_actual_parent_machine_bound(self):
        w=self.fixture();candidate=nested.InnerPreparationJob(w);job=candidate.create();proof=candidate.verify(job)
        self.assertEqual(proof['relative_parent_cpu_hard_cap_percent'],100)
        self.assertEqual(proof['maximum_system_CPU_percent'],6.25);self.assertEqual(w.cpu_rate,625)
        self.assertFalse(proof['default_Windows_or_Native_policy_changed'])
        self.assertNotIn('cpu_hard_cap_machine_percent',proof)
    def test_no_current_job_or_original_query_failure_is_not_accepted(self):
        w=self.fixture()
        def fail(job):raise ValueError('ORIGINAL_LIMIT_QUERY_FAILED')
        w.verify_job_limits=fail
        with self.assertRaisesRegex(ValueError,'ORIGINAL_LIMIT_QUERY_FAILED'):nested.InnerPreparationJob(w)
    def test_breakaway_affinity_priority_or_kill_drift_rejected_before_creation(self):
        for key,value in (('breakaway_disabled',False),('affinity_mask',3),('priority_class',0x20),
            ('kill_on_close',False),('active_process_limit',32)):
            w=self.fixture();w.parent[key]=value
            with self.assertRaises(ValueError):nested.InnerPreparationJob(w)
    def test_parent_cpu_mismatch_or_unlimited_parent_not_accepted(self):
        for rate in (0,10000,626):
            w=self.fixture();w.cpu_rate=rate;w.parent['cpu_hard_cap_machine_percent']=rate/100
            with self.assertRaises(ValueError):nested.InnerPreparationJob(w)
    def test_changed_parent_blocks_creation_and_later_readback(self):
        w=self.fixture();candidate=nested.InnerPreparationJob(w);w.parent['job_private_limit_mib']=999
        with self.assertRaisesRegex(ValueError,'SAME_ACTUAL_PARENT_LIMITS'):candidate.create()
        with self.assertRaises(ValueError):candidate.verify(42)
    def test_inner_subtree_keeps_all_other_original_protections(self):
        w=self.fixture();candidate=nested.InnerPreparationJob(w);candidate.create()
        candidate.relative.parent=dict(w.parent,breakaway_disabled=False)
        with self.assertRaisesRegex(ValueError,'SAME_INNER_PROTECTIONS'):candidate.verify(42)
    def test_only_one_inner_job_can_be_created(self):
        w=self.fixture();candidate=nested.InnerPreparationJob(w);candidate.create()
        with self.assertRaisesRegex(ValueError,'ONE_INNER_JOB_CREATION'):candidate.create()
