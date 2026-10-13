from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_case158_attempt_v7 as m
import reviewed_runtime_attempt_v2 as retry


class Tests(unittest.TestCase):
    def test_root_task_public_and_identity_codes_match_run005(self):
        new=m.identity(retry)
        self.assertEqual(new.task(158),m.TASK)
        self.assertEqual(new.public_run(158,5),1)
        for name in ("root_path","task","public_run","validate_actual"):
            self.assertIs(getattr(new,name).__code__,getattr(retry,name).__code__)
    def test_old_physical_attempts_and_boolean_rejected(self):
        new=m.identity(retry)
        for n in (True,1,2,3,4,6):
            with self.assertRaises(ValueError):new.public_run(158,n)
    def test_original_historical_attempts_not_relabelled(self):
        new=m.identity(retry)
        for index in (153,154,157,159):self.assertEqual(new.task(index),retry.task(index))
        self.assertEqual(retry.physical_run(158),1)
    def test_worker_task005_connector_does_not_mutate_original(self):
        self.assertEqual(m.connect_worker.__globals__["TASK"],m.TASK)
        self.assertEqual(m.original.connect_worker.__globals__["TASK"],"case158-current-r004-tests")


if __name__=="__main__":unittest.main()
