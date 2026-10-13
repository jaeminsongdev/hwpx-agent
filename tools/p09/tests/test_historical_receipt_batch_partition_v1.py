import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import historical_receipt_batch_partition_v1 as m

R="implementation/p09/evidence/p09-361-case155-current-runtime-run001.v1.json"
A="implementation/p09/evidence/p09-361-case155-current-epoch-accept001.v1.json"
D="implementation/p09/evidence/p09-361-case155-native-pressure-data017.v1.json"
E="target/current.exe"
def pin(name,size=1):return dict(path=name,bytes=size,sha256="0"*64)
def rows(*names):return {n:pin(n) for n in names}

class Tests(unittest.TestCase):
    def run_candidate(self,r=None,index=157,deps=(E,),guard=lambda:None):
        return m.candidate(rows(R,A,D,E) if r is None else r,index,deps,guard)
    def test_all_original_pins_preserved_disjoint_no_mutation(self):
        r=rows(R,A,D,E);before=copy.deepcopy(r);v=self.run_candidate(r)
        self.assertEqual(r,before)
        self.assertEqual({p["path"]:p for p in v["full_preservation_scope"]},r)
        self.assertEqual(len(v["batch_preservation_candidate"]),3)
        self.assertEqual(v["per_case_candidate"],[r[E]])
    def test_current_dependency_overrides_historical_name(self):
        v=self.run_candidate(deps=tuple(sorted((E,R))))
        self.assertIn(R,{p["path"] for p in v["per_case_candidate"]})
        self.assertNotIn(R,{p["path"] for p in v["batch_preservation_candidate"]})
    def test_current_and_future_receipts_never_lexically_moved(self):
        for index in (157,158):
            n=R.replace("case155","case"+str(index));v=self.run_candidate(rows(E,n))
            self.assertEqual(v["batch_preservation_candidate"],[])
    def test_product_sources_fixtures_and_code_never_match(self):
        names=(E,"crates/provider.rs","fixtures/original.hwpx","tools/p09/controller.py")
        v=self.run_candidate(rows(*names));self.assertEqual(v["batch_preservation_candidate"],[])
    def test_foreign_and_ambiguous_receipt_names_never_match(self):
        for n in (R+".bak",R.replace("implementation/","foreign/"),R.replace("run001","run1"),R.replace("case155","case0")):
            v=self.run_candidate(rows(E,n));self.assertEqual(v["batch_preservation_candidate"],[])
    def test_deterministic_with_reversed_mapping(self):
        r=rows(R,A,D,E);self.assertEqual(self.run_candidate(r),self.run_candidate(dict(reversed(list(r.items())))))
    def test_current_dependency_missing_and_duplicates_rejected(self):
        for deps in (("missing",),(E,E),()):
            with self.assertRaises(ValueError):self.run_candidate(deps=deps)
    def test_wrong_map_binding_and_boolean_bytes_rejected(self):
        r=rows(E);r[E]["path"]="other"
        with self.assertRaises(ValueError):self.run_candidate(r)
        r=rows(E);r[E]["bytes"]=True
        with self.assertRaises(ValueError):self.run_candidate(r)
    def test_next_index_bool_and_out_of_range_rejected(self):
        for index in (True,114,250):
            with self.assertRaises(ValueError):self.run_candidate(index=index)
    def test_absolute_parent_linklike_path_rejected(self):
        for n in ("/absolute","../outside","foo\\bar"):
            with self.assertRaises(ValueError):self.run_candidate(rows(E,n))
    def test_guard_exception_identity_first_and_mid_loop(self):
        for stop in (1,3):
            calls=[];error=ValueError("ORIGINAL_STOP")
            def guard():
                calls.append(1)
                if len(calls)==stop:raise error
            with self.assertRaises(ValueError) as ctx:self.run_candidate(guard=guard)
            self.assertIs(ctx.exception,error);self.assertEqual(len(calls),stop)
    def test_candidate_does_not_authorize_native_batch_close_or_queue(self):
        v=self.run_candidate()
        for key in ("Native_scope_change_authorized","batch_closing_actual","queue_advance_authorized","PC_freeze_resolved"):
            self.assertIs(v[key],False)
        self.assertEqual(v["accepted_count_delta"],0)
        self.assertIs(v["batch_initial_and_final_whole_bytes_required"],True)
    def test_partitions_are_independent_copies(self):
        r=rows(R,A,D,E);v=self.run_candidate(r)
        v["batch_preservation_candidate"][0]["bytes"]=9
        self.assertEqual(r[A]["bytes"],1)
        self.assertEqual(v["full_preservation_scope"][0]["bytes"],1)

if __name__=="__main__":unittest.main()
