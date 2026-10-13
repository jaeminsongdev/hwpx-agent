from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_binding_v2 as m
import runtime_failed_receipt_projection_v1 as first
import runtime_failed_receipt_projection_v2 as second
import runtime_envelope_scope_binding_v1 as default
from test_runtime_successor_binding_v1 import lineage,physical
from test_runtime_failed_receipt_projection_v1 import graph


class Tests(unittest.TestCase):
    def connected(self):
        source,binding=graph();proof=m.connect(binding,m.declaration(lineage()),first,second)
        return source,binding,proof
    def test_exact_private160_constructor_and_descriptor(self):
        source,binding,_=self.connected();pin=dict(path="implementation/p09/evidence/future160.json",bytes=1,sha256="b"*64)
        rows=[source.descriptor(f.ROOT,physical(f),next_case=160) for f in (first,second)]
        self.assertEqual(binding.Binding(rows,pin,next_case=160).next_case,160)
    def test_only_exact160_not_bool_or_old_context(self):
        source,binding,_=self.connected()
        for index in (True,158,159,161):
            with self.subTest(index=index),self.assertRaises(ValueError):source.descriptor(first.ROOT,physical(first),next_case=index)
    def test_wrong_context_or_promoted_history_rejected(self):
        for change in (dict(next_case=159),dict(next_case=True),dict(accepted_count_before=152),dict(historical_failures_promoted=True)):
            _,binding=graph()
            with self.subTest(change=change),self.assertRaises(ValueError):m.connect(binding,dict(m.declaration(lineage()),**change),first,second)
    def test_default_module_never_mutated(self):
        ctor=default.Binding.__init__
        with self.assertRaises((ValueError,AttributeError)):m.connect(default,m.declaration(lineage()),first,second)
        self.assertIs(default.Binding.__init__,ctor)
    def test_all_original_oracle_methods_identity_retained(self):
        _,binding=graph();names=("semantic_union","project","runtime_budget","validate_scope_evidence")
        before={name:getattr(binding.Binding,name) for name in names}
        m.connect(binding,m.declaration(lineage()),first,second)
        for name in names:self.assertIs(getattr(binding.Binding,name),before[name])
    def test_inverse_constructor_restores_entire_original158_code(self):
        _,binding=graph();old=binding.Binding.__init__
        m.connect(binding,m.declaration(lineage()),first,second);new=binding.Binding.__init__
        restored=new.__code__.replace(co_consts=tuple(158 if type(x) is int and x==160 else x for x in new.__code__.co_consts))
        self.assertEqual(restored,old.__code__);self.assertIs(new.__defaults__,old.__defaults__)
        self.assertIs(new.__closure__,old.__closure__);self.assertIs(new.__kwdefaults__,old.__kwdefaults__)
    def test_representation_has_explicit_current_and_unchanged_historical_context(self):
        source,binding,_=self.connected();pin=dict(path="implementation/p09/evidence/future160.json",bytes=1,sha256="b"*64)
        rows=[source.descriptor(f.ROOT,physical(f),next_case=160) for f in (first,second)]
        bound=binding.Binding(rows,pin,next_case=160);scope={f.ROOT["path"]:f.ROOT for f in (first,second)};scope[pin["path"]]=pin
        projection,_=bound.project(scope,lambda:None);row=bound.representation(projection)
        self.assertEqual(row["next_case"],160)
        self.assertEqual(row["historical_case159_failure_lineage"],lineage())
        self.assertEqual(row["historical_case159_failure_lineage"]["next_case"],159)
        self.assertEqual(row["successor_context"],m.declaration(lineage()))
        self.assertNotIn("prior_failure_lineage",row)
    def test_context_copy_cannot_mutate_frozen_original(self):
        source,binding,_=self.connected();pin=dict(path="implementation/p09/evidence/future160.json",bytes=1,sha256="b"*64)
        rows=[source.descriptor(f.ROOT,physical(f),next_case=160) for f in (first,second)]
        bound=binding.Binding(rows,pin,next_case=160);scope={f.ROOT["path"]:f.ROOT for f in (first,second)};scope[pin["path"]]=pin
        projection,_=bound.project(scope,lambda:None);row=bound.representation(projection)
        row["successor_context"]["authority_pin"]["sha256"]="0"*64
        self.assertEqual(bound.representation(projection)["successor_context"],m.declaration(lineage()))
    def test_wrong_original_failure_bytes_or_physical_path_rejected(self):
        source,_,_=self.connected()
        with self.assertRaises(ValueError):source.descriptor(dict(first.ROOT,sha256="0"*64),physical(first),next_case=160)
        with self.assertRaises(ValueError):source.descriptor(first.ROOT,dict(physical(first),path="wrong.json"),next_case=160)
    def test_unrelated_source_binary_fixture_still_not_representable(self):
        source,_,_=self.connected()
        for path in ("crates/original.rs","target/run.exe","fixtures/original.hwpx"):
            with self.subTest(path=path),self.assertRaises(ValueError):source.descriptor(dict(first.ROOT,path=path),physical(first),next_case=160)


if __name__=="__main__":unittest.main()
