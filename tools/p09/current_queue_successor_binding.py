"""Private successor Binding preserving every original scope/byte oracle.

Only the reviewed constructor cursor is projected. Historical provenance is
carried unchanged; original modules and accepted files are not mutated.
"""
import copy
from types import FunctionType

SELF="tools/p09/current_queue_successor_binding.py"
TEST="tools/p09/tests/test_current_queue_successor_binding.py"
PINS=[
    dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"),
    dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f"),
    dict(path="tools/p09/runtime_envelope_source_projection_v1.py",bytes=6401,sha256="728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b"),
    dict(path="tools/p09/runtime_envelope_scope_binding_v1.py",bytes=10750,sha256="0105881d365213e70bd047b5c7fa8de6fda842f3103b71870c8f2224b3e4db3b")]
PROVENANCE_KEYS=("prior_failure_lineage","successor_context","same_case_failed_receipt_provenance",
    "same_case_failed004_receipt_provenance","same_case_failed160_partial_receipt_provenance",
    "same_case_failed160_extra_receipt_provenance")


def connect(root, loader, scope, index, provenance, historical_pairs=()):
    if type(index) is not int or not 161 <= index <= 249:raise ValueError("CLOSED_SUCCESSOR_BINDING_INDEX")
    if type(provenance) is not dict or any(key not in PROVENANCE_KEYS for key in provenance):
        raise ValueError("CLOSED_HISTORICAL_PROVENANCE")
    namespaces, source_proofs=loader.load(root,PINS,{"current_stored_runtime_scope":scope})
    module=namespaces.runtime_envelope_scope_binding_v1
    module.require(type(historical_pairs) in (list,tuple) and len(historical_pairs) <= 249,"BOUNDED_PRIOR_PAIRS")
    ordinary_descriptor=module.source.descriptor
    inherited={}
    for row in historical_pairs:
        module.require(type(row) is dict and set(row) == {"schema_version","semantic_original_pin","physical_envelope_pin","next_case"},
            "CLOSED_INHERITED_PAIR")
        old,new=module.source.copy_pin(row["semantic_original_pin"]),module.source.copy_pin(row["physical_envelope_pin"])
        module.require(old["path"] not in inherited,"UNIQUE_INHERITED_ORIGINAL")
        module.require(row["schema_version"] == module.source.SCHEMA and type(row["next_case"]) is int and row["next_case"] < index,
            "HISTORICAL_PAIR_NOT_CURRENT")
        module.require(new["path"].startswith(module.source.PREFIX) and new["path"].endswith(".envelope.v1.json"),
            "EXPLICIT_INHERITED_PHYSICAL_PATH")
        inherited[old["path"]]=(old,new)
    def descriptor(old,new,*,next_case):
        if type(old) is dict and old.get("path") in inherited:
            module.require(type(next_case) is int and next_case == index,"EXACT_SUCCESSOR_INHERITED_CONTEXT")
            expected_old,expected_new=inherited[old["path"]]
            module.exact(module.source.copy_pin(old),expected_old,"EXACT_INHERITED_ORIGINAL_PIN")
            module.exact(module.source.copy_pin(new),expected_new,"EXACT_INHERITED_PHYSICAL_PIN")
            return dict(schema_version=module.source.SCHEMA,semantic_original_pin=expected_old,
                physical_envelope_pin=expected_new,next_case=next_case)
        return ordinary_descriptor(old,new,next_case=next_case)
    module.source.descriptor=descriptor
    module.source.Projection.__init__.__globals__["descriptor"]=descriptor
    original=module.Binding.__init__
    code=original.__code__
    module.require(sum(type(x) is int and x == 158 for x in code.co_consts) == 1,"ONE_CONSTRUCTOR_CURSOR")
    module.require(not any(type(x) is int and x == index for x in code.co_consts),"UNAMBIGUOUS_CURSOR_INVERSE")
    revised=code.replace(co_consts=tuple(index if type(x) is int and x == 158 else x for x in code.co_consts))
    inverse=revised.replace(co_consts=tuple(158 if type(x) is int and x == index else x for x in revised.co_consts))
    module.require(inverse == code,"ENTIRE_CONSTRUCTOR_INVERSE")
    projected=FunctionType(revised,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    projected.__kwdefaults__=original.__kwdefaults__
    methods={name:value for name,value in vars(module.Binding).items() if name not in ("__init__","representation")}
    represented=module.Binding.representation
    frozen=copy.deepcopy(provenance)
    def representation(self, projection):
        result=represented(self,projection)
        result["historical_predecessor_provenance"]=copy.deepcopy(frozen)
        result["historical_provenance_is_current_acceptance"]=False
        return result
    module.Binding.__init__=projected;module.Binding.representation=representation
    module.require(all(vars(module.Binding).get(name) is value for name,value in methods.items()),
        "ALL_SCOPE_RESOURCE_BYTE_HANDLE_ORACLES_UNCHANGED")
    return module,dict(source_proofs=source_proofs,original_constructor=original,original_methods=methods,
        original_representation=represented,all_nonconstructor_oracle_methods_retained=True,
        exact_constructor_inverse_code_equal=True,default_modules_not_mutated=True,
        historical_provenance_not_relabelled=True,product_or_Native_or_GO_qualified=False)


def descriptors(source, prior_rows, additions, index):
    source.require(type(index) is int and 161 <= index <= 249,"SUCCESSOR_DESCRIPTOR_CONTEXT")
    source.require(type(prior_rows) is list and type(additions) is list and prior_rows and additions,"COMPLETE_DESCRIPTOR_INPUTS")
    result=[];logical=set();physical=set()
    for row in prior_rows+additions:
        source.require(type(row) is dict and set(row) == {"schema_version","semantic_original_pin","physical_envelope_pin","next_case"},
            "CLOSED_EXISTING_DESCRIPTOR")
        old,new=row["semantic_original_pin"],row["physical_envelope_pin"]
        source.require(old["path"] not in logical and new["path"] not in physical,"NO_PRIOR_PAIR_REPLACEMENT")
        # Past row context stays in the predecessor receipt. New descriptors
        # validate the same exact original/encoded pins under the current index.
        result.append(source.descriptor(old,new,next_case=index))
        logical.add(old["path"]);physical.add(new["path"])
    return result


def inherited_scope(scope, representation, fresh_inputs, preparation_inputs, checkpoint):
    """One validated bulk union instead of revalidating the whole scope per pin."""
    checkpoint()
    required=scope.pins(representation["semantic_source_freeze"])
    reverse={row["physical_envelope_pin"]["path"]:row for row in representation["descriptors"]}
    fresh=scope.pins(fresh_inputs);added={}
    for name,pin in fresh.items():
        checkpoint()
        if name in reverse:
            row=reverse[name]
            scope.require(pin == row["physical_envelope_pin"],"EXACT_APPROVED_PHYSICAL_ALIAS")
            pin=dict(row["semantic_original_pin"])
        name=pin["path"]
        scope.require(name not in added or added[name] == pin,"NO_FRESH_ALIAS_CONFLICT")
        added[name]=pin
    required=scope.extend(required,added)
    required=scope.extend(required,preparation_inputs)
    checkpoint()
    return required


def prepare(index, attempt=1):
    """Real private binding/manifest metadata; no engine, worker or GO."""
    import hashlib
    import json
    import os
    from pathlib import Path
    import sys
    import time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import runtime_envelope_namespace_bundle_v1 as loader
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    guard=pressure.guard_type(distinct.guard_type(a.Guard))()
    if type(attempt) is not int or not 1 <= attempt <= 8:raise ValueError("CLOSED_BINDING_PREPARATION_ATTEMPT")
    manifest_name=f"implementation/p09/evidence/p09-361-case{index}-successor-manifest{attempt:03}.v1.json"
    report_name=f"implementation/p09/evidence/p09-361-case{index}-successor-binding{attempt:03}.v1.json"
    if type(index) is not int or not 161 <= index <= 249:raise ValueError("CLOSED_SUCCESSOR_PREPARE_INDEX")
    a.require(not (c.ROOT/manifest_name).exists() and not (c.ROOT/report_name).exists(),"EXCLUSIVE_SUCCESSOR_BINDING_OUTPUTS")
    out=dict(state="FAILED_SUCCESSOR_BINDING_NOT_ADOPTED",accepted_count_delta=0,product_or_Native_executed=False,
        GO_authorized=False,P09_gate="OPEN")
    started=time.monotonic();last=started;phases={}
    def mark(name):
        nonlocal last
        now=time.monotonic();phases[name]=now-last;last=now
    def publish(name,row):
        raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
        a.require(0 < len(raw) <= 262144,"BOUNDED_SUCCESSOR_BINDING_PUBLICATION")
        path=c.ROOT/name
        for parent in (path.parent,*path.parent.parents):
            a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_BINDING_ANCESTORS")
            if parent == c.ROOT:break
        with path.open("xb") as stream:
            a.exact(stream.write(raw),len(raw),"ALL_BINDING_METADATA_BYTES");stream.flush();os.fsync(stream.fileno())
        return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    q=None
    try:
        guard.acquire();mark("resource_admission")
        q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST);q.pin(loader.SELF)
        selected=q.json(f"implementation/p09/evidence/p09-361-case{index}-successor-selection001.v1.json")
        produced=q.json(f"implementation/p09/evidence/p09-361-case{index}-lossless-receipts001.v1.json")
        a.fields(selected,dict(state="PREPARED_EXACT_SUCCESSOR_STEP_AND_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
            cleanup_confirmed=True,accepted_count_delta=0),"EXACT_SUCCESSOR_SELECTION")
        a.fields(produced,dict(state="PREPARED_FOUR_LOSSLESS_SUCCESSOR_RECEIPTS_NOT_ADOPTED_RUNTIME_OR_GO",
            next_case=index,decode_passes=8,original_receipts_rewritten=False,cleanup_confirmed=True),"EXACT_LOSSLESS_PRODUCER")
        for pin in selected["fresh_input_pins"]+produced["source_pins"]+PINS:
            a.exact(q.pin(pin["path"]),pin,"UNCHANGED_BINDING_DEPENDENCIES")
        step=selected["step"];a.require(step["index"] == index and step["before"] == index-7,"REAL_SUCCESSOR_STEP")
        authority=a.read_exact(q,step["prior_queue_pin"])
        a.fields(authority,dict(accepted_count_after=index-7,next_runtime_index=index,runtime_candidate_pin=step["prior_candidate_pin"],
            resource_cleanup_confirmed=True),"ACTUAL_PREDECESSOR_AUTHORITY")
        prior=a.read_exact(q,step["prior_candidate_pin"]);representation=prior["source_input_representation"]
        mark("predecessor_and_dependency_reads")
        history={key:copy.deepcopy(representation[key]) for key in PROVENANCE_KEYS if key in representation}
        module,proof=connect(c.ROOT,loader,scope,index,history,representation["descriptors"])
        rows=descriptors(module.source,representation["descriptors"],produced["explicit_descriptors"],index)
        a.require(len(rows) == len(representation["descriptors"])+4,"ALL_OLD_AND_FOUR_NEW_PAIRS")
        for row in rows:
            for pin in (row["semantic_original_pin"],row["physical_envelope_pin"]):
                a.exact(q.pin(pin["path"]),pin,"ALL_REAL_ORIGINAL_AND_PHYSICAL_PINS")
        mark("all_original_and_envelope_reads")
        manifest=dict(schema_version="hwpx-agent.p09-current-successor-binding-manifest/v1",index=index,before=index-7,
            authority_pin=step["prior_queue_pin"],prior_runtime_pin=step["prior_candidate_pin"],
            prior_manifest_pin=representation["manifest_pin"],producer_pin=q.snapshots[f"implementation/p09/evidence/p09-361-case{index}-lossless-receipts001.v1.json"],
            descriptors=rows,historical_predecessor_provenance=history)
        guard.check(force=True)
        manifest_pin=publish(manifest_name,manifest)
        a.exact(q.pin(manifest_name),manifest_pin,"ACTUAL_PUBLISHED_MANIFEST_BYTES")
        binding=module.Binding(rows,manifest_pin,next_case=index)
        required=inherited_scope(scope,representation,authority["fresh_input_pins"],q.snapshots,guard.check)
        projection,_=binding.project(required,guard.check)
        a.require(len(projection.semantic_pins) == len(projection.physical_pins),"NO_INPUT_SCOPE_REMOVED")
        mark("manifest_publication_and_scope_projection")
        # finish is a terminal operation, not reusable: it hashes ALL current
        # snapshots once more and checks its cumulative counter against inventory.
        # Close only after the published manifest joins the same fresh scope.
        q.finish();guard.check(force=True)
        mark("one_complete_final_fresh_hash")
        out.update(state="PREPARED_REAL_SUCCESSOR_BINDING_ALL_PAIRS_NOT_WHOLE_RUNTIME_OR_GO",
            index=index,manifest_pin=manifest_pin,pair_count=len(rows),semantic_input_count=len(projection.semantic_pins),
            physical_input_count=len(projection.physical_pins),physical_bytes=sum(p["bytes"] for p in projection.physical_pins.values()),
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_read_passes=q.read_passes,actual_bytes_read=q.bytes_read,
            original_constructor_inverse=True,all_nonconstructor_oracle_methods_retained=True,
            original_private_source_ast_and_pin_proofs=proof["source_proofs"],
            historical_provenance_not_relabelled=True,new_controller_config_CODE_preflight_not_included=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,
            elapsed_seconds=time.monotonic()-started,phase_seconds=phases,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    a.require(guard.cleanup,"SUCCESSOR_BINDING_CLEANUP");publish(report_name,out)
    print(json.dumps({key:out.get(key) for key in ("state","pair_count","fresh_inputs","final_fresh_hashes","physical_input_count","physical_bytes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("PREPARED_") else 1


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--attempt",type=int,default=1)
    args=parser.parse_args();raise SystemExit(prepare(args.case,args.attempt))
