import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_input_checkpoint_v1 as m

def p(name):return dict(path=name,bytes=1,sha256="a"*64)
class Binding:
    next_case=160
    manifest_pin=p("manifest")
    def project(self,scope,checkpoint):checkpoint();return scope,{}
    def representation(self,scope):return dict(manifest_pin=dict(self.manifest_pin),scope=list(scope.values()))
class Tests(unittest.TestCase):
    def setUp(self):
        self.scope={n:p(n) for n in ("data","pref","authority","prior","manifest","extra")}
        self.q=NS(snapshots=copy.deepcopy(self.scope),final_fresh_hashes=len(self.scope),checkpoint=lambda:None)
        self.args=dict(context=dict(index=160,before=153,physical_product_run=3),data_pin=p("data"),
            preflight_pin=p("pref"),authority_pin=p("authority"),prior_runtime_pin=p("prior"),whole_oracle_completed=True)
        self.binding=Binding()
    def test_complete_export_is_not_native_or_go(self):
        row=m.export(self.q,self.scope,self.binding,**self.args)
        self.assertEqual(len(row["complete_scope"]),len(self.scope))
        self.assertFalse(row["GO_authorized"]);self.assertFalse(row["runtime_admission_qualified"])
        self.assertTrue(row["future_actual_Native_two_byte_boundaries_and_independent_oracle_required"])
    def test_missing_whole_oracle_rejected(self):
        with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,**dict(self.args,whole_oracle_completed=False))
    def test_partial_final_freshness_rejected(self):
        self.q.final_fresh_hashes-=1
        with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,**self.args)
    def test_boolean_final_count_rejected(self):
        self.q.final_fresh_hashes=True
        with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,**self.args)
    def test_other_physical_or_cursor_rejected(self):
        for values in (dict(physical_product_run=2),dict(index=159),dict(before=152)):
            with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,
                **dict(self.args,context=dict(self.args["context"],**values)))
    def test_unbound_data_pin_rejected(self):
        self.q.snapshots["data"]=dict(p("data"),sha256="b"*64)
        with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,**self.args)
    def test_manifest_missing_rejected(self):
        del self.scope["manifest"]
        with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,**self.args)
    def test_result_mutation_does_not_change_current_scope(self):
        before=copy.deepcopy(self.scope)
        row=m.export(self.q,self.scope,self.binding,**self.args);row["complete_scope"][0]["bytes"]=90
        self.assertEqual(self.scope,before)
    def test_wrong_scope_key_rejected(self):
        self.scope["extra"]["path"]="renamed"
        with self.assertRaises(ValueError):m.export(self.q,self.scope,self.binding,**self.args)
    def test_original_resource_stop_preserved(self):
        error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop():raise error
        self.q.checkpoint=stop
        with self.assertRaises(ValueError) as caught:m.export(self.q,self.scope,self.binding,**self.args)
        self.assertIs(caught.exception,error)
if __name__=="__main__":unittest.main()
