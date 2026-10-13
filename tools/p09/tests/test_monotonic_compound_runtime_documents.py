"""P266 문서prefix·예산·원실행계약수20. 제품 재실행 없음."""
import copy
import unittest
import sync_monotonic_compound_runtime_documents as d


def plan():
    return dict(runtime_source_qualified_individual_cases=86,runtime_remaining_individual_cases=163,
        runtime_remaining_regular_cases=157,runtime_remaining_corpus_cases=6,next_runtime_index=93,
        all_successful_bodies_pending_whole_reconciliation=83,runtime_successful_candidates_requiring_closing=0)


class PrefixTests(unittest.TestCase):
    def setUp(self):
        self.plan=plan();self.before=b'original r108 bytes\r\n'
        self.text='> P265~P266 runtime-r109 '+' '.join(d.words(self.plan))+'\n\n'
        self.after=self.text.encode()+self.before
    def test_exact_previous_preserved(self):self.assertEqual(d.prefix(self.before,self.after,self.plan,109),self.text)
    def test_previous_bytes_mutated(self):
        with self.assertRaises(ValueError):d.prefix(self.before,self.after[:-1]+b'x',self.plan,109)
    def test_no_prefix_rejected(self):
        with self.assertRaises(ValueError):d.prefix(self.before,self.before,self.plan,109)
    def test_wrong_count_rejected(self):
        with self.assertRaises(ValueError):d.prefix(self.before,self.after.replace(b'86/249',b'87/249'),self.plan,109)
    def test_wrong_next_rejected(self):
        with self.assertRaises(ValueError):d.prefix(self.before,self.after.replace(b'index93',b'index94'),self.plan,109)
    def test_scope_words_missing(self):
        with self.assertRaises(ValueError):d.prefix(self.before,self.after.replace('본문 재실행 없음'.encode(),b''),self.plan,109)
    def test_wrong_revision(self):
        with self.assertRaises(ValueError):d.prefix(self.before,self.after,self.plan,110)
    def test_empty_previous_not_claimed(self):
        with self.assertRaises(ValueError):d.prefix(b'',self.after,self.plan,109)


class ProjectionTests(unittest.TestCase):
    def test_four_new_plus_two_original(self):self.assertEqual(d.projection(314)['projected_next_shared_reads'],320)
    def test_near_cap_reports_rotation_needed(self):self.assertFalse(d.projection(718)['next_fits_current_controller'])
    def test_no_720_or_guard_extension(self):
        row=d.projection(314);self.assertEqual(row['unchanged_shared_limit'],720);self.assertFalse(row['CPU_RAM_or600_guard_extended'])
    def test_invalid_preparation_rejected(self):
        for v in (0,True,719,720):
            with self.assertRaises(ValueError):d.projection(v)


class CounterTests(unittest.TestCase):
    def setUp(self):
        self.doc=dict(runtime_contract_executions=558,original_retained_contract_executions=498,
            own_queue_contract_tests_passed=30,synthetic_following_queue_contract_tests_passed=30,
            old_contract_scope='ORIGINAL1555_NO_BODY_REEXECUTION',new_contract_scope='EXPLICIT_SYNTHETIC_CURRENT_AND_FOLLOWING1563',
            receipt_serialization_policy=copy.deepcopy(d.m.r.policy()),monotonic_binding_policy=d.m.review.policy(),
            aggregate_post_reader_connection_verified=True)
    def test_exact558(self):d.counters(self.doc)
    def test_total_missing_or_bool(self):
        for v in (0,True):
            self.doc['runtime_contract_executions']=v
            with self.assertRaises(ValueError):d.counters(self.doc)
    def test_original498_cannot_removed(self):
        self.doc['original_retained_contract_executions']=0
        with self.assertRaises(ValueError):d.counters(self.doc)
    def test_following30_cannot_removed(self):
        self.doc['synthetic_following_queue_contract_tests_passed']=0
        with self.assertRaises(ValueError):d.counters(self.doc)
    def test_domain_not_current_product_claim(self):
        self.doc['old_contract_scope']='CURRENT1563'
        with self.assertRaises(ValueError):d.counters(self.doc)
    def test_serialization_not_replaced(self):
        self.doc['receipt_serialization_policy']={}
        with self.assertRaises(ValueError):d.counters(self.doc)
    def test_monotonic_policy_preserved(self):
        self.doc['monotonic_binding_policy']['failed_reader_counters_not_removed']=False
        with self.assertRaises(ValueError):d.counters(self.doc)
    def test_post_reader_connection_verified(self):
        self.doc['aggregate_post_reader_connection_verified']=False
        with self.assertRaises(ValueError):d.counters(self.doc)
