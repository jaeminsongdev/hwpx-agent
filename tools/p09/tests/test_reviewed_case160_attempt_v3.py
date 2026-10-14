from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_case160_attempt_v3 as m
import reviewed_runtime_attempt_v2 as original
class Tests(unittest.TestCase):
    def test_all_run004_identities_agree(self):
        api=m.identity(original);self.assertEqual(api.root_path(NS(index=160)),m.ROOT)
        self.assertEqual(api.task(160),m.TASK);self.assertEqual(api.public_run(160,4),1)
    def test_previous_and_bool_public_runs_rejected(self):
        api=m.identity(original)
        for value in (1,2,3,True):
            with self.assertRaises(ValueError):api.public_run(160,value)
    def test_historical_identities_unchanged(self):
        api=m.identity(original)
        for index in (153,154,155,157,159,249):
            self.assertEqual(api.physical_run(index),original.physical_run(index))
            self.assertEqual(api.task(index),original.task(index))
            self.assertEqual(api.root_path(NS(index=index)),original.root_path(NS(index=index)))
    def test_original_function_codes_retained(self):
        api=m.identity(original)
        for name in ("root_path","task","public_run","validate_actual"):
            self.assertIs(getattr(api,name).__code__,getattr(original,name).__code__)
    def test_default_namespace_not_modified(self):
        m.identity(original);self.assertEqual(original.physical_run(160),1)
        self.assertEqual(original.task(160),"case160-current-r001-tests")
    def test_observation_not_relabelled(self):
        api=m.identity(original);row=dict(selected_test_index=160,task="case160-current-r003-tests");before=dict(row)
        with self.assertRaises(ValueError):api.validate_actual(row,NS(index=160),dict(path=m.ROOT))
        self.assertEqual(row,before)
    def test_correct_identity_is_not_product_acceptance(self):
        proof=m.identity(original).validate_actual(dict(selected_test_index=160,task=m.TASK),NS(index=160),dict(path=m.ROOT))
        self.assertEqual(proof["physical_product_run"],4);self.assertFalse(proof["full_product_oracle_replaced"])
    def test_wrong_root_or_bool_case_rejected(self):
        api=m.identity(original)
        for row,pin in ((dict(selected_test_index=160,task=m.TASK),dict(path="run003")),
                        (dict(selected_test_index=True,task=m.TASK),dict(path=m.ROOT))):
            with self.assertRaises(ValueError):api.validate_actual(row,NS(index=160),pin)
if __name__=="__main__":unittest.main()
