import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_diagnostic_connection_v3 as connector
from test_native_diagnostic_connection_v1 import fixture


def current():
    row=fixture();info=row["serial_CPU_attribution"]
    info["backend"]=connector.BACKEND
    info["native_backend_connection"]["native_backend_source"]="tools/p09/native_process_cpu_attribution_v3.py"
    p=info["probes"][0]
    p.update(backend=connector.BACKEND,capture_api_source="tools/p09/bounded_cpu_attribution_probe_v2.py",
     constructor_and_first_capture_share_setup_budget=True,cooperative_capture_deadline_seconds=.05,
     partial_capture_never_baseline_or_valid_sample=True,time_scratch_allocations_per_capture=1,
     create_and_close_in_capture_clock=True,OS_call_hard_preemption_guaranteed=False,
     capture_api_constructor_seconds=.001,cooperative_budget_stops=0,partial_captures_discarded=0)
    return row


class Tests(unittest.TestCase):
    def test_new_backend_and_real_helper_policy_valid(self):
        row=current();before=copy.deepcopy(row)
        self.assertTrue(connector.validate(row)["capture_v2_provenance_and_partial_setup_policy_checked"])
        self.assertEqual(row,before)

    def test_original_checker_all_nonversion_code_fields_unchanged(self):
        old=connector.prior.validate.__code__;new=connector._validate.__code__
        self.assertEqual(new.replace(co_consts=old.co_consts),old)
        self.assertIs(connector._validate.__defaults__,connector.prior.validate.__defaults__)

    def test_historical_v2_stays_original_and_new_not_relabelled(self):
        connector.validate_historical_v2(fixture())
        with self.assertRaises(ValueError):connector.validate(fixture())
        with self.assertRaises(ValueError):connector.validate_historical_v2(current())

    def test_unknown_cleanup_and_changed_budget_still_rejected(self):
        for key,value in (("cleanup_confirmed",False),("maximum_sample_budget_seconds",.1),
                          ("partial_capture_never_baseline_or_valid_sample",False),
                          ("capture_api_source","other.py")):
            row=current();row["serial_CPU_attribution"]["probes"][0][key]=value
            with self.assertRaises(ValueError):connector.validate(row)

    def test_partial_stops_not_silently_valid(self):
        row=current();p=row["serial_CPU_attribution"]["probes"][0]
        p["partial_captures_discarded"]=1
        with self.assertRaises(ValueError):connector.validate(row)
        p["cooperative_budget_stops"]=1
        with self.assertRaises(ValueError):connector.validate(row)
        p["disabled_reason"]="MEASUREMENT_COST_BUDGET_EXCEEDED"
        connector.validate(row)

    def test_actual_private_entry_only_one_dependency_changed(self):
        def run():return attribution
        fn=FunctionType(run.__code__,dict(attribution=object()))
        api=NS(run_owned=fn);state=dict(actual_local_bindings=0);calls=[]
        old=NS(bind_entry=lambda api,raw:calls.append("old_pins_first"))
        backend=NS(SELF="tools/p09/native_process_cpu_attribution_v3.py",windows_type=lambda *a:None,
         close=lambda *a:True,summary=lambda *a:dict(backend=connector.BACKEND))
        connector.connect_entry(api,b"raw",old,backend,state)
        self.assertEqual(calls,["old_pins_first"])
        self.assertEqual(state["actual_local_bindings"],1)
        self.assertIs(api.run_owned.__code__,run.__code__)
        self.assertEqual(api.run_owned().summary([])["backend"],connector.BACKEND)


if __name__=="__main__":unittest.main()
