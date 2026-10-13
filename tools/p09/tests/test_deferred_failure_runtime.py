"""P228: 감사된 STOP만 보존하고 새 미수용 사례를 선택하는 경계 계약."""
import copy
import unittest
import resume_deferred_failure_runtime as m

FIXTURES=None


class RuntimeBoundary(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_DEFERRED_QUEUE_FIXTURES_REQUIRED')
        self.legacy,self.plan,self.names,self.stop=copy.deepcopy(FIXTURES)
    def check(self,doc=None,pin=None,plan=None):
        m.reviewed_stop(doc if doc is not None else self.stop,pin if pin is not None else m.STOP_PIN,
            plan if plan is not None else self.plan)
    def test_audited_stop_stays_failed_and_plan_unchanged(self):
        before=copy.deepcopy(self.plan);self.check();self.assertEqual(self.plan,before)
        self.assertEqual(self.stop['state'],'FAILED_NOT_ACCEPTED')
    def test_stop_cannot_be_reclassified_PASS(self):
        self.stop['state']=m.PASS
        with self.assertRaises(ValueError):self.check()
    def test_reason_cannot_be_removed(self):
        self.stop['resource_stop_reason']=None
        with self.assertRaises(ValueError):self.check()
    def test_literal_failure_pin_required(self):
        pin=dict(m.STOP_PIN,sha256='0'*64)
        with self.assertRaises(ValueError):self.check(pin=pin)
    def test_next_cannot_skip60(self):
        self.plan['next_runtime_index']=61
        with self.assertRaises(ValueError):self.check()
    def test_unclosed_input_stop_denied(self):
        self.stop['terminal_source_frame']['handles']['input_lock_handles_remaining']=1
        with self.assertRaises(ValueError):self.check()
    def test_scope_adds7_not_replaces_original(self):
        self.assertEqual(len(m.NEW),7);self.assertEqual(len(m.EXTRAS),43)
        self.assertTrue(set(m.original.EXTRAS)<set(m.EXTRAS))
    def test_next_is_original_unaccepted_regular60(self):
        index,name=m.g.old.select(self.plan,self.names)
        self.assertEqual(index,60);self.assertNotIn(name,self.plan['runtime_qualified_test_names'])
        self.assertFalse(name.startswith(m.p.v.CORPUS_PREFIX))
    def test_original_guard_policy_stays_unchanged(self):
        self.assertEqual(m.policy(),m.original.policy())
        self.assertFalse(m.policy()['CPU_or_PC_freeze_improvement_claimed'])
    def test_new_failed_attempt_blocks_repetition(self):
        with self.assertRaises(ValueError):m.closed_attempt(dict(state='FAILED_NOT_ACCEPTED'))
    def test_partial_cleanup_never_accepts(self):
        with self.assertRaises(ValueError):m.closed_attempt(dict(state=m.PASS,error_code=None,
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=False))
    def test_failed_record_cannot_advance(self):
        doc=dict(schema_version=m.SCHEMA,state='FAILED_NOT_ACCEPTED')
        with self.assertRaises(ValueError):m.record(doc,None,None,{},None,{},self.names,self.legacy,self.plan)


if __name__=='__main__':unittest.main()
