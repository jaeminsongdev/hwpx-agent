import unittest
from unittest.mock import patch
import run_observed_writer_inventory as d
class ObservedInventoryTests(unittest.TestCase):
    def test_stopped_or_old_build_rejected(self):
        for state in ('FAILED_NOT_ACCEPTED','PASS_OBSERVED_WRITER_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE'):
            with self.assertRaises(ValueError):d.closing_scope({'state':state})
    def test_exact_r06_worker_and_restore(self):
        before=d.i.EXE_RUN;seen=[]
        with patch.object(d.i,'worker',side_effect=lambda task:seen.append((task,d.i.EXE_RUN,d.d.c.TARGET)) or 0):
            self.assertEqual(d.worker(d.i.task_for(6)),0)
        self.assertEqual(seen,[(d.i.task_for(6),6,d.d.TARGET)]);self.assertEqual(before,d.i.EXE_RUN)
    def test_foreign_worker_cannot_launch(self):
        with patch.object(d.i,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.worker(d.i.task_for(5))
if __name__=='__main__':unittest.main()
