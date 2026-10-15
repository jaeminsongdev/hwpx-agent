"""Closed-source policy contracts; fixtures never count as product evidence."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import closed_prebody_source_alias_v1 as m
import current_queue_successor_wire_runtime_v2 as bridge
import current_queue_successor_binding as bindings
import current_stored_runtime_scope as scope
import runtime_envelope_namespace_bundle_v1 as loader
import runtime_record_envelope_v2 as codec


def exact(left,right,label):
    if type(left) is not type(right) or left!=right:raise ValueError(label)
def fields(row,expected,label):
    for name,value in expected.items():exact(row.get(name),value,label)
def read_exact(q,pin):
    value=q.json(pin["path"]);exact(q.snapshots[pin["path"]],pin,"EXACT_FIXTURE_PIN");return value
API=NS(exact=exact,fields=fields,read_exact=read_exact,require=lambda ok,label:ok or m.require(False,label))


class Tests(unittest.TestCase):
    def setUp(self):
        self.root=dict(state="DEFERRED_NOT_STARTED",task="case165-current-r002-tests",worker_created=False,
            product_body_observed=False,actual_product_child_executed=False,cleanup_confirmed=True,
            owned_tree_empty=True,accepted_count_delta=0,current_generation_runtime_candidate_qualified=False,
            Native_source_frame_qualified=False,passed_test_names=[],stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",
            source_frame=None,actual_Cargo_SQL_Hangul_run=False,product_complete=False)
        raw=json.dumps(self.root,separators=(",",":"),sort_keys=True).encode()
        self.old=dict(path=m.PREFIX+"p09-361-case165-current-runtime-run002.v1.json",bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        encoded=codec.encode(raw,lambda:None)
        self.new=dict(path=m.encoded_path(self.old,165,4,scope),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        self.pair=dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=165,
            semantic_original_pin=self.old,physical_envelope_pin=self.new)
        self.producer_pin=dict(path=m.PREFIX+"p09-361-case165-closed-prebody-sources001.v1.json",bytes=100,sha256="a"*64)
        self.code_pin=dict(path=m.PREFIX+"p09-361-case165-closed-prebody-code001.v1.json",bytes=100,sha256="b"*64)
        sources=[dict(path=n,bytes=1,sha256="c"*64) for n in (m.SELF,m.TEST)]+[m.BRIDGE_PIN]
        self.code=dict(state=m.CODE_STATE,contracts=dict(run=14,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            accepted_count_delta=0,product_or_Native_executed=False,source_pins=sources,fresh_inputs=3,final_fresh_hashes=3)
        allpins=sources+[self.old,self.new,self.code_pin]
        self.row=dict(m.producer_fields(165,4,self.code_pin,[self.old],[self.pair]),cleanup_confirmed=True,
            original_receipts_rewritten=False,product_or_Native_executed=False,accepted_count_delta=0,
            source_qualification_pin=self.code_pin,source_pins=sources,fresh_input_pins=allpins,
            fresh_inputs=len(allpins),final_fresh_hashes=len(allpins),closed_descriptors=[self.pair],
            original_bytes=len(raw),encoded_bytes=len(encoded),bytes_saved=len(raw)-len(encoded),decode_passes=2)
        pins={p["path"]:p for p in allpins+[self.producer_pin]}
        docs={self.old["path"]:self.root,self.code_pin["path"]:self.code,self.producer_pin["path"]:self.row}
        outer=self
        class Reader:
            def __init__(self):self.snapshots={};self.root=Path(__file__).resolve().parents[3]
            def checkpoint(self):pass
            def pin(self,name):self.snapshots[name]=dict(pins[name]);return self.snapshots[name]
            def json(self,name):self.pin(name);return copy.deepcopy(docs[name])
            def _read(self,name,parse=False):
                value=outer.encoded
                return dict(path=name,bytes=len(value),sha256=hashlib.sha256(value).hexdigest()),bytearray(value)
            def _bind(self,name,pin):self.snapshots[name]=pin
        self.encoded=encoded;self.q=Reader()
    def verify(self):return m.verify(self.q,self.producer_pin,165,4,API,scope,bridge,codec,self.pair["schema_version"])
    def module(self):return bindings.connect(self.q.root,loader,scope,165,{},())[0]
    def test_exact_closed_source_verified_and_policy_immutable(self):
        self.assertEqual(self.row["schema_version"],m.SCHEMA)
        policy=self.verify();self.assertEqual(policy.descriptors(),[self.pair])
        with self.assertRaises(AttributeError):policy.index=166
        with self.assertRaises(TypeError):policy.producer_pin["bytes"]=0
    def test_successful_or_observed_body_never_aliased(self):
        for key,value in (("state","PASS"),("product_body_observed",True),("actual_product_child_executed",True)):
            before=self.root[key];self.root[key]=value
            with self.assertRaises(ValueError):self.verify()
            self.root[key]=before
    def test_worker_cleanup_and_current_generation_flags_rejected(self):
        for key in ("worker_created","current_generation_runtime_candidate_qualified","Native_source_frame_qualified"):
            self.root[key]=True
            with self.assertRaises(ValueError):self.verify()
            self.root[key]=False
        self.root["cleanup_confirmed"]=False
        with self.assertRaises(ValueError):self.verify()
    def test_unresolved_or_byte_observed_frame_rejected(self):
        for frame in (dict(frame_state="COMMITTED",registered_live_frame=False),
            dict(frame_state="CLOSED",registered_live_frame=False,actual_byte_boundaries=[{}])):
            self.root["source_frame"]=frame
            with self.assertRaises(ValueError):self.verify()
    def test_current_future_other_case_and_boolean_context_rejected(self):
        for path in (self.old["path"].replace("002","004"),self.old["path"].replace("002","007"),self.old["path"].replace("case165","case164")):
            with self.assertRaises(ValueError):m.root_attempt(dict(self.old,path=path),165,4,scope)
        with self.assertRaises(ValueError):m.root_attempt(self.old,165,True,scope)
    def test_changed_physical_bytes_rejected(self):
        self.encoded=b"tampered"
        with self.assertRaises(ValueError):self.verify()
    def test_changed_semantic_pin_and_physical_destination_rejected(self):
        self.pair["semantic_original_pin"]=dict(self.old,sha256="d"*64)
        with self.assertRaises(ValueError):self.verify()
        self.pair["semantic_original_pin"]=self.old;self.pair["physical_envelope_pin"]=dict(self.new,path=m.PREFIX+"wrong.json")
        with self.assertRaises(ValueError):self.verify()
    def test_incomplete_final_hashes_wrong_accounting_and_bad_code_rejected(self):
        for key,value in (("final_fresh_hashes",0),("decode_passes",1),("original_bytes",1)):
            before=self.row[key];self.row[key]=value
            with self.assertRaises(ValueError):self.verify()
            self.row[key]=before
        self.code["contracts"]["skipped"]=1
        with self.assertRaises(ValueError):self.verify()
    def test_duplicate_pair_and_undeclared_original_rejected(self):
        self.row["closed_descriptors"].append(copy.deepcopy(self.pair))
        with self.assertRaises(ValueError):self.verify()
        self.row["closed_descriptors"].pop();self.row["fresh_input_pins"].remove(self.old)
        self.row["fresh_inputs"]-=1;self.row["final_fresh_hashes"]-=1
        with self.assertRaises(ValueError):self.verify()
    def test_default_namespace_not_modified(self):
        import runtime_envelope_scope_binding_v1 as default
        original=default.source.descriptor
        with self.assertRaises(ValueError):m.install(default,self.verify())
        self.assertIs(default.source.descriptor,original)
    def test_private_binding_keeps_scope_methods_and_explicit_new_policy(self):
        module=self.module();before=module.Binding.validate_scope_evidence
        m.install(module,self.verify());bound=module.Binding([self.pair],self.producer_pin,next_case=165)
        projection,proof=bound.project({self.old["path"]:self.old,self.producer_pin["path"]:self.producer_pin},lambda:None)
        self.assertIn(self.old["path"],projection.semantic_pins);self.assertIn(self.new["path"],projection.physical_pins)
        self.assertIs(module.Binding.validate_scope_evidence,before)
        self.assertEqual(bound.representation(projection)["closed_prebody_source_policy"]["index"],165)
    def test_unlisted_current_source_still_rejected_after_install(self):
        module=self.module();m.install(module,self.verify())
        other=dict(self.old,path=self.old["path"].replace("002","003"))
        with self.assertRaises(ValueError):module.source.descriptor(other,self.new,next_case=165)
    def test_wrong_case_or_pin_rejected_by_installed_descriptor(self):
        module=self.module();m.install(module,self.verify())
        with self.assertRaises(ValueError):module.source.descriptor(self.old,self.new,next_case=166)
        with self.assertRaises(ValueError):module.source.descriptor(dict(self.old,bytes=1),self.new,next_case=165)
    def test_ordinary_prior_and_unmapped_file_not_removed(self):
        module=self.module();m.install(module,self.verify())
        prior_old=dict(self.old,path=self.old["path"].replace("case165","case164"))
        prior_new=dict(self.new,path=self.new["path"].replace("case165","case164"))
        self.assertEqual(module.source.descriptor(prior_old,prior_new,next_case=165)["semantic_original_pin"],prior_old)
        ordinary=dict(path="Cargo.toml",bytes=1,sha256="f"*64)
        bound=module.Binding([self.pair],self.producer_pin,next_case=165)
        projection,proof=bound.project({self.old["path"]:self.old,self.producer_pin["path"]:self.producer_pin,ordinary["path"]:ordinary},lambda:None)
        self.assertEqual(dict(projection.physical_pins["Cargo.toml"]),ordinary)
        self.assertEqual(len(projection.semantic_pins),len(projection.physical_pins))


if __name__=="__main__":unittest.main()
