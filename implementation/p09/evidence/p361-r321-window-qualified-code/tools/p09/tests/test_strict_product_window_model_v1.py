import ast
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import strict_product_window_model_v1 as m
import native_pressure_failfast_v1 as policy
import current_stored_runtime_scope as scope

ROOT=Path(__file__).resolve().parents[3]
RAW=(ROOT/policy.MODEL_PIN["path"]).read_bytes()
def old_model():
    node=next(n for n in ast.parse(RAW.decode()).body if isinstance(n,ast.FunctionDef) and n.name=="model")
    env=dict(require=policy.require)
    exec(compile(ast.Module(body=[node],type_ignores=[]),policy.MODEL_PIN["path"],"exec",dont_inherit=True),env)
    return policy.model_projection(env["model"],RAW,scope)
def pins(size=1048576):return {n:dict(path=n,bytes=size,sha256="0"*64) for n in ("a.exe","a.rs")}

class Tests(unittest.TestCase):
    def test_only_product_reservation5_reduced_other_terms_identical(self):
        old=old_model();new,proof=m.project(old,RAW,policy,scope);before=old(pins(),167);after=new(pins(),167)
        self.assertEqual(before["predicted_runtime_combined_seconds"]-after["predicted_runtime_combined_seconds"],5)
        self.assertEqual(after["product_allowance_seconds"],15)
        for key,value in before.items():
            if key not in ("product_allowance_seconds","predicted_runtime_combined_seconds","nominal_fits_unchanged_deadline"):
                self.assertEqual(after[key],value,key)
        self.assertIs(proof["GO_authorized"],False)
    def test_unchanged600_rejects_overbudget(self):
        new,_=m.project(old_model(),RAW,policy,scope)
        with self.assertRaises(ValueError):new(pins(300*1048576),167)
    def test_original_byte_acquisition_inventory_early11_margin60_and_PDH_kept(self):
        new,_=m.project(old_model(),RAW,policy,scope);row=new(pins(),167)
        self.assertEqual(row["selected_acquisition_rate_per_second"],14)
        self.assertEqual(row["final_inventory_pacing_seconds"],167/20)
        self.assertEqual(row["additional_early_source_wait_allowance_seconds"],11)
        self.assertEqual(row["unallocated_margin_seconds"],60)
        with self.assertRaises(ValueError):new(pins(),167,PDH_seconds=0)
    def test_changed_raw_or_wrong_original_model_rejected(self):
        with self.assertRaises(ValueError):m.project(old_model(),RAW+b"\n",policy,scope)
        with self.assertRaises(ValueError):m.project(lambda *a:None,RAW,policy,scope)
    def test_actual_window_binding_required_no_scope_or_GO_authority(self):
        new,_=m.project(old_model(),RAW,policy,scope);row=new(pins(),167)
        self.assertIs(row["actual_window_binding_and_complete_capture_required_before_acceptance"],True)
        self.assertIs(row["input_scope_reduction_or_rate_change"],False)
        self.assertIs(row["GO_authorized"],False)

if __name__=="__main__":unittest.main()
