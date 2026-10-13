#!/usr/bin/env python3
"""Actual public managed-value API qualification; never native/product acceptance."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import reproduce_value_output_pre_export as history
from tools.p09 import qualify_form_input_public_export as input_public

old, ROOT = history.old, history.ROOT
q, public, oracle = old.q, old.public, old.oracle
LIB, ARCHIVE = history.LIB, history.ARCHIVE
CURRENT_LIB = "bf31a1b7ac34a11724280fd498a722a28bced3c2a264a48a101c058f0ab262bd"
DELTA = b"pub mod native_form_value_output;\n"
TEST = "crates/hwpx-package/tests/native_form_value_output_public.rs"
SOURCES = (LIB, ARCHIVE, TEST, "tools/p09/reproduce_value_output_pre_export.py",
           "tools/p09/qualify_native_form_value_public_export.py",
           "tools/p09/tests/test_native_form_value_public_export.py",
           "implementation/p09/P09-41_NATIVE_FORM_VALUE_PUBLIC_EXPORT_POLICY.md")


def project(raw, archived):
    oracle.require(q.sha(raw) == CURRENT_LIB and q.sha(archived) == history.OLD_LIB
                   and raw.count(DELTA) == 1 and raw.replace(DELTA, b"", 1) == archived,
                   "value_public_complete_inverse_invalid")


def lineage(actual, pending):
    marker = b"fn hex("
    common = b"use sha2::{Digest as _, Sha256};\n"
    prefix = (b"//! Complete predecessor cases through the actual public versioned value API only.\n"
              b"use domain_ir::form_input::*;\nuse domain_ir::*;\n"
              b"use hwpx_package::native_form_value_output::*;\npub use hwpx_package::*;\n")
    oracle.require(actual.count(marker) == pending.count(marker) == 1
                   and pending.count(common) == 1
                   and actual[:actual.index(marker)] == prefix + pending[pending.index(common):pending.index(marker)]
                   and actual[actual.index(marker):] == pending[pending.index(marker):]
                   and b"#[path" not in actual and b"../src/" not in actual
                   and b"use hwpx_package::native_form_value_output::*;\n" in actual
                   and b"use native_value::" not in actual,
                   "value_public_complete_case_lineage_invalid")
    return {"complete_predecessor_case_and_helper_body_byte_exact": True,
            "public_library_only_no_source_inclusion": True,
            "body_bytes": len(actual[actual.index(marker):])}


def authority(root=ROOT):
    capsule = q.shared.lifecycle.checked_json(root / history.CAPSULE, history.CAPSULE_SHA)
    for path, digest in capsule["source_sha256"].items(): public.checked(root / path, digest)
    project(public.checked(root / LIB, CURRENT_LIB), public.checked(root / ARCHIVE, history.OLD_LIB))
    public.checked(root / "crates/domain-ir/src/lib.rs", old.SHARED["crates/domain-ir/src/lib.rs"])
    lineage(public.bounded_bytes(root / TEST, 2*1024*1024), public.checked(root / old.RUST_TEST, capsule["source_sha256"][old.RUST_TEST]))
    # Guard the actual physical-view inputs without changing any predecessor checks.
    return {name:q.sha(raw) for name,raw in history.select(root).items()}


def protocol(stdout, expected, count, filtered=None):
    found = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$", stdout)
    summary = re.findall(r"(?m)^test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; (\d+) filtered out;.*$", stdout)
    oracle.require(len(found) == count and {n for n,_ in found} == expected
                   and all(s == "ok" for _,s in found) and len(summary) == 1
                   and int(summary[0][0]) == count
                   and (int(summary[0][1]) == 0 if filtered is None else int(summary[0][1]) == filtered),
                   "value_public_compiled_inventory_invalid")
    return {"passed":count,"failed":0,"ignored":0,"filtered_unrelated":int(summary[0][1]),
            "names":sorted(expected),"locked":True,"offline":True}


def run(command, root=ROOT, environment=None, timeout=180):
    process = subprocess.run(command, cwd=root, env=environment, capture_output=True, timeout=timeout,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    oracle.require(len(process.stdout) <= 256*1024 and len(process.stderr) <= 2*1024*1024,
                   "value_public_process_output_limit")
    return process.returncode, process.stdout.decode("utf-8", errors="strict"), process.stderr


def generate(directory, root=ROOT):
    authority(root)
    oracle.directory_guard(directory, root)
    oracle.require(not any(directory.iterdir()), "value_public_generation_nonempty")
    environment = dict(os.environ); environment[old.ENVIRONMENT] = str(directory)
    code, stdout, stderr = run(["cargo","test","--offline","--locked","-p","hwpx-package",
                                "--test","native_form_value_output_public","--","--show-output","--test-threads=1"], root, environment)
    oracle.require(code == 0, "value_public_execution_failed")
    tests = protocol(stdout, old.INTEGRATION_TESTS, 22)
    independent = oracle.inspect_bundle(directory, root)
    manifest = json.loads(oracle.checked_bytes(directory / "fixture-manifest.json",64*1024), object_pairs_hook=oracle.duplicate_guard)
    probes = re.findall(r"P09_40_COMPONENT_BUNDLE_PROBE=(\{[^\r\n]+\})", stdout)
    actual = re.findall(r"P09_40_ACTUAL_VALUE_PROBE=(\{[^\r\n]+\})", stdout)
    oracle.require(len(probes) == len(actual) == 1, "value_public_probe_inventory")
    probe = json.loads(probes[0], object_pairs_hook=oracle.duplicate_guard)
    oracle.require(probe == {"cases":5,"files":11,"manifest_sha256":independent["manifest_sha256"],
                            "artifact_bytes":independent["artifact_bytes"],"native_session_started":False}
                   and all(type(probe[k]) is int for k in ("cases","files","artifact_bytes"))
                   and probe["native_session_started"] is False
                   and json.loads(actual[0], object_pairs_hook=oracle.duplicate_guard) == manifest["cases"][0]["receipt"],
                   "value_public_probe_mismatch")
    previous = q.shared.lifecycle.checked_json(root / history.CAPSULE, history.CAPSULE_SHA)
    oracle.require(independent == previous["independent_oracle"] and manifest == previous["fixture_manifest"],
                   "value_public_whole_predecessor_output_parity_changed")
    return {"compiled_tests":tests,"independent_oracle":independent,"fixture_manifest":manifest,
            "zip_limit_drop_diagnostic_observed":b"ZipWriter::drop" in stderr}


def legacy(root=ROOT):
    # The unchanged original accessor checks predecessor source, not the new library.
    # All 35 actual current validator CLIs are then run unchanged, with no root alias.
    old1,_ = public.old4.old3.predecessors(root)
    paths = {**old1.REQUIRED_VALIDATORS, **{"tools/p09/"+p:d for p,d in input_public.LEGACY_P09.items()}}
    result = []
    for path,digest in paths.items():
        public.checked(root/path,digest)
        code,stdout,_ = run([sys.executable,"-B",path],root,timeout=60)
        value,banners = input_public.legacy_result(stdout)
        oracle.require(type(value) is dict and value.get("state") in ("pass","fail")
                       and code == (0 if value["state"] == "pass" else 1), "value_public_legacy_protocol")
        errors = value.get("errors",[])
        oracle.require(type(errors) is list and all(type(e) is str and re.fullmatch(r"[a-z0-9_:.\-/]+",e) for e in errors),
                       "value_public_legacy_errors")
        result.append({"path":path,"source_sha256":digest,"state":value["state"],"exit_code":code,
                       "errors":errors,"public_summary_banner_lines":banners,"actually_invoked":True,"source_locks_refreshed":False})
    oracle.require(len(result)==35,"value_public_legacy_inventory")
    for path,digest in paths.items(): public.checked(root/path,digest)
    return result


def qualify(root=ROOT):
    before = {p:q.sha(public.bounded_bytes(root/p,2*1024*1024)) for p in SOURCES}
    guard = authority(root)
    code,_,_ = run(["cargo","check","--offline","--locked","-p","hwpx-package","--lib"],root)
    oracle.require(code==0,"value_public_production_library_check_failed")
    bundles=[]
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="p09-40-component-", dir=root/"fixtures/target-build") as temporary:
            bundles.append(generate(Path(temporary),root))
        oracle.require(not Path(temporary).exists(),"value_public_scratch_not_cleaned")
    oracle.require(bundles[0]==bundles[1],"value_public_two_generations_differ")
    code,stdout,_ = run(["cargo","test","--offline","--locked","-p","hwpx-package","--lib","native_form_value_output::tests::"],root)
    oracle.require(code==0,"value_public_actual_library_units_failed")
    units = protocol(stdout,{n.replace("native_value::","native_form_value_output::",1) for n in old.PRIVATE_TESTS},3,32)
    code,stdout,_ = run(["cargo","test","--offline","--locked","-p","hwpx-package","--test","native_form_value_output_pending_export"],root)
    oracle.require(code==0,"value_public_unchanged_pending_parity_failed")
    pending = old.tests_protocol(stdout)
    try: old.authority(root)
    except ValueError as error:
        oracle.require(str(error)=="public_export_source_identity_changed","value_public_old_current_failure_changed")
        failure = {"state":"fail","error_code":str(error),"actually_invoked":True,"old_locks_unchanged":True}
    else: raise ValueError("value_public_old_current_failure_missing")
    validators = legacy(root)
    replay = history.reproduce(root)
    oracle.require(authority(root)==guard and before=={p:q.sha(public.bounded_bytes(root/p,2*1024*1024)) for p in SOURCES},
                   "value_public_sources_changed")
    return {"schema_version":"hwpx-agent.p09-41-native-form-value-public-export/v1",
            "state":"actual_public_value_api_and_complete_output_parity_qualified_non_green","source_sha256":before,
            "source_transition":{"current_raw_sha256":CURRENT_LIB,"archived_raw_sha256":history.OLD_LIB,
                                 "exact_single_namespace_export":True,"complete_inverse_byte_exact":True,"runtime_dependencies_added":False},
            "public_case_lineage":lineage(public.bounded_bytes(root/TEST,2*1024*1024),public.bounded_bytes(root/old.RUST_TEST,2*1024*1024)),
            "production_library_check":{"state":"pass","offline":True,"locked":True},
            **bundles[0],"actual_production_private_units":units,"unchanged_pending_suite":pending,
            "two_fresh_public_generations_byte_exact":True,"whole_component_output_parity_byte_exact":True,
            "actual_old_current_source_failure":failure,"actual_current_legacy_validators":validators,
            "physical_pre_export_original_reproduction":replay,
            "claims":{"public_value_api_connected":True,"product_routing":False,"native_execution":False,"native_protection":False,
                      "native_defaults":False,"native_date":False,"external_validation":False,"current_legacy_aggregate_pass":False,
                      "render":"not_run","product_differential":"not_run","green_rows":0,"p09_complete":False},
            "privacy":{"raw_document_values_present":False,"absolute_private_paths_present":False,"native_session_started":False,
                       "trust_or_registry_changed":False}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(); group.add_argument("--output",type=Path); group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        value=qualify(); raw=q.shared.lifecycle.canonical_bytes(value)
        for path in (args.output,args.verify):
            if path:
                q.shared.within(path.absolute().parent,ROOT/"implementation/p09/evidence")
                oracle.no_links(path.absolute().parent)
                oracle.require("private" not in path.absolute().relative_to(ROOT).parts and not path.is_symlink() and not path.is_junction(),"value_public_evidence_boundary")
        if args.output:
            with args.output.open("xb") as stream: stream.write(raw)
        if args.verify: oracle.require(public.bounded_bytes(args.verify,2*1024*1024)==raw,"value_public_capsule_reproduction_mismatch")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"value_public_qualification_failed"})); return 2
    print(json.dumps({"state":"pass","qualification_sha256":q.sha(raw),"public_cases":22,"production_private_units":3,
                      "independent_complete_output_pairs":5,"native_session_started":False,"green_rows":0})); return 0


if __name__=="__main__": raise SystemExit(main())
