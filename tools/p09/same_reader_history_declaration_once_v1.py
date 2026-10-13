"""Reuse only the complete historical159 lineage declaration, never rows."""
import copy
import os
import threading
import weakref

SELF="tools/p09/same_reader_history_declaration_once_v1.py"
TEST="tools/p09/tests/test_same_reader_history_declaration_once_v1.py"

def require(ok,label):
    if not ok:raise ValueError("HISTORY_DECLARATION_ONCE_"+label)

def connect(original,expected):
    require(callable(original),"ORIGINAL_COMPLETE_ADMISSION")
    frozen=copy.deepcopy(expected)
    require(type(frozen) is dict and frozen.get("next_case")==159 and
        frozen.get("accepted_count_before")==152 and frozen.get("prior_case")==158 and
        frozen.get("prior_failures_promoted") is False and frozen.get("current159_or_GO_qualified") is False,
        "HISTORICAL_NOT_CURRENT160_OR_PRODUCT")
    records=weakref.WeakKeyDictionary()
    counts=dict(original_complete_admissions=0,duplicate_declarations_avoided=0)
    def admission(q,a,first,second):
        require(type(q.snapshots) is dict and len(q.snapshots)<=4096,"BOUNDED_READER_LEDGER")
        owner=(os.getpid(),threading.get_ident())
        deps=(a,first,second)
        record=records.get(q)
        if (record is not None and type(q.final_fresh_hashes) is int and q.final_fresh_hashes==0 and
            record["owner"]==owner and all(x is y for x,y in zip(deps,record["deps"])) and
            record["checkpoint"] is q.checkpoint and record["code"] is original.__code__ and
            all(q.snapshots.get(path)==pin for path,pin in record["ledger"].items())):
            q.checkpoint()
            require(type(q.final_fresh_hashes) is int and q.final_fresh_hashes==0 and
                all(q.snapshots.get(path)==pin for path,pin in record["ledger"].items()),
                "UNCHANGED_BEFORE_FINAL_AFTER_ORIGINAL_GUARD")
            counts["duplicate_declarations_avoided"]+=1
            return copy.deepcopy(frozen)
        records.pop(q,None)
        result=original(q,a,first,second)
        require(type(result) is dict and result==frozen,"FULL_ORIGINAL_EXACT_DECLARATION_NO_RUNTIME_JSON")
        require(len(q.snapshots)<=4096,"BOUNDED_COMPLETE_LEDGER")
        counts["original_complete_admissions"]+=1
        if type(q.final_fresh_hashes) is int and q.final_fresh_hashes==0:
            records[q]=dict(owner=owner,deps=deps,checkpoint=q.checkpoint,code=original.__code__,
                ledger=copy.deepcopy(q.snapshots))
        return result
    return admission,counts
