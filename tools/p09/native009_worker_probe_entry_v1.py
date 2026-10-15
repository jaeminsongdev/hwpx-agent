"""Diagnostic-only actual run009 worker. ALL subprocess creation is denied.

Do not use as production dispatch: no parent Source Frame is asserted here.
The real original worker/Job/GO/policy body is executed with the full69 graph.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SELF="tools/p09/native009_worker_probe_entry_v1.py"
PINS=[
dict(path="tools/p09/worker_readiness_v1.py",bytes=6890,sha256="047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45"),
dict(path="tools/p09/ast_clone_namespace_v1.py",bytes=2361,sha256="d9f0094355c628cb76743221598032a4007890fe1d08867ea4f54118c3f17b4c"),
dict(path="tools/p09/ast_copy_namespace_connection_v1.py",bytes=3055,sha256="08c1e02736849832490a8dbabf792d0ec96e9ffb136852dd89cebe835bc744ec"),
dict(path="tools/p09/native009_worker_transport_v1.py",bytes=18239,sha256="18f41dfa319f50ac4c5e3aa8623cc8f5c6562a9347f222305b7c9967990e8d2c"),
dict(path="tools/p09/native009_engine_connection_v1.py",bytes=9522,sha256="fee9a1af80ec92b7422db8d4b707422c8b7efe1699fa17336b2a38b258baff18"),
dict(path="tools/p09/prepared_run_closure_v1.py",bytes=23900,sha256="c159da53076f5bb88dce252db163f82a1f1d71522c9dd248349ca615dc84e672"),
dict(path="tools/p09/receipt_xz_envelope_v1.py",bytes=4012,sha256="21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09"),
dict(path="tools/p09/bounded_successor_capsule_wire_v2.py",bytes=5102,sha256="3f604ad4f98c6592e37e6174b11ddac7c73f1f37373738ecc8baa2b6cfb1dd30"),
dict(path="tools/p09/post_product_recovery_window_v1.py",bytes=12876,sha256="ce0dd3fdddc238dd7181d5c12c0a161a2dea74c791dc8053dd99a2b0ca7e8890"),
dict(path="tools/p09/post_product_recovery_connection_v1.py",bytes=8676,sha256="105e55a7534defdd5ea804a03a007c72a96079de042d21fa53d5675064968f77")]
PREFIX="implementation/p09/evidence/p09-361-case165-"
HINT=dict(path=PREFIX+"successor-worker-bootstrap009.v1.json",bytes=8297,sha256="ea5f9e6c6f251053bbe58edeec6739e07012fd452c6f040a1befb8a64df5c879")
WIRE=dict(path=PREFIX+"successor-worker-capsule009.compact.v1.json",bytes=9803,sha256="0b3c5ccb0dc4e80ea395dbccfc6c66b8b0b1e48d72db17ccc03b57870be1e711")


def require(ok,label):
    if not ok:raise ValueError("NATIVE009_PROBE_ENTRY_"+label)


def main():
    arguments=sys.argv[1:]
    require(len(arguments)==4 and arguments[::2]==["--ready-handle","--task"]
        and arguments[3]=="case165-current-r009-tests","ONLY_EXPLICIT_DIAGNOSTIC_TASK9")
    value=arguments[1]
    require(re.fullmatch(r"[1-9][0-9]{0,19}",value) is not None and int(value)<2**64,"INHERITED_EVENT_INTEGER")
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/"tools/p09"))
    import conservative_maintenance as c
    c.Windows()
    import subprocess,copy
    original_copy=copy.deepcopy;observed=dict(expected=None,command_verified=None,historical_runtime_reads=0)
    def audit(event,args):
        if event=="subprocess.Popen":
            expected=observed["expected"];actual=args[1]
            observed["command_verified"]=expected is not None and actual in (expected,subprocess.list2cmdline(expected))
            # Even a mismatched/unexpected command is blocked before OS create.
            raise ValueError("DIAG_SUBPROCESS_DENIED" if observed["command_verified"] else "DIAG_UNEXPECTED_COMMAND_DENIED")
        if event=="open" and args and isinstance(args[0],str) and "current-runtime-run" in args[0].replace("\\","/") and args[0].endswith(".json"):
            observed["historical_runtime_reads"]+=1
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_product_window_runtime_v18 as original_window
    modules,_=envelope.namespace_bundle.load(root,PINS,{})
    xz=modules.receipt_xz_envelope_v1;bounded=modules.bounded_successor_capsule_wire_v2
    window_tool=modules.post_product_recovery_window_v1;recovery=modules.post_product_recovery_connection_v1
    modules.prepared_run_closure_v1.configure_host_policy(c)
    protocol=modules.worker_readiness_v1;optimizer=modules.ast_copy_namespace_connection_v1
    loader,_=optimizer.connect(envelope.namespace_bundle,modules.ast_clone_namespace_v1)
    def read(pin):
        path=root/pin["path"]
        for parent in (path.parent,*path.parent.parents):
            require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_METADATA_ANCESTORS")
            if parent==root:break
        require(path.is_file() and not path.is_symlink() and not path.is_junction(),"DIRECT_METADATA_FILE")
        with path.open("rb") as stream:raw=stream.read(16385)
        require(len(raw)==pin["bytes"]<=16384 and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_BOUNDED_METADATA_PIN")
        return raw
    hint=json.loads(read(HINT));wire=read(WIRE)
    observed["expected"]=[str(root/scope.EXE_PIN["path"]),hint["step"]["case"],"--exact","--test-threads=1","--format=pretty","--color=never"]
    api=modules.native009_worker_transport_v1.connect(root,loader,scope,bytes_policy,xz,bounded,lambda:None,a.exact)
    graph,proof=api.reconstruct(hint,wire,lambda:None)
    linked=modules.native009_engine_connection_v1.build(root,loader,api,graph,original_window,recovery,window_tool,lambda:None)
    event=protocol.WindowsEvent(int(value));stdin=sys.stdin
    try:
        sys.stdin=protocol.ReadyReader(stdin,event)
        try:linked.execute("case165-current-r009-tests")
        except ValueError as error:
            require(error.args in (("WORKER_NOT_AUTHORIZED",),("DIAG_SUBPROCESS_DENIED",)),"EXPECTED_ORIGINAL_WORKER_STOP")
            require(observed["historical_runtime_reads"]==0 and copy.deepcopy is original_copy,"NO_HISTORICAL_RAW_IO_OR_DEFAULT_COPY_MUTATION")
            private=("worker_readiness_v1","ast_clone_namespace_v1","ast_copy_namespace_connection_v1","native009_worker_transport_v1","native009_engine_connection_v1",
                "receipt_xz_envelope_v1","bounded_successor_capsule_wire_v2","post_product_recovery_window_v1","post_product_recovery_connection_v1")
            require(not any(name in sys.modules for name in private),"PRIVATE_HELPERS_NOT_DEFAULT_IMPORTED")
            helpers={Path(filename).absolute() for module in tuple(sys.modules.values()) if (filename:=getattr(module,"__file__",None))
                and Path(filename).absolute().is_relative_to(root/"tools/p09")}
            print(json.dumps(dict(terminal=error.args[0],task=graph.worker.TASK,descriptor_count=len(graph.binding.descriptors()),
                actual_worker_attempts=linked.state.attempts,actual_worker_calls=linked.state.calls,
                original_worker_code=Path(linked.original_worker.__code__.co_filename).name,
                raw_policy_restored=linked.policy.restored,product_command_verified=observed["command_verified"],
                historical_runtime_reads=0,private_helpers_not_default_imported=True,
                child_default_project_helper_count=len(helpers),actual_product_created=False)),file=sys.stderr)
            return 1
    finally:sys.stdin=stdin;event.close()
    raise ValueError("NATIVE009_PROBE_UNEXPECTED_NORMAL_WORKER_RETURN")


if __name__=="__main__":raise SystemExit(main())
