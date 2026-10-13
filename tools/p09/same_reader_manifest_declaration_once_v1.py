"""Reuse only a completed159 manifest declaration in one original reader.

First admission invokes the whole unchanged loader. Replay reconstructs typed
Binding from admitted descriptors; file payload/parsed JSON are never retained.
Original final fresh hashes and both live Native byte boundaries remain needed.
"""
import copy
import os
import threading
import weakref

SELF="tools/p09/same_reader_manifest_declaration_once_v1.py"
TEST="tools/p09/tests/test_same_reader_manifest_declaration_once_v1.py"
KEYS={"old_manifest","new_module","successor","failed003","failed004"}


def require(ok,label):
    if not ok:raise ValueError("MANIFEST_DECLARATION_ONCE_"+label)


def connect(original,identity=lambda:(os.getpid(),threading.get_ident())):
    require(callable(original) and callable(identity),"ORIGINAL_LOADER_AND_OWNER")
    owner=identity();records=weakref.WeakKeyDictionary()
    counts=dict(original_complete_admissions=0,duplicate_declarations_avoided=0)
    def load(reader,pin,a,**deps):
        require(identity()==owner,"SAME_OWNER_PROCESS_THREAD")
        require(set(deps)==KEYS,"EXACT_ORIGINAL_DEPENDENCIES")
        require(type(pin) is dict and set(pin)=={"path","bytes","sha256"} and
            type(pin["path"]) is str and type(pin["bytes"]) is int and pin["bytes"]>0 and
            type(pin["sha256"]) is str,"EXACT_MANIFEST_PIN")
        require(type(reader.snapshots) is dict and len(reader.snapshots)<=4096 and
            callable(reader.checkpoint),"BOUNDED_ORIGINAL_READER")
        reader.checkpoint()
        require(type(reader.final_fresh_hashes) is int and reader.final_fresh_hashes==0,"BEFORE_FINAL_FRESH_ONLY")
        values=(a,)+(tuple(deps[k] for k in sorted(KEYS)))
        key=(tuple(id(v) for v in values),tuple(pin[k] for k in ("path","bytes","sha256")))
        rows=records.setdefault(reader,{})
        require(len(rows)<8 or key in rows,"BOUNDED_DECLARATIONS_PER_READER")
        if key in rows:
            packet,ledger,retained=rows[key]
            require(all(v is r for v,r in zip(values,retained)),"IDENTICAL_RETAINED_DEPENDENCIES")
            require(all(reader.snapshots.get(name)==p for name,p in ledger.items()),"UNCHANGED_READER_BINDING_LEDGER")
            module=deps["new_module"]
            bound=module.Binding(copy.deepcopy(packet["descriptors"]),dict(packet["manifest_pin"]),next_case=159)
            require(type(bound) is module.Binding and bound.next_case==159,"SAME_TYPED159_BINDING")
            require(bound.descriptors()==packet["descriptors"] and dict(bound.manifest_pin)==packet["manifest_pin"],
                "EXACT_RECONSTRUCTED_DECLARATION")
            scope={p["path"]:dict(p) for p in packet["scope"]}
            counts["duplicate_declarations_avoided"]+=1
            reader.checkpoint()
            return bound,scope,copy.deepcopy(packet["proof"])
        bound,scope,proof=original(reader,pin,a,**deps)
        require(type(bound) is deps["new_module"].Binding and type(bound.next_case) is int and
            bound.next_case==159 and type(scope) is dict and type(proof) is dict,"WHOLE_ORIGINAL159_RESULT")
        require(dict(bound.manifest_pin)==pin and reader.snapshots.get(pin["path"])==pin,"ADMITTED_REAL_MANIFEST")
        require(type(reader.final_fresh_hashes) is int and reader.final_fresh_hashes==0 and
            len(reader.snapshots)<=4096,"BOUNDED_BEFORE_FINISH_LEDGER")
        packet=copy.deepcopy(dict(descriptors=bound.descriptors(),manifest_pin=dict(bound.manifest_pin),
            scope=list(scope.values()),proof=proof))
        require(len(packet["scope"])==len(scope),"EXACT_SCOPE_DECLARATION")
        rows[key]=(packet,copy.deepcopy(reader.snapshots),values)
        counts["original_complete_admissions"]+=1
        reader.checkpoint()
        return bound,scope,proof
    return load,counts
