#!/usr/bin/env python3
"""Actual legacy module path in child process only; no policy/trust/system change."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_owned_exit_wait_admission as previous
ROOT=previous.ROOT
q,binding,public,old,prior=previous.q,previous.binding,previous.public,previous.old,previous.prior
HARNESS,HARNESS_SHA,SHELL=previous.HARNESS,previous.HARNESS_SHA,previous.SHELL
require=previous.require
CAPSULE="implementation/p09/evidence/p09-36-native-form-owned-exit-environment.r05.json"
DISPATCH="implementation/p09/evidence/p09-36-native-form-owned-exit-dispatch.r05.json"
BOUND="implementation/p09/evidence/p09-36-native-form-owned-exit-bound.r05.json"
PREFIX="p09-35-20261003-r05"
PREVIOUS_SHA="d9d75f6fe4442ecbe702cd9d90fd5f0584b47de60825269bc6ed64325c1a4125"
PROBE="implementation/p09/tools/probe-hancom-native-preflight-no-com.ps1"
MODULE_ROOT=Path("C:/Windows/SysWOW64/WindowsPowerShell/v1.0/Modules")
LEGACY_PATHS=(str(MODULE_ROOT),"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\Modules")
MODULES=(MODULE_ROOT/"Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1",
         MODULE_ROOT/"Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psm1")
SOURCES=("tools/p09/qualify_native_owned_exit_wait_environment.py","tools/p09/run_native_owned_exit_wait_environment_batch.py",
         "tools/p09/tests/test_native_owned_exit_wait_environment.py",
         "implementation/p09/P09-36_NATIVE_OWNED_EXIT_WAIT_ENVIRONMENT_POLICY.md",PROBE,previous.CAPSULE)
GUARDS={"test_child_environment_changes_only_legacy_module_path_not_parent_or_policy",
        "test_whole_dispatcher_inverse_only_fixed_import_and_child_environment_changed",
        "test_prefix_probe_is_exact_original_pre_native_body_no_com_or_run_creation",
        "test_old_r04_first_case_has_no_trace_or_owned_session_to_promote",
        "test_new_fixed_capsule_paths_reject_prior_private_alias_and_traversal",
        "test_full_new_fifteen_case_inventory_and_zero_threshold_remain_strict"}

def child_environment(parent=None):
    result=dict(os.environ if parent is None else parent);result["PSModulePath"]=";".join(LEGACY_PATHS)
    return result

def own_pins():return {name:q.sha(public.bounded_bytes(ROOT/name,2097152)) for name in SOURCES}

def path_guard(path,kind="admission"):
    target=path.absolute();expected={"admission":CAPSULE,"dispatch":DISPATCH,"bound":BOUND}[kind]
    require(str(target)==str(ROOT/expected) and ".." not in path.parts,"owned_exit_environment_path_invalid")
    q.shared.within(target.parent,ROOT/"implementation/p09/evidence")
    if target.exists():q.shared.within(target,ROOT/"implementation/p09/evidence")
    return target

def prior_attempts():return previous.prior_attempts()

def prefix_inverse():
    actual=public.bounded_bytes(ROOT/PROBE,65536)
    original=public.checked(ROOT/HARNESS,HARNESS_SHA,65536)
    marker=b"[void][IO.Directory]::CreateDirectory($run)"
    suffix=b"[Console]::Write('P09_EXACT_PRE_NATIVE_PREFIX_PASS')\nexit 0\n"
    require(original.count(marker)==1 and actual==original[:original.index(marker)]+suffix,
            "owned_exit_environment_probe_inverse_changed")
    return True

def dispatcher_inverse():
    original=public.bounded_bytes(ROOT/"tools/p09/run_native_owned_exit_wait_batch.py",65536)
    actual=public.bounded_bytes(ROOT/"tools/p09/run_native_owned_exit_wait_environment_batch.py",65536)
    import_old=b"from tools.p09 import qualify_native_owned_exit_wait_admission as a"
    import_new=b"from tools.p09 import qualify_native_owned_exit_wait_environment as a"
    require(original.count(import_old)==1,"owned_exit_environment_dispatch_import_changed")
    expected=original.replace(import_old,import_new,1)
    # Same full dispatcher, with ONLY explicit legacy environment for the two child shell calls.
    expected=expected.replace(b"cwd=a.ROOT,capture_output=True,timeout=30,",b"cwd=a.ROOT,env=a.child_environment(),capture_output=True,timeout=30,",1)
    expected=expected.replace(b"process=subprocess.Popen(command,cwd=a.ROOT,stdout=",b"process=subprocess.Popen(command,cwd=a.ROOT,env=a.child_environment(),stdout=",1)
    require(actual==expected,"owned_exit_environment_dispatch_complete_inverse_changed")
    return True

def module_proof():
    before={str(path):q.sha(public.bounded_bytes(path,1048576)) for path in MODULES}
    command="$c=Get-Command Get-FileHash -ErrorAction Stop;[pscustomobject]@{command_type=[string]$c.CommandType;module_name=$c.ModuleName;module_path=$c.Module.Path}|ConvertTo-Json -Compress"
    process=subprocess.run([str(SHELL),"-NoProfile","-Command",command],cwd=ROOT,env=child_environment(),
                           capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    require(process.returncode==0 and not process.stderr and len(process.stdout)<=8192,"owned_exit_legacy_module_command_failed")
    value=json.loads(process.stdout,object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    old.exact(value,{"command_type":"Function","module_name":"Microsoft.PowerShell.Utility","module_path":str(MODULES[0])},
              "owned_exit_legacy_module_command_changed")
    require({str(path):q.sha(public.bounded_bytes(path,1048576)) for path in MODULES}==before,"owned_exit_legacy_module_files_changed")
    return {"actual_builtin_get_file_hash":value,"installed_windows_module_sha256":before,"no_module_install_or_replacement":True}

def prefix_run(environment):
    manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    row=manifest["cases"][0];target=binding.attempt_paths(previous.PREFIX)[0]
    require(not target.exists(),"owned_exit_failed_r04_native_state_changed")
    source=(ROOT/binding.MANIFEST).parent/row["file"]
    process=subprocess.run([str(SHELL),"-NoProfile","-STA","-File",str(ROOT/PROBE),"-InputPath",str(source),
                            "-ExpectedInputSha256",row["package_sha256"],"-RunDirectory",str(target)],
                           cwd=ROOT,env=environment,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    require(len(process.stdout)<=131072 and len(process.stderr)<=131072 and not target.exists(),"owned_exit_prefix_native_or_output_changed")
    text=process.stderr.decode("utf-8",errors="replace")
    return process,text

def qualify():
    before=own_pins();environment_before=dict(os.environ);old_raw=public.checked(ROOT/previous.CAPSULE,PREVIOUS_SHA,2097152)
    prefix_inverse();dispatcher_inverse()
    previous_value=previous.qualify();prior.raw_equal(q.shared.lifecycle.canonical_bytes(previous_value),old_raw)
    inherited,text=prefix_run(dict(os.environ))
    require(inherited.returncode==1 and b"Get-FileHash" in inherited.stderr and "CommandNotFoundException" in text,
            "owned_exit_inherited_module_failure_changed")
    corrected,_=prefix_run(child_environment())
    require(corrected.returncode==0 and corrected.stdout==b"P09_EXACT_PRE_NATIVE_PREFIX_PASS" and not corrected.stderr,
            "owned_exit_actual_legacy_prefix_failed")
    module=module_proof()
    actual_guards=previous.guards("tools.p09.tests.test_native_owned_exit_wait_environment","OwnedExitEnvironmentTests",GUARDS)
    old.exact(own_pins(),before,"owned_exit_environment_sources_changed")
    require(dict(os.environ)==environment_before,"owned_exit_parent_environment_changed")
    require(all(not path.exists() for path in binding.attempt_paths(previous.PREFIX)),"owned_exit_r04_not_run_changed")
    return {"schema_version":"hwpx-agent.p09-native-owned-exit-environment/v1",
            "state":"actual_legacy_child_environment_and_exit_wait_admitted_non_green","source_sha256":before,
            "prior_r04_sha256":PREVIOUS_SHA,"whole_original_r04_admission_reexecuted_byte_exact":True,
            "prior_r04_admission":previous_value,"harness_sha256":HARNESS_SHA,
            "fixed_child_module_paths":LEGACY_PATHS,"actual_legacy_module_proof":module,
            "actual_prefix_diagnostics":{"inherited":{"exit_code":1,"error_id":"CommandNotFoundException","missing_builtin":"Get-FileHash"},
                                        "corrected":{"exit_code":0,"exact_pre_native_prefix_pass":True},
                                        "no_com_session_or_new_run_directory":True,"parent_environment_unchanged":True},
            "actual_source_guards":actual_guards,"whole_dispatcher_inverse_only_import_and_two_environment_arguments":True,
            "prior_r04_native_attempt":{"native_session_started":False,"run_directories":0,"trace_files":0,"actual_dispatch_exit":1},
            "claims":{"actual_new_native_batch":"not_run","native_semantics_or_render_or_differential_qualified":False,
                      "old_authority_or_full_source_pass":False,"machine_settings_trust_or_security_changed":False,
                      "green_rows":0,"p09_complete":False}}

def binding_proof():
    admission=qualify();raw=q.shared.lifecycle.canonical_bytes(admission)
    prior.raw_equal(public.bounded_bytes(ROOT/CAPSULE,2097152),raw)
    dispatch=json.loads(public.bounded_bytes(ROOT/DISPATCH,2097152),object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    require(dispatch["state"]=="all_fifteen_actual_attempts_terminal" and dispatch["prefix"]==PREFIX
            and dispatch["harness_sha256"]==HARNESS_SHA and dispatch["admission_sha256"]==q.sha(raw),"owned_exit_environment_dispatch_unbound")
    old.exact(dispatch["source_sha256"],admission["source_sha256"],"owned_exit_environment_dispatch_sources_unbound")
    manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    records,pins=binding.traces(manifest,PREFIX)
    old.exact(dispatch["native_evidence_sha256"],pins,"owned_exit_environment_dispatch_evidence_unbound")
    observed=old.bind(PREFIX)
    old.exact(observed["native_evidence_sha256"],pins,"owned_exit_environment_readback_evidence_changed")
    require([row["case_id"] for row in dispatch["cases"]]==[row["case_id"] for row in manifest["cases"]],"owned_exit_environment_case_inventory")
    for row,record in zip(dispatch["cases"],records,strict=True):
        old.exact(row,{"case_id":record[0]["case_id"],"harness_exit":0 if record[3] else 2,
                       "lifecycle":"pass" if record[3] else "fail","sessions":len(record[2]["sessions"])},"owned_exit_environment_case_unbound")
    old.exact(own_pins(),admission["source_sha256"],"owned_exit_environment_bound_sources_changed")
    old.exact(prior_attempts(),admission["prior_r04_admission"]["prior_partial_batch_preserved"],"owned_exit_environment_prior_evidence_changed")
    return {"schema_version":"hwpx-agent.p09-native-owned-exit-environment-bound/v1","state":"actual_complete_legacy_environment_native_batch_bound_non_green",
            "admission_sha256":q.sha(raw),"dispatch_sha256":q.sha(public.bounded_bytes(ROOT/DISPATCH,2097152)),
            "source_sha256":admission["source_sha256"],"actual_native_batch":observed,"harness_sha256":HARNESS_SHA,
            "actual_legacy_module_proof":admission["actual_legacy_module_proof"],
            "claims":{"actual_owned_exit_wait_and_child_environment_native_tested":True,
                      "native_semantics_or_render_or_differential_qualified":False,"old_authority_or_full_source_pass":False,
                      "green_rows":0,"p09_complete":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--bind",action="store_true")
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        kind="bound" if args.bind else "admission";output=path_guard(args.output,kind) if args.output else None
        verify=path_guard(args.verify,kind) if args.verify else None;require(not output or not output.exists(),"owned_exit_environment_capsule_exists")
        value=binding_proof() if args.bind else qualify();raw=q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:prior.raw_equal(public.bounded_bytes(verify,2097152),raw)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":value["state"],"sha256":q.sha(raw),"bytes":len(raw),"green_rows":0}));return 0
if __name__=="__main__":raise SystemExit(main())
