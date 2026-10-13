#!/usr/bin/env python3
"""Exact public package export/source successor; not a new native or product Gate."""
from __future__ import annotations
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import verify_p08_additive_export_source_bridge_v3 as old3
from tools.p09 import qualify_native_form_package_binding as binding
from tools.p09 import qualify_native_form_package_output as output

ROOT = old3.ROOT
LIB = old3.LIB
sha256 = old3.sha256
bounded_bytes = old3.bounded_bytes
checked = old3.checked
CURRENT_LIB = "b625b6fb85d9312a3c8a2582e4eff7e0196fac11c059f0b4be4936ce78db8e3b"
ARCHIVE = "implementation/p09/source-archive/p09-31-pre-package-export/"
ARCHIVES = {
    LIB: (ARCHIVE+"lib.rs", old3.CURRENT_LIB),
    "tools/p09/tests/test_native_form_public_export.py": (ARCHIVE+"test_native_form_public_export.py", "39cd10c35e9df9d0e84854dca9db910a829b2fb258cc9fdeeab5f020f9b2dba8"),
    "tools/p09/tests/test_p08_additive_export_source_bridge.py": (ARCHIVE+"test_p08_additive_export_source_bridge.py", "e4f6fd8c83cd7c603dbaa23a2069f381f415a6c01773a6c701d4937c2a4f9cb6"),
    "tools/p09/tests/test_native_form_package_binding.py": (ARCHIVE+"test_native_form_package_binding.py", "f51ec514322ded4c952d3964eb85bdc0f10f12a20b3ee7d01bca46bcdcae2b9f"),
    "tools/p09/tests/test_native_form_package_output.py": (ARCHIVE+"test_native_form_package_output.py", "029cd43dfb0056d61b3313f736e33571f0d099356d9b933f9e17c34688abf147"),
    "crates/hwpx-package/tests/native_form_package_pending_export.rs": (ARCHIVE+"native_form_package_pending_export.rs", "74b8840255ff610bb7b49c3a8c2ff37f7d0b20d9521d85eebe07f70c3d1b5df0"),
    "crates/hwpx-package/tests/native_form_package_output_pending_export.rs": (ARCHIVE+"native_form_package_output_pending_export.rs", "ae489c4ce86807852df4f9b8191c7c94ee396853ed784b2cdb097d998a0ce504"),
}
RECEIPTS = {
    "P09-28-r02": ("implementation/p09/evidence/p09-28-native-form-public-export-source.current-2020.r02.v3.json", "cc9318ba2f75d16dad15f59ee5a6d704fcca14e6e772b4740d5b6d94a14026bc"),
    "P09-29": ("implementation/p09/evidence/p09-29-native-form-package-binding.current-2020.v1.json", output.RECEIPT_SHA),
    "P09-30": ("implementation/p09/evidence/p09-30-native-form-package-output.current-2020.v1.json", "ff7aeade25379f5b53f8f4e76da2fc08c902d4002897f6f11077572cf94bb099"),
}
DELTAS = (b"mod native_form_package;\n", b"mod native_form_package_lowering;\n", b"""pub use native_form_package::{
    NATIVE_FORM_PACKAGE_BINDING_PROFILE_ID, NativeFormPackageBindings, NativeFormPackageError,
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePlan, NativeFormPackagePolicy,
    NativeFormPackageReadback, NativeFormPackageReader, NativeFormPackageSectionMap,
};
""", b"""pub use native_form_package_lowering::{
    NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID, NativeFormPackageLowerer, NativeFormPackageOutput,
    NativeFormPackageOutputError, NativeFormPackageOutputLimits, NativeFormPackageOutputPlan,
    NativeFormPackageOutputReceipt,
};
""")
PUBLIC_BINDING = "crates/hwpx-package/tests/native_form_package_public.rs"
PUBLIC_OUTPUT = "crates/hwpx-package/tests/native_form_package_output_public.rs"
SOURCES = ("tools/p09/verify_p08_additive_export_source_bridge_v4.py",
           "tools/p09/tests/test_native_form_package_public_export.py",
           "implementation/p09/P09-31_NATIVE_FORM_PACKAGE_PUBLIC_EXPORT_POLICY.md",
           "protocol/migrations/p09-p08-additive-export-source-bridge-v3-to-v4.md",
           LIB, PUBLIC_BINDING, PUBLIC_OUTPUT, *tuple(p for p in ARCHIVES if p != LIB),
           "crates/hwpx-package/src/native_form_package.rs", "crates/hwpx-package/src/native_form_package_lowering.rs",
           "Cargo.toml", "Cargo.lock", "crates/hwpx-package/Cargo.toml", "crates/domain-ir/Cargo.toml")


