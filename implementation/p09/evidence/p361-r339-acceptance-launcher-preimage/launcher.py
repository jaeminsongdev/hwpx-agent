"""Original full optimized acceptance, explicit V25/run005 facade only.

No product replay, new oracle, source exclusion or retroactive Native inputs.
The qualified v1/v2/v3 acceptance readers, AST, guards and writer remain intact.
"""
import ctypes
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS

k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
p=k.GetCurrentProcess()
if not (k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import optimized_current_queue_acceptance_v3 as acceptance

SELF="tools/p09/accept_case158_envelope_run005_r339.py"
ROOT=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run005.v1.json",
    bytes=4404465,sha256="34db0892a40886196a3307ba21decfdcb7ecdede4e6e02feb48422636a54ded4")
DIAGNOSTIC="implementation/p09/evidence/p09-361-case158-optimized-acceptance-attempt001.v2.json"


def facade(m):
    m.require(m.base.CONFIG is not None and m.base.CONFIG.index==158 and m.base.CONFIG.before==151,
              "EXACT_CURRENT158_ACCEPTANCE_FACADE")
    source=m.API.accept.__globals__["source"]
    # All old snapshot/prior/metadata/oracle dependencies remain. Only the exact
    # independently executed root pathname is provided to the generic runner.
    private_source=NS(**{**vars(source),"root_path":m.RETRY.root_path})
    return NS(**{**vars(m),"source":private_source})


def main():
    import flat_current_queue_envelope_runtime_v25 as m
    m.base.configure(158);runtime=facade(m)
    canonical=m.c.ROOT/"implementation/p09/evidence/p09-361-case158-current-epoch-accept001.v1.json"
    m.require(not canonical.exists(),"REFUSE_EXISTING_CANONICAL_ACCEPTANCE")
    m.require(not (m.c.ROOT/DIAGNOSTIC).exists(),"REFUSE_EXISTING_ACCEPTANCE_DIAGNOSTIC")
    def pin(path):
        import hashlib
        # Small fixed qualification files; their own guarded code admission
        # remains mandatory inside the original full acceptance execution.
        m.prior.lean.base.stable.stable.prior.build.direct_path(m.c.ROOT/path,file_required=True)
        with (m.c.ROOT/path).open("rb") as stream:raw=stream.read(256*1024+1)
        m.require(0<len(raw)<=256*1024,"BOUNDED_ACCEPTANCE_QUALIFICATION_BOOTSTRAP")
        return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    row,receipt=acceptance.run(runtime,ROOT,pin(acceptance.prior.prior.QUAL_PATH),
        pin(acceptance.prior.QUAL_PATH),pin(acceptance.QUAL_PATH),DIAGNOSTIC)
    print(json.dumps(dict(state=row["state"],error_code=row.get("error_code"),diagnostic_pin=receipt,
        accepted_count_delta=row.get("accepted_count_delta"),cleanup_confirmed=row.get("cleanup_confirmed"))))
    return 0 if row["state"].startswith("PASS_") and row.get("cleanup_confirmed") is True else 1


if __name__=="__main__":raise SystemExit(main())
