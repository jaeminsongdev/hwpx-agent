"""Isolated connection contracts. No fake actual-source PASS saved or accepted."""
import copy
import unittest
from unittest.mock import patch
import close_flat_case129_preserved_source_observer_v2 as subject

PREVIOUS = None
CHECKPOINT = lambda: None


class ConnectionContracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
    def test_all1904_previous_inputs_retained_with_new_disjoint_pin(self):
        extra = dict(path="tools/p09/connection-fixture-only.py",bytes=1,sha256="a"*64)
        result = subject.retain_previous_scope({extra["path"]:extra},PREVIOUS)
        self.assertEqual(len(result),1905)
        self.assertTrue(all(result[p["path"]]==p for p in PREVIOUS["required_source_pins"]))
    def test_conflicting_input_is_not_rebased(self):
        pin=dict(PREVIOUS["required_source_pins"][0],sha256="a"*64)
        with self.assertRaises(ValueError):
            subject.retain_previous_scope({pin["path"]:pin},PREVIOUS)
    def test_nonempty_old_handle_cannot_start_new_frame(self):
        row=dict(PREVIOUS,source_frame=copy.deepcopy(PREVIOUS["source_frame"]))
        row["source_frame"]["handles"]["input_lock_handles_remaining"]=1
        with self.assertRaises(ValueError):
            subject.retain_previous_scope({},row)
    def test_failed_source_state_is_not_promoted(self):
        row=dict(PREVIOUS,state=subject.original.PASS)
        with self.assertRaises(ValueError):
            subject.retain_previous_scope({},row)
    def test_exact_run_code_and_original_module_classes_unchanged(self):
        windows,guard=subject.c.Windows,subject.a.Guard
        execute=subject.project_run(object,lambda *x:None,lambda x:x)
        self.assertIs(execute.__code__,subject.original.run.__code__)
        self.assertIs(subject.c.Windows,windows);self.assertIs(subject.a.Guard,guard)
    def test_guard_cleanup_still_runs_and_reports_optional_close_failure(self):
        class Base:
            def __init__(self):
                self.closed=False
            def close(self):
                self.closed=True
        closed={}
        Guard=subject.guard_type(Base,object,[],closed)
        self.assertIs(Guard.__init__.__code__,Base.__init__.__code__)
        guard=Guard()
        with patch.object(subject.observer,"close",return_value=False):
            guard.close()
        self.assertTrue(guard.closed);self.assertFalse(closed["PDH_cleanup_confirmed"])
    def test_pdh_failure_demotes_success_never_promotes_old_failure(self):
        with patch.object(subject.observer,"summary",return_value={"fixture":True}):
            out=dict(state=subject.original.PASS,independent_source_frame_qualified=True)
            subject.decorate_document(out,[],{"PDH_cleanup_confirmed":False},{"connection_qualification_pin":{"fixture":True}})
        self.assertEqual(out["state"],"FAILED_NOT_QUALIFIED")
        self.assertFalse(out["independent_source_frame_qualified"])
    def test_original_failure_and_resource_types_preserved_by_decoration(self):
        original=dict(state="FAILED_NOT_QUALIFIED",error_code="ORIGINAL_STOP",
            independent_source_frame_qualified=False,CPU_max=0.0,resource_samples=[{"cpu":0.0}])
        out=dict(original)
        with patch.object(subject.observer,"summary",return_value={"fixture":True}):
            subject.decorate_document(out,[],{"PDH_cleanup_confirmed":True},{"connection_qualification_pin":{"fixture":True}})
        for key,value in original.items():
            self.assertEqual(out[key],value);self.assertIs(type(out[key]),type(value))
        self.assertFalse(out["source_observer_epoch"]["old_failed_root_promoted"])
    def test_scope_budget_keeps_original_rates_margins_deadline_pdh(self):
        model=subject.original.source_budget(subject.scope.pins(PREVIOUS["required_source_pins"]))
        self.assertEqual(model["unallocated_margin_seconds"],60)
        self.assertEqual(model["unchanged_lock_deadline_seconds"],600)
        self.assertEqual(model["selected_acquisition_rate_per_second"],14)
        self.assertEqual(model["additional_serial_PDH_maximum_sample_budget_seconds"],2.05)
        self.assertEqual(model["final_postcleanup_distinct_sample_wait_allowance_seconds"],.5)
    def test_wrong_attempt_cannot_retry_or_overwrite(self):
        with self.assertRaisesRegex(ValueError,"ONE_EXPLICIT_SECOND_ATTEMPT"):
            subject.run("source",3,{})
