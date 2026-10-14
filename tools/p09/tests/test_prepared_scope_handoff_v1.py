import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_input_checkpoint_v1 as prepared
import prepared_scope_handoff_v1 as m

def pin(name):return dict(path=name,bytes=1,sha256="a"*64)
class Binding:
    next_case=160
    manifest_pin=pin("manifest")
    def project(self,scope,checkpoint):checkpoint();return scope,{}
    def representation(self,scope):return dict(manifest_pin=dict(self.manifest_pin),scope=[scope[n] for n in sorted(scope)],full_oracle_required=True)
    def descriptors(self):return [{}]
class Reader:
    def __init__(self,row):self.row=row;self.snapshots={};self.calls=0;self.checks=0
    def json(self,name):self.calls+=1;self.snapshots[name]=pin(name);return copy.deepcopy(self.row)
    def checkpoint(self):self.checks+=1
class Tests(unittest.TestCase):
    def setUp(self):
        self.scope={n:pin(n) for n in ("data","pref","authority","prior","manifest","producer","crates/x/src/lib.rs")}
        self.binding=Binding()
        self.context=dict(index=160,before=153,physical_product_run=3)
        self.current=dict(data_pin=pin("data"),preflight_pin=pin("pref"),authority_pin=pin("authority"),prior_runtime_pin=pin("prior"))
        q=NS(snapshots=copy.deepcopy(self.scope),final_fresh_hashes=len(self.scope),checkpoint=lambda:None)
        checkpoint=prepared.export(q,self.scope,self.binding,context=self.context,**self.current,whole_oracle_completed=True)
        self.row=dict(state="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO",cleanup_confirmed=True,
            Native_or_product_executed=False,GO_authorized=False,queue_advance_authorized=False,product_entrypoint_called=False,
            accepted_count_delta=0,checkpoint=checkpoint,source_pins=[pin("producer")],
            fresh_inputs=len(self.scope),final_fresh_hashes=len(self.scope),current_Rust_input_count=1,source_pairs=1)
        self.args=dict(expected_context=self.context,expected_current_pins=self.current,
            expected_rust=frozenset(("crates/x/src/lib.rs",)),expected_source_paths=frozenset(("producer",)))
    def load(self):return m.load(Reader(self.row),pin("checkpoint"),self.binding,**self.args)
    def test_full_scope_and_checkpoint_retained_without_go(self):
        q=Reader(self.row);scope,rust,proof=m.load(q,pin("checkpoint"),self.binding,**self.args)
        self.assertEqual(scope,{**self.scope,"checkpoint":pin("checkpoint")})
        self.assertEqual(q.calls,1);self.assertFalse(proof["GO_authorized"])
        self.assertFalse(proof["runtime_handoff_connected_or_qualified"])
    def test_failed_preparation_rejected(self):
        self.row["state"]="FAILED_PREPARATION_NOT_ACCEPTED"
        with self.assertRaises(ValueError):self.load()
    def test_cleanup_false_rejected(self):
        self.row["cleanup_confirmed"]=False
        with self.assertRaises(ValueError):self.load()
    def test_product_or_go_claim_rejected(self):
        for key in ("Native_or_product_executed","GO_authorized","queue_advance_authorized","product_entrypoint_called"):
            self.row[key]=True
            with self.assertRaises(ValueError):self.load()
            self.row[key]=False
    def test_wrong_actual_checkpoint_pin_rejected(self):
        with self.assertRaises(ValueError):m.load(Reader(self.row),dict(pin("checkpoint"),sha256="b"*64),self.binding,**self.args)
    def test_oversized_pin_rejected_before_read(self):
        q=Reader(self.row)
        with self.assertRaises(ValueError):m.load(q,dict(pin("checkpoint"),bytes=m.MAX_CHECKPOINT_BYTES+1),self.binding,**self.args)
        self.assertEqual(q.calls,0)
    def test_foreign_context_rejected(self):
        self.row["checkpoint"]["context"]["physical_product_run"]=4
        with self.assertRaises(ValueError):self.load()
    def test_missing_current_authority_rejected(self):
        del self.row["checkpoint"]["authority_pin"]
        with self.assertRaises(ValueError):self.load()
    def test_duplicate_scope_path_rejected(self):
        self.row["checkpoint"]["complete_scope"].append(pin("data"))
        with self.assertRaises(ValueError):self.load()
    def test_partial_final_rejected(self):
        self.row["final_fresh_hashes"]-=1
        with self.assertRaises(ValueError):self.load()
    def test_bool_final_rejected(self):
        self.row["checkpoint"]["final_fresh_hashes"]=True
        with self.assertRaises(ValueError):self.load()
    def test_rewritten_partition_rejected(self):
        self.row["checkpoint"]["scope_inputs_declared_not_final_fresh_read_here"]=[pin("data")]
        with self.assertRaises(ValueError):self.load()
    def test_declared_input_does_not_become_fresh(self):
        q=NS(snapshots=copy.deepcopy(self.scope),final_fresh_hashes=len(self.scope),checkpoint=lambda:None)
        self.scope["declared"]=pin("declared")
        self.row["checkpoint"]=prepared.export(q,self.scope,self.binding,context=self.context,**self.current,whole_oracle_completed=True)
        scope,_,proof=self.load();self.assertIn("declared",scope)
        self.assertFalse(proof["GO_authorized"])
    def test_rust_omission_rejected(self):
        self.args["expected_rust"]=frozenset(("crates/other/src/lib.rs",))
        with self.assertRaises(ValueError):self.load()
    def test_manifest_drift_rejected(self):
        self.binding.manifest_pin=dict(pin("manifest"),sha256="b"*64)
        with self.assertRaises(ValueError):self.load()
    def test_representation_bool_int_drift_rejected(self):
        self.row["checkpoint"]["representation"]["full_oracle_required"]=1
        with self.assertRaises(ValueError):self.load()
    def test_unbound_producer_source_rejected(self):
        self.row["source_pins"][0]["sha256"]="b"*64
        with self.assertRaises(ValueError):self.load()
    def test_source_pair_omission_rejected(self):
        self.row["source_pairs"]=0
        with self.assertRaises(ValueError):self.load()
    def test_scope_projection_mutation_rejected(self):
        def project(scope,checkpoint):scope["data"]["bytes"]=9;return scope,{}
        self.binding.project=project
        with self.assertRaises(ValueError):self.load()
    def test_original_resource_error_identity_preserved(self):
        error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop(scope,checkpoint):raise error
        self.binding.project=stop
        with self.assertRaises(ValueError) as caught:self.load()
        self.assertIs(caught.exception,error)
if __name__=="__main__":unittest.main()
