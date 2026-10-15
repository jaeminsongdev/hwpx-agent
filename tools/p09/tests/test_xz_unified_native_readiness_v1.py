"""Synthetic readiness boundaries only; no Native/Frame/GO or receipt writes."""
import copy
from types import SimpleNamespace as NS
import unittest


class Tests(unittest.TestCase):
    def fixture(self):
        pref=MODULE.PREFIX+"successor-recovery-preflight-run008-attempt015.v1.json"
        qual=MODULE.PREFIX+"successor-recovery-dispatch-qualification-run008-attempt008.v1.json"
        pins={pref:dict(path=pref,bytes=1,sha256="0"*64),qual:dict(path=qual,bytes=1,sha256="1"*64)}
        common=dict(index=165,physical_run=8,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
            fresh_inputs=1,final_fresh_hashes=1,code_pin=copy.deepcopy(BINDING.WHOLE_CODE))
        p=dict(common,state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",product_worker_or_Native_frame_executed=False)
        q=dict(common,state="PASS_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",product_or_Native_executed=False,
            contracts=dict(run=6,errors=0,failures=0,skipped=0),runtime_default_imports=60,actual_Native_helper_count=64,
            preflight_pin=copy.deepcopy(pins[pref]),complete_runtime_budget=dict(unchanged_lock_deadline_seconds=600,
                unallocated_margin_seconds=60,aggregate_envelope_decoder_allowance_seconds=5,predicted_runtime_combined_seconds=580.))
        records={pref:p,qual:q}
        return NS(json=lambda name:records[name],snapshots=pins),p,q

    def test_exact_metadata_reference_only_not_product_authorization(self):
        reader,p,q=self.fixture();result=MODULE.readiness(reader,API,BINDING,15,8)
        self.assertEqual(result.preflight_pin,q["preflight_pin"])
        self.assertFalse(p["GO_authorized"]);self.assertFalse(q["product_or_Native_executed"])

    def test_old_code_reference_is_not_promoted(self):
        for key in ("preflight","qualification"):
            reader,p,q=self.fixture();row=p if key=="preflight" else q
            row["code_pin"]=dict(BINDING.WHOLE_CODE,path=BINDING.WHOLE_CODE["path"].replace("006","001"))
            with self.assertRaises(ValueError):MODULE.readiness(reader,API,BINDING,15,8)

    def test_different_preflight_bytes_rejected(self):
        reader,p,q=self.fixture();q["preflight_pin"]["sha256"]="f"*64
        with self.assertRaises(ValueError):MODULE.readiness(reader,API,BINDING,15,8)

    def test_actual_native_helper64_bound_is_not_raised(self):
        reader,p,q=self.fixture();q["actual_Native_helper_count"]=65
        with self.assertRaises(ValueError):MODULE.readiness(reader,API,BINDING,15,8)

    def test_failed_or_incomplete_closure_is_not_readiness(self):
        for field,value in (("cleanup_confirmed",False),("final_fresh_hashes",0),("fresh_inputs",True)):
            reader,p,q=self.fixture();q[field]=value
            with self.assertRaises(ValueError):MODULE.readiness(reader,API,BINDING,15,8)

    def test_unchanged_budget_margin_decoder_and_real_finite_total(self):
        edits=[("unchanged_lock_deadline_seconds",601),("unallocated_margin_seconds",0),
            ("aggregate_envelope_decoder_allowance_seconds",6),("predicted_runtime_combined_seconds",601),
            ("predicted_runtime_combined_seconds",-1),("predicted_runtime_combined_seconds",float("nan")),
            ("predicted_runtime_combined_seconds",True)]
        for field,value in edits:
            reader,p,q=self.fixture();q["complete_runtime_budget"][field]=value
            with self.subTest(field=field,value=str(value)):
                with self.assertRaises(ValueError):MODULE.readiness(reader,API,BINDING,15,8)