def record(name, root=ROOT):
    if name not in RECEIPTS:
        return old3.record(name, root)
    path, digest = RECEIPTS[name]
    return json.loads(checked(root/path, digest, 512*1024))


def historical_sources(name, root=ROOT):
    if name not in RECEIPTS:
        return old3.historical_sources(name, root)
    result = {}
    for path, digest in record(name, root)["source_sha256"].items():
        actual = path
        if path in ARCHIVES:
            actual, expected = ARCHIVES[path]
            if expected != digest:
                raise ValueError("package_public_export_archive_pin_not_exact")
        checked(root/actual, digest)
        result[path] = {"sha256":digest,"checked_path":actual,"archived_predecessor_source":actual != path}
    return result


def project(raw, root=ROOT, *, require_current=True):
    if require_current and sha256(raw) != CURRENT_LIB:
        raise ValueError("current_package_public_export_lib_identity_changed")
    value = raw
    for delta in DELTAS:
        if value.count(delta) != 1:
            raise ValueError("package_public_export_delta_not_unique")
        value = value.replace(delta,b"",1)
    if value != checked(root/ARCHIVES[LIB][0],ARCHIVES[LIB][1]):
        raise ValueError("package_public_export_projection_changed")
    return value


def public_lineage(public_path, pending_path, root=ROOT):
    archive, digest = ARCHIVES[pending_path]
    old = checked(root/archive,digest)
    current_pending = bounded_bytes(root/pending_path,2*1024*1024)
    public = bounded_bytes(root/public_path,2*1024*1024)
    marker = b"use sha2::{Digest as _, Sha256};"
    if any(raw.count(marker) != 1 for raw in (old,current_pending,public)):
        raise ValueError("package_public_export_case_lineage_changed")
    if any(raw[raw.index(marker):] != old[old.index(marker):] for raw in (current_pending,public)):
        raise ValueError("package_public_export_case_lineage_changed")
    expected_header = b'//! Complete predecessor cases through the real public `hwpx_package` API only.\nuse domain_ir::*;\nuse hwpx_package::*;\n'
    if public[:public.index(marker)] != expected_header or b"#[path" in public or b"../src/" in public:
        raise ValueError("package_public_export_case_lineage_changed")
    expected_pending = old[:old.index(marker)].replace(b"use native_form_package::*;\n", DELTAS[2])
    if pending_path.endswith("output_pending_export.rs"):
        expected_pending = expected_pending.replace(b"use native_form_package_lowering::*;\n", DELTAS[3])
    if current_pending[:current_pending.index(marker)] != expected_pending:
        raise ValueError("package_public_export_pending_import_delta_changed")
    return {"public_test":public_path,"original_test_body_byte_exact":True,"pending_test_body_byte_exact":True,
            "public_library_only":True,"public_raw_sha256":sha256(public)}


def test_inventory(stdout, expected, count):
    matches = re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\s*$",stdout)
    if len(matches) != count or {n for n,_ in matches} != expected or any(s != "ok" for _,s in matches) or len(re.findall(
        rf"(?m)^test result: ok\. {count} passed; 0 failed; 0 ignored; 0 measured; \d+ filtered out;.*$",stdout)) != 1:
        raise ValueError("package_public_export_test_inventory_invalid")
    return {"passed":count,"failed":0,"ignored":0,"names":sorted(expected),"locked":True,"offline":True}


