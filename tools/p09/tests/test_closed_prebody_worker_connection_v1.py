"""Real transport contracts; synthetic inputs are not product evidence."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import closed_prebody_worker_connection_v1 as m
import closed_prebody_source_alias_v1 as alias
import current_queue_successor_runtime as runtime
import current_queue_successor_connections as metadata
import current_queue_successor_binding as bindings
import current_stored_runtime_scope as scope
import runtime_envelope_namespace_bundle_v1 as loader
import owned_source_read_pressure as bytes_policy
import bounded_successor_capsule_wire_v2 as bounded_wire
from tests import test_closed_prebody_source_alias_v1 as source_fixture


class Tests(unittest.TestCase):
    def setUp(self):
        checkpoint=globals().get("CHECKPOINT",lambda:None);checkpoint()
        self.fixture=source_fixture.Tests();self.fixture.setUp();self.policy=self.fixture.verify()
        self.module=self.fixture.module();alias.install(self.module,self.policy)
        self.root=self.fixture.q.root
        self.runtime,self.metadata=m.private_transport(self.root,loader,source_fixture.bridge,bounded_wire,checkpoint)
        self.manifest_pin=dict(path=alias.PREFIX+"p09-361-case165-successor-manifest004.v1.json",bytes=100,sha256="e"*64)
        self.bound=self.module.Binding(self.policy.descriptors(),self.manifest_pin,next_case=165)
        self.step=dict(schema_version="hwpx-agent.p09-flat-current-queue-step/v1",index=165,before=158,
            case="actual_import::fixture",prior_queue_pin=dict(path=alias.PREFIX+"p09-361-case164-current-epoch-accept001.v1.json",bytes=100,sha256="c"*64),
            prior_candidate_pin=dict(path=alias.PREFIX+"p09-361-case164-current-runtime-run006.v1.json",bytes=100,sha256="d"*64))
        self.graph,_=self.metadata.connect(self.root,loader,bytes_policy,self.module,self.bound,self.step,4,lambda:None)
        self.wire,pin=self.graph.worker.encode(self.bound,self.step["prior_queue_pin"],self.step["prior_candidate_pin"],lambda:None)
        self.capsule=dict(pin,path=alias.PREFIX+"p09-361-case165-successor-worker-capsule004.compact.v1.json")
        self.manifest=dict(descriptors=self.bound.descriptors(),historical_predecessor_provenance={})
        self.hint=m.parent_hint(self.runtime,self.step,4,self.capsule,self.manifest_pin,self.manifest,[],self.policy,alias,scope,self.module.source)
    def reconstruct(self,hint=None,wire=None):
        return m.reconstruct(self.runtime,bindings,self.root,loader,scope,bytes_policy,
            self.hint if hint is None else hint,self.wire if wire is None else wire,lambda:None,alias)
    def test_real_wire_roundtrip_without_evidence_IO(self):
        original=Path.open
        def checked(path,*args,**kwargs):
            if "implementation/p09/evidence" in path.as_posix():raise AssertionError("EVIDENCE_IO")
            return original(path,*args,**kwargs)
        with patch.object(Path,"open",checked):graph,proof=self.reconstruct()
        self.assertEqual(graph.binding.descriptors(),self.bound.descriptors())
        self.assertFalse(proof["original_closed_source_bytes_verified_here"])
        self.assertTrue(proof["original_worker_reconstruction_code_defaults_closure_retained"])
    def test_identical_parent_worker_representation_and_original_scope_oracle(self):
        graph,_=self.reconstruct();pins={self.fixture.old["path"]:self.fixture.old,self.manifest_pin["path"]:self.manifest_pin}
        parent,_=self.bound.project(pins,lambda:None);worker,_=graph.binding.project(pins,lambda:None)
        self.assertEqual(self.bound.representation(parent),graph.binding.representation(worker))
        self.assertEqual(graph.binding_module.Binding.validate_scope_evidence.__code__,self.module.Binding.validate_scope_evidence.__code__)
    def test_parent_rejects_declaration_as_verified_policy(self):
        with self.assertRaises(ValueError):m.parent_hint(runtime,self.step,4,self.capsule,self.manifest_pin,self.manifest,[],self.policy.evidence(),alias,scope,self.module.source)
    def test_extra_hint_key_rejected(self):
        with self.assertRaises(ValueError):self.reconstruct(dict(self.hint,unexpected=True))
    def test_current_future_and_wrong_case_declarations_rejected(self):
        for path in (self.fixture.old["path"].replace("002","004"),self.fixture.old["path"].replace("002","005"),self.fixture.old["path"].replace("case165","case164")):
            hint=copy.deepcopy(self.hint);hint[m.FIELD]["closed_descriptors"][0]["semantic_original_pin"]["path"]=path
            with self.assertRaises(ValueError):self.reconstruct(hint)
    def test_changed_declared_hash_or_wire_rejected(self):
        hint=copy.deepcopy(self.hint);hint[m.FIELD]["closed_descriptors"][0]["physical_envelope_pin"]["sha256"]="0"*64
        with self.assertRaises(ValueError):self.reconstruct(hint)
        with self.assertRaises(ValueError):self.reconstruct(wire=self.wire+b" ")
    def test_duplicate_pair_and_false_policy_flags_rejected(self):
        hint=copy.deepcopy(self.hint);hint[m.FIELD]["closed_descriptors"]*=2
        with self.assertRaises(ValueError):self.reconstruct(hint)
        hint=copy.deepcopy(self.hint);hint[m.FIELD]["earlier_closed_prebody_only"]=False
        with self.assertRaises(ValueError):self.reconstruct(hint)
    def test_missing_declared_pair_in_parent_manifest_rejected(self):
        with self.assertRaises(ValueError):m.parent_hint(runtime,self.step,4,self.capsule,self.manifest_pin,dict(self.manifest,descriptors=[]),[],self.policy,alias,scope,self.module.source)
    def test_shared_namespace_rejected_and_not_mutated(self):
        import runtime_envelope_scope_binding_v1 as shared
        before=shared.source.descriptor
        with self.assertRaises(ValueError):m.install_declaration(shared,self.policy.evidence(),165,4,alias,scope)
        self.assertIs(shared.source.descriptor,before)
    def test_unlisted_same_case_not_admitted(self):
        graph,_=self.reconstruct();other=dict(self.fixture.old,path=self.fixture.old["path"].replace("002","003"))
        with self.assertRaises(ValueError):graph.binding_module.source.descriptor(other,self.fixture.new,next_case=165)


if __name__=="__main__":unittest.main()
