import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_additional_observer_connection_v1 as connection


def fake():
    seen=[]
    def fields(data,expected,code):
        seen.append(code)
        for key,value in expected.items():
            if data.get(key)!=value:raise ValueError(code)
    def observer(row):
        original.fields(row["budget"],dict(cost=2.05),"PDH_COST_NOT_OMITTED")
        original.fields(row["serial_CPU_attribution"],dict(additional_PDH_queries_explicit=True),"ONE_ORIGINAL_OBSERVER")
        probes=row["serial_CPU_attribution"]["probes"]
        if len(probes)!=1:raise ValueError("ONE_QUERY_OWNER")
        original.fields(probes[0],dict(query_remaining=False,cleanup_confirmed=True),"PDH_QUERY_CLEANUP")
        original.fields(row["guard"],dict(warning_stops=0),"NEW_ACQUISITION_GUARD")
    old=NS(fields=fields);fn=FunctionType(observer.__code__,dict(original=old))
    row=dict(selected_test_index=147,budget=dict(cost=2.05),guard=dict(warning_stops=0),
     serial_CPU_attribution=dict(backend="NATIVE",additional_PDH_queries_explicit=False,
     probes=[dict(query_remaining=False,cleanup_confirmed=True)]))
    diagnostic=NS(BACKEND="NATIVE",validate=lambda row:True)
    return fn,row,diagnostic,seen,old


class Tests(unittest.TestCase):
    def test_native_record_unchanged_and_three_original_checks_retained(self):
        fn,row,diag,seen,old=fake();before=copy.deepcopy(row)
        proof=connection.dispatch(fn,row,diag)
        self.assertEqual(row,before)
        self.assertEqual(seen,["PDH_COST_NOT_OMITTED","PDH_QUERY_CLEANUP","NEW_ACQUISITION_GUARD"])
        self.assertTrue(proof["original_observer_bytecode_retained"])
        self.assertIs(fn.__globals__["original"],old)

    def test_cost_cleanup_and_acquisition_failure_not_suppressed(self):
        for label in ("budget","guard","serial_CPU_attribution"):
            fn,row,diag,seen,old=fake()
            if label=="budget":row[label]["cost"]=0
            elif label=="guard":row[label]["warning_stops"]=1
            else:row[label]["probes"][0]["cleanup_confirmed"]=False
            with self.assertRaises(ValueError):connection.dispatch(fn,row,diag)

    def test_native_validation_failure_propagates(self):
        fn,row,diag,seen,old=fake()
        def failed(row):raise ValueError("NATIVE_SCHEMA_FAILED")
        diag.validate=failed
        with self.assertRaisesRegex(ValueError,"NATIVE_SCHEMA_FAILED"):connection.dispatch(fn,row,diag)

    def test_historical_original_pdh_check_and_no_native_rebase(self):
        fn,row,diag,seen,old=fake();row["selected_test_index"]=146
        row["serial_CPU_attribution"].pop("backend")
        row["serial_CPU_attribution"]["additional_PDH_queries_explicit"]=True
        connection.dispatch(fn,row,diag)
        self.assertIn("ONE_ORIGINAL_OBSERVER",seen)
        row["serial_CPU_attribution"]["backend"]="NATIVE"
        with self.assertRaises(ValueError):connection.dispatch(fn,row,diag)

    def test_prepare_projection_preserves_code_and_all_other_globals(self):
        fn,row,diag,seen,old=fake()
        def prepare(q):return additional_observer_evidence(q)
        original=FunctionType(prepare.__code__,dict(additional_observer_evidence=fn,marker=old))
        new=connection.connect_projection(lambda raw:original,diag)(b"source")
        self.assertIs(new.__code__,original.__code__)
        self.assertIs(new.__globals__["marker"],old)
        new(row)
        self.assertNotIn("ONE_ORIGINAL_OBSERVER",seen)


if __name__=="__main__":unittest.main()
