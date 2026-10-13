import copy
import json
import unittest
import audit_r07_closing_workload as a


class WorkloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prep=json.loads((a.c.ROOT/a.b.BASE_PREP['path']).read_text(encoding='utf-8'))
        cls.expected=a.v.pins(prep['whole_inputs']);cls.exe=prep['binding']['compiled_test_executable_pin']
        cls.engine={n:dict(path=n,bytes=10,sha256='a'*64) for n in (a.b.SELF,a.b.TEST)}
    def test_exact_scope_and_closed_non_promotion(self):
        row=a.classify(self.expected,self.exe,self.engine)
        self.assertEqual(row['historical_EXE_count'],67);self.assertEqual(row['actual_case_runtime_input_count'],1405)
        self.assertTrue(row['historical_pins_are_sealed_references_not_current_byte_verification'])
        self.assertTrue(row['workload_inventory_not_permission_to_skip_whole_gate'])
    def test_historical_read_cost_is_not_current_EXE_cost(self):
        row=a.classify(self.expected,self.exe,self.engine)
        self.assertEqual(row['runtime_current_EXE_bytes'],14216704)
        self.assertEqual(row['historical_only_EXE_bytes_one_pass'],361560576)
        self.assertEqual(row['historical_only_EXE_bytes_two_passes'],723121152)
    def test_changed_executable_binding_is_rejected(self):
        exe=copy.deepcopy(self.exe);exe['sha256']='b'*64
        with self.assertRaises(ValueError):a.classify(self.expected,exe,self.engine)
    def test_non_EXE_or_engine_dropped_scope_rejected(self):
        expected=dict(self.expected);name=next(n for n in expected if not n.endswith('.exe'));expected.pop(name)
        with self.assertRaises(ValueError):a.classify(expected,self.exe,self.engine)
        with self.assertRaises(ValueError):a.classify(self.expected,self.exe,{})


if __name__=='__main__':unittest.main()
