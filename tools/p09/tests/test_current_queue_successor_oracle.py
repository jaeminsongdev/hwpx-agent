"""Exact whole-oracle connection and independently declared expected scope."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS,FunctionType
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
sys.path.insert(0,str(Path(__file__).parent))
import current_queue_successor_oracle as m
import current_queue_successor_connections as metadata
import current_stored_runtime_scope as scope
import runtime_envelope_namespace_bundle_v1 as loader
from test_current_queue_successor_connections import fixture

ROOT=Path(__file__).parents[3]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import case160_run007_controller as old
        cls.legacy=old.CURRENT

    def connection(self,index=161):
        graph,_,unused=fixture(index,2)
        step=NS(index=index,before=index-7)
        inherited={graph.binding.manifest_pin["path"]:dict(graph.binding.manifest_pin)}
        for row in graph.binding.descriptors():inherited[row["semantic_original_pin"]["path"]]=row["semantic_original_pin"]
        connected,proof=m.connect(self.legacy,graph,step,NS(),inherited,lambda:None)
        return connected,proof,inherited

    def test_entire_original_full_validator_inverse_and_default_family_unchanged(self):
        original=self.legacy.M.validate_candidate;before=dict(original.__globals__)
        connected,proof,inherited=self.connection()
        inverse=metadata.project(connected.validate_candidate,connected.environment,{161:160})
        self.assertEqual(inverse.__code__,original.__code__)
        self.assertIs(inverse.__defaults__,original.__defaults__)
        self.assertIs(inverse.__closure__,original.__closure__)
        self.assertEqual(original.__globals__,before)
        self.assertTrue(proof["independent_declared_scope_not_current_observations"])
        self.assertFalse(proof["actual_current_candidate_or_Native_or_product_qualified"])

    def test_current_guard_and_complete_window_projection(self):
        connected,proof,inherited=self.connection()
        connected.environment["only159"]()
        check=connected.environment["prior"].WINDOW_LINK.check_evidence
        current,proof=connected.environment["window"].connect(check)
        with self.assertRaises(ValueError):current({"selected_test_index":160},connected.environment["a"])
        frozen,_=self.legacy.M.validate_candidate.__globals__["window"].connect(check)
        inverse=metadata.project(current,current.__globals__,{161:160})
        self.assertEqual(inverse.__code__,frozen.__code__)

    def test_scope_is_copied_before_caller_changes_and_metadata_late_case(self):
        connected,proof,inherited=self.connection(249)
        count=len(inherited);inherited.clear()
        self.assertEqual(proof["inherited_input_count"],count)
        connected.environment["only159"]()
        original=self.legacy.M.validator
        inverse=metadata.project(connected.validator,connected.environment,{249:160})
        self.assertEqual(inverse.__code__,original.__code__)

    def test_original_guard_error_is_not_relabelled(self):
        graph,_,unused=fixture();error=ValueError("ORIGINAL_GUARD_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:m.connect(self.legacy,graph,NS(index=161,before=154),NS(),{},stop)
        self.assertIs(caught.exception,error)

    def test_projector_uses_declared_scope_even_when_candidate_omits_it(self):
        graph,_,unused=fixture(161,2)
        base_pin=dict(graph.binding.manifest_pin)
        body={base_pin["path"]:base_pin};current=dict(body)
        required={**body,**{r["semantic_original_pin"]["path"]:r["semantic_original_pin"] for r in graph.binding.descriptors()}}
        extra=dict(path="crates/product-cli/src/independent-not-observed.rs",bytes=1,sha256="a"*64)
        required[extra["path"]]=extra
        original_scope=NS(**{**vars(scope),"compose":lambda old,new:scope.extend(old,new)})
        def original_generator(*args):return None
        generator=FunctionType(original_generator.__code__,dict(original=NS(scope=original_scope),ORACLE_SCOPE=original_scope))
        observed=[]
        def spy(scoped,*args,**kwargs):
            observed.append(scoped.__globals__["ORACLE_SCOPE"].compose(body,current))
            return lambda *args:None,NS()
        graph=NS(**{**vars(graph),"full_oracle":NS(projector=spy)})
        connected,proof=m.connect(self.legacy,graph,NS(index=161,before=154),NS(),required,lambda:None)
        before=dict(generator.__globals__);required.clear()
        candidate={"source_freeze":[]}  # Never used to derive expected pins.
        connected.graph.full_oracle.projector(generator,candidate)
        self.assertEqual(observed[0][extra["path"]],extra)
        self.assertEqual(generator.__globals__,before)
        self.assertEqual(candidate,{"source_freeze":[]})


if __name__=="__main__":unittest.main()
