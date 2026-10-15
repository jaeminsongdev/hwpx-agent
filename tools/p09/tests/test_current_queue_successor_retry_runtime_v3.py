"""Closed graph-only retry predicates; fixtures never become Native evidence."""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import copy
import unittest
from unittest.mock import patch
import current_queue_successor_retry_runtime_v3 as m

CHECKPOINT=lambda:None


def require(ok,label):
    if not ok:raise ValueError(label)


def fields(row,expected,label):
    require(all(type(row.get(k)) is type(v) and row[k]==v for k,v in expected.items()),label)


class Tests(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        self.api=NS(require=require,fields=fields)
        self.row=dict(state="FAILED_SUCCESSOR_GRAPH_PREPARATION_NOT_ADOPTED",index=164,accepted_count_delta=0,
            product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN",cleanup_confirmed=True,
            error_code="STOP_TERMINAL_METADATA_WARNING_BEFORE_MORE_WORK",elapsed_seconds=5.0,CPU_max=98.64,RAM_min=45.0)
    def tearDown(self):CHECKPOINT()
    def test_exact_failed_graph_and_no_pass_or_product_substitution(self):
        m.failed_graph(self.row,164,self.api)
        for change in (dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO"),
            dict(product_or_Native_executed=True),dict(GO_authorized=True),dict(cleanup_confirmed=False),
            dict(accepted_count_delta=True),dict(index=165),dict(error_code="OTHER_FAILURE"),dict(worker_created=True)):
            row=dict(self.row,**change)
            with self.assertRaises(ValueError):m.failed_graph(row,164,self.api)
    def test_nonfinite_or_invalid_metric_rejected(self):
        for change in (dict(CPU_max=float("nan")),dict(CPU_max=101),dict(RAM_min=-1),dict(elapsed_seconds=True)):
            with self.assertRaises(ValueError):m.failed_graph(dict(self.row,**change),164,self.api)
    def test_absent_native_reads_real_graph_not_fabricated_native(self):
        calls=[];q=NS(json=lambda name:(calls.append(name) or copy.deepcopy(self.row)),checkpoint=CHECKPOINT)
        bridge=NS(closed_prebody_stop=lambda *args:require(False,"UNEXPECTED_NATIVE_VALIDATION"))
        with patch.dict(m.previous_stops.__globals__,absent=lambda *args:True):m.previous_stops(q,NS(index=164,run=3),self.api,bridge)
        self.assertEqual(calls,["implementation/p09/evidence/p09-361-case164-successor-connections002.v2.json"])
    def test_existing_native_keeps_v2_complete_prebody_validator(self):
        calls=[];row=object();q=NS(json=lambda name:row,checkpoint=CHECKPOINT)
        bridge=NS(closed_prebody_stop=lambda *args:calls.append(args))
        with patch.dict(m.previous_stops.__globals__,absent=lambda *args:False):m.previous_stops(q,NS(index=164,run=3),self.api,bridge)
        self.assertEqual(calls,[(row,164,2,self.api)])
    def test_unresolved_worker_artifact_or_absence_race_rejected(self):
        q=NS(json=lambda name:copy.deepcopy(self.row),checkpoint=CHECKPOINT)
        for decisions in ((True,False),(True,True,True,False)):
            sequence=iter(decisions)
            with patch.dict(m.previous_stops.__globals__,absent=lambda *args:next(sequence)),self.assertRaises(ValueError):
                m.previous_stops(q,NS(index=164,run=3),self.api,NS())
    def test_entry_metadata_changes_no_original_function_body(self):
        def original():return SELF,TEST
        env=dict(original.__globals__,__name__="p09_exact_fixture",SELF="old",TEST="old-test")
        fn=FunctionType(original.__code__,env);bridge=NS(original=fn)
        m.bind_metadata(bridge)
        self.assertIs(bridge.original.__code__,fn.__code__)
        self.assertEqual(bridge.original(),(m.SELF,m.TEST))


if __name__=="__main__":unittest.main()
