import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_diagnostic_connection_v4 as m
from test_native_diagnostic_connection_v3 import current as v3

def current():
    row=v3();info=row["serial_CPU_attribution"];p=info["probes"][0]
    info["backend"]=p["backend"]=m.BACKEND
    info["native_backend_connection"]["native_backend_source"]="tools/p09/native_process_cpu_attribution_v4.py"
    info.update(warning_optional_attribution_suppressed=True,warning_suppression_percent=75)
    p.update(warning_optional_attribution_suppressed=True,warning_suppression_percent=75,
       warning_attribution_suppressions=0,original_low_load_sample_code_retained=True,
       suppressed_result_is_unavailable_not_zero=True,suppression_does_not_change_original_guard_decisions=True,
       suppression_does_not_close_reset_or_rebaseline_probe=True)
    return row

def add_suppression(row,cpu=90.):
    sample=copy.deepcopy(row["samples"][0]);sample["system_cpu_percent"]=cpu
    sample["serial_cpu_attribution"]=dict(available=False,reason=m.SUPPRESSED,values=None,
      fresh_for_this_original_resource_sample=True,optional_native_query_attempted=False,
      original_K32_CPU_RAM_decisions_replaced=False,diagnostic_measurement_fresh=False)
    row["samples"].append(sample);row["serial_CPU_attribution"]["probes"][0]["warning_attribution_suppressions"]=1
    return row

class Tests(unittest.TestCase):
    def test_valid_v4_full_prior_capture_policy_and_no_row_mutation(self):
        row=add_suppression(current());before=copy.deepcopy(row)
        self.assertTrue(m.validate(row)["explicit_warning_suppression_not_a_fresh_native_measurement"])
        self.assertEqual(row,before)
    def test_invalid_warning_or_query_or_fresh_measurement_rejected(self):
        for cpu in (20.,True,101.):
            with self.assertRaises(ValueError):m.validate(add_suppression(current(),cpu))
        for key,value in (("optional_native_query_attempted",True),("values",0),("diagnostic_measurement_fresh",True)):
            row=add_suppression(current());row["samples"][-1]["serial_cpu_attribution"][key]=value
            with self.assertRaises(ValueError):m.validate(row)
    def test_source_enum_only_code_change_and_original_capture_policy_code(self):
        old=m.prior._validate.__code__
        self.assertEqual(m._validate.__code__.replace(co_consts=old.co_consts),old)
        self.assertIs(m._capture_policy.__code__,m.prior.validate.__code__)
    def test_old_v3_v2_not_relabelled_or_accepted_as_v4(self):
        m.validate_historical_v3(v3())
        with self.assertRaises(ValueError):m.validate(v3())
        with self.assertRaises(ValueError):m.validate_historical_v3(current())
    def test_counts_and_original_cleanup_budget_checks_not_weakened(self):
        row=add_suppression(current());row["serial_CPU_attribution"]["probes"][0]["warning_attribution_suppressions"]=2
        with self.assertRaises(ValueError):m.validate(row)
        for key,value in (("cleanup_confirmed",False),("maximum_sample_budget_seconds",.1)):
            row=current();row["serial_CPU_attribution"]["probes"][0][key]=value
            with self.assertRaises(ValueError):m.validate(row)
    def test_original_private_entry_binding_only_one_dependency(self):
        def run():return attribution
        api=NS(run_owned=FunctionType(run.__code__,dict(attribution=object())))
        state=dict(actual_local_bindings=0);calls=[]
        old=NS(bind_entry=lambda a,r:calls.append("original-first"))
        b=NS(SELF="tools/p09/native_process_cpu_attribution_v4.py",windows_type=lambda *a:None,
          close=lambda *a:True,summary=lambda *a:dict(backend=m.BACKEND))
        m.connect_entry(api,b"raw",old,b,state)
        self.assertEqual(state["actual_local_bindings"],1);self.assertEqual(calls,["original-first"])
        self.assertIs(api.run_owned.__code__,run.__code__)

if __name__=="__main__":unittest.main()
