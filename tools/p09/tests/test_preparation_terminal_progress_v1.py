from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preparation_terminal_progress_v1 as m

class Tests(unittest.TestCase):
    def reader(self):
        def forbidden(*args,**kwargs):raise AssertionError("No new read or checkpoint")
        return NS(snapshots={"a":{},"b":{}},read_passes=7,bytes_read=900,
            final_fresh_hashes=1,checkpoint=forbidden,json=forbidden,pin=forbidden,finish=forbidden)
    def test_no_reader_after_admission_stop(self):
        row=m.summary(None,"admission")
        self.assertFalse(row["reader_created"])
        self.assertNotIn("read_passes",row)
    def test_existing_partial_counters_only(self):
        q=self.reader();row=m.summary(q,"final_freshness")
        self.assertEqual((row["bound_inputs"],row["read_passes"],row["bytes_read"],row["final_fresh_hashes"]),(2,7,900,1))
        self.assertFalse(row["additional_read_or_sample_or_retry"])
    def test_whole_binding_stop_is_not_pass(self):
        row=m.summary(self.reader(),"whole_binding")
        self.assertFalse(row["whole_scope_or_runtime_qualified"])
    def test_completed_label_does_not_authorize_runtime(self):
        row=m.summary(self.reader(),"completed")
        self.assertFalse(row["whole_scope_or_runtime_qualified"])
    def test_other_phase_rejected(self):
        with self.assertRaises(ValueError):m.summary(self.reader(),"GO")
    def test_boolean_counter_rejected(self):
        q=self.reader();q.bytes_read=True
        with self.assertRaises(ValueError):m.summary(q,"whole_binding")
    def test_negative_counter_rejected(self):
        q=self.reader();q.read_passes=-1
        with self.assertRaises(ValueError):m.summary(q,"whole_binding")
    def test_final_count_greater_than_inventory_rejected(self):
        q=self.reader();q.final_fresh_hashes=3
        with self.assertRaises(ValueError):m.summary(q,"final_freshness")
    def test_mapping_type_rejected_without_iteration(self):
        q=self.reader();q.snapshots=[]
        with self.assertRaises(ValueError):m.summary(q,"whole_binding")
if __name__=="__main__":unittest.main()
