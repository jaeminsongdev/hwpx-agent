"""감사된 과거 STOP는 고정, 현재 queue는 동적으로 선택·advance하는 계약."""
import copy
import unittest
import resume_current_queue_runtime as m

FIXTURES=None


class CurrentQueue(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_CURRENT_QUEUE_FIXTURES_REQUIRED')
        self.legacy,self.current,self.names,self.stop=copy.deepcopy(FIXTURES)
        self.fixtures=(self.legacy,self.current,self.names,self.stop)
    def test_audited_plan_not_current_plan(self):
        audited=m.audited_fixture(self.fixtures)
        self.assertEqual(audited[1],self.stop['prior_runtime_plan'])
        self.assertIsNot(audited[1],self.current)
    def test_current_not_forced_to60(self):
        index,name=m.g.old.select(self.current,self.names)
        self.assertEqual(index,self.current['next_runtime_index'])
        self.assertGreater(index,60);self.assertNotIn(name,self.current['runtime_qualified_test_names'])
    def test_past_failed_state_unchanged(self):
        before=copy.deepcopy(self.stop);m.audited_fixture(self.fixtures)
        self.assertEqual(self.stop,before);self.assertEqual(self.stop['state'],'FAILED_NOT_ACCEPTED')
    def test_corrupt_past_index_denied(self):
        self.stop['selected_test_index']=61
        with self.assertRaises(ValueError):m.audited_fixture(self.fixtures)
    def test_corrupt_past_next_denied(self):
        self.stop['prior_runtime_plan']['next_runtime_index']=61
        with self.assertRaises(ValueError):m.audited_fixture(self.fixtures)
    def test_advance_preserves_current_and_prior(self):
        before=copy.deepcopy(self.current);index,_=m.g.old.select(self.current,self.names)
        new=m.g.advance(self.legacy,self.current,self.names,index)
        self.assertEqual(self.current,before)
        self.assertEqual(new['runtime_source_qualified_individual_cases'],before['runtime_source_qualified_individual_cases']+1)
    def test_following_selection_is_supported(self):
        index,_=m.g.old.select(self.current,self.names)
        new=m.g.advance(self.legacy,self.current,self.names,index)
        later,name=m.g.old.select(new,self.names)
        self.assertNotEqual(later,index);self.assertNotIn(name,new['runtime_qualified_test_names'])
    def test_current_regular_not_corpus(self):
        _,name=m.g.old.select(self.current,self.names)
        self.assertFalse(name.startswith(m.p.v.CORPUS_PREFIX))
    def test_scope_adds2_preserves_previous(self):
        self.assertEqual(len(m.NEW),2);self.assertEqual(len(m.EXTRAS),45)
        self.assertTrue(set(m.previous.EXTRAS)<set(m.EXTRAS))
    def test_original_policy_unchanged(self):self.assertEqual(m.policy(),m.previous.policy())
    def test_new_failed_attempt_blocks_retry(self):
        with self.assertRaises(ValueError):m.closed_attempt(dict(state='FAILED_NOT_ACCEPTED'))
    def test_failed_record_cannot_advance(self):
        with self.assertRaises(ValueError):m.record(dict(schema_version=m.SCHEMA,state='FAILED_NOT_ACCEPTED'),
            None,None,{},None,{},self.names,self.legacy,self.current)


if __name__=='__main__':unittest.main()
