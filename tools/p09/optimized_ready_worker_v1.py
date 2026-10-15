"""Candidate optimized/readiness entry on the unchanged complete v18 worker.

No Native/graph/acceptance CLI, no successor metadata rebase. A genuine
inherited event and the original worker task/Job/GO checks are mandatory.
All project optimization dependencies are source-pinned private namespaces.
"""
import hashlib
import re
import runpy
import sys
from pathlib import Path

SELF="tools/p09/optimized_ready_worker_v1.py"
WORKER=dict(path="tools/p09/xz_unified_runtime_v1.py",bytes=23320,
    sha256="d1daf6cd120e11ea81472aa76d80b6af17afe01a2c1c2b7323bea4daef3a2af9")
PINS=[dict(path="tools/p09/worker_readiness_v1.py",bytes=6890,
    sha256="047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45"),
    dict(path="tools/p09/ast_clone_namespace_v1.py",bytes=2361,
    sha256="d9f0094355c628cb76743221598032a4007890fe1d08867ea4f54118c3f17b4c"),
    dict(path="tools/p09/ast_copy_namespace_connection_v1.py",bytes=3055,
    sha256="08c1e02736849832490a8dbabf792d0ec96e9ffb136852dd89cebe835bc744ec")]


def require(ok,label):
    if not ok:raise ValueError("OPTIMIZED_READY_WORKER_"+label)


def main():
    arguments=sys.argv[1:]
    require(len(arguments)==4 and arguments[::2]==["--ready-handle","--task"],"ONLY_EXPLICIT_OWNED_WORKER")
    value,task=arguments[1],arguments[3]
    require(re.fullmatch(r"[1-9][0-9]{0,19}",value) is not None and int(value)<2**64,"INHERITED_HANDLE_INTEGER")
    require(re.fullmatch(r"case165-current-r00[89]-tests",task) is not None,"CURRENT_OR_SUCCESSOR_TASK_STILL_CHECKED_BY_ORIGINAL_WORKER")
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"tools/p09"))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    require(c.ROOT==root,"SAME_REPOSITORY")
    modules,_=envelope.namespace_bundle.load(root,PINS,{})
    protocol=modules.worker_readiness_v1;connection=modules.ast_copy_namespace_connection_v1
    loader,proof=connection.connect(envelope.namespace_bundle,modules.ast_clone_namespace_v1)
    proxy=connection.envelope(envelope,loader)
    raw=(root/WORKER["path"]).read_bytes()
    require(len(raw)==WORKER["bytes"] and hashlib.sha256(raw).hexdigest()==WORKER["sha256"],"EXACT_UNCHANGED_UNIFIED_ENTRY")
    del raw
    original=runpy.run_path(str(root/WORKER["path"]),run_name="p09_original_unified_entry")
    event=protocol.WindowsEvent(int(value));stdin=sys.stdin
    try:
        sys.stdin=protocol.ReadyReader(stdin,event)
        sys.argv=[str(root/WORKER["path"]),"--owned-worker","--task",task]
        require(proof["complete_original_loader_code_retained"],"WHOLE_LOADER_PROOF")
        return connection.invoke(original["main"],proxy)
    finally:sys.stdin=stdin;event.close()


if __name__=="__main__":raise SystemExit(main())
