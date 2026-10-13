"""One admission per original bootstrap reader; final fresh verification stays.

Only duplicate calls on the same reader/owner before finish may reuse the
already-checked declaration. No shared/cross-reader cache or final-read bypass.
Every retained pin must remain exact in that reader's binding ledger. Caller
results are copied so later changes cannot mutate the retained declaration.
"""
import copy
import os
import threading
import weakref

SELF="tools/p09/same_reader_source_admission_once_v1.py"
TEST="tools/p09/tests/test_same_reader_source_admission_once_v1.py"


def require(ok,code):
    if not ok:raise ValueError("SAME_READER_ADMISSION_"+code)


def connect(original,identity=lambda:(os.getpid(),threading.get_ident())):
    require(callable(original) and callable(identity),"CALLABLES")
    owner=identity();records=weakref.WeakKeyDictionary()
    counts=dict(actual_admissions=0,duplicate_admissions_avoided=0)
    def execute(reader):
        require(identity()==owner,"SAME_OWNER_PROCESS_THREAD")
        require(callable(reader.checkpoint) and type(reader.snapshots) is dict,"ORIGINAL_READER_INTERFACE")
        reader.checkpoint()
        require(type(reader.final_fresh_hashes) is int and reader.final_fresh_hashes==0,"BEFORE_FINAL_FRESH_ONLY")
        if reader in records:
            row,pins=records[reader]
            require(all(reader.snapshots.get(name)==pin for name,pin in pins.items()),"RETAINED_BINDING_LEDGER_UNCHANGED")
            counts["duplicate_admissions_avoided"]+=1
            return copy.deepcopy(row)
        row=original(reader)
        require(type(row) is dict and reader.final_fresh_hashes==0,"ADMISSION_DECLARATION_BEFORE_FINISH")
        records[reader]=(copy.deepcopy(row),copy.deepcopy(reader.snapshots))
        counts["actual_admissions"]+=1
        return row
    return execute,counts
