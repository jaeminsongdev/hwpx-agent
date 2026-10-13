#!/usr/bin/env python3
"""Bounded real-exit wait qualification; original trace and zero requirement unchanged."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_current_native_form_diagnostic_admission_r03 as prior
from tools.p09.tests.test_native_owned_exit_wait_harness import WAIT
ROOT=prior.ROOT
old=prior.old
q,binding,public=old.q,old.binding,old.public
HARNESS="implementation/p09/tools/run-hancom-2020-field-auto-number-target-owned-exit-wait.ps1"
HARNESS_SHA="7463b70fce52407f5173da8ccff75344ce740ab88f664620796d591edd3ec1a3"
PRIOR_SHA="091ead43b66a3cdc6bde7c36e44cf027875d188e39fd91d7df3d30912459aa86"
CAPSULE="implementation/p09/evidence/p09-36-native-form-owned-exit-admission.r04.json"
BOUND="implementation/p09/evidence/p09-36-native-form-owned-exit-bound.r04.json"
DISPATCH="implementation/p09/evidence/p09-36-native-form-owned-exit-dispatch.r04.json"
PREFIX="p09-35-20261003-r04"
SHELL=Path("C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe")
SOURCES=(HARNESS,"tools/p09/tests/test_native_owned_exit_wait_harness.py",
         "implementation/p09/P09-36_NATIVE_OWNED_EXIT_WAIT_POLICY.md",
         "tools/p09/qualify_native_owned_exit_wait_admission.py",
         "tools/p09/tests/test_native_owned_exit_wait_admission.py",
         "implementation/p09/P09-36_NATIVE_OWNED_EXIT_WAIT_ADMISSION_POLICY.md",
         "tools/p09/run_native_owned_exit_wait_batch.py",prior.CAPSULE)
GUARDS={"test_complete_candidate_inverse_and_same_zero_exit_reject_unrelated_change",
        "test_exact_raw_byte_protocol_rejects_types_missing_extra_and_mutation",
        "test_old_seven_attempts_preserve_rejected_cleanup_and_all_thirty_five_files",
        "test_fixed_current_paths_reject_original_private_traversal_and_alias",
        "test_current_dispatch_inventory_only_complete_fifteen_cases_unique_unused_paths",
        "test_guard_protocol_requires_all_names_code_zero_no_skip_extra_or_coercion"}
WAIT_GUARDS={"test_whole_original_inverse_and_only_bounded_read_only_wait_inserted",
             "test_final_zero_process_requirement_and_failed_exit_unchanged",
             "test_actual_rejected_c07_trace_remains_one_not_rewritten"}

def require(value,code):
    if not value:raise ValueError(code)

def inverse(actual,original):
    require(type(actual) is bytes and type(original) is bytes and actual.count(WAIT)==1
            and actual.replace(WAIT,b"",1)==original,"owned_exit_complete_inverse_changed")
    require(actual.index(WAIT)>actual.index(b"Start-Sleep -Milliseconds 500")
            and actual.index(WAIT)<actual.index(b"$trace.completed_at_utc"),"owned_exit_wait_position_changed")
    return {"only_bounded_read_only_post_quit_wait":True,"global_actual_zero_count_required":True,
            "target_input_session_security_and_exit_body_unchanged":True,"force_kill_or_security_click":False}

def own_pins():return {name:q.sha(public.bounded_bytes(ROOT/name,2097152)) for name in SOURCES}

def guard_protocol(code,stdout,stderr,module,klass,names):
    text=stderr.decode("utf-8",errors="strict");found=[]
    pattern=rf"(test_[a-z0-9_]+) \({re.escape(module)}\.{re.escape(klass)}\.([a-z0-9_]+)\) \.\.\. ok"
    for line in text.splitlines():
        match=re.fullmatch(pattern,line)
        if match:
            require(match.group(1)==match.group(2),"owned_exit_guards_failed");found.append(match.group(1))
    count=len(names)
    require(type(code) is int and code==0 and type(stdout) is bytes and not stdout.strip() and len(found)==count
            and set(found)==names and text.count(" ... ")==count and "skipped" not in text
            and re.search(rf"\nRan {count} tests in [0-9.]+s\s+OK\s*$",text),"owned_exit_guards_failed")
    return {"passed":count,"failed":0,"errors":0,"skipped":0,"names":sorted(names),"actually_invoked":True}

def guards(module,klass,names):
    result=subprocess.run([sys.executable,"-B","-m","unittest","-v",module],cwd=ROOT,capture_output=True,timeout=120,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
    require(len(result.stdout)<=131072 and len(result.stderr)<=1048576,"owned_exit_guard_output_limit")
    return guard_protocol(result.returncode,result.stdout,result.stderr,module,klass,names)

def prior_attempts():
    manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    paths=binding.attempt_paths("p09-35-20261003-r03");pins={};records=[]
    require(all(not path.exists() for path in paths[7:]),"owned_exit_old_not_run_changed")
    for index,path in enumerate(paths[:7]):
        raw=public.bounded_bytes(path/"target-trace.json",131072)
        trace=json.loads(raw,object_pairs_hook=q.shared.lifecycle.duplicate_guard)
        if index<6:
            require(binding.verify_case_trace(trace,manifest["cases"][index]) is True,"owned_exit_old_trace_changed")
            binding.artifact_snapshot(path,trace,True)
        else:
            require(trace["remaining_hwp_process_count"]==1 and trace["state"]=="pass", "owned_exit_failed_trace_changed")
            try:binding.verify_case_trace(trace,manifest["cases"][index])
            except ValueError as error:require(str(error)=="lifecycle_trace_mismatch","owned_exit_failure_changed")
            else:raise ValueError("owned_exit_failed_trace_promoted")
        require({file.name for file in path.iterdir()}=={"target-trace.json",*binding.ARTIFACTS},"owned_exit_old_files_changed")
        pins[(path/"target-trace.json").relative_to(ROOT).as_posix()]=q.sha(raw)
        for name,(digest_key,bytes_key,maximum) in binding.ARTIFACTS.items():
            value=public.checked(path/name,trace[digest_key],maximum)
            require(type(trace[bytes_key]) is int and len(value)==trace[bytes_key],"owned_exit_old_artifact_bytes_changed")
            pins[(path/name).relative_to(ROOT).as_posix()]=q.sha(value)
        records.append({"case_id":manifest["cases"][index]["case_id"],"trace_binding":"pass" if index<6 else "fail",
                        "recorded_remaining":trace["remaining_hwp_process_count"],"owned_sessions":len(trace["sessions"])})
    require(len(pins)==35,"owned_exit_old_artifact_inventory")
    return {"source_sha256":pins,"cases":records,"not_run_cases":8,"old_failed_trace_edited_or_promoted":False}

def path_guard(path,kind="admission"):
    expected={"admission":CAPSULE,"bound":BOUND,"dispatch":DISPATCH}[kind];target=path.absolute()
    require(str(target)==str(ROOT/expected) and ".." not in path.parts,"owned_exit_evidence_boundary_invalid")
    q.shared.within(target.parent,ROOT/"implementation/p09/evidence")
    if target.exists():q.shared.within(target,ROOT/"implementation/p09/evidence")
    return target

def parser_proof():
    script_path=str(ROOT/HARNESS).replace("'","''")
    command="$t=$null;$e=$null;[void][System.Management.Automation.Language.Parser]::ParseFile('"+script_path+"',[ref]$t,[ref]$e);if (@($e).Count -ne 0) {exit 2};[Console]::Write('P09_OWNED_EXIT_PARSER_PASS')"
    # A fixed command and fixed script path; no user data, UI or COM session.
    result=subprocess.run([str(SHELL),"-NoProfile","-STA","-Command",command],cwd=ROOT,
                          capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    require(result.returncode==0 and result.stdout==b"P09_OWNED_EXIT_PARSER_PASS" and not result.stderr,
            "owned_exit_actual_x86_parser_failed")
    return {"actual_x86_powershell_parser_errors":0,"native_session_started":False,
            "shell_sha256":q.sha(public.bounded_bytes(SHELL,16777216))}

def qualify():
    before=own_pins();previous=prior_attempts()
    transition=inverse(public.checked(ROOT/HARNESS,HARNESS_SHA),public.checked(ROOT/q.HARNESS,q.HARNESS_SHA))
    prior_raw=public.checked(ROOT/prior.CAPSULE,PRIOR_SHA,2097152)
    current=prior.qualify();prior.raw_equal(q.shared.lifecycle.canonical_bytes(current),prior_raw)
    actual_wait=guards("tools.p09.tests.test_native_owned_exit_wait_harness","NativeOwnedExitWaitHarnessTests",WAIT_GUARDS)
    actual_guards=guards("tools.p09.tests.test_native_owned_exit_wait_admission","OwnedExitAdmissionTests",GUARDS)
    parser=parser_proof()
    old.exact(own_pins(),before,"owned_exit_sources_changed");old.exact(prior_attempts(),previous,"owned_exit_old_evidence_changed")
    return {"schema_version":"hwpx-agent.p09-native-owned-exit-admission/v1",
            "state":"bounded_actual_exit_wait_diagnostic_admitted_non_green","source_sha256":before,
            "prior_admission_sha256":PRIOR_SHA,"whole_original_r03_preflight_reexecuted_byte_exact":True,
            "current_source_diagnostic_admission":current,"harness_sha256":HARNESS_SHA,
            "whole_harness_inverse":transition,"actual_wait_guards":actual_wait,"actual_admission_guards":actual_guards,
            "actual_parser":parser,"prior_partial_batch_preserved":previous,
            "prepared_cases":15,"prepared_stages":30,"claims":{"actual_owned_exit_wait_native_tested":False,
            "native_semantics_or_render_or_differential_qualified":False,"old_authority_or_full_source_pass":False,
            "signed_production_routing":False,"green_rows":0,"p09_complete":False}}

def binding_proof():
    admission=qualify();raw=q.shared.lifecycle.canonical_bytes(admission)
    prior.raw_equal(public.bounded_bytes(ROOT/CAPSULE,2097152),raw)
    dispatch=json.loads(public.bounded_bytes(ROOT/DISPATCH,2097152),object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    require(dispatch["state"]=="all_fifteen_actual_attempts_terminal" and dispatch["prefix"]==PREFIX
            and dispatch["harness_sha256"]==HARNESS_SHA and dispatch["admission_sha256"]==q.sha(raw),"owned_exit_dispatch_unbound")
    old.exact(dispatch["source_sha256"],admission["source_sha256"],"owned_exit_dispatch_sources_unbound")
    manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    records,native_pins=binding.traces(manifest,PREFIX)
    old.exact(dispatch["native_evidence_sha256"],native_pins,"owned_exit_dispatch_evidence_unbound")
    observed=old.bind(PREFIX)
    old.exact(observed["native_evidence_sha256"],native_pins,"owned_exit_native_evidence_changed")
    require([row["case_id"] for row in dispatch["cases"]]==[row["case_id"] for row in manifest["cases"]],"owned_exit_dispatch_case_inventory")
    for row,record in zip(dispatch["cases"],records,strict=True):
        trace=record[2]
        old.exact(row,{"case_id":record[0]["case_id"],"harness_exit":0 if record[3] else 2,
                       "lifecycle":"pass" if record[3] else "fail","sessions":len(trace["sessions"])},"owned_exit_dispatch_case_unbound")
    old.exact(own_pins(),admission["source_sha256"],"owned_exit_bound_source_change")
    old.exact(prior_attempts(),admission["prior_partial_batch_preserved"],"owned_exit_bound_old_evidence_change")
    return {"schema_version":"hwpx-agent.p09-native-owned-exit-bound/v1","state":"actual_whole_owned_exit_batch_bound_non_green",
            "admission_sha256":q.sha(raw),"dispatch_sha256":q.sha(public.bounded_bytes(ROOT/DISPATCH,2097152)),
            "source_sha256":admission["source_sha256"],"actual_native_batch":observed,
            "claims":{"actual_owned_exit_wait_native_tested":True,"native_semantics_or_render_or_differential_qualified":False,
                      "old_authority_or_full_source_pass":False,"green_rows":0,"p09_complete":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--bind",action="store_true")
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        kind="bound" if args.bind else "admission"
        output=path_guard(args.output,kind) if args.output else None;verify=path_guard(args.verify,kind) if args.verify else None
        require(not output or not output.exists(),"owned_exit_capsule_exists")
        value=binding_proof() if args.bind else qualify();raw=q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:prior.raw_equal(public.bounded_bytes(verify,2097152),raw)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":value["state"],"sha256":q.sha(raw),"bytes":len(raw),"green_rows":0}));return 0
if __name__=="__main__":raise SystemExit(main())