def cargo(target, extra=(), directory=None, root=ROOT, *, library=False):
    env = dict(os.environ); env.pop(output.ORACLE_ENV,None)
    if directory is not None: env[output.ORACLE_ENV] = str(directory)
    command = ["cargo","test","-p","hwpx-package",*( ["--lib",target] if library else ["--test",target]),"--locked","--offline",*extra]
    process = subprocess.run(command,cwd=root,capture_output=True,timeout=60,env=env,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode or not 0 < len(process.stdout) <= 256*1024 or len(process.stderr)>1024*1024:
        raise ValueError("package_public_export_actual_tests_failed")
    return process.stdout.decode("utf-8",errors="strict")


def public_binding(root=ROOT):
    lineage = public_lineage(PUBLIC_BINDING,"crates/hwpx-package/tests/native_form_package_pending_export.rs",root)
    result = test_inventory(cargo("native_form_package_public",root=root),binding.EXPECTED_TESTS,17)
    raw = cargo("native_form_package_public",(binding.ACTUAL_TEST,"--","--exact","--nocapture"),root=root)
    probes = re.findall(r"p09_29_probe_json=(\{[^\n]*\})",raw)
    if len(probes) != 1: raise ValueError("package_public_export_binding_probe_missing")
    independent = binding.independent_actual(root)
    binding.verify_probe(json.loads(probes[0],object_pairs_hook=output.SHARED.lifecycle.duplicate_guard),independent)
    return {**result,**lineage,"independent_actual_original_bindings":independent}


def public_output(root=ROOT):
    lineage = public_lineage(PUBLIC_OUTPUT,"crates/hwpx-package/tests/native_form_package_output_pending_export.rs",root)
    expected = {n for n in output.EXPECTED_TESTS if not n.startswith("native_form_package_lowering::tests::")}
    with tempfile.TemporaryDirectory(prefix="hwpx-p09-31-public-output-") as temporary:
        directory = Path(temporary).resolve()
        result = test_inventory(cargo("native_form_package_output_public",directory=directory,root=root),expected,19)
        proofs = output.artifacts(directory,root)
        raw = cargo("native_form_package_output_public",(output.ACTUAL_TEST,"--","--exact","--nocapture"),root=root)
        probes = re.findall(r"p09_30_probe_json=(\{[^\n]*\})",raw)
        if len(probes) != 1: raise ValueError("package_public_export_output_probe_missing")
        output.verify_probe(json.loads(probes[0],object_pairs_hook=output.SHARED.lifecycle.duplicate_guard),proofs["actual-property"],binding.independent_actual(root))
    units = {n for n in output.EXPECTED_TESTS if n.startswith("native_form_package_lowering::tests::")}
    low_level = test_inventory(cargo("native_form_package_lowering::tests::",root=root,library=True),units,2)
    return {**result,**lineage,"actual_library_unit_tests":low_level,"independent_generated_package_checks":proofs}


def verify(root=ROOT):
    sys.path.insert(0,str(root)); sys.path.insert(0,str(root/"tools/p08"))
    historical = {name:historical_sources(name,root) for name in (*old3.RECEIPTS,*RECEIPTS)}
    old1,old2 = old3.predecessors(root)
    raw = checked(root/LIB,CURRENT_LIB)
    v3 = project(raw,root); v2 = old3.project(v3,root); v1 = old2.project(v2,root); p08 = old1.project(v1)
    for mapping in (old1.PREDECESSORS,old1.ADDITIONS,old1.REQUIRED_VALIDATORS,old2.ADDITIONS):
        old1.check_locked(root,mapping)
    observation = importlib.import_module("tools.p09.qualify_native_form_observation_component")
    failures = {
        "P09-21":old3.expected_failure(lambda:old1.verify(root),"current_shared_lib_identity_changed"),
        "P09-23":old3.expected_failure(lambda:old2.verify(root),"current_successor_lib_identity_changed"),
        "P09-27":old3.expected_failure(lambda:observation.qualify(root),"native_form_observation_pending_export_boundary_changed"),
        "P09-28":old3.expected_failure(lambda:old3.verify(root),"public_export_source_identity_changed"),
        "P09-29":old3.expected_failure(lambda:binding.qualify(root),"public_export_source_identity_changed"),
        "P09-30":old3.expected_failure(lambda:output.qualify(root),"public_export_source_identity_changed"),
    }
    before = {p:sha256(bounded_bytes(root/p,2*1024*1024)) for p in SOURCES}
    tests = {"binding":public_binding(root),"output":public_output(root)}
    aggregate = importlib.import_module("validate_object_conformance_contract")
    if list(aggregate.EXPECTED_UPSTREAM) != list(old1.REQUIRED_VALIDATORS)[:23]:
        raise ValueError("package_public_export_upstream_inventory_changed")
    checks = [old1.run_json_validator(root,p) for p in old1.REQUIRED_VALIDATORS]
    if before != {p:sha256(bounded_bytes(root/p,2*1024*1024)) for p in SOURCES} or historical != {n:historical_sources(n,root) for n in (*old3.RECEIPTS,*RECEIPTS)}:
        raise ValueError("package_public_export_source_or_authority_changed_during_test")
    return {"schema_version":"hwpx-agent.p09-p08-additive-export-source-bridge/v4","task":"P09-31",
            "state":"package_public_export_source_qualified_non_gate","source_sha256":before,
            "predecessor_current_verifier_state":"fail","actual_predecessor_current_failures":failures,
            "historical_source_checks":historical,"preserved_receipt_sha256":{n:p for n,(_,p) in {**old3.RECEIPTS,**RECEIPTS}.items()},
            "shared_lib":{"current_raw_sha256":sha256(raw),"v3_raw_sha256":sha256(v3),"v2_raw_sha256":sha256(v2),
                          "v1_raw_sha256":sha256(v1),"p08_predecessor_raw_sha256":sha256(p08),"new_exact_deltas_sha256":[sha256(d) for d in DELTAS]},
            "actual_public_rust_tests":tests,"required_current_validators":checks,
            "historical_p08_authority":aggregate.validate(run_upstream=False),
            "claims":{"shared_library_export_connected":True,"exact_additive_export_chain":True,"dependency_source_qualification":True,
                      "public_package_reader_and_lowerer_tests_executed":True,"package_part_bindings_independently_read":True,
                      "complete_generated_output_packages_independently_verified":True,
                      "archived_sources_are_current_full_verifier_pass":False,"predecessor_receipts_rewritten":False,
                      "legacy_live_aggregate_now_pass":False,"new_adapter_target_execution":False,"current_target_promotion":False,
                      "production_routing_qualified":False,"render":"not_run","product_differential":"not_run",
                      "green_rows":0,"p09_complete":False,"product_complete":False},
            "privacy":{"absolute_private_paths":False,"raw_document_text_present":False,"native_session_started":False,
                       "registry_or_trust_setting_changed":False,"external_network_invoked":False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group()
    group.add_argument("--output",type=Path); group.add_argument("--verify",type=Path); args = parser.parse_args()
    try:
        value = verify(); raw = output.SHARED.lifecycle.canonical_bytes(value)
        if args.output:
            path = args.output.absolute(); output.SHARED.within(path.parent,ROOT/"implementation/p09/evidence")
            if "private" in path.relative_to(ROOT).parts or path.is_symlink() or path.is_junction():
                raise ValueError("package_public_export_evidence_boundary")
            with path.open("xb") as handle: handle.write(raw)
        if args.verify and bounded_bytes(args.verify,512*1024) != raw:
            raise ValueError("package_public_export_receipt_reproduction_mismatch")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+",str(error)) else "package_public_export_qualification_failed"
        print(json.dumps({"state":"fail","error_code":code})); return 2
    print(json.dumps({"state":"pass","qualification_state":value["state"],"qualification_sha256":sha256(raw),
                      "public_integration_passed":36,"library_unit_passed":2,"validator_count":25,"p09_complete":False})); return 0


if __name__ == "__main__": raise SystemExit(main())
