import copy
import math
from pathlib import Path
import sys
from types import FunctionType
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_case112_current_epoch as a
import strict_product_window_connection_v1 as original
import successor_strict_window_v1 as m


def fixture(index=159):
    # Synthetic predicate fixture, never a runtime receipt or accepted case.
    return dict(selected_test_index=index,source_frame=dict(frame_state="COMMITTED",registered_live_frame=False,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True),
        complete_runtime_budget=dict(product_allowance_seconds=15,strict_GO_to_complete_capture_window_seconds=15,
        actual_window_binding_and_complete_capture_required_before_acceptance=True,unallocated_margin_seconds=60,
        additional_early_source_wait_allowance_seconds=11,unchanged_lock_deadline_seconds=600,
        input_scope_reduction_or_rate_change=False),strict_product_window=dict(maximum_GO_to_complete_capture_seconds=15,
        original_GO_bytes_retained=True,actual_GO_writes=1,actual_capture_count=1,
        actual_complete_capture_within_window=True,stopped=False,added_sampler_thread_or_process_query=False,
        capture_constructor_window_check_failed=False,original_source_scope_rates_CPU_RAM600_and_1200_retained=True,
        blocking_OS_latency_hard_preemption_guaranteed=False,capture_and_GO_actual_connection_required_before_acceptance=True,
        queue_advance_authorized=False,PC_freeze_resolved=False,GO_to_complete_capture_elapsed_seconds=1.5,
        actual_GO_to_last_window_check_seconds=1.5))


class Tests(unittest.TestCase):
    def setUp(self):self.check,self.proof=m.connect(original.check_evidence)
    def test_nominal_synthetic_fixture_same_original_result(self):
        self.assertEqual(self.check(fixture(),a),original.check_evidence(fixture(157),a))
    def test_inverse_entire_original_code_not_only_disassembly(self):
        c=self.check.__code__
        self.assertEqual(c.replace(co_consts=tuple(157 if type(x) is int and x==159 else x for x in c.co_consts)),original.check_evidence.__code__)
    def test_original_callable_not_mutated(self):
        self.assertIn(157,original.check_evidence.__code__.co_consts)
        self.assertIsNot(self.check.__globals__,original.check_evidence.__globals__)
        self.assertIs(self.check.__closure__,original.check_evidence.__closure__)
        self.assertIs(self.check.__defaults__,original.check_evidence.__defaults__)
        self.assertIs(self.check.__kwdefaults__,original.check_evidence.__kwdefaults__)
    def test_only_exact159_not_bool_float_or_other_cases(self):
        for index in (True,159.0,157,158,160,None):
            with self.subTest(index=index),self.assertRaises(ValueError):self.check(fixture(index),a)
    def test_each_original_scalar_predicate_mutation_rejected(self):
        for section in ("source_frame","complete_runtime_budget","strict_product_window"):
            for key,value in fixture()[section].items():
                if key in ("GO_to_complete_capture_elapsed_seconds","actual_GO_to_last_window_check_seconds"):continue
                bad=(not value) if type(value) is bool else value+1 if type(value) is int else "CLOSED"
                row=fixture();row[section][key]=bad
                before=copy.deepcopy(row)
                with self.subTest(section=section,key=key),self.assertRaises(ValueError):self.check(row,a)
                self.assertEqual(row,before)
                row["selected_test_index"]=157
                with self.assertRaises(ValueError):original.check_evidence(row,a)
    def test_elapsed_strict_boundary_and_nonfinite_rejected(self):
        for elapsed in (-.1,15,16,math.inf,math.nan,"1.5",True):
            row=fixture();row["strict_product_window"].update(GO_to_complete_capture_elapsed_seconds=elapsed,actual_GO_to_last_window_check_seconds=elapsed)
            with self.subTest(elapsed=elapsed),self.assertRaises(ValueError):self.check(row,a)
    def test_last_check_same_type_and_same_time_required(self):
        for last in (1,1.4,1.6,None):
            row=fixture();row["strict_product_window"]["actual_GO_to_last_window_check_seconds"]=last
            with self.subTest(last=last),self.assertRaises(ValueError):self.check(row,a)
    def test_fifteen_not_twenty_seconds(self):
        row=fixture();row["strict_product_window"].update(GO_to_complete_capture_elapsed_seconds=19.,actual_GO_to_last_window_check_seconds=19.)
        with self.assertRaises(ValueError):self.check(row,a)
    def test_absent_case_literal_rejected(self):
        with self.assertRaises(ValueError):m.connect(lambda row,a:None)
    def test_ambiguous_inverse_rejected(self):
        def wrong(row,a):return (157,159)
        # Put exact literals at the top level, matching the original shape.
        def template(row,a):return row==157
        code=template.__code__.replace(co_consts=template.__code__.co_consts+(159,))
        fn=FunctionType(code,template.__globals__)
        with self.assertRaises(ValueError):m.connect(fn)
    def test_nominal_row_unmodified(self):
        row=fixture();before=copy.deepcopy(row);self.check(row,a);self.assertEqual(row,before)
    def test_connection_never_authorizes_GO(self):
        self.assertIs(self.proof["actual159_product_or_GO_qualified"],False)


if __name__=="__main__":unittest.main()
