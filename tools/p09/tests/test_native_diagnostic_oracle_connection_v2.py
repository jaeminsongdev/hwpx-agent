import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_diagnostic_oracle_connection_v2 as oracle
import flat_current_queue_native_diagnostic_runtime_v9 as v9
from test_native_diagnostic_connection_v1 import fixture
from test_native_diagnostic_connection_v3 import current


class Tests(unittest.TestCase):
    def test_historical147_148_keeps_original_v2(self):
        for index in (147,148):
            row=fixture();row["selected_test_index"]=index;old=copy.deepcopy(row)
            oracle.dispatch(lambda row:False,row)
            self.assertEqual(old,row)

    def test_new149_strict_v3_and_no_legacy_relabel(self):
        row=current();row["selected_test_index"]=149;old=copy.deepcopy(row)
        oracle.dispatch(lambda row:False,row)
        self.assertEqual(row,old)
        wrong=fixture();wrong["selected_test_index"]=149
        with self.assertRaises(ValueError):oracle.dispatch(lambda row:True,wrong)

    def test_historical_new_backend_cannot_be_rebased(self):
        row=current();row["selected_test_index"]=148
        with self.assertRaises(ValueError):oracle.dispatch(lambda row:True,row)

    def test_original_legacy_called_and_types_closed(self):
        seen=[];row=dict(selected_test_index=146,serial_CPU_attribution={})
        self.assertEqual(oracle.dispatch(lambda row:seen.append(row) or "old",row),"old")
        self.assertEqual(seen,[row])
        row["selected_test_index"]=True
        with self.assertRaises(ValueError):oracle.dispatch(lambda row:"old",row)

    def test_real_six_full_code_bodies_and_two_diagnostic_leaves_retained(self):
        source=v9.OLD8._full_prepare.__globals__["source"]
        fn,proof=oracle.connect_full(source.validate_candidate,
          v9.M.source.prior.accepted.original.candidate,v9.M.V3.ORACLE)
        self.assertIs(fn.__code__,source.validate_candidate.__code__)
        self.assertEqual(len(proof["budget"]["cloned_functions"]),6)
        self.assertEqual(proof["budget"]["diagnostic_leaf_changes"],1)
        self.assertEqual(proof["additional"]["retained_leaf_changes"],1)

    def test_original_source_and_resource_failure_not_masked(self):
        row=current();row["selected_test_index"]=149
        row["serial_CPU_attribution"]["probes"][0]["cleanup_confirmed"]=False
        with self.assertRaises(ValueError):oracle.dispatch(lambda row:True,row)
        row=current();row["selected_test_index"]=149
        row["serial_CPU_attribution"]["native_backend_connection"]["original_GO_Job_source_byte_resource_and_cleanup_unchanged"]=False
        with self.assertRaises(ValueError):oracle.dispatch(lambda row:True,row)


if __name__=="__main__":unittest.main()
