#!/usr/bin/env python3
"""ONE complete diagnostic matrix through the qualified fixed x86/STA harness."""
import json
import subprocess
import sys
if not __package__:
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_owned_exit_wait_environment as a

def hwp_zero():
    command="if (@(Get-CimInstance Win32_Process -Filter \"Name='Hwp.exe'\" -ErrorAction Stop).Count -ne 0) {exit 2};[Console]::Write('P09_HWP_ZERO')"
    result=subprocess.run([str(a.SHELL),"-NoProfile","-Command",command],cwd=a.ROOT,env=a.child_environment(),capture_output=True,timeout=30,
                          creationflags=subprocess.CREATE_NO_WINDOW)
    a.require(result.returncode==0 and result.stdout==b"P09_HWP_ZERO" and not result.stderr,"owned_exit_preexisting_hwp")

def case_plan(manifest,prefix=a.PREFIX):
    a.require(prefix==a.PREFIX and type(manifest) is dict and type(manifest.get("cases")) is list
              and len(manifest["cases"])==15,"owned_exit_dispatch_inventory")
    paths=a.binding.attempt_paths(prefix);result=[]
    for index,(row,path) in enumerate(zip(manifest["cases"],paths,strict=True)):
        a.require(type(row) is dict and row.get("case_id")==f"P09-35-C{index+1:02}"
                  and row.get("file")==f"p09-35-c{index+1:02}-{a.binding.prepared.LABELS[index]}.hwpx",
                  "owned_exit_dispatch_case_identity")
        a.require(not path.exists(),"owned_exit_dispatch_attempt_exists")
        a.q.shared.within(path.parent,a.ROOT/"implementation/p09/evidence/private")
        source=(a.ROOT/a.binding.MANIFEST).parent/row["file"]
        raw=a.public.checked(source,row["package_sha256"],4194304)
        a.require(type(row["package_bytes"]) is int and len(raw)==row["package_bytes"],"owned_exit_dispatch_input_bytes")
        result.append((row,source,path))
    return result

def run():
    output=a.path_guard(a.ROOT/a.DISPATCH,"dispatch");a.require(not output.exists(),"owned_exit_dispatch_receipt_exists")
    admission=a.qualify();raw=a.q.shared.lifecycle.canonical_bytes(admission)
    a.prior.raw_equal(a.public.bounded_bytes(a.ROOT/a.CAPSULE,2097152),raw)
    manifest=a.q.shared.lifecycle.checked_json(a.ROOT/a.binding.MANIFEST,a.binding.MANIFEST_SHA)
    plan=case_plan(manifest);before=a.own_pins();a.old.exact(before,admission["source_sha256"],"owned_exit_dispatch_pin_change")
    cases=[];native_pins={}
    for row,source,path in plan:
        a.old.exact(a.own_pins(),before,"owned_exit_dispatch_pin_change");hwp_zero()
        print(json.dumps({"event":"case_start","case_id":row["case_id"],"of":15}),flush=True)
        command=[str(a.SHELL),"-NoProfile","-STA","-File",str(a.ROOT/a.HARNESS),"-InputPath",str(source),
                 "-ExpectedInputSha256",row["package_sha256"],"-RunDirectory",str(path)]
        # No permission timeout/relaunch. Exact pinned harness writes its own trace.
        process=subprocess.Popen(command,cwd=a.ROOT,env=a.child_environment(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        size=0
        for line in process.stdout:
            size+=len(line)
            marker=line.strip()
            if marker in (b"P09_FIELD_AUTO_NUMBER_READY_FOR_INPUT_OPEN",b"P09_FIELD_AUTO_NUMBER_READY_FOR_FRESH_REOPEN"):
                print(json.dumps({"event":marker.decode("ascii"),"case_id":row["case_id"]}),flush=True)
        code=process.wait();a.require(size<=131072,"owned_exit_dispatch_child_output_limit")
        trace_raw=a.public.bounded_bytes(path/"target-trace.json",131072)
        trace=json.loads(trace_raw,object_pairs_hook=a.q.shared.lifecycle.duplicate_guard)
        # Keep partial evidence; rejected trace/global cleanup stops, never forced kill.
        hwp_zero();passed=a.binding.verify_case_trace(trace,row);snapshot=a.binding.artifact_snapshot(path,trace,passed)
        a.require(code==(0 if passed else 2),"owned_exit_dispatch_exit_unbound")
        case={"case_id":row["case_id"],"harness_exit":code,"lifecycle":"pass" if passed else "fail","sessions":len(trace["sessions"])}
        cases.append(case);print(json.dumps(case),flush=True)
        native_pins[(path/"target-trace.json").relative_to(a.ROOT).as_posix()]=a.q.sha(trace_raw)
        native_pins.update({(path/name).relative_to(a.ROOT).as_posix():data["sha256"] for name,data in snapshot.items()})
        a.old.exact(a.own_pins(),before,"owned_exit_dispatch_pin_change")
    records,actual_pins=a.binding.traces(manifest,a.PREFIX)
    # Original binder uses Windows string paths, not portable slash aliases.
    a.old.exact({str(a.ROOT/name):digest for name,digest in native_pins.items()},
                {str(a.ROOT/name):digest for name,digest in actual_pins.items()},"owned_exit_dispatch_native_pin_change")
    a.old.exact(a.prior_attempts(),admission["prior_partial_batch_preserved"],"owned_exit_dispatch_prior_changed")
    value={"schema_version":"hwpx-agent.p09-native-owned-exit-dispatch/v1","state":"all_fifteen_actual_attempts_terminal",
           "prefix":a.PREFIX,"harness_sha256":a.HARNESS_SHA,"admission_sha256":a.q.sha(raw),"source_sha256":before,
           "cases":cases,"native_evidence_sha256":actual_pins,"session_inventory":a.binding.session_inventory(records,15),
           "permission_click_attestation":"not_attested","computer_use_click_or_type_invoked":False,
           "claims":{"native_semantics_or_render_or_differential_qualified":False,"green_rows":0,"p09_complete":False}}
    with output.open("xb") as stream:stream.write(a.q.shared.lifecycle.canonical_bytes(value))
    print(json.dumps({"state":"pass","actual_attempts":15,"native_semantics_qualified":False,"green_rows":0}),flush=True)

if __name__=="__main__":
    try:run()
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and a.re.fullmatch(r"[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code,"partial_evidence_preserved":True}),flush=True);raise SystemExit(2)
