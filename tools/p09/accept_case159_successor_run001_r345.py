"""Original full optimized acceptance, explicit current159/run001 facade only.

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

SELF="tools/p09/accept_case159_successor_run001_r345.py"
ROOT=dict(path="implementation/p09/evidence/p09-361-case159-current-runtime-run001.v1.json",
    bytes=4580676,sha256="090e2e069852a45d2db306f9968c2ca997962222e3bc622c7c10c7dee2d830d2")
DIAGNOSTIC="implementation/p09/evidence/p09-361-case159-optimized-acceptance-attempt001.v2.json"


def facade(m):
    m.require(m.base.CONFIG is not None and m.base.CONFIG.index==159 and m.base.CONFIG.before==152,
              "EXACT_CURRENT159_ACCEPTANCE_FACADE")
    source=m.old.API.accept.__globals__["source"]
    # All old snapshot/prior/metadata/oracle dependencies remain. Only the exact
    # independently executed root pathname is provided to the generic runner.
    private_source=NS(**{**vars(source),"root_path":m.RETRY.root_path})
    return NS(**{**vars(m),"source":private_source})


def main():
    import flat_current_queue_envelope_runtime_v27 as controller
    m=controller.M;m.base.configure(159);runtime=facade(m)
    import current_successor_acceptance_prepare_v1 as adapter
    errors=[]
    def traced_prepare(*args,**kwargs):
        try:
            q=args[0]
            proof=q.json("implementation/p09/evidence/p09-361-case159-successor-full-prepare-r751.v1.json")
            m.a.fields(proof,dict(state="PASS_CURRENT159_SUCCESSOR_FULL_READ_ONLY_PREPARE_NOT_QUEUE_ACCEPTANCE",
                runtime_pin=ROOT,accepted_count_delta=0,product_or_Native_reexecuted=False,
                queue_acceptance_called=False,cleanup_confirmed=True),"QUALIFIED_FULL_CURRENT_PREPARE_ONLY")
            for source_pin in proof["source_pins"]:
                m.a.exact(q.pin(source_pin["path"]),source_pin,"CURRENT_FULL_PREPARE_CODE_BYTES")
            return adapter.prepare(*args,m=m,**kwargs)
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
            import traceback
            import re
            fields=dict(error_type=type(error).__name__,
                frames=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
                    for x in traceback.extract_tb(error.__traceback__)[-12:]])
            if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
                fields["closed_error_symbol"]=error.args[0]
            errors.append(fields)
            raise
    runtime.API=NS(**{**vars(m.API),"prepare":traced_prepare,"accept":m.old.API.accept})
    canonical=m.c.ROOT/"implementation/p09/evidence/p09-361-case159-current-epoch-accept001.v1.json"
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
        accepted_count_delta=row.get("accepted_count_delta"),cleanup_confirmed=row.get("cleanup_confirmed"),
        safe_prepare_errors=errors)))
    return 0 if row["state"].startswith("PASS_") and row.get("cleanup_confirmed") is True else 1


if __name__=="__main__":raise SystemExit(main())
