"""Measure original160 binding read multiplicity; no Native/product/retry.

Counts only request metadata after each unchanged original _read returns.
No payload/hash/JSON cache, extra sampler, rate or deadline change.
"""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback

k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
p=k.GetCurrentProcess()
if not (k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import terminal_metadata_pressure_v1 as pressure

SELF="tools/p09/trace_successor160_binding_reads_r352.py"
REVIEW="implementation/p09/evidence/p09-361-case160-run001-shared-metadata-stop-review-r770.v1.json"


class Reader(a.AcceptanceReader):
    def __init__(self,root,checkpoint):
        super().__init__(root,checkpoint)
        self.multiplicity={}
    def _read(self,name,parse=False):
        pin,raw=super()._read(name,parse=parse)
        a.require(len(self.multiplicity)<4096 or name in self.multiplicity,"BOUNDED_READ_MULTIPLICITY")
        row=self.multiplicity.setdefault(name,dict(path=name,calls=0,bytes=0))
        # Non-parsing original reads deliberately return no payload.
        # The just-completed original read's pin contains its byte count.
        row["calls"]+=1;row["bytes"]+=pin["bytes"]
        return pin,raw


def summary(reader):
    rows=[dict(r,repeat_bytes=r["bytes"]-r["bytes"]//r["calls"]) for r in reader.multiplicity.values()]
    return dict(request_count=sum(r["calls"] for r in rows),read_bytes=sum(r["bytes"] for r in rows),
        unique_paths=len(rows),repeated_read_bytes=sum(r["repeat_bytes"] for r in rows),
        top_repeated_sources=sorted((r for r in rows if r["calls"]>1),
            key=lambda r:r["repeat_bytes"],reverse=True)[:16],
        counts_only_no_payload_or_hash_or_JSON_cache=True)


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=Reader(a.c.ROOT,g.check)
        import flat_current_queue_envelope_runtime_v28 as controller
        m=controller.M;m.base.configure(160)
        pins=[q.pin(path) for path in (SELF,m.SELF,m.TEST,pressure.SELF,pressure.TEST)]
        review=q.json(REVIEW)
        a.fields(review,dict(state="REVIEW_ACTUAL160_SHARED_METADATA_DEADLINE_NOT_RUNTIME_OR_ACCEPTANCE_PASS",
            stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",cleanup_confirmed=True,
            whole_Runtime_or_two_byte_boundary_qualified=False),"EXACT_PRESERVED160_STOP_REVIEW")
        a.exact(q.pin(review["runtime_pin"]["path"]),review["runtime_pin"],"ORIGINAL_FAILED160_UNCHANGED")
        required,rust=m.binding(q)
        out["binding_reads_before_final"]=summary(q)
        a.exact(out["binding_reads_before_final"]["read_bytes"],q.bytes_read,"ALL_ORIGINAL_READS_COUNTED")
        q.finish();g.check(force=True)
        a.exact(summary(q)["read_bytes"],q.bytes_read,"FINAL_ORIGINAL_READS_COUNTED")
        out.update(state="PASS_ORIGINAL160_WHOLE_BINDING_READ_MULTIPLICITY_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            source_pins=pins,full_source_scope=len(required),rust_source_count=len(rust),
            source_pairs=len(m.graph_value().binding.descriptors()),all_reads_including_final=summary(q),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
