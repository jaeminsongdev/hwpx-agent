"""Serial CODE12, exclusive artifact producer, focused real held-byte proof.

Modes are separate. Focus proves CLOSED eight-input component behavior, never
COMMITTED/current158/whole2532/product acceptance. No passing product replay.
"""
import argparse
import hashlib
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0, str(Path(__file__).resolve().parent))
# This existing bootstrap sets affinity1/BelowNormal before controller imports.
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_physical_io_v1 as physical

SELF = "tools/p09/qualify_case158_envelope_physical_io_r324.py"
CODE = "implementation/p09/evidence/p09-361-case158-envelope-physical-code12-r623.v1.json"
PRODUCER = "implementation/p09/evidence/p09-361-case158-eight-envelope-producer-r624.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-361-case158-eight-runtime-envelope-candidate-r620.v1.json"


def main(mode):
    a = launch.a; g = launch.distinct.guard_type(a.Guard)()
    result = dict(state="FAILED_NOT_ACCEPTED", mode=mode, accepted_count_delta=0,
        actual_product_or_acceptance_executed=False, current158_Native_scope_changed=False,
        P09_gate="OPEN", P10_allowed=False, files_created=[])
    frame = None; latched = False
    def check():
        nonlocal latched
        g.check(); a.require(not latched, "STOP_LATCHED_ENVELOPE_COMPONENT_PRESSURE")
        if g.samples and g.samples[-1]["system_cpu_percent"] >= 75:
            latched = True; raise ValueError("STOP_ENVELOPE_COMPONENT_PRESSURE_NO_COOLING")
    try:
        g.acquire(); check(); q = a.AcceptanceReader(a.c.ROOT, check)
        pins = [q.pin(path) for path in (SELF, physical.SELF, physical.TEST, physical.source.SELF,
            physical.source.TEST, physical.source.codec.SELF, physical.source.codec.TEST,
            "tools/p09/runtime_record_envelope_v1.py", launch.distinct.SELF, launch.distinct.TEST)]
        if mode == "contracts":
            import unittest
            suite = unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"), pattern="test_runtime_envelope_physical_io_v1.py")
            tests = unittest.TestResult(); suite.run(tests); check()
            counts = dict(run=tests.testsRun, errors=len(tests.errors), failures=len(tests.failures), skipped=len(tests.skipped))
            result["contracts"] = counts
            a.exact(counts, dict(run=12, errors=0, failures=0, skipped=0), "CODE12")
            result.update(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE12_NOT_ACTUAL_IO_OR_PRODUCT",
                new_code_pins=pins[:3], source_pins=pins, Native_or_derivative_file_creation_executed=False)
        else:
            code = q.json(CODE)
            a.fields(code, dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE12_NOT_ACTUAL_IO_OR_PRODUCT",
                contracts=dict(run=12, errors=0, failures=0, skipped=0), cleanup_confirmed=True), "CURRENT_CODE12")
            for pin in code["source_pins"]: a.exact(q.pin(pin["path"]), pin, "QUALIFIED_CODE_BYTES")
            ar = a.read_exact(q, launch.review.AUTHORITY_PIN)
            a.fields(ar, dict(accepted_count_after=151, next_runtime_index=158, resource_cleanup_confirmed=True), "CURRENT151")
            a.exact(ar["runtime_candidate_pin"], launch.review.ROOT_PIN, "CURRENT157")
            candidate = q.json(CANDIDATE)
            a.fields(candidate, dict(state="PASS_EIGHT_REAL_RECEIPT_LOSSLESS_SOURCE_CANDIDATE_NOT_FULL_PREFLIGHT_NATIVE_PRODUCT_OR_ADOPTED",
                original_indices=list(range(150,158)), cleanup_confirmed=True), "CANDIDATE8")
            root = a.read_exact(q, launch.review.ROOT_PIN)
            semantic = physical.source.scope.extend(physical.source.scope.pins(root["source_freeze"]),
                physical.source.scope.pins([launch.review.ROOT_PIN]))
            descriptors = candidate["descriptors"]
            full = physical.source.Projection(semantic, descriptors, next_case=158, checkpoint=check)
            result.update(qualification_pin=q.snapshots[CODE], authority151_pin=launch.review.AUTHORITY_PIN,
                actual157_pin=launch.review.ROOT_PIN, explicit_descriptors=descriptors)
            if mode == "produce":
                parent = a.c.ROOT/physical.source.PREFIX
                for ancestor in (parent.parent, *parent.parent.parents):
                    a.require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(), "DIRECT_DERIVATIVE_PARENT")
                    if ancestor == a.c.ROOT: break
                if not parent.exists(): parent.mkdir()
                a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), "DERIVATIVE_DIRECTORY")
                observed = []
                for desc in descriptors:
                    original = desc["semantic_original_pin"]; encoded = desc["physical_envelope_pin"]
                    pin, buffer = q._read(original["path"], parse=True); q._bind(pin["path"], pin)
                    a.exact(pin, original, "FRESH_ORIGINAL")
                    raw = bytes(buffer); compressed = physical.source.codec.encode(raw, check)
                    a.exact(full.decode_fresh(original["path"], encoded, compressed, check), raw, "ENCODED_SOURCE_EXACT")
                    destination = a.c.ROOT/encoded["path"]
                    if destination.exists():
                        a.exact(q.fresh_pin(encoded["path"]), encoded, "EXISTING_ONLY_IF_EXACT")
                    else:
                        physical.publish_exclusive(a.c.ROOT, compressed, encoded, check)
                        result["files_created"].append(encoded["path"])
                    a.exact(q.fresh_pin(encoded["path"]), encoded, "ACTUAL_EXCLUSIVE_OUTPUT")
                    observed.append(encoded); del buffer, raw, compressed
                result.update(state="PASS_EIGHT_EXPLICIT_LOSSLESS_DERIVATIVES_FRESH_ORIGINALS_AND_OUTPUTS_NOT_CURRENT_NATIVE_OR_PRODUCT",
                    derivative_pins=observed, exclusive_no_original_overwrite=True, total_derivative_bytes=sum(p["bytes"] for p in observed),
                    current_physical_scope_adopted=False)
            else:
                produced = q.json(PRODUCER)
                a.fields(produced, dict(state="PASS_EIGHT_EXPLICIT_LOSSLESS_DERIVATIVES_FRESH_ORIGINALS_AND_OUTPUTS_NOT_CURRENT_NATIVE_OR_PRODUCT",
                    exclusive_no_original_overwrite=True, cleanup_confirmed=True), "ACTUAL_PRODUCER")
                a.exact(produced["explicit_descriptors"], descriptors, "SAME_DESCRIPTORS")
                import flat_current_queue_product_window_runtime_v18 as v
                for pin in v.COMPONENT_PINS: a.exact(q.pin(pin["path"]), pin, "QUALIFIED_NATIVE_COMPONENTS")
                for pin in produced["derivative_pins"]: a.exact(q.fresh_pin(pin["path"]), pin, "FRESH_PHYSICAL_ARTIFACT")
                api = v.NATIVE.load(q,14,a.c)
                owner = NS(lock=threading.RLock(), samples=g.samples, checkpoint_io=check)
                context = NS(phase="final_fresh_hash")
                early = api.EarlySourceCheckpoint(check, owner)
                held = api.InputLocks(a.c.ROOT, early, owner, context)
                subset = {d["semantic_original_pin"]["path"]:d["semantic_original_pin"] for d in descriptors}
                focused = physical.source.Projection(subset, descriptors, next_case=158, checkpoint=check)
                physical_inputs = {n:dict(p) for n,p in focused.physical_pins.items()}
                frame = v.NATIVE.frames.Frame(v.NATIVE.frames.Registry(), physical_inputs, early, held=held)
                engine,_ = v.template()
                OriginalReader = engine.run_owned.__globals__["BoundaryReader"]
                budget = physical.DecoderBudget(check)
                Reader = physical.boundary_reader_type(OriginalReader, focused, budget)
                def factory(guard): return Reader(a.c.ROOT,guard,owner=owner,api=api)
                frame.acquire()
                frame.read_boundary(factory,check); frame.read_boundary(factory,check)
                a.require(held.verify_two_byte_passes(physical_inputs)["locked_inputs"]==8, "TWO_PHYSICAL_IDENTITY_PASSES")
                for reader in frame.readers:
                    a.exact(reader.semantic_decode_counts, {name:1 for name in subset}, "ONE_FRESH_DECODE_PER_BOUNDARY")
                a.exact(budget.completed,16,"BOTH_BOUNDARIES_SHARED_DECODER")
                a.require(not budget.error and budget.elapsed<=5 and budget.active is None,"ACTUAL_SHARED_DECODER_LIMIT")
                a.require(frame.close(),"FOCUSED_NATIVE_CLEANUP")
                summary = frame.summary(); a.exact(summary["frame_state"],"CLOSED","NOT_COMMITTED_OR_PRODUCT")
                result.update(state="PASS_ACTUAL_EIGHT_ENVELOPES_TWO_HELD_PHYSICAL_BYTE_AND_SEMANTIC_BOUNDARIES_NOT_WHOLE_CURRENT158_OR_PRODUCT",
                    focused_frame=summary, shared_decoder_budget=budget.evidence(),
                    focused_semantic_input_count=8, whole_current_Native_scope_qualified=False,
                    original_boundary_reader_code_retained=True, existing_native_factory_reused=True,
                    independent_full_oracle_connection_qualified=False, focused_reader_bindings_restored=True)
        q.finish(); g.check(force=True); check()
        result.update(source_pins=pins, fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples), RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["state"]="FAILED_NOT_ACCEPTED"; result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            message=str(error);result["error_code"]=message if re.fullmatch("[A-Za-z0-9_]{1,256}",message) else "REDACTED_R324_ERROR"
    finally:
        native_closed = True if frame is None else frame.close()
        g.close(); result["cleanup_confirmed"]=g.cleanup and native_closed
        if frame is not None and result["state"]=="FAILED_NOT_ACCEPTED":result["failed_frame"]=frame.summary()
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("contracts","produce","focus"),required=True)
    raise SystemExit(main(p.parse_args().mode))
