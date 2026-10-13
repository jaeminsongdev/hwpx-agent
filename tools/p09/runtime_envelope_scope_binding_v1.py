"""Explicit full semantic/physical scope binding, not a product acceptor.

Metadata union may encounter both representations of the SAME pinned receipt.
Only exact manifest pairs can reconcile that alias; arbitrary conflicts remain
errors. Physical evidence is checked as physical, never rewritten for an old
oracle. Full original product/resource/cleanup oracle still must run separately.
"""
from pathlib import PurePosixPath
import math
from types import MappingProxyType
import runtime_envelope_source_projection_v1 as source

SELF="tools/p09/runtime_envelope_scope_binding_v1.py"
TEST="tools/p09/tests/test_runtime_envelope_scope_binding_v1.py"
SCHEMA="hwpx-agent.p09-explicit-runtime-source-binding/v1"


def require(ok,code):
    if not ok:raise ValueError("ENVELOPE_SCOPE_BINDING_"+code)


def exact(actual,expected,code):
    require(type(actual) is type(expected),code)
    if type(expected) is dict:
        require(set(actual)==set(expected),code)
        for key in expected:exact(actual[key],expected[key],code)
    elif type(expected) in (list,tuple):
        require(len(actual)==len(expected),code)
        for x,y in zip(actual,expected):exact(x,y,code)
    else:require(actual==expected,code)


