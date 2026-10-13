import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_diagnostic_oracle_connection_v3 as m
from test_native_diagnostic_connection_v1 import fixture as v2
from test_native_diagnostic_connection_v3 import current as v3
from test_native_diagnostic_connection_v4 import current as v4
import flat_current_queue_native_diagnostic_runtime_v12 as runtime

class Tests(unittest.TestCase):
    def row(self,source,index):
        row=source();row["selected_test_index"]=index;return row
    def test_historical_v2_v3_records_keep_original_typed_version(self):
        for index,source in ((147,v2),(148,v2),(149,v3),(150,v3),(152,v3)):
            row=self.row(source,index);before=copy.deepcopy(row)
            m.dispatch(lambda x:None,row);self.assertEqual(row,before)
    def test_new153_v4_and_no_generic_version_or_wrong_source_fallback(self):
        row=self.row(v4,153);m.dispatch(lambda x:None,row)
        for source,index in ((v3,153),(v4,152),(v2,153)):
            with self.assertRaises(ValueError):m.dispatch(lambda x:None,self.row(source,index))
    def test_legacy_and_invalid_indices_not_silently_rebased(self):
        for index in (True,114,250):
            with self.assertRaises(ValueError):m.dispatch(lambda x:None,self.row(v3,index))
        with self.assertRaises(ValueError):m.dispatch(lambda x:None,self.row(v3,146))
    def test_original_full_six_bodies_and_both_diagnostic_leaves(self):
        fn,proof=m.connect_full(runtime.CURRENT_SOURCE.validate_candidate,
             runtime.M.source.prior.accepted.original.candidate,runtime.M.V3.ORACLE)
        self.assertIs(fn.__code__,runtime.CURRENT_SOURCE.validate_candidate.__code__)
        self.assertEqual(len(proof["budget"]["cloned_functions"]),6)
        self.assertEqual(proof["budget"]["diagnostic_leaf_changes"],1)
        self.assertEqual(len(proof["additional"]["cloned_functions"]),6)
        self.assertEqual(proof["additional"]["retained_leaf_changes"],1)
    def test_original_capture_cleanup_and_budget_failures_propagate(self):
        for key,value in (("cleanup_confirmed",False),("maximum_sample_budget_seconds",.1)):
            row=self.row(v4,153);row["serial_CPU_attribution"]["probes"][0][key]=value
            with self.assertRaises(ValueError):m.dispatch(lambda x:None,row)
    def test_version_selection_is_closed_and_no_row_rewriting(self):
        for index,backend in ((148,"V2"),(152,"V3"),(153,"V4"),(249,"V4")):
            self.assertTrue(m.for_index(index).BACKEND.endswith(backend))
        for index in (146,True,250):
            with self.assertRaises(ValueError):m.for_index(index)

if __name__=="__main__":unittest.main()
