import copy
import unittest
import recovery_workflow_plan_v1 as m


class Tests(unittest.TestCase):
    def cost_fixture(self):
        return {path:dict(path=path,bytes=size,sha256="a"*64) for path,size in (
            ("target/public.exe",1048576),("fixtures/public.bin",2097152))}

    def test_cost_has_same_original_serial_rates_and_allowances(self):
        row=m.declared_cost(self.cost_fixture(),10)
        self.assertEqual(row["directories"],3)
        expected=5/14+2+2+60+10+3+167/20+11+5+2.05+.5+5
        self.assertAlmostEqual(row["predicted_seconds"],expected)

    def test_only_product_window_difference_is_five_seconds(self):
        rows=self.cost_fixture()
        self.assertAlmostEqual(m.declared_cost(rows,15)["predicted_seconds"]-
            m.declared_cost(rows,10)["predicted_seconds"],5)
        for value in (True,0,9,11):
            with self.assertRaises(ValueError):m.declared_cost(rows,value)

    def test_adding_required_input_never_lowers_declared_cost(self):
        rows=self.cost_fixture();before=m.declared_cost(rows,10)["predicted_seconds"]
        rows["fixtures/extra.bin"]=dict(path="fixtures/extra.bin",bytes=1,sha256="b"*64)
        after=m.declared_cost(rows,10)["predicted_seconds"]
        self.assertAlmostEqual(after-before,1/14+1/1048576)

    def test_metadata_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):m.unique_json([("public",1),("public",2)])

    def test_actual_metadata_lower_bound_is_not_whole_qualification_or_GO(self):
        import conservative_maintenance as c
        result=m.budget_lower_bound(m.BoundedReader(c.ROOT))
        self.assertEqual(result["mandatory_lower_bound"]["inputs"],3024)
        self.assertAlmostEqual(result["mandatory_lower_bound"]["predicted_seconds"],594.2498719079153)
        self.assertTrue(result["future_pref_qualification_and_other_inputs_not_included"])
        self.assertFalse(result["GO_authorized"])

    def test_modified_failed_receipt_cannot_be_used_for_cost_audit(self):
        import conservative_maintenance as c
        class Tampered(m.BoundedReader):
            def chunks(self,name):
                if name==m.PREFIX+"current-runtime-run007.v1.json":yield b"{}"
                else:yield from super().chunks(name)
        with self.assertRaisesRegex(ValueError,"EXACT_COST_METADATA_PIN"):
            m.budget_lower_bound(Tampered(c.ROOT))

    def test_setup_only_failure_consumes_its_attempt_without_overwrite(self):
        existing={m.PREFIX+"successor-recovery-preflight-run008-attempt001.v1.json",
            m.PREFIX+"closed-recovery-io-preflight-setup-run008-attempt003.v1.json"}
        result=m.discover_attempts(existing.__contains__)
        self.assertEqual(result,dict(consumed_attempts=[1,3],latest_attempt=3,next_unused_attempt=4))

    def test_missing_whole_preflight_distinguishes_failed_or_pending_setup(self):
        stage=m.stages(3)[-1];stage=dict(stage,dependencies=())
        for setup,expected in ((dict(state="FAILED_SETUP",error_code="CPU_STOP"),"FAILED_SETUP_NO_PREFLIGHT"),
            (dict(state="PASS_SETUP"),"SETUP_EXISTS_PREFLIGHT_MISSING")):
            def read(path):
                if path==stage["path"]:raise FileNotFoundError
                return setup
            result=m.analyze([stage],read,lambda path:None)
            self.assertEqual(result["stages"][0]["status"],expected)
            self.assertFalse(result["GO_authorized"])

    def test_consumed_slots_are_bounded_and_error_values_are_not_echoed(self):
        self.assertEqual(m.discover_attempts(lambda path:False)["next_unused_attempt"],1)
        self.assertIsNone(m.discover_attempts(lambda path:True)["next_unused_attempt"])
        first_eight=lambda path:any(f"-attempt{i:03}.v1.json" in path for i in range(1,9))
        self.assertEqual(m.discover_attempts(first_eight)["next_unused_attempt"],9)
        self.assertTrue(m.stages(16)[-1]["path"].endswith("attempt016.v1.json"))
        self.assertIsNone(m.safe_error(dict(error_code="private arbitrary log text")))
        self.assertIsNone(m.safe_error(dict(error_code=["private"])))

    def data(self):
        pin=dict(path="tools/p09/public.py",bytes=1,sha256="a"*64)
        receipt=dict(state="CLOSED",cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
            fresh_inputs=1,final_fresh_hashes=1,source_pins=[pin])
        rows=[dict(name="code",path="evidence/code.json",state="CLOSED",dependencies=()),
            dict(name="pref",path="evidence/pref.json",state="CLOSED",dependencies=("code",))]
        return rows,receipt,pin
    def test_shared_input_hashed_once_and_no_runtime_authority(self):
        rows,receipt,pin=self.data();calls=[]
        def signature(path):calls.append(path);return pin
        report=m.analyze(rows,lambda path:receipt,signature)
        self.assertEqual(calls,[pin["path"]]);self.assertEqual(report["reusable_stages"],2)
        self.assertFalse(report["GO_authorized"]);self.assertFalse(report["queue_advance_authorized"])
        self.assertTrue(report["actual_stage_admission_must_recheck_all_inputs"])
    def test_changed_source_only_invalidates_its_dependent_records(self):
        rows,receipt,pin=self.data();other=copy.deepcopy(receipt)
        other["source_pins"][0]["path"]="tools/p09/other.py"
        records={rows[0]["path"]:receipt,rows[1]["path"]:other}
        report=m.analyze(rows,records.__getitem__,lambda path:dict(pin,path=path,bytes=2) if path==pin["path"] else dict(pin,path=path))
        self.assertEqual([r["status"] for r in report["stages"]],["STALE_INPUTS","WAIT_FOR_DEPENDENCIES"])
    def test_failed_preflight_does_not_invalidate_unchanged_CODE(self):
        rows,receipt,pin=self.data()
        report=m.analyze(rows,lambda path:receipt if path==rows[0]["path"] else dict(state="FAILED",error_code="CPU_STOP"),lambda path:pin)
        self.assertEqual([r["status"] for r in report["stages"]],["REUSE_CANDIDATE_NOT_RERUN","FAILED_OR_OTHER_STATE"])
    def test_missing_stage_is_not_skipped_or_promoted(self):
        rows,receipt,pin=self.data()
        def read(path):
            if path==rows[1]["path"]:raise FileNotFoundError
            return receipt
        report=m.analyze(rows,read,lambda path:pin)
        self.assertEqual(report["stages"][1]["status"],"MISSING_NOT_RUN")
    def test_wrong_types_unclosed_hashes_or_GO_claim_not_reusable(self):
        rows,receipt,pin=self.data()
        for key,value in (("fresh_inputs",True),("final_fresh_hashes",0),("cleanup_confirmed",False),
            ("accepted_count_delta",False),("GO_authorized",True)):
            row=dict(receipt,**{key:value})
            with self.subTest(key=key):self.assertEqual(m.analyze(rows[:1],lambda path:row,lambda path:pin)["reusable_stages"],0)
    def test_duplicate_invented_or_unsafe_inputs_rejected(self):
        rows,receipt,pin=self.data()
        for path in ("../secret","C:/secret","/secret","tools\\secret","tools//secret"):
            row=copy.deepcopy(receipt);row["source_pins"][0]["path"]=path
            with self.subTest(path=path),self.assertRaises(ValueError):m.analyze(rows[:1],lambda path:row,lambda path:pin)
        row=dict(receipt,source_pins=[pin,pin],fresh_inputs=2,final_fresh_hashes=2)
        with self.assertRaises(ValueError):m.analyze(rows[:1],lambda path:row,lambda path:pin)
    def test_cycle_or_forward_dependencies_rejected(self):
        rows,receipt,pin=self.data();rows[0]["dependencies"]=("pref",)
        with self.assertRaises(ValueError):m.analyze(rows,lambda path:receipt,lambda path:pin)
    def test_time_and_byte_bound_fail_closed(self):
        import io
        from types import SimpleNamespace as NS
        reader=m.BoundedReader(None,seconds=-1)
        with self.assertRaisesRegex(ValueError,"PLANNING_TIME_BOUND"):reader.check()
        reader=m.BoundedReader(None,max_bytes=2)
        reader.path=lambda name:NS(open=lambda *args:io.BytesIO(b"abc"))
        with self.assertRaisesRegex(ValueError,"PLANNING_BYTE_BOUND"):list(reader.chunks("public.bin"))
        for value in (True,0,17):
            with self.assertRaises(ValueError):m.stages(value)

    def test_large_stage_bound_retains_closed_prior_without_promoting_incomplete(self):
        rows,receipt,pin=self.data();extra=copy.deepcopy(receipt)
        extra["source_pins"][0]["path"]="evidence/large.json"
        calls=[]
        def signature(path):
            calls.append(path)
            if path==extra["source_pins"][0]["path"]:raise ValueError("PLANNING_BYTE_BOUND")
            return pin
        report=m.analyze(rows,lambda path:receipt if path==rows[0]["path"] else extra,signature)
        self.assertEqual(report["reusable_stages"],1)
        self.assertEqual(report["stages"][1]["status"],"BOUNDED_CHECK_INCOMPLETE_NOT_REUSABLE")
        self.assertEqual(report["stages"][1]["error_code"],"PLANNING_BYTE_BOUND")
        self.assertEqual(len(calls),2);self.assertFalse(report["GO_authorized"])

    def test_record_bounds_are_reported_but_unknown_validation_errors_propagate(self):
        rows,receipt,pin=self.data()
        for code in m.PLANNING_BOUNDS:
            def read(path):
                if path==rows[1]["path"]:raise ValueError(code)
                return receipt
            report=m.analyze(rows,read,lambda path:pin)
            self.assertEqual(report["reusable_stages"],1)
            self.assertEqual(report["stages"][1]["status"],"BOUNDED_CHECK_INCOMPLETE_NOT_REUSABLE")
        with self.assertRaises(ValueError):m.analyze(rows,lambda path:receipt,lambda path:(_ for _ in ()).throw(ValueError("UNKNOWN_PRIVATE_ERROR")))


if __name__=="__main__":unittest.main()
