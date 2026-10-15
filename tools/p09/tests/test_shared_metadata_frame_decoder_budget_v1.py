"""Original real budget objects with deterministic bounded clocks, not Native."""
import unittest
from unittest.mock import patch
import shared_metadata_frame_decoder_budget_v1 as m
import runtime_envelope_physical_io_v1 as physical

CHECKPOINT=lambda:None


class Tests(unittest.TestCase):
    def setUp(self):CHECKPOINT();self.clock=[0.0]
    def tearDown(self):CHECKPOINT()
    def budget(self,checkpoint=CHECKPOINT):
        return physical.DecoderBudget(checkpoint,clock=lambda:self.clock[0])
    def work(self,budget,seconds):
        def operation(check):self.clock[0]+=seconds;check();return "fresh"
        return budget.run(operation)
    def test_sum_under_five_with_original_type_and_run_identity(self):
        shared=m.SharedBudget();meta=self.budget();frame=self.budget();code=meta.run.__func__.__code__
        shared.attach("metadata",meta);self.work(meta,1.4);shared.attach("frame",frame);self.work(frame,2.5)
        self.assertIs(type(frame),physical.DecoderBudget)
        self.assertIs(frame.run.__func__.__code__,code)
        self.assertAlmostEqual(shared.evidence()["total_decoder_work_seconds"],3.9)
    def test_each_individually_under_five_but_sum_over_five_rejected(self):
        shared=m.SharedBudget();meta=self.budget();shared.attach("metadata",meta);self.work(meta,3.0)
        frame=self.budget();shared.attach("frame",frame)
        with self.assertRaisesRegex(ValueError,"STOP_SHARED_METADATA_FRAME_DECODER5"):self.work(frame,2.1)
        self.assertEqual(frame.completed,0);self.assertIsNotNone(frame.error)
    def test_active_work_is_in_sum_not_only_completed_work(self):
        shared=m.SharedBudget();meta=self.budget();shared.attach("metadata",meta);self.work(meta,4.0)
        frame=self.budget();shared.attach("frame",frame)
        with self.assertRaisesRegex(ValueError,"STOP_SHARED_METADATA_FRAME_DECODER5"):self.work(frame,1.01)
    def test_frame_counts_remain_frame_only(self):
        shared=m.SharedBudget();meta=self.budget();shared.attach("metadata",meta)
        self.work(meta,.1);self.work(meta,.1)
        outer=self
        class OriginalFrame:
            def __init__(self):self.decoder_budget=outer.budget()
            def summary(self):return dict(original=True,aggregate_envelope_decoder=self.decoder_budget.evidence())
        original_code=OriginalFrame.__init__.__code__
        Frame=m.frame_type(object,object(),lambda *args:OriginalFrame,shared)
        instance=Frame();frame=instance.decoder_budget;self.work(frame,.1)
        self.assertEqual((meta.completed,frame.completed),(2,1))
        self.assertEqual(frame.evidence()["completed_decodes"],1)
        self.assertIs(OriginalFrame.__init__.__code__,original_code)
        self.assertTrue(instance.summary()["original"])
        self.assertEqual(instance.summary()["aggregate_envelope_decoder"]["completed_decodes"],1)
        self.assertEqual(instance.summary()["shared_metadata_frame_decoder"]["metadata_completed"],2)
    def test_duplicate_nonfresh_budget_rejected(self):
        shared=m.SharedBudget();meta=self.budget();shared.attach("metadata",meta)
        with self.assertRaises(ValueError):shared.attach("metadata",self.budget())
        frame=self.budget();self.work(frame,.1)
        with self.assertRaises(ValueError):shared.attach("frame",frame)
    def test_original_guard_failure_has_priority(self):
        def fail():raise ValueError("fixture_original_guard")
        shared=m.SharedBudget();meta=self.budget(fail);shared.attach("metadata",meta)
        with self.assertRaisesRegex(ValueError,"fixture_original_guard"):meta.check()
        self.assertEqual(shared.checks,0)
    def test_restore_original_check_without_sampling_and_no_resume(self):
        shared=m.SharedBudget();meta=self.budget();original=meta.check;shared.attach("metadata",meta)
        shared.restore();self.assertIs(meta.check,shared.original_checks["metadata"])
        self.assertIs(meta.check.__func__,original.__func__);self.assertIs(meta.check.__self__,meta)
        with self.assertRaises(ValueError):shared.check()
    def test_wrong_owner_rejected(self):
        shared=m.SharedBudget();meta=self.budget();meta.owner=(-1,-1)
        with self.assertRaises(ValueError):shared.attach("metadata",meta)


if __name__=="__main__":unittest.main()
