import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_failed_run003_v1 as m

def exact(a,b,label):
    if type(a) is not type(b):raise ValueError(label)
    if type(b) is dict:
        if set(a)!=set(b):raise ValueError(label)
        for k,v in b.items():exact(a[k],v,label)
    elif type(b) is list:
        if len(a)!=len(b):raise ValueError(label)
        for x,y in zip(a,b):exact(x,y,label)
    elif a!=b:raise ValueError(label)
def require(ok,label):
    if not ok:raise ValueError(label)
def fields(row,expected,label):
    for k,v in expected.items():exact(row.get(k),v,label)
def pins(values,count):
    require(type(values) is list and len(values)==count,"pins")
    result={p["path"]:p for p in values};require(len(result)==count,"duplicate");return result
API=NS(exact=exact,require=require,fields=fields,scope=NS(pins=pins))
def row():
    values=[dict(path="p"+str(i),bytes=1,sha256="a"*64) for i in range(2801)]
    values[0]["bytes"]+=247714063-2801
    return dict(state="STOPPED_NOT_ACCEPTED",selected_test_index=160,task="case160-current-r003-tests",
        stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",operation_phase="final_source_freeze",cleanup_confirmed=True,
        owned_tree_empty=True,actual_product_child_executed=True,product_body_observed=True,accepted_count_delta=0,
        Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,source_freeze=values,
        source_frame=dict(frame_state="CLOSED",registered_live_frame=False,input_count=2801,input_bytes=247714063,
            actual_byte_boundaries=[dict(role="before",actual_byte_pins=copy.deepcopy(values),
                reader_diagnostics=dict(read_passes=2801,bytes_read=247714063))],
            handles=dict(input_lock_handles_opened=3173,input_lock_handles_closed=3173,input_lock_handles_remaining=0,
                input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,active_reader_bindings=0,active_byte_streams=0,
                maximum_lock_seconds=600,byte_stream_identity_checks=5589,borrowed_byte_streams=dict(logical_views_opened=5589,
                    logical_views_closed=5589,logical_views_remaining=0,logical_view_close_failed_attempts=0,active_borrow_binding=False))),
        aggregate_envelope_decoder=dict(aggregate_limit_seconds=5.0,attempted_decodes=44,completed_decodes=44,
            active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True))
class Tests(unittest.TestCase):
    def setUp(self):self.row=row()
    def test_exact_failure_is_not_accepted_or_retry_permission(self):
        result=m.review(self.row,API);self.assertFalse(result["whole_Runtime_or_two_byte_boundary_qualified"])
        self.assertFalse(result["retry_or_GO_authorized"])
    def test_pass_state_rejected(self):
        self.row["state"]="PASS"
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_committed_frame_rejected(self):
        self.row["source_frame"]["frame_state"]="COMMITTED"
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_second_boundary_not_fabricated(self):
        self.row["source_frame"]["actual_byte_boundaries"].append(copy.deepcopy(self.row["source_frame"]["actual_byte_boundaries"][0]))
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_first_boundary_pin_drift_rejected(self):
        self.row["source_frame"]["actual_byte_boundaries"][0]["actual_byte_pins"][0]["sha256"]="b"*64
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_open_handle_rejected(self):
        self.row["source_frame"]["handles"]["input_lock_handles_remaining"]=1
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_borrowed_view_leak_rejected(self):
        self.row["source_frame"]["handles"]["borrowed_byte_streams"]["logical_views_remaining"]=1
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_partial_decoder_not_full_pass(self):
        self.row["aggregate_envelope_decoder"]["completed_decodes"]=58
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_bool_delta_rejected(self):
        self.row["accepted_count_delta"]=False
        with self.assertRaises(ValueError):m.review(self.row,API)
    def test_original_resource_exception_not_replaced(self):
        error=ValueError("ORIGINAL_STOP")
        def stop(*args):raise error
        with self.assertRaises(ValueError) as caught:m.review(self.row,NS(**{**vars(API),"fields":stop}))
        self.assertIs(caught.exception,error)
if __name__=="__main__":unittest.main()
