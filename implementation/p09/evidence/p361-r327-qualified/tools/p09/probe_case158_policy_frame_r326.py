"""Actual11 pair + manifest held boundaries under original-raw path policy.

Only component CLOSED evidence, no Job/product/whole2580/Gate promotion. The
original Frame/reader factories and full scope checker stay in their namespaces.
"""
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_source_manifest_v2 as manifest
import runtime_envelope_frame_connection_v1 as frame_connection
import runtime_envelope_raw_access_policy_v1 as raw_policy
import flat_current_queue_product_window_runtime_v18 as v
SELF="tools/p09/probe_case158_policy_frame_r326.py"


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)();frame=None
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_product_or_acceptance_executed=False,full_current158_Native_or_product_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        binding,_,admission=manifest.load(q,q.pin(manifest.PATH),a)
        q.pin(SELF)
        for code in ("p09-361-case158-raw-live-access-policy-code10-r640.v1.json",
            "p09-361-case158-full-oracle-connection-code9-r642.v1.json"):
            record=q.json("implementation/p09/evidence/"+code)
            a.require(record["cleanup_confirmed"] is True and record["state"].startswith("PASS_"),"CODE_COMPONENT_ONLY")
            for p in record["new_code_pins"]:a.exact(q.pin(p["path"]),p,"FRESH_CURRENT_POLICY_ORACLE_CODE")
        if v.M.base.CONFIG is None:v.M.base.configure(157)
        for pin in v.COMPONENT_PINS:a.exact(q.pin(pin["path"]),pin,"CURRENT_ORIGINAL_FACTORY_CODE")
        api=v.NATIVE.load(q,14,a.c)
        owner=NS(lock=threading.RLock(),samples=g.samples,checkpoint_io=g.check);context=NS(phase="final_fresh_hash")
        early=api.EarlySourceCheckpoint(g.check,owner);held=api.InputLocks(a.c.ROOT,early,owner,context)
        required={n:dict(p) for n,p in binding.originals.items()};required[binding.manifest_pin["path"]]=dict(binding.manifest_pin)
        registry=v.NATIVE.frames.Registry();Frame=frame_connection.frame_type(v.NATIVE.frames.Frame,binding)
        frame=Frame(registry,required,early,held=held)
        policy=raw_policy.Policy(a.c.ROOT,binding,lambda:registry.active is frame,g.check)
        engine,_=v.template();OriginalReader=engine.run_owned.__globals__["BoundaryReader"]
        def factory(guard):return OriginalReader(a.c.ROOT,guard,owner=owner,api=api)
        with policy.install():
            frame.acquire()
            # A deliberate denied access proves actual policy hooking; it is
            # not relabelled as zero attempts in this diagnostic component run.
            name=next(iter(binding.originals))
            try:(a.c.ROOT/name).open("rb")
            except ValueError as error:a.exact(str(error),"STOP_LIVE_RAW_ENVELOPE_RECEIPT_ACCESS","ACTUAL_DENY")
            else:raise ValueError("RAW_RECEIPT_POLICY_NOT_CONNECTED")
            frame.read_boundary(factory,g.check);frame.read_boundary(factory,g.check)
            held.verify_two_byte_passes({n:dict(p) for n,p in frame.inputs.items()})
            a.require(frame.close(),"ALL_FOCUSED_HANDLES_CLOSED")
        summary=frame.summary()
        row=dict(source_input_representation=summary["explicit_source_input_representation"],
            source_freeze=[dict(p) for p in frame.inputs.values()],source_frame=summary,
            aggregate_envelope_decoder=summary["aggregate_envelope_decoder"])
        scope_proof=binding.validate_scope_evidence(row,required,g.check,require_committed=False)
        try:binding.validate_scope_evidence(row,required,g.check)
        except ValueError as error:a.exact(str(error),"ENVELOPE_SCOPE_BINDING_EXACT_TERMINAL_FRAME_NOT_PROMOTION","CLOSED_REJECTED")
        else:raise ValueError("FOCUSED_CLOSED_FALSE_PRODUCT_PROMOTION")
        q.finish();g.check(force=True)
        result.update(state="PASS_ACTUAL_POLICY_PROJECTED_FRAME11_PAIRS_MANIFEST_TWO_BOUNDARIES_CLOSED_NOT_WHOLE158_OR_PRODUCT",
            manifest_pin=dict(binding.manifest_pin),focused_frame=summary,scope_component_proof=scope_proof,
            parent_python_raw_policy=policy.evidence(),deliberate_diagnostic_raw_attempts=1,
            worker_process_policy_or_whole_product_connection_qualified=False,
            actual_source_pins=[q.snapshots[SELF],q.snapshots[raw_policy.SELF],q.snapshots[frame_connection.SELF]],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            message=str(error);result["error_code"]=message if re.fullmatch("[A-Za-z0-9_]{1,256}",message) else "REDACTED_POLICY_FRAME_ERROR"
    finally:
        closed=True if frame is None else frame.close();g.close();result["cleanup_confirmed"]=g.cleanup and closed
        if frame is not None and result["state"]=="FAILED_NOT_ACCEPTED":result["failed_frame"]=frame.summary()
    print(json.dumps(result,ensure_ascii=True,allow_nan=False));return 0 if result["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
