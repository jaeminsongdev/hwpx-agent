"""Reuse only a completed failure-review declaration within one live reader.

The first complete reviewer and final freshness checks remain mandatory. No
file bytes, parsed runtime rows, or hash calculations are cached. This helper
is not yet connected to a qualified product controller.
"""
import copy
import os
import threading
import weakref

SELF="tools/p09/same_reader_failure_review_once_v1.py"
TEST="tools/p09/tests/test_same_reader_failure_review_once_v1.py"
FIELDS={"failed_runtime_pin","review_pin","original_failure_promoted",
    "queue_acceptance_called","physical_run002_or_GO_authorized"}

def require(ok,label):
    if not ok:raise ValueError("FAILURE_REVIEW_ONCE_"+label)

def connect(original,*,expected_runtime_pin,expected_review_pin):
    require(callable(original),"ORIGINAL_COMPLETE_REVIEWER_REQUIRED")
    expected=(copy.deepcopy(expected_runtime_pin),copy.deepcopy(expected_review_pin))
    for pin in expected:
        require(type(pin) is dict and set(pin)=={"path","bytes","sha256"} and
            type(pin["path"]) is str and type(pin["bytes"]) is int and pin["bytes"]>0 and
            type(pin["sha256"]) is str and len(pin["sha256"])==64 and
            all(c in "0123456789abcdef" for c in pin["sha256"]),"EXACT_EXPECTED_PINS")
    records=weakref.WeakKeyDictionary()
    counts=dict(original_complete_reviews=0,duplicate_declarations_avoided=0)
    def checked(q,a):
        owner=(os.getpid(),threading.get_ident())
        record=records.get(q)
        eligible=(type(q.final_fresh_hashes) is int and q.final_fresh_hashes==0)
        if (record is not None and eligible and record["owner"]==owner and record["api"] is a and
                record["checkpoint"] is q.checkpoint and record["code"] is original.__code__ and
                all(q.snapshots.get(path)==pin for path,pin in record["ledger"].items())):
            q.checkpoint()
            require(q.final_fresh_hashes==0,"BEFORE_FINAL_FRESHNESS_ONLY")
            require(all(q.snapshots.get(path)==pin for path,pin in record["ledger"].items()),
                "LEDGER_UNCHANGED_AFTER_ORIGINAL_CHECKPOINT")
            counts["duplicate_declarations_avoided"]+=1
            return copy.deepcopy(record["declaration"])
        records.pop(q,None)
        row=original(q,a)
        counts["original_complete_reviews"]+=1
        require(type(row) is dict and set(row)==FIELDS,"CLOSED_DECLARATION_NO_RUNTIME_ROW_CACHE")
        require(row["failed_runtime_pin"]==expected[0] and row["review_pin"]==expected[1],"EXACT_REVIEWED_FAILURE")
        require(all(row[name] is False for name in FIELDS-{"failed_runtime_pin","review_pin"}),
            "FAILURE_NOT_PRODUCT_OR_GO_AUTHORIZATION")
        require(all(q.snapshots.get(pin["path"])==pin for pin in expected),"FIRST_COMPLETE_REVIEW_BOUND_BOTH_PINS")
        if eligible and type(q.final_fresh_hashes) is int and q.final_fresh_hashes==0:
            require(len(q.snapshots)<=4096,"BOUNDED_METADATA_LEDGER")
            records[q]=dict(owner=owner,api=a,checkpoint=q.checkpoint,code=original.__code__,
                ledger=copy.deepcopy(q.snapshots),declaration=copy.deepcopy(row))
        return row
    return checked,counts
