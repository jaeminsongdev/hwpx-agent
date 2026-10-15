"""Connection contracts, never Native/product/Gate qualification."""
import copy
from types import FunctionType,SimpleNamespace as NS
import unittest
import closed_prebody_runtime_connection_v1 as m
import closed_prebody_source_alias_v1 as alias
import closed_prebody_worker_connection_v1 as transport
import current_queue_successor_binding as bindings
import current_stored_runtime_scope as scope
import runtime_envelope_namespace_bundle_v1 as loader
import owned_source_read_pressure as bytes_policy
from tests import test_closed_prebody_worker_connection_v1 as fixture


class Tests(unittest.TestCase):
    def setUp(self):
        globals().get("CHECKPOINT",lambda:None)()
        self.f=fixture.Tests();self.f.setUp()
        self.runtime=self.f.runtime;self.calls=[]
        def current_input_scope(q,graph,step,report_pin,manifest_pin,source_pins):
            calls.append("ORIGINAL_FULL_PARENT_CALLBACK")
            return dict(q.snapshots),{"crates/fixture.rs"}
        env=dict(__name__="p09_exact_parent_scope_fixture",calls=self.calls)
        self.original=FunctionType(current_input_scope.__code__,env)
        self.runtime.current_input_scope=self.original
        self.runtime.reconstruct_worker_graph.__globals__["current_input_scope"]=self.original
    def install(self,parent=True):
        return m.connect(self.runtime,bindings,alias,transport,scope,fixture.source_fixture.API,
            fixture.source_fixture.bridge,fixture.source_fixture.codec,self.f.fixture.pair["schema_version"],
            parent_policy=self.f.policy if parent else None)
    def graph(self):
        return self.runtime.reconstruct_worker_graph(self.f.root,loader,scope,bytes_policy,self.f.hint,self.f.wire,lambda:None)[0]
    def invoke(self,graph):
        return self.runtime.current_input_scope(self.f.fixture.q,graph,self.f.step,{},self.f.manifest_pin,{})
    def test_parent_fresh_original_then_original_full_callback(self):
        proof=self.install();required,rust=self.invoke(self.graph())
        self.assertEqual(self.calls,["ORIGINAL_FULL_PARENT_CALLBACK"])
        self.assertIn(self.f.fixture.old["path"],required)
        self.assertEqual(rust,{"crates/fixture.rs"})
        self.assertIs(proof["original_parent_input_callback"],self.original)
    def test_changed_original_rejected_before_whole_callback(self):
        self.install();graph=self.graph();self.f.fixture.root["worker_created"]=True
        with self.assertRaises(ValueError):self.invoke(graph)
        self.assertEqual(self.calls,[])
    def test_worker_declaration_never_authorizes_parent(self):
        self.install(False);graph=self.graph()
        with self.assertRaises(ValueError):self.invoke(graph)
        self.assertEqual(self.calls,[])
    def test_parent_hint_matches_admitted_policy_and_original_task_checks(self):
        self.install()
        hint=self.runtime.worker_hint(self.f.step,4,self.f.capsule,self.f.manifest_pin,self.f.manifest,[],)
        self.assertEqual(hint,self.f.hint)
        with self.assertRaises(ValueError):self.runtime.validate_worker_hint(hint,"case166-current-r004-tests")
    def test_changed_declaration_rejected_by_parent(self):
        self.install();hint=copy.deepcopy(self.f.hint)
        hint[transport.FIELD]["producer_pin"]["sha256"]="0"*64
        with self.assertRaises(ValueError):self.runtime.reconstruct_worker_graph(self.f.root,loader,scope,bytes_policy,hint,self.f.wire,lambda:None)
    def test_factory_binding_namespace_and_full_oracle_retained(self):
        facade=m.binding_api(bindings,alias,self.f.policy)
        module,proof=facade.connect(self.f.root,loader,scope,165,{},[])
        bound=module.Binding(self.f.policy.descriptors(),self.f.manifest_pin,next_case=165)
        self.assertEqual(bound.descriptors(),self.f.policy.descriptors())
        self.assertTrue(proof["all_nonconstructor_oracle_methods_retained"])
    def test_dynamic_runtime_is_configured_without_replacing_old_constructor(self):
        seen=[]
        def current_namespaces(q,*args,**kwargs):return "runtime","controller",{"original":True}
        original=FunctionType(current_namespaces.__code__,dict(__name__="p09_exact_dispatch_fixture"))
        dispatch=NS(current_namespaces=original)
        proof=m.connect_dynamic(dispatch,lambda runtime,q:seen.append((runtime,q)))
        self.assertEqual(dispatch.current_namespaces("reader"),("runtime","controller",{"original":True}))
        self.assertEqual(seen,[("runtime","reader")]);self.assertIs(proof["original_dynamic_namespace_function"],original)
    def test_default_runtime_rejected_before_any_change(self):
        import current_queue_successor_runtime as shared
        before=shared.worker_hint
        with self.assertRaises(ValueError):m.connect(shared,bindings,alias,transport,scope,fixture.source_fixture.API,
            fixture.source_fixture.bridge,fixture.source_fixture.codec,self.f.fixture.pair["schema_version"],parent_policy=self.f.policy)
        self.assertIs(shared.worker_hint,before)


if __name__=="__main__":unittest.main()
