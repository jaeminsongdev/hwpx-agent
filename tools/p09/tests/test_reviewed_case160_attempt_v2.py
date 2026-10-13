from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_case160_attempt_v2 as m
import reviewed_runtime_attempt_v2 as original


class Tests(unittest.TestCase):
    def test_all160_identities_agree_with_run002(self):
        new=m.identity(original)
        self.assertEqual(new.root_path(NS(index=160)),m.ROOT)
        self.assertEqual(new.task(160),m.TASK)
        self.assertEqual(new.public_run(160,3),1)
    def test_run001_and_boolean_public_runs_rejected(self):
        new=m.identity(original)
        for value in (1,True,2):
            with self.assertRaises(ValueError):new.public_run(160,value)
    def test_historical_cases_preserve_original_physical_attempts(self):
        new=m.identity(original)
        for index in (153,154,155,157,159,249):
            self.assertEqual(new.physical_run(index),original.physical_run(index))
            self.assertEqual(new.task(index),original.task(index))
            self.assertEqual(new.root_path(NS(index=index)),original.root_path(NS(index=index)))
    def test_whole_original_identity_function_codes_are_retained(self):
        new=m.identity(original)
        for name in ("root_path","task","public_run","validate_actual"):
            self.assertIs(getattr(new,name).__code__,getattr(original,name).__code__)
    def test_original_namespace_unmodified(self):
        m.identity(original)
        self.assertEqual(original.physical_run(160),1)
        self.assertEqual(original.task(160),"case160-current-r001-tests")
    def test_observation_not_relabelled_and_wrong_task_rejected(self):
        new=m.identity(original);row=dict(selected_test_index=160,task="case160-current-r001-tests")
        before=dict(row)
        with self.assertRaises(ValueError):new.validate_actual(row,NS(index=160),dict(path=m.ROOT))
        self.assertEqual(row,before)
    def test_exact_actual_identity_pass_is_not_product_acceptance(self):
        proof=m.identity(original).validate_actual(dict(selected_test_index=160,task=m.TASK),
            NS(index=160),dict(path=m.ROOT))
        self.assertEqual(proof["physical_product_run"],3)
        self.assertFalse(proof["full_product_oracle_replaced"])
    def test_wrong_root_or_boolean_case_is_rejected(self):
        new=m.identity(original)
        for row,pin in ((dict(selected_test_index=160,task=m.TASK),dict(path="run001")),
                        (dict(selected_test_index=True,task=m.TASK),dict(path=m.ROOT))):
            with self.assertRaises(ValueError):new.validate_actual(row,NS(index=160),pin)


if __name__=="__main__":unittest.main()
