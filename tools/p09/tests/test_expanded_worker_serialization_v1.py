"""Expected bytes derive from a declared format, never observed file bytes."""
import copy
import json
import unittest
from types import FunctionType
import qualify_expanded_worker_startup_v1 as m


class Tests(unittest.TestCase):
    def row(self):return dict(schema_version="hwpx-agent.p09-current-successor-worker-bootstrap/v1",index=165,run=4,
        capsule_pin=dict(path="implementation/p09/evidence/p09-361-case165-successor-worker-capsule004.compact.v9.json"),
        closed_prebody_source_declaration=dict(index=165,schema_version="hwpx-agent.p09-qualified-closed-prebody-source-policy/v1"))
    def test_exact_publisher_bytes_and_whole_values(self):
        row=self.row();before=copy.deepcopy(row)
        text=m.expected_dumps(row,ensure_ascii=True,allow_nan=False,separators=(",",":"))
        self.assertEqual(text,json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2))
        self.assertEqual(json.loads(text),row);self.assertEqual(row,before)
    def test_other_profiles_and_json_calls_unchanged(self):
        row=self.row();row["capsule_pin"]["path"]=row["capsule_pin"]["path"].replace("v9","v4")
        options=dict(ensure_ascii=True,allow_nan=False,separators=(",",":"))
        self.assertEqual(m.expected_dumps(row,**options),json.dumps(row,**options))
        self.assertEqual(m.expected_dumps(self.row(),indent=2),json.dumps(self.row(),indent=2))
    def test_wrong_context_or_missing_declaration_rejected(self):
        row=self.row();row["index"]=166
        with self.assertRaises(ValueError):m.expected_dumps(row,ensure_ascii=True,allow_nan=False,separators=(",",":"))
    def test_late_admission_updates_reach_same_function_family(self):
        def qualify_factory():return marker
        env=dict(__name__="p09_exact_fixture",marker="before")
        original=FunctionType(qualify_factory.__code__,env)
        linked=m.in_family(original)
        env["marker"]="after"
        self.assertEqual(linked(),"after");self.assertIs(linked.__globals__,env)
        self.assertIs(linked.__code__,original.__code__)
        row=self.row();del row["closed_prebody_source_declaration"]
        with self.assertRaises(ValueError):m.expected_dumps(row,ensure_ascii=True,allow_nan=False,separators=(",",":"))


if __name__=="__main__":unittest.main()
