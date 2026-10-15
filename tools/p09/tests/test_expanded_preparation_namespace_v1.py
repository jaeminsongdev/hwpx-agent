"""Namespace projection contracts, not Native or product acceptance."""
from types import FunctionType,SimpleNamespace as NS
import copy
import unittest
import expanded_preparation_namespace_v1 as m
from tests import test_closed_prebody_worker_connection_v1 as fixture
import closed_prebody_runtime_connection_v1 as connection
import current_queue_successor_binding as bindings
import closed_prebody_source_alias_v1 as alias
import closed_prebody_worker_connection_v1 as transport
import current_stored_runtime_scope as scope
import runtime_envelope_namespace_bundle_v1 as loader
import owned_source_read_pressure as bytes_policy


class Tests(unittest.TestCase):
    def setUp(self):
        globals().get("CHECKPOINT",lambda:None)()
        self.f=fixture.Tests();self.f.setUp()
        # Fixture private runtime begins at v1, as opposed to the qualified v4
        # production entry. Project exact metadata only to obtain its v4 shape.
        for name in ("validate_worker_hint","owned_worker_entry","qualify_factory"):
            fn=getattr(self.f.runtime,name)
            changed,_=m.literal_function(fn,{".compact.v1.json":".compact.v4.json"} if name=="validate_worker_hint" else {".v1.json":".v4.json"})
            fn.__globals__[name]=changed;setattr(self.f.runtime,name,changed)
    def test_recursive_literal_inverse_preserves_other_behavior(self):
        def original(value=3):
            def nested():return ".v6.json"
            return value,nested(),"v6"
        fn=FunctionType(original.__code__,dict(__name__="p09_exact_fixture"),argdefs=original.__defaults__)
        changed,proof=m.literal_function(fn,{".v6.json":".v7.json","v6":"v7"})
        self.assertEqual(changed(),(3,".v7.json","v7"));self.assertIs(changed.__defaults__,fn.__defaults__)
        self.assertTrue(proof["exact_entire_code_inverse"])
    def test_default_and_missing_literal_rejected(self):
        with self.assertRaises(ValueError):m.literal_function(self.test_default_and_missing_literal_rejected,{"a":"b"})
        with self.assertRaises(ValueError):m.literal_function(self.f.runtime.validate_worker_hint,{"absent":"new"})
    def test_unhooked_private_validator_accepts_only_new_capsule_namespace(self):
        m.install(self.f.runtime)
        hint={k:copy.deepcopy(v) for k,v in self.f.hint.items() if k!=transport.FIELD}
        hint["capsule_pin"]["path"]=hint["capsule_pin"]["path"].replace(".v1.json",".v9.json")
        self.assertEqual(self.f.runtime.validate_worker_hint(hint,self.f.graph.worker.TASK),(165,4))
        hint["capsule_pin"]["path"]=hint["capsule_pin"]["path"].replace(".v9.json",".v4.json")
        with self.assertRaises(ValueError):self.f.runtime.validate_worker_hint(hint,self.f.graph.worker.TASK)
    def test_hooked_snapshot_reconstructs_new_namespace_with_all_rows(self):
        connection.connect(self.f.runtime,bindings,alias,transport,scope,fixture.source_fixture.API,
            fixture.source_fixture.bridge,fixture.source_fixture.codec,self.f.fixture.pair["schema_version"],parent_policy=self.f.policy)
        m.install(self.f.runtime)
        hint=copy.deepcopy(self.f.hint);hint["capsule_pin"]["path"]=hint["capsule_pin"]["path"].replace(".v1.json",".v9.json")
        graph,_=self.f.runtime.reconstruct_worker_graph(self.f.root,loader,scope,bytes_policy,hint,self.f.wire,lambda:None)
        self.assertEqual(graph.binding.descriptors(),self.f.bound.descriptors())
    def test_install_idempotent_and_shared_runtime_unchanged(self):
        import current_queue_successor_runtime as shared
        before=shared.validate_worker_hint
        m.install(self.f.runtime);first=self.f.runtime.validate_worker_hint;m.install(self.f.runtime)
        self.assertIs(first,self.f.runtime.validate_worker_hint);self.assertIs(shared.validate_worker_hint,before)
    def test_worker_entry_path_is_explicit_and_private(self):
        m.install(self.f.runtime);m.retarget_worker(self.f.runtime,"tools/p09/expanded_closed_preparation_v1.py")
        self.assertEqual(self.f.runtime.owned_worker_entry.__globals__["SELF"],"tools/p09/expanded_closed_preparation_v1.py")
        with self.assertRaises(ValueError):m.retarget_worker(self.f.runtime,"other/app.py")


if __name__=="__main__":unittest.main()
