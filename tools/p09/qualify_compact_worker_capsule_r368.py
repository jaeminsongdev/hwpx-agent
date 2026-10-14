"""Actual29 compact wire through unchanged worker encoder/decoder code."""
import ctypes
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest

SELF="tools/p09/qualify_compact_worker_capsule_r368.py"
OUTPUT="implementation/p09/evidence/p09-361-compact-worker-capsule-code14-r841.v1.json"
CAPSULE="implementation/p09/evidence/p09-361-case160-worker-policy-capsule005.compact.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not (k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):
        raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import compact_worker_capsule_wire_v1 as compact
    destination=a.c.ROOT/OUTPUT;capsule_path=a.c.ROOT/CAPSULE
    a.require(not destination.exists() and not capsule_path.exists(),"COMPACT_CAPSULE_EXCLUSIVE_DESTINATIONS")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_COMPACT_CAPSULE_NOT_ACCEPTED",accepted_count_delta=0,
        worker_product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        for path in (SELF,compact.SELF,compact.TEST):q.pin(path)
        result=unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_compact_worker_capsule_wire_v1"))
        a.require(result.wasSuccessful() and result.testsRun==14 and not result.skipped,"ALL_CODE14_CONTRACTS")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160);graph,bootstrap=c.bootstrap.load(c.old,q.checkpoint)
        for pin in bootstrap["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_BOUNDED29_SOURCE")
        original=graph.worker;api,proof=compact.connect(original)
        authority=c._env["current_binding"].successor.AUTHORITY;prior=c._env["current_binding"].successor.ROOT
        raw,raw_pin=original.encode(graph.binding,authority,prior,q.checkpoint)
        wire,wire_pin=api.encode(graph.binding,authority,prior,q.checkpoint)
        restored,decoded=api.decode(wire,wire_pin,q.checkpoint)
        a.exact(restored.descriptors(),graph.binding.descriptors(),"EVERY_ORIGINAL29_DESCRIPTOR")
        a.exact(dict(restored.manifest_pin),dict(graph.binding.manifest_pin),"EXACT_ORIGINAL_MANIFEST028")
        a.exact(compact.unpack(json.loads(wire.decode("ascii"))),json.loads(raw.decode("ascii")),"ALL_ORIGINAL_CAPSULE_FIELDS")
        a.require(len(wire)<len(raw)<=16384 and api.encode.__code__ is original.encode.__code__
            and api.decode.__code__ is original.decode.__code__,"SAME_CODE_SMALLER_WIRE_ORIGINAL16K")
        with capsule_path.open("xb") as stream:
            count=stream.write(wire);a.require(count==len(wire),"COMPLETE_COMPACT_CAPSULE_WRITE")
        physical=dict(path=CAPSULE,**wire_pin)
        a.exact(q.fresh_pin(CAPSULE),physical,"ACTUAL_COMPACT_CAPSULE_FILE")
        q.finish();g.check(force=True)
        row.update(state="PASS_ACTUAL29_COMPACT_WORKER_CAPSULE_CODE14_NOT_NEW_MANIFEST_WORKER_OR_GO",
            contracts=dict(run=14,errors=0,failures=0,skipped=0),original_capsule_pin=c.CAPSULE,
            original_canonical_wire_pin=raw_pin,compact_wire_pin=physical,semantic_descriptor_count=29,
            original_canonical_wire_bytes=len(raw),compact_wire_bytes=len(wire),bytes_saved=len(raw)-len(wire),
            maximum_capsule_bytes=16384,connection_proof=proof,original_decoder_evidence=decoded,
            source_pins=[q.snapshots[x] for x in (SELF,compact.SELF,compact.TEST)],
            bounded_graph_proof=bootstrap,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_bytes_read=q.bytes_read,new_actual_manifest_or_controller_connected=False,
            larger31_descriptors_unit_fixture_only_not_actual_manifest=True,
            original_worker_function_not_invoked=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            row["error_code"]=error.args[0]
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"COMPACT_CAPSULE_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(row,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:row.get(key) for key in ("state","error_code","original_canonical_wire_bytes","compact_wire_bytes",
        "bytes_saved","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed")},allow_nan=False))
    return 0 if row["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
