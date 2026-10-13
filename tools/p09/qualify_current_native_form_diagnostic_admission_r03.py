#!/usr/bin/env python3
"""Append-only diagnostic admission successor with strict raw-byte verification."""
import argparse
import json
from pathlib import Path
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_current_native_form_diagnostic_admission as old
ROOT=old.ROOT
CAPSULE="implementation/p09/evidence/p09-36-native-form-diagnostic-current-admission.r03.json"
BOUND="implementation/p09/evidence/p09-36-native-form-diagnostic-current-bound.r03.json"
OLD_SHA="48539d43331e7d75f376de2ae4734d934f7d7de6867e0f304fb41e602be90702"
SOURCES=("tools/p09/qualify_current_native_form_diagnostic_admission_r03.py",
         "tools/p09/tests/test_current_native_form_diagnostic_admission_r03.py",
         "implementation/p09/P09-36_CURRENT_NATIVE_DIAGNOSTIC_ADMISSION_R03_POLICY.md")
def raw_equal(actual,expected):
    if type(actual) is not bytes or type(expected) is not bytes or actual!=expected:
        raise ValueError("current_diagnostic_raw_capsule_changed")
def pins():return {n:old.q.sha(old.public.bounded_bytes(ROOT/n,2097152)) for n in SOURCES}
def qualify(prefix=None):
    before=pins();raw=old.public.checked(ROOT/old.CAPSULE,OLD_SHA,2097152)
    preserved=json.loads(raw,object_pairs_hook=old.q.shared.lifecycle.duplicate_guard)
    # Diagnose the r02 raw-bytes JSON comparison bug without calling it PASS.
    try:old.exact(b"{}",b"{}","r02_probe")
    except TypeError:pass
    else:raise ValueError("current_diagnostic_r02_failure_missing")
    current=old.preflight()
    raw_equal(old.q.shared.lifecycle.canonical_bytes(current),raw)
    value=old.bind(prefix) if prefix else current
    for name,digest in preserved["source_sha256"].items():old.public.checked(ROOT/name,digest,2097152)
    raw_equal(old.public.checked(ROOT/old.CAPSULE,OLD_SHA,2097152),raw)
    old.exact(pins(),before,"current_diagnostic_r03_sources_changed")
    return {"schema_version":"hwpx-agent.p09-current-native-diagnostic-r03/v1",
            "state":value["state"],"source_sha256":before,"original_r02_sha256":OLD_SHA,
            "entire_original_r02_preflight_reexecuted_raw_byte_exact":True,
            "original_r02_fresh_verify_failure":{"state":"fail","error_type":"TypeError",
                "cause":"raw_bytes_passed_to_json_comparator","original_sources_unchanged":True},
            "diagnostic":value,"old_authority_or_full_source_or_gate_promoted":False}
def path_guard(path,prefix):
    target=path.absolute()
    if target!=ROOT/(BOUND if prefix else CAPSULE) or ".." in path.parts:
        raise ValueError("current_diagnostic_r03_path_invalid")
    old.q.shared.within(target.parent,ROOT/"implementation/p09/evidence")
    if target.exists():old.q.shared.within(target,ROOT/"implementation/p09/evidence")
    return target
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--prefix")
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    a=parser.parse_args()
    try:
        output=path_guard(a.output,a.prefix) if a.output else None
        verify=path_guard(a.verify,a.prefix) if a.verify else None
        if output and output.exists():raise ValueError("current_diagnostic_r03_exists")
        v=qualify(a.prefix);raw=old.q.shared.lifecycle.canonical_bytes(v)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:raw_equal(old.public.bounded_bytes(verify,2097152),raw)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,old.binding.subprocess.SubprocessError) as e:
        code=str(e) if type(e) is ValueError and old.binding.re.fullmatch(r"[a-z_]+",str(e)) else type(e).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":v["state"],"sha256":old.q.sha(raw),"bytes":len(raw),"green_rows":0}));return 0
if __name__=="__main__":raise SystemExit(main())
