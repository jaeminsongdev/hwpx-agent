import copy
import unittest
import recovery_workflow_plan_v1 as m


class Tests(unittest.TestCase):
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
        for value in (True,0,9):
            with self.assertRaises(ValueError):m.stages(value)


if __name__=="__main__":unittest.main()
