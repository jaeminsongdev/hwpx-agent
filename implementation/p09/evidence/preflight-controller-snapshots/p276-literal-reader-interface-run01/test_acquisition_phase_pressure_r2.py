"""P276 신규6. 원P27532는 실행기에서 별도로 보존한다."""
import copy
import unittest
import qualify_acquisition_phase_pressure_r2 as m
FIXTURES=None


class LiteralQualificationTests(unittest.TestCase):
    def setUp(self):self.root,self.body,self.prototype=copy.deepcopy(FIXTURES)
    def test_literal_complete_old_pair_not_new_runtime(self):
        plan,required=m.accepted(self.root,self.body);self.assertEqual(plan['runtime_source_qualified_individual_cases'],88)
        self.assertEqual(len(required),1579);self.assertFalse(self.root['full249_current_qualified'])
    def test_declared_old_pair_not_only_fields(self):
        self.root['closing_component']['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'][0]['bytes']+=1
        with self.assertRaises(ValueError):m.accepted(self.root,self.body)
    def test_gate_or_wrong_case_not_promoted(self):
        self.root['selected_test_index']=95
        with self.assertRaises(ValueError):m.accepted(self.root,self.body)
    def test_original_support_stop_not_native_pass(self):
        row=m.support_failure(self.prototype);self.assertFalse(row['original_small_native_executed'])
        self.prototype['small_native_probe']={}
        with self.assertRaises(ValueError):m.support_failure(self.prototype)
    def test_support_fresh_budget_not_fullscope_claim(self):
        io=dict(bound_inputs=26,read_passes=52,bytes_read=3000000,finished=True,final_fresh_hashes=26)
        m.read_budget(io);io['final_fresh_hashes']=25
        with self.assertRaises(ValueError):m.read_budget(io)
    def test_future_full1585_keeps_original600_and720(self):
        row=m.future_budget();self.assertEqual(row['full_scope_upper_inputs'],1585)
        self.assertEqual(row['original_IO_scope_seconds'],600);self.assertEqual(row['original_shared_metadata_read_limit'],720)
        self.assertLess(row['nominal_seconds'],600);self.assertFalse(row['input_or_byte_checks_removed'])


if __name__=='__main__':unittest.main()
