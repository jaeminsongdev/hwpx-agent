"""Export one actual whole preparation; never dispatch a product or Native GO.

전체 선행 oracle과 원 final byte reads를 수행한다. checkpoint는 실행 권한이
아니며, 선언만 된 scope 입력은 실제 fresh read와 분리해 기록한다.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

SELF="tools/p09/produce_prepared_input_checkpoint_r366.py"
OUTPUT="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json"
MAX_OUTPUT_BYTES=4*1024*1024

def local_limits():
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not (k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):
        raise ValueError("LOCAL_LIMITS_NOT_APPLIED")

def main():
    local_limits()
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import prepared_input_checkpoint_v1 as prepared
    import preparation_terminal_progress_v1 as progress
    import owned_source_read_pressure as pacing
    destination=a.c.ROOT/OUTPUT
    a.require(not destination.exists() and not destination.is_symlink(),"CHECKPOINT_REFUSE_OVERWRITE")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))()
    q=None;phase="admission";started=time.monotonic()
    row=dict(state="FAILED_PREPARATION_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,queue_advance_authorized=False,
        P09_gate="OPEN",PC_freeze_resolved=False)
    try:
        guard.acquire();q=a.AcceptanceReader(a.c.ROOT,guard.check)
        phase="source_pins"
        source_paths=(SELF,prepared.SELF,prepared.TEST,progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,
            distinct.SELF,distinct.TEST)
        for path in source_paths:q.pin(path)
        phase="controller_import"
        import flat_current_queue_envelope_runtime_v31 as controller
        m=controller.M;m.base.configure(160)
        controller._env["_execution_requested"]=True
        phase="whole_binding";scope,rust=m.binding(q)
        graph=m.graph_value()
        data=q.snapshots[controller.DATA];preflight=q.snapshots[controller.PREFLIGHT]
        successor=controller._env["current_binding"].successor
        # Pin all output dependencies before finish; no late pin is permitted.
        a.exact(q.pin(successor.AUTHORITY["path"]),successor.AUTHORITY,"CURRENT_AUTHORITY153")
        a.exact(q.pin(successor.ROOT["path"]),successor.ROOT,"CURRENT_SUCCESS159")
        scope=m.base.scope.extend(scope,q.snapshots)
        phase="final_freshness";q.finish();guard.check(force=True)
        phase="checkpoint_export"
        checkpoint=prepared.export(q,scope,graph.binding,
            context=dict(index=160,before=153,physical_product_run=3),
            data_pin=data,preflight_pin=preflight,authority_pin=successor.AUTHORITY,
            prior_runtime_pin=successor.ROOT,whole_oracle_completed=True)
        row.update(state="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO",
            checkpoint=checkpoint,source_pins=[q.snapshots[x] for x in source_paths],
            current_Rust_input_count=len(rust),source_pairs=len(graph.binding.descriptors()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,
            controller_binding_called_once=True,product_entrypoint_called=False,
            diagnostic_preparation_not_runtime_handoff=True,
            runtime_handoff_and_new_physical_identity_still_require_qualification=True)
        phase="completed"
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            row["error_code"]=error.args[0]
    finally:
        guard.close()
        try:row["terminal_preparation_progress"]=progress.summary(q,phase)
        except ValueError:row["terminal_preparation_progress"]=dict(phase=phase,counters_invalid=True)
        row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            metadata_warning=pressure.summary(guard),
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in guard.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"CHECKPOINT_CLEANUP")
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0<len(raw)<=MAX_OUTPUT_BYTES,"CHECKPOINT_BOUNDED_OUTPUT")
    for parent in (destination.parent,*destination.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"CHECKPOINT_DIRECT_ANCESTORS")
        if parent==a.c.ROOT:break
    pacer=pacing.OwnedPacer();pacer.select(OUTPUT)
    completed=row["state"]=="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO"
    if not completed:a.require(len(raw)<=65536,"CHECKPOINT_BOUNDED_FAILURE_SUMMARY")
    # A latched resource stop must not trigger more audit work. Only its tiny
    # terminal report is written; it cannot contain a completed checkpoint.
    write_checkpoint=guard.check if completed else lambda:None
    # Exclusive creation preserves partial/failed evidence instead of replacing it.
    with destination.open("xb") as stream:
        for offset in range(0,len(raw),65536):
            block=raw[offset:offset+65536];pacer.reserve(write_checkpoint)
            written=stream.write(block);a.require(written==len(block),"CHECKPOINT_COMPLETE_CHUNK")
            pacer.refund(written)
        stream.flush();os.fsync(stream.fileno())
    print(json.dumps(dict(state=row["state"],output=OUTPUT,bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),fresh_inputs=row.get("fresh_inputs"),
        final_fresh_hashes=row.get("final_fresh_hashes"),CPU_max=row["CPU_max"],
        RAM_min=row["RAM_min"],parent_CPU_max=row["parent_CPU_max"],
        cleanup_confirmed=guard.cleanup,accepted_count_delta=0,
        error_code=row.get("error_code")),allow_nan=False))
    return 0 if row["state"]=="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO" else 1

if __name__=="__main__":raise SystemExit(main())
