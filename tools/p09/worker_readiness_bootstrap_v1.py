"""Explicit owned-worker entry for the readiness candidate, never Native CLI.

Only a genuine inherited event is accepted. The protocol is source-pinned in
a private namespace, not another default project-module import. The complete
unchanged public worker still validates its task, capsule, Job and original GO.
"""
import hashlib
import re
import runpy
import sys
from pathlib import Path

SELF="tools/p09/worker_readiness_bootstrap_v1.py"
PROTOCOL=dict(path="tools/p09/worker_readiness_v1.py",bytes=6890,
    sha256="047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45")
WORKER=dict(path="tools/p09/xz_unified_runtime_v1.py",bytes=23320,
    sha256="d1daf6cd120e11ea81472aa76d80b6af17afe01a2c1c2b7323bea4daef3a2af9")


def require(ok,label):
    if not ok:raise ValueError("READINESS_BOOTSTRAP_"+label)


def main():
    arguments=sys.argv[1:]
    require(len(arguments)==4 and arguments[::2]==["--ready-handle","--task"],"ONLY_EXPLICIT_OWNED_WORKER")
    value,task=arguments[1],arguments[3]
    require(re.fullmatch(r"[1-9][0-9]{0,19}",value) is not None and int(value)<2**64,"INHERITED_HANDLE_INTEGER")
    require(re.fullmatch(r"case165-current-r00[89]-tests",task) is not None,"ONLY_CURRENT_OR_SUCCESSOR_TASK")
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/"tools/p09"))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    require(c.ROOT==root,"SAME_REPOSITORY")
    protocols,_=envelope.namespace_bundle.load(root,[PROTOCOL],{})
    protocol=protocols.worker_readiness_v1
    raw=(root/WORKER["path"]).read_bytes()
    require(len(raw)==WORKER["bytes"] and hashlib.sha256(raw).hexdigest()==WORKER["sha256"],"UNCHANGED_PUBLIC_WORKER_SOURCE")
    event=protocol.WindowsEvent(int(value));original=sys.stdin
    try:
        sys.stdin=protocol.ReadyReader(original,event)
        sys.argv=[str(root/WORKER["path"]),"--owned-worker","--task",task]
        # No virtual GO, private replacement worker or skipped original main.
        runpy.run_path(sys.argv[0],run_name="__main__")
    finally:
        sys.stdin=original;event.close()


if __name__=="__main__":main()