class Binding:
    def __init__(self, descriptors, manifest_pin, *, next_case):
        require(type(next_case) is int and next_case==158,"ONLY_REVIEWED_NEXT158_CONTEXT")
        require(type(descriptors) is list and 0<len(descriptors)<=source.MAX_BINDINGS,"BOUNDED_MANIFEST")
        originals={};reverse={};rows=[]
        for row in descriptors:
            require(type(row) is dict and set(row)=={"schema_version","semantic_original_pin","physical_envelope_pin","next_case"},"CLOSED_DESCRIPTOR")
            require(type(row["next_case"]) is int and row["next_case"]==next_case,"TYPED_CONTEXT")
            expected=source.descriptor(row["semantic_original_pin"],row["physical_envelope_pin"],next_case=next_case)
            require(row==expected,"EXACT_DESCRIPTOR")
            old,new=expected["semantic_original_pin"],expected["physical_envelope_pin"]
            require(old["path"] not in originals and new["path"] not in reverse,"BIJECTIVE_DESCRIPTORS")
            originals[old["path"]]=old;reverse[new["path"]]=old["path"];rows.append(expected)
        self.next_case=next_case;self.manifest_pin=MappingProxyType(source.copy_pin(manifest_pin))
        self.rows=tuple(MappingProxyType({**r,"semantic_original_pin":MappingProxyType(r["semantic_original_pin"]),
            "physical_envelope_pin":MappingProxyType(r["physical_envelope_pin"])}) for r in rows)
        self.originals=MappingProxyType({n:MappingProxyType(p) for n,p in originals.items()})
        self.physical=MappingProxyType({r["physical_envelope_pin"]["path"]:MappingProxyType(dict(r["physical_envelope_pin"])) for r in rows})
        self.reverse=MappingProxyType(reverse)

    def descriptors(self):
        return [dict(schema_version=r["schema_version"],next_case=r["next_case"],
            semantic_original_pin=dict(r["semantic_original_pin"]),physical_envelope_pin=dict(r["physical_envelope_pin"])) for r in self.rows]

    def semantic_union(self, rows, checkpoint):
        require(callable(checkpoint),"CHECKPOINT");checkpoint()
        require(type(rows) is dict,"INPUT_MAPPING")
        verified=source.scope.pins(list(rows.values()));require(verified==rows,"MAPPING_KEYS")
        result={};aliases=0
        for name,pin in verified.items():
            checkpoint()
            if name in self.reverse:
                require(pin==self.physical[name],"EXACT_PHYSICAL_ALIAS")
                logical=self.reverse[name];pin=dict(self.originals[logical]);aliases+=1
            else:logical=name
            if logical in self.originals:require(pin==self.originals[logical],"EXACT_SEMANTIC_ALIAS")
            require(logical not in result or result[logical]==pin,"NO_ARBITRARY_CONFLICT_REBASE")
            result[logical]=dict(pin)
        require(all(result.get(n)==p for n,p in self.originals.items()),"ALL_DECLARED_ORIGINALS_PRESENT")
        return result,dict(input_representations=len(verified),semantic_inputs=len(result),
            physical_aliases_encountered=aliases,explicit_exact_pair_reconciliation_only=True)

    def project(self, rows, checkpoint):
        semantic,proof=self.semantic_union(rows,checkpoint)
        require(semantic.get(self.manifest_pin["path"])==self.manifest_pin,"MANIFEST_IN_FULL_SOURCE_SCOPE")
        projection=source.Projection(semantic,self.descriptors(),next_case=self.next_case,checkpoint=checkpoint)
        return projection,proof

    def representation(self, projection):
        require(type(projection) is source.Projection,"EXACT_PROJECTION")
        return dict(schema_version=SCHEMA,next_case=self.next_case,manifest_pin=dict(self.manifest_pin),
            semantic_source_freeze=[dict(p) for n,p in sorted(projection.semantic_pins.items())],
            physical_source_freeze=[dict(p) for n,p in sorted(projection.physical_pins.items())],
            descriptors=self.descriptors(),full_original_product_oracle_required=True,
            original_raw_receipts_not_claimed_as_physically_locked=True)

    def runtime_budget(self, rows, requests, original_complete_budget, checkpoint):
        projection,_=self.project(rows,checkpoint)
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        result=original_complete_budget(physical,requests)
        require(type(result) is dict and result["unchanged_lock_deadline_seconds"]==600
            and result["unallocated_margin_seconds"]==60,"ORIGINAL_COMPLETE_LIMITS")
        result=dict(result)
        total=result["predicted_runtime_combined_seconds"]+5.0
        require(type(total) in (int,float) and math.isfinite(total) and total<600,"COMPLETE_COST_PLUS_SHARED_DECODER5")
        result.update(predicted_runtime_combined_seconds=total,nominal_fits_unchanged_deadline=True,
            aggregate_envelope_decoder_allowance_seconds=5.0,decoder_allowance_requires_actual_shared_limit=True,
            semantic_input_count=len(projection.semantic_pins),semantic_input_bytes=sum(p["bytes"] for p in projection.semantic_pins.values()),
            physical_source_representation_schema=SCHEMA,physical_input_scope_projected_explicitly=True,
            semantic_source_scope_reduced=False,GO_authorized=False)
        return result

    def validate_scope_evidence(self, row, expected_semantic, checkpoint, *, require_committed=True):
        require(type(require_committed) is bool and type(row) is dict,"EXACT_VALIDATION_MODE")
        projection,_=self.project(expected_semantic,checkpoint)
        expected=self.representation(projection)
        exact(row.get("source_input_representation"),expected,"EXPLICIT_SOURCE_REPRESENTATION")
        semantic=source.scope.pins(expected["semantic_source_freeze"])
        physical=source.scope.pins(expected["physical_source_freeze"])
        require(source.scope.pins(row["source_freeze"])==physical,"ACTUAL_FREEZE_IS_PHYSICAL")
        frame=row["source_frame"]
        require(frame["frame_state"]==("COMMITTED" if require_committed else "CLOSED")
            and frame["registered_live_frame"] is False,"EXACT_TERMINAL_FRAME_NOT_PROMOTION")
        if require_committed:
            require(frame["original_owned_cleanup_confirmed_before_release"] is True,"REAL_OWNED_CLEANUP")
        n=len(physical);total=sum(p["bytes"] for p in physical.values())
        require(type(frame["input_count"]) is int and frame["input_count"]==n
            and type(frame["input_bytes"]) is int and frame["input_bytes"]==total,"PHYSICAL_ACCOUNTING")
        require(type(frame["actual_byte_boundaries"]) is list and len(frame["actual_byte_boundaries"])==2,"TWO_PHYSICAL_BOUNDARIES")
        counts={name:1 for name in self.originals};decoded=sum(p["bytes"] for p in self.originals.values())
        for phase,role in zip(frame["actual_byte_boundaries"],("before","after")):
            checkpoint();require(phase["role"]==role and source.scope.pins(phase["actual_byte_pins"])==physical,"EVERY_PHYSICAL_PIN_ACTUAL")
            d=phase["reader_diagnostics"]
            require(type(d["read_passes"]) is int and d["read_passes"]==n
                and type(d["bytes_read"]) is int and d["bytes_read"]==total,"ACTUAL_DISK_BYTE_COUNTERS")
            e=d["explicit_envelope_semantic_decode"]
            require(e["counts"]==counts and all(type(x) is int for x in e["counts"].values())
                and type(e["decoded_bytes"]) is int and e["decoded_bytes"]==decoded
                and e["semantic_bytes_not_reported_as_disk_bytes"] is True,"ALL_ORIGINAL_SEMANTIC_BYTES")
            g=d["original_live_boundary_guard_during_decode"]
            require(type(g["calls"]) is int and g["calls"]>0
                and g["shared_budget_callback_restored"] is True
                and g["original_reader_pressure_Frame_and_lock_checkpoint_retained"] is True,"LIVE_GUARD_NOT_SKIPPED")
        h=frame["handles"]
        require(all(type(h[key]) is int for key in ("input_lock_handles_remaining","input_lock_handles_opened",
            "input_lock_handles_closed","handle_close_failed_attempts","byte_stream_identity_checks",
            "active_reader_bindings","active_byte_streams","maximum_lock_seconds")),"TYPED_HANDLE_COUNTERS")
        require(h["input_lock_handles_remaining"]==0 and h["input_lock_cleanup_confirmed"] is True
            and h["input_lock_handles_opened"]==h["input_lock_handles_closed"]
            and h["handle_close_failed_attempts"]==0 and h["byte_stream_identity_checks"]==2*n
            and h["active_reader_bindings"]==h["active_byte_streams"]==0 and h["maximum_lock_seconds"]==600,"ORIGINAL_CLEANUP_AND_IDENTITY")
        b=row["aggregate_envelope_decoder"]
        require(type(b["aggregate_limit_seconds"]) is float and b["aggregate_limit_seconds"]==5.0
            and type(b["elapsed_decoder_work_seconds"]) is float and math.isfinite(b["elapsed_decoder_work_seconds"])
            and 0<=b["elapsed_decoder_work_seconds"]<=5.0
            and type(b["attempted_decodes"]) is int and type(b["completed_decodes"]) is int
            and b["attempted_decodes"]==b["completed_decodes"]==2*len(self.rows)
            and b["active_decode"] is False and b["terminal_error_seen"] is False
            and b["two_boundaries_share_one_budget"] is True,"ACTUAL_AGGREGATE5_NOT_TIMEOUT_PASS")
        return dict(semantic_input_count=len(semantic),physical_input_count=n,
            explicit_lossless_physical_scope_checked=True,original_full_product_resource_and_cost_oracles_still_required=True,
            original_metadata_and_worker_live_receipt_access_policy_connected=False,
            product_or_Gate_qualified=False,GO_authorized=False)
