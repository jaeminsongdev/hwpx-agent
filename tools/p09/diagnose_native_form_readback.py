#!/usr/bin/env python3
"""Real public SDK diagnosis, redacted and reproducible; never semantic/Gate repair."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
CAPSULE="implementation/p09/evidence/p09-47-native-readback-diagnosis.v1.json"
RECOVERY="implementation/p09/evidence/p09-36-native-form-complete-recovery.r06.json"
RECOVERY_SHA="47df877e392f1ffd0a79f16eb2629db8eedc1f85390f4b75e47a5d77029586cb"
MANIFEST="fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json"
MANIFEST_SHA="ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750"
SOURCES=("tools/p09/diagnose_native_form_readback.py",
         "tools/p09/tests/test_native_form_readback_diagnosis.py",
         "implementation/p09/P09-47_NATIVE_READBACK_DIAGNOSIS_POLICY.md",
         "crates/hwpx-package/examples/p09_47_native_readback_diagnosis.rs",
         "crates/hwpx-package/src/native_form_package.rs",
         "crates/hwpx-package/src/native_form_hwpx.rs",
         "crates/hwpx-package/src/preserving_xml.rs",
         "crates/hwpx-package/src/character_style.rs",
         "crates/hwpx-package/src/lib.rs","crates/hwpx-package/Cargo.toml",
         "crates/domain-ir/src/form_control.rs","Cargo.lock")
RUST_TESTS={"changed_fields_are_reported_as_fingerprints_without_values",
            "equal_missing_array_and_null_remain_distinct",
            "real_fifteen_case_reader_failures_are_not_promoted"}

def require(value,code):
    if not value:raise ValueError(code)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def canonical(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()

def duplicate_guard(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,"diagnosis_duplicate_json_key");result[key]=value
    return result

def read(path,limit=4*1024*1024):
    for item in (path,*path.parents):
        stat=item.lstat()
        require(not item.is_symlink() and not getattr(stat,"st_file_attributes",0)&0x400,"diagnosis_link_refused")
    stat=path.stat();require(path.is_file() and 0<stat.st_size<=limit,"diagnosis_file_bound")
    raw=path.read_bytes();require(len(raw)==stat.st_size,"diagnosis_source_changed_during_read");return raw

def checked(path,digest):
    raw=read(path);require(sha(raw)==digest,"diagnosis_source_identity_changed");return raw

def path_guard(path):
    target=path.absolute()
    require(target==ROOT/CAPSULE and ".." not in path.parts,"diagnosis_output_boundary")
    for item in (target.parent,*target.parent.parents):
        stat=item.lstat();require(not item.is_symlink() and not getattr(stat,"st_file_attributes",0)&0x400,"diagnosis_link_refused")
    if target.exists():read(target)
    return target

def pins():return {name:sha(read(ROOT/name)) for name in SOURCES}

def native_pins(recovery):
    expected=recovery["native_evidence_sha256"]
    require(isinstance(expected,dict) and len(expected)==75,"diagnosis_native_inventory")
    actual={}
    directories=set()
    for relative,digest in expected.items():
        parts=re.split(r"[/\\]",relative)
        require(len(parts)==6 and parts[:4]==["implementation","p09","evidence","private"]
                and re.fullmatch(r"p09-17-field-auto-number-target-p09-35-20261003-r05-c(?:0[1-9]|1[0-5])-attempt01",parts[4])
                and parts[5] in {"saved.hwpx","reopened.hwpx","saved.pdf","reopened.pdf","target-trace.json"},"diagnosis_native_path_boundary")
        actual[relative]=sha(checked(ROOT.joinpath(*parts),digest));directories.add(parts[4])
    require(len(directories)==15,"diagnosis_partial_native_inventory")
    return actual

def run(args):
    result=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    require(result.returncode==0,"diagnosis_actual_command_failed")
    return result.stdout,result.stderr

def rust_test_protocol(raw):
    text=raw.decode("utf-8",errors="strict")
    names=re.findall(r"^test tests::([a-z_]+) \.\.\. ok$",text,re.M)
    require(len(names)==3 and set(names)==RUST_TESTS and text.count(" ... ")==3
            and re.search(r"test result: ok\. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;",text)
            and "FAILED" not in text,"diagnosis_rust_test_protocol")
    return {"passed":3,"failed":0,"ignored":0,"filtered":0,"names":sorted(names),"actually_invoked":True}

def validate_observation(value,recovery):
    require(type(value) is dict and value.get("schema_version")=="hwpx-agent.p09-native-public-readback-diagnosis/v1"
            and value.get("recovery_sha256")==RECOVERY_SHA and value.get("manifest_sha256")==MANIFEST_SHA
            and value.get("native_session_started") is False and value.get("native_semantic_repair_qualified") is False
            and value.get("raw_document_values_present") is False and type(value.get("green_rows")) is int and value["green_rows"]==0
            and value.get("p09_complete") is False and value.get("all_seventy_five_native_files_before_after_exact") is True,
            "diagnosis_claim_protocol")
    rows=value.get("cases");old=recovery["actual_native_batch"]["cases"]
    require(type(rows) is list and len(rows)==len(old)==15,"diagnosis_case_inventory")
    for index,(row,prior) in enumerate(zip(rows,old)):
        require(row.get("case_id")==prior["case_id"]==f"P09-35-C{index+1:02}","diagnosis_case_order")
        for stage in ("saved","reopened"):
            actual=row[stage];previous=prior["complete_public_readback"][stage]
            require(actual["package_sha256"]==previous["package_sha256"] and actual["public_package_reader"]=="pass","diagnosis_actual_readback_identity")
            policy=actual["public_policy_binding"];domain=actual["independent_public_domain_validator"]
            require(len(actual["independent_public_section_readers"])==(2 if index<2 else 1)
                    and all(s["public_section_reader"]["state"]=="pass" for s in actual["independent_public_section_readers"]),"diagnosis_section_inventory")
            if index==0:
                require(previous.get("complete_public_reader_or_policy_binding")=="fail"
                        and policy=={"state":"fail","error_code":"NATIVE_FORM_PACKAGE_POLICY_REJECTED"}
                        and domain=={"state":"fail","error_code":"form_control_invalid_tab_order","duplicate_tab_order_count":1},"diagnosis_original_failure_lost")
            else:
                require(previous.get("complete_policy_binding")=="pass" and policy["state"]==domain["state"]=="pass"
                        and policy["canonical_sha256"]==domain["canonical_sha256"]==previous["target_state_sha256"],"diagnosis_policy_binding_changed")
            require(actual["document_flow_exact"] is (previous.get("document_flow_exact",True)),"diagnosis_flow_changed")
            for group in ("control_field_differences","package_binding_differences"):
                require(type(actual[group]) is list and len(actual[group])<=256,"diagnosis_differences_bound")
                for difference in actual[group]:
                    require(set(difference)=={"field","expected","observed"}
                            and re.fullmatch(r"/(?:controls|bindings)(?:/[a-z_0-9]+)+",difference["field"]),"diagnosis_difference_privacy")
                    for side in ("expected","observed"):
                        item=difference[side]
                        require(type(item.get("present")) is bool and set(item)==({"present","sha256"} if item["present"] else {"present"}),"diagnosis_difference_fingerprint")
                        if item["present"]:require(re.fullmatch(r"[a-f0-9]{64}",item["sha256"]),"diagnosis_difference_digest")
    return value

def diagnose():
    before=pins();recovery=json.loads(checked(ROOT/RECOVERY,RECOVERY_SHA),object_pairs_hook=duplicate_guard)
    checked(ROOT/MANIFEST,MANIFEST_SHA);native=native_pins(recovery)
    tests=rust_test_protocol(run(["cargo","test","--locked","--offline","-p","hwpx-package","--example","p09_47_native_readback_diagnosis"])[0])
    run(["cargo","clippy","--locked","--offline","-p","hwpx-package","--example","p09_47_native_readback_diagnosis","--","-D","warnings"])
    raw,errors=run(["cargo","run","--quiet","--locked","--offline","-p","hwpx-package","--example","p09_47_native_readback_diagnosis"])
    require(not errors.strip() and 0<len(raw)<=512*1024,"diagnosis_actual_output_protocol")
    observed=validate_observation(json.loads(raw,object_pairs_hook=duplicate_guard),recovery)
    require(pins()==before and native_pins(recovery)==native,"diagnosis_before_after_changed")
    checked(ROOT/RECOVERY,RECOVERY_SHA);checked(ROOT/MANIFEST,MANIFEST_SHA)
    return {"schema_version":"hwpx-agent.p09-public-native-readback-diagnosis-receipt/v1",
            "state":"actual_fifteen_case_thirty_stage_readonly_diagnosis_non_green","immediate_source_sha256":before,
            "source_scope":"immediate_consumer_and_selected_public_implementation_not_complete_transitive_qualification",
            "actual_rust_tests":tests,"actual_clippy_warnings_denied":True,"native_evidence_sha256":native,"observation":observed,
            "original_recovery_fresh_verification":"separately_completed_not_reexecuted_by_this_diagnostic",
            "claims":{"original_failure_retained":True,"new_native_session_started":False,"semantic_fix_qualified":False,
                      "render":"not_run","product_differential":"not_run","whole_source_qualification":False,"green_rows":0,"p09_complete":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        target=path_guard(args.output or args.verify)
        require(not args.output or not target.exists(),"diagnosis_receipt_exists")
        value=diagnose();raw=canonical(value)
        if args.output:
            with target.open("xb") as stream:stream.write(raw)
        else:require(read(target)==raw,"diagnosis_fresh_whole_result_changed")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":value["state"],"bytes":len(raw),"sha256":sha(raw),"actual_cases":15,"actual_stages":30,"semantic_fix":False,"green_rows":0}));return 0

if __name__=="__main__":raise SystemExit(main())
