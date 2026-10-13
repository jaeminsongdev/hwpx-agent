"""Bounded real binding then public helper inventory; no Native/product."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import flat_current_queue_envelope_runtime_v19 as m
import distinct_final_sample_guard_v1 as distinct
import accept_case112_current_epoch as a


def names():
    return sorted({Path(x.__file__).absolute().relative_to(m.c.ROOT).as_posix()
        for x in tuple(sys.modules.values()) if getattr(x,"__file__",None)
        and Path(x.__file__).absolute().is_relative_to(m.c.ROOT/"tools/p09")
        and Path(x.__file__).suffix==".py"})


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        P09_gate="OPEN",actual_product_or_Native_executed=False)
    try:
        g.acquire();m.base.configure(158);q=a.AcceptanceReader(m.c.ROOT,g.check)
        before=names();m.template();m.binding_attempt(q,1);after=names()
        declared={m.SELF,m.TEST,m.base.SELF,m.base.TEST,m.base.native.SELF,m.base.native.TEST,
            m.base.scope.SELF,m.base.scope.TEST}
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL_BINDING_HELPER_COUNT_DIAGNOSTIC_NOT_PREFLIGHT_OR_PRODUCT",
            imported_before=len(before),imported_after=len(after),added_imports=sorted(set(after)-set(before)),
            declared_nonimported_names=sorted(declared-set(after)),exact_union_count=len(set(after)|declared),
            diagnostic_only_extra_modules=["tools/p09/diagnose_case158_helper_count_r329.py","tools/p09/distinct_final_sample_guard_v1.py"],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out.update(error_type=type(e).__name__)
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
