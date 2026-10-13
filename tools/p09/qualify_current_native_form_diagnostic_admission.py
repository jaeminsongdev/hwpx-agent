#!/usr/bin/env python3
"""Current-source diagnostic admission/binding; never an old authority or Gate PASS."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_diagnostic_batch as binding
from tools.p09 import qualify_native_form_value_public_export as sdk
from tools.p09 import record_stored_form_provider_progress as provider

ROOT=binding.ROOT
p,q,public=binding.prepared,binding.q,binding.public
CAPSULE="implementation/p09/evidence/p09-36-native-form-diagnostic-current-admission.r02.json"
BOUND="implementation/p09/evidence/p09-36-native-form-diagnostic-current-bound.r02.json"
COMPONENT="implementation/p09/evidence/p09-36-native-form-diagnostic-binding-component.current-2020.v1.json"
COMPONENT_SHA="aa2cf63c8de33bc9ceb1476b2ebcfd488586d6059cbef9d429c53a00b0d0bff7"
OWN=("tools/p09/qualify_current_native_form_diagnostic_admission.py",
     "tools/p09/tests/test_current_native_form_diagnostic_admission.py",
     "implementation/p09/P09-36_CURRENT_NATIVE_DIAGNOSTIC_ADMISSION_POLICY.md")
ARCHIVES={sdk.LIB:(sdk.ARCHIVE,sdk.history.OLD_LIB),
          "Cargo.lock":(provider.ARCHIVE+provider.CHANGED["Cargo.lock"][0],provider.CHANGED["Cargo.lock"][1])}

def exact(value,expected,code):q.exact(value,expected,code)

def lock_inverse(current,original):
    marker=b'name = "hwpx-agent-cli"\nversion = "0.1.0"\ndependencies = [\n'
    if current.count(marker)!=1 or original.count(marker)!=1:raise ValueError("current_diagnostic_lock_inverse_invalid")
    start=current.index(marker)+len(marker);end=current.index(b"]",start);section=current[start:end]
    for delta in (b' "artifact-service",\n',b' "revision-service",\n'):
        if section.count(delta)!=1:raise ValueError("current_diagnostic_lock_inverse_invalid")
        section=section.replace(delta,b"",1)
    if current[:start]+section+current[end:]!=original:raise ValueError("current_diagnostic_lock_inverse_invalid")

def lineage():
    old=q.shared.lifecycle.checked_json(ROOT/p.CAPSULE,p.CAPSULE_SHA)
    exact(len(old["source_sha256"]),50,"current_diagnostic_original_pin_inventory")
    for name,digest in old["source_sha256"].items():
        origin,expected=ARCHIVES[name] if name in ARCHIVES else (name,digest)
        exact(expected,digest,"current_diagnostic_archive_pin_invalid")
        public.checked(ROOT/origin,digest,2*1024*1024)
    sdk.project(public.checked(ROOT/sdk.LIB,sdk.CURRENT_LIB),public.checked(ROOT/sdk.ARCHIVE,sdk.history.OLD_LIB))
    public.project(public.checked(ROOT/sdk.ARCHIVE,sdk.history.OLD_LIB),ROOT)
    lock_inverse(public.bounded_bytes(ROOT/"Cargo.lock",2*1024*1024),
                 public.checked(ROOT/ARCHIVES["Cargo.lock"][0],ARCHIVES["Cargo.lock"][1]))
    public.module_lineage();public.public_lineage()
    # Check immutable original preparation/binder sources, not their obsolete current authority.
    prep=q.shared.lifecycle.checked_json(ROOT/binding.PREPARATION,binding.PREPARATION_SHA)
    component=q.shared.lifecycle.checked_json(ROOT/COMPONENT,COMPONENT_SHA)
    exact(sorted(prep["source_sha256"]),sorted(p.SOURCES),"current_diagnostic_preparation_pins_invalid")
    exact(sorted(component["source_sha256"]),sorted(binding.SOURCES),"current_diagnostic_binding_pins_invalid")
    for value in (prep,component):
        for name,digest in value["source_sha256"].items():public.checked(ROOT/name,digest,2*1024*1024)
    public.checked(ROOT/q.HARNESS,q.HARNESS_SHA)
    try:binding.preflight()
    except ValueError as error:
        exact(str(error),"public_export_source_identity_changed","current_diagnostic_old_failure_changed")
    else:raise ValueError("current_diagnostic_old_failure_missing")
    return old,prep,component

def pins(old,prep,component):
    names=set(old["source_sha256"])|set(prep["source_sha256"])|set(component["source_sha256"])
    names.update((p.CAPSULE,binding.PREPARATION,COMPONENT,q.HARNESS,*OWN,
                  *(path for path,_ in ARCHIVES.values()),
                  "tools/p09/qualify_native_form_value_public_export.py"))
    return {name:q.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in sorted(names)}

def preflight():
    old,prep,component=lineage();before=pins(old,prep,component)
    # Explicit independent component check, NOT a call to or bypass of old qualify().
    result=p.inspect(ROOT/binding.MANIFEST,binding.MANIFEST_SHA,check_authority=False)
    manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    p.verify_real_manifest(manifest,p.real_manifest())
    result["actual_public_generator_manifest_exact"]=True
    result["read_only_missing_native_output_probe"]=p.missing_native_outputs()
    result["actual_public_generator_rust_tests"]=p.compiled_tests()
    result["source_sha256"]=prep["source_sha256"]
    exact(result,prep,"current_diagnostic_independent_preparation_payload_changed")
    historical=binding.previous.verified_traces();historical_pins={}
    for row,path,trace,passed in historical:
        exact(binding.verify_case_trace(trace,row),passed,"current_diagnostic_old_trace_changed")
        artifacts=binding.artifact_snapshot(path,trace,passed)
        historical_pins[str((path/"target-trace.json").relative_to(ROOT))]=q.sha(public.bounded_bytes(path/"target-trace.json",128*1024))
        historical_pins.update({str((path/name).relative_to(ROOT)):data["sha256"] for name,data in artifacts.items()})
    exact(binding.session_inventory(historical,6),component["historical_trace_reverification"],"current_diagnostic_old_sessions_changed")
    exact(historical_pins,component["historical_trace_and_artifact_sha256"],"current_diagnostic_old_artifact_pins_changed")
    lineage();exact(pins(old,prep,component),before,"current_diagnostic_sources_changed")
    return {"schema_version":"hwpx-agent.p09-current-native-diagnostic-admission/v1",
            "state":"current_source_diagnostic_preparation_only_not_old_authority_pass",
            "source_sha256":before,"original_root_capsule_sha256":p.CAPSULE_SHA,
            "original_preparation_sha256":binding.PREPARATION_SHA,"original_binding_sha256":COMPONENT_SHA,
            "old_current_preflight":{"state":"fail","error_code":"public_export_source_identity_changed","actually_invoked":True},
            "declared_changes":{"root_public_export_whole_inverse_exact":True,"only_two_cli_path_dependencies_lock_inverse_exact":True},
            "independent_preparation_payload_original_exact":True,"current_actual_public_generator_manifest_exact":True,
            "current_actual_rust_tests":result["actual_public_generator_rust_tests"],
            "historical_trace_reverification":component["historical_trace_reverification"],
            "historical_trace_and_artifact_sha256":historical_pins,
            "manifest_sha256":binding.MANIFEST_SHA,"cases":15,"stages":30,
            "claims":{"whole_old_authority_reexecuted":False,"full_source_successor_qualification":False,
                      "native_session_started":False,"native_semantics_or_color_name_repair":False,
                      "signed_production_route":False,"render":"not_run","product_differential":"not_run",
                      "green_rows":0,"p09_complete":False}}

def bind(prefix):
    before=preflight();manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    records,native_pins=binding.traces(manifest,prefix)
    observed=binding.rust_observations(prefix);binding.verify_rust(observed,records)
    cases=[]
    for actual,(row,path,trace,passed) in zip(observed["cases"],records,strict=True):
        input_raw=public.checked((ROOT/binding.MANIFEST).parent/row["file"],row["package_sha256"],4*1024*1024)
        item={"case_id":row["case_id"],"lifecycle":"pass" if passed else "fail",
              "failed_phase":trace["failed_phase"],"error_code":trace["error_code"],
              "permission_click_attestation":"not_attested","complete_public_readback":actual,
              "register_module_returns":[s["register_module_return"] for s in trace["sessions"]],
              "pdf_identity":{n:d for n,d in binding.artifact_snapshot(path,trace,passed).items() if n.endswith(".pdf")}}
        for stage,key in (("saved","output_sha256"),("reopened","reopened_sha256")):
            item[stage]={"state":"not_run"}
            if passed:
                raw=public.checked(path/(stage+".hwpx"),trace[key],4*1024*1024)
                try:item[stage]=q.compare_native(input_raw,raw)
                except (ValueError,KeyError,binding.ET.ParseError,binding.zipfile.BadZipFile):
                    item[stage]={"state":"fail","error_code":"independent_complete_projection_failed","package_sha256":q.sha(raw)}
        cases.append(item)
    exact(binding.traces(manifest,prefix)[1],native_pins,"current_diagnostic_native_evidence_changed")
    exact(preflight(),before,"current_diagnostic_admission_changed")
    return {"schema_version":"hwpx-agent.p09-current-native-diagnostic-bound/v1",
            "state":"actual_whole_diagnostic_batch_bound_non_green","current_admission":before,
            "native_evidence_sha256":native_pins,"cases":cases,"session_inventory":binding.session_inventory(records,15),
            "claims":{"native_semantics_or_color_name_repair_qualified":False,"signed_production_route":False,
                      "render":"not_run","product_differential":"not_run","green_rows":0,"p09_complete":False}}

def path_guard(path,prefix):
    target=path.absolute();expected=ROOT/(BOUND if prefix else CAPSULE)
    if target!=expected or ".." in path.parts:raise ValueError("current_diagnostic_evidence_boundary_invalid")
    q.shared.within(target.parent,ROOT/"implementation/p09/evidence")
    if target.exists():q.shared.within(target,ROOT/"implementation/p09/evidence")
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--prefix")
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        output=path_guard(args.output,args.prefix) if args.output else None
        verify=path_guard(args.verify,args.prefix) if args.verify else None
        if output and output.exists():raise ValueError("current_diagnostic_evidence_exists")
        value=bind(args.prefix) if args.prefix else preflight();raw=q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:exact(public.bounded_bytes(verify,2*1024*1024),raw,"current_diagnostic_capsule_changed")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,binding.subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and binding.re.fullmatch(r"[a-z_]+",str(error)) else "current_diagnostic_check_failed"
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":value["state"],"sha256":q.sha(raw),"bytes":len(raw),"green_rows":0}));return 0

if __name__=="__main__":raise SystemExit(main())
