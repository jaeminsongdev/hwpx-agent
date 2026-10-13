from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_binding_v1 as m
import runtime_failed_receipt_projection_v1 as first
import runtime_failed_receipt_projection_v2 as second
import runtime_envelope_scope_binding_v1 as default_binding
from test_runtime_failed_receipt_projection_v1 import graph


def lineage():
    return m.declaration([dict(schema_version=f.ADMISSION_SCHEMA,source_role=f.ROLE,
        failed_runtime_pin=f.ROOT,independent_review_pin=f.REVIEW,current_case=158,
        original_failure_promoted=False,current_product_or_GO_qualified=False) for f in (first,second)])


def physical(f):return dict(path=f.PHYSICAL,bytes=1,sha256="a"*64)


class Tests(unittest.TestCase):
    def connected(self):
        source,binding=graph();proof=m.connect(binding,lineage(),first,second)
        return source,binding,proof
    def test_default_next159_rejected_then_private_exact_constructor(self):
        source,binding=graph();pin=dict(path="implementation/p09/evidence/future159.json",bytes=1,sha256="b"*64)
        with self.assertRaises(ValueError):binding.Binding([],pin,next_case=159)
        m.connect(binding,lineage(),first,second)
        desc=[source.descriptor(f.ROOT,physical(f),next_case=159) for f in (first,second)]
        self.assertEqual(binding.Binding(desc,pin,next_case=159).next_case,159)
    def test_inverse_constructor_code_defaults_closure_and_other_methods_exact(self):
        source,binding=graph();ctor=binding.Binding.__init__
        methods={name:getattr(binding.Binding,name) for name in ("semantic_union","project","runtime_budget","validate_scope_evidence")}
        m.connect(binding,lineage(),first,second);new=binding.Binding.__init__
        restored=new.__code__.replace(co_consts=tuple(158 if type(x) is int and x==159 else x for x in new.__code__.co_consts))
        self.assertEqual(restored,ctor.__code__);self.assertIs(new.__defaults__,ctor.__defaults__)
        self.assertIs(new.__closure__,ctor.__closure__);self.assertIs(new.__kwdefaults__,ctor.__kwdefaults__)
        for name,original in methods.items():self.assertIs(getattr(binding.Binding,name),original)
    def test_wrong_case_boolean_and_failed_physical_name_rejected(self):
        source,_,_=self.connected()
        for index in (True,158,160):
            with self.assertRaises(ValueError):source.descriptor(first.ROOT,physical(first),next_case=index)
        with self.assertRaises(ValueError):source.descriptor(first.ROOT,dict(physical(first),path="wrong.json"),next_case=159)
    def test_changed_failed_pin_rejected(self):
        source,_,_=self.connected()
        with self.assertRaises(ValueError):source.descriptor(dict(first.ROOT,sha256="0"*64),physical(first),next_case=159)
    def test_promoted_lineage_wrong_cursor_or_boolean_rejected(self):
        for values in (dict(prior_failures_promoted=True),dict(prior_failures_promoted=0),dict(next_case=160),dict(accepted_count_before=151)):
            _,binding=graph()
            with self.assertRaises(ValueError):m.connect(binding,dict(lineage(),**values),first,second)
    def test_default_namespace_and_reinstallation_rejected(self):
        before=default_binding.Binding.__init__
        with self.assertRaises(ValueError):m.connect(default_binding,lineage(),first,second)
        self.assertIs(default_binding.Binding.__init__,before)
        _,binding,_=self.connected()
        with self.assertRaises(ValueError):m.connect(binding,lineage(),first,second)
    def test_prior_failure_provenance_preserved_not_relabelled_as_product(self):
        source,binding,_=self.connected()
        desc=[source.descriptor(f.ROOT,physical(f),next_case=159) for f in (first,second)]
        pin=dict(path="implementation/p09/evidence/future159.json",bytes=1,sha256="b"*64)
        obj=binding.Binding(desc,pin,next_case=159)
        scope={f.ROOT["path"]:f.ROOT for f in (first,second)};scope[pin["path"]]=pin
        projection,_=obj.project(scope,lambda:None);row=obj.representation(projection)
        self.assertEqual(row["prior_failure_lineage"],lineage())
        self.assertEqual(row["prior_failure_lineage"]["source_role"],m.ROLE)
        self.assertFalse(row["prior_failure_lineage"]["prior_failures_promoted"])
    def test_returned_provenance_cannot_mutate_frozen_declaration(self):
        source,binding,_=self.connected();pin=dict(path="implementation/p09/evidence/future159.json",bytes=1,sha256="b"*64)
        desc=[source.descriptor(f.ROOT,physical(f),next_case=159) for f in (first,second)]
        obj=binding.Binding(desc,pin,next_case=159);scope={f.ROOT["path"]:f.ROOT for f in (first,second)};scope[pin["path"]]=pin
        projection,_=obj.project(scope,lambda:None);row=obj.representation(projection)
        row["prior_failure_lineage"]["failures"][0]["failed_runtime_pin"]["sha256"]="0"*64
        self.assertEqual(obj.representation(projection)["prior_failure_lineage"],lineage())
    def test_ordinary_source_executable_and_fixture_still_not_transformable(self):
        source,_,_=self.connected()
        for path in ("crates/private.rs","target/run.exe","fixtures/original.hwpx"):
            with self.assertRaises(ValueError):source.descriptor(dict(first.ROOT,path=path),physical(first),next_case=159)


if __name__=="__main__":unittest.main()
