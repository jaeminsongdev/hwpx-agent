"""Current-case wire isolation and same private whole connector graph."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
import unittest
from types import FunctionType,SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).parents[1]))
sys.path.insert(0,str(Path(__file__).parent))
import current_queue_successor_connections as m
import current_queue_successor_binding as bindings
import current_stored_runtime_scope as scope
import runtime_envelope_namespace_bundle_v1 as loader
import owned_source_read_pressure as byte_policy
import runtime_envelope_worker_connection_v1 as default_worker

ROOT=Path(__file__).parents[3]


def fixture(index=161,run=1):
    module,proof=bindings.connect(ROOT,loader,scope,index,{})
    def pin(name,raw):return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    old=pin(f"implementation/p09/evidence/p09-361-case{index-1}-current-runtime-run001.v1.json",b"receipt")
    encoded=pin(module.source.PREFIX+f"case{index-1}-runtime-run001.envelope.v1.json",b"encoded")
    manifest=pin("implementation/p09/evidence/fixture-current-connection.v1.json",b"manifest")
    bound=module.Binding([module.source.descriptor(old,encoded,next_case=index)],manifest,next_case=index)
    authority=pin(f"implementation/p09/evidence/p09-361-case{index-1}-current-epoch-accept001.v1.json",b"authority")
    step=dict(index=index,before=index-7,prior_queue_pin=authority,prior_candidate_pin=old)
    graph,proof=m.connect(ROOT,loader,byte_policy,module,bound,step,run,lambda:None)
    return graph,proof,step


class Tests(unittest.TestCase):
    def test_extra_selector_only_prior_unmapped_receipts_in_size_order(self):
        def pin(name,size):return dict(path=name,bytes=size,sha256="a"*64)
        rows=[pin(f"implementation/p09/evidence/p09-361-case{i}-current-runtime-run001.v1.json",size)
            for i,size in ((112,5),(113,9),(114,9),(161,100))]
        rows+=[pin("crates/product-cli/src/lib.rs",1000),pin("target/current.exe",1000)]
        mapped=[dict(semantic_original_pin=rows[0])]
        selected=m.select_extra_receipts(scope,rows,mapped,161,2)
        self.assertEqual(selected,rows[1:3])
        with self.assertRaises(ValueError):m.select_extra_receipts(scope,rows,mapped,161,3)
        for count in (True,-1,7,"1",1.0):
            with self.assertRaises(ValueError):m.select_extra_receipts(scope,rows,mapped,161,count)

    def test_one_private_namespace_and_source_pins(self):
        graph,proof,step=fixture()
        self.assertTrue(proof["one_private_binding_namespace"])
        self.assertEqual(len(proof["source_proofs"]),len(m.PINS))
        self.assertIs(graph.parent.access.source,graph.binding_module)
        self.assertIs(graph.full_oracle.binding_module,graph.binding_module)
        self.assertFalse(proof["GO_authorized"])

    def test_roundtrip_all_rows_without_original_receipt_IO(self):
        graph,proof,step=fixture();api=graph.worker
        wire,pin=api.encode(graph.binding,step["prior_queue_pin"],step["prior_candidate_pin"],lambda:None)
        with patch.object(Path,"open",side_effect=AssertionError("NO_HISTORY_IO")):
            decoded,proof=api.decode(wire,pin,lambda:None)
        self.assertEqual(decoded.descriptors(),graph.binding.descriptors())
        self.assertEqual(dict(decoded.manifest_pin),dict(graph.binding.manifest_pin))
        self.assertEqual(proof["historical_receipt_files_read_by_capsule_decoder"],0)
        self.assertLessEqual(len(wire),16384)

    def test_late_case_and_no_default_namespace_mutation(self):
        before=default_worker.TASK;code=default_worker.encode.__code__
        graph,proof,step=fixture(249,8)
        wire,pin=graph.worker.encode(graph.binding,step["prior_queue_pin"],step["prior_candidate_pin"],lambda:None)
        decoded,_=graph.worker.decode(wire,pin,lambda:None)
        self.assertEqual(decoded.next_case,249)
        self.assertEqual(graph.worker.TASK,"case249-current-r008-tests")
        self.assertEqual(default_worker.TASK,before);self.assertIs(default_worker.encode.__code__,code)
        original=graph.namespaces.runtime_envelope_worker_connection_v1.connect_worker
        self.assertIs(graph.worker.connect_worker.__code__,original.__code__)

    def test_other_case_or_transport_tamper_rejected(self):
        graph,_,step=fixture();wire,pin=graph.worker.encode(graph.binding,step["prior_queue_pin"],step["prior_candidate_pin"],lambda:None)
        with self.assertRaises(ValueError):graph.worker.decode(wire,dict(pin,sha256="0"*64),lambda:None)
        for key in ("context","descriptor_context"):
            row=json.loads(wire);row[key][1]=162
            changed=json.dumps(row).encode("ascii");bad=dict(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest())
            with self.assertRaises(ValueError):graph.worker.decode(changed,bad,lambda:None)
        other,_,other_step=fixture(162)
        with self.assertRaises(ValueError):other.worker.decode(wire,pin,lambda:None)

    def test_resource_stop_identity_and_no_auto_retry(self):
        graph,_,step=fixture();error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:graph.worker.encode(graph.binding,step["prior_queue_pin"],step["prior_candidate_pin"],stop)
        self.assertIs(caught.exception,error)
        policy=graph.namespaces.runtime_envelope_raw_access_policy_v1.Policy(ROOT,graph.binding,lambda:False,lambda:None)
        execute,state=graph.worker.connect_worker(lambda task:7,policy)
        self.assertEqual(execute(graph.worker.TASK),7)
        with self.assertRaises(ValueError):execute(graph.worker.TASK)
        self.assertEqual(state.calls,1)

    def test_closed_run_count_and_original_function_inverse(self):
        for index in (161,162,165,167,249):
            graph,_,step=fixture(index)
            for run in (True,0,9,"1",1.0):
                with self.assertRaises(ValueError):m.worker_api(graph.namespaces.runtime_envelope_worker_connection_v1,
                    graph.namespaces.compact_worker_capsule_wire_v1,graph.binding_module,step,run)
        graph,_,step=fixture();bad=copy.deepcopy(step);bad["before"]=153
        with self.assertRaises(ValueError):m.worker_api(graph.namespaces.runtime_envelope_worker_connection_v1,
            graph.namespaces.compact_worker_capsule_wire_v1,graph.binding_module,bad,1)

    def connected_parent_fixture(self):
        from test_runtime_envelope_parent_connection_v1 import make_engine
        engine,old,semantic,held,made,seen,error=make_engine()
        module,_=bindings.connect(ROOT,loader,scope,161,{})
        rows=[dict(row,next_case=161) for row in old.descriptors()]
        bound=module.Binding(rows,dict(old.manifest_pin),next_case=161)
        unused,_,step=fixture()
        graph,proof=m.connect(ROOT,loader,byte_policy,module,bound,step,1,lambda:None)
        connected,state=graph.parent.connect_engine(engine,bound)
        return graph,connected,state,semantic,held,engine

    def test_current_parent_keeps_real_fixture_frame_two_reads_and_cleanup(self):
        graph,engine,state,semantic,held,original=self.connected_parent_fixture()
        code=original.run_owned.__code__;worker=original.worker
        row=engine.run_owned(1)
        self.assertIs(original.run_owned.__code__,code);self.assertIs(engine.worker,worker)
        self.assertEqual(row["source_input_representation"]["next_case"],161)
        self.assertEqual(len(row["source_frame"]["actual_byte_boundaries"]),2)
        self.assertEqual(row["aggregate_envelope_decoder"]["completed_decodes"],2)
        self.assertTrue(state.frames[0].raw_policy.restored)
        self.assertFalse(held.open)
        self.assertEqual(state.bootstrap_calls,1)

    def test_current_full_oracle_keeps_whole_checker_and_failure(self):
        from test_runtime_envelope_full_oracle_connection_v1 import generator
        graph,engine,state,semantic,held,original=self.connected_parent_fixture()
        row=engine.run_owned(1);row["original_terminal_predicate"]=True
        original_generator=FunctionType(generator.__code__,dict(generator.__globals__,
            original=NS(scope=scope),ORACLE_SCOPE=scope,mechanics_projection=lambda node:node),closure=generator.__closure__)
        def budget(rows,requests):return dict(unchanged_lock_deadline_seconds=600,
            unallocated_margin_seconds=60,predicted_runtime_combined_seconds=590.0)
        project,observed=graph.full_oracle.projector(original_generator,graph.binding,budget,lambda:None)
        current={graph.binding.manifest_pin["path"]:dict(graph.binding.manifest_pin)}
        check,proof=project(b"fixture-source",row,current,semantic)
        result=check(row,current,semantic,None,lambda:None)
        self.assertTrue(result["original_terminal_checked"])
        self.assertEqual(result["model"]["predicted_runtime_combined_seconds"],595.0)
        self.assertTrue(proof["whole_original_checker_code_retained"])
        row["original_terminal_predicate"]=False
        with self.assertRaisesRegex(ValueError,"ORIGINAL_TERMINAL_FAILURE"):check(row,current,semantic,None,lambda:None)


if __name__=="__main__":unittest.main()
