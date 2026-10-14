import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import compact_worker_capsule_wire_v1 as m

def pin(name):return dict(path=name,bytes=1,sha256="a"*64)
def row(n=2):return dict(schema_version="semantic/v6",next_case=160,accepted_count_before=153,
    manifest_pin=pin("manifest"),authority_pin=pin("authority"),prior_runtime_pin=pin("prior"),
    descriptors=[dict(schema_version="descriptor/v1",next_case=160,
        semantic_original_pin=pin("original"+str(i)),physical_envelope_pin=pin("physical"+str(i))) for i in range(n)])
def encode(value,check):check();return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(",",":"))
def decode(value,check):check();return json.loads(value)
class Tests(unittest.TestCase):
    def test_exact_all_fields_roundtrip(self):
        value=row();self.assertEqual(m.unpack(m.pack(value)),value)
    def test_many_descriptors_retained_and_smaller(self):
        value=row(31);wire=json.dumps(m.pack(value),separators=(",",":"))
        self.assertLess(len(wire),len(json.dumps(value,separators=(",",":"))))
        self.assertEqual(len(m.unpack(json.loads(wire))["descriptors"]),31)
    def test_shared_context_is_not_erased(self):
        wire=m.pack(row());wire["descriptor_context"][1]=159
        with self.assertRaises(ValueError):m.unpack(wire)
    def test_mixed_context_rejected(self):
        value=row();value["descriptors"][1]["schema_version"]="other"
        with self.assertRaises(ValueError):m.pack(value)
    def test_boolean_pin_size_rejected(self):
        value=row();value["authority_pin"]["bytes"]=True
        with self.assertRaises(ValueError):m.pack(value)
    def test_other_current_case_rejected(self):
        value=row();value["next_case"]=161
        with self.assertRaises(ValueError):m.pack(value)
    def test_extra_wire_key_rejected(self):
        value=m.pack(row());value["extra"]=False
        with self.assertRaises(ValueError):m.unpack(value)
    def test_incomplete_pin_rejected(self):
        value=m.pack(row());value["manifest"].pop()
        with self.assertRaises(ValueError):m.unpack(value)
    def test_binding_count_remains_bounded(self):
        with self.assertRaises(ValueError):m.pack(row(250))
    def test_original_code_and_default_namespace_retained(self):
        api=NS(MAX_BYTES=16384,encode=encode,decode=decode)
        private,proof=m.connect(api);self.assertIs(private.encode.__code__,encode.__code__)
        self.assertIs(api.encode.__globals__["json"],json)
        self.assertEqual(private.decode(private.encode(row(),lambda:None),lambda:None),row())
        self.assertFalse(proof["actual_worker_Native_or_GO_qualified"])
    def test_resource_stop_preserved(self):
        api,_=m.connect(NS(MAX_BYTES=16384,encode=encode,decode=decode));error=ValueError("ORIGINAL_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:api.encode(row(),stop)
        self.assertIs(caught.exception,error)
    def test_original_wire_limit_not_raised(self):
        with self.assertRaises(ValueError):m.JSON.loads(" "*16385)
    def test_large_rows_are_rejected_by_wire_size(self):
        with self.assertRaises(ValueError):m.JSON.dumps(row(249),ensure_ascii=True)
    def test_input_objects_not_mutated(self):
        value=row();before=copy.deepcopy(value);m.unpack(m.pack(value));self.assertEqual(value,before)
if __name__=="__main__":unittest.main()
