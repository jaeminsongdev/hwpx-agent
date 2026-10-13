#!/usr/bin/env python3
"""Complete stored-provider source successor; not signed route/CAS/native/Gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import reproduce_product_request_pre_stored_provider as history

ROOT=history.ROOT
progress,old,oracle,public=history.progress,history.old,history.oracle,history.public
CAPSULE="implementation/p09/evidence/p09-45-stored-form-provider.source-qualified.v1.json"
PROGRESS_SHA="d6fdb75d8e6acc69e2dfc26fddd7d48116e4bb7878dfcc47553d06f5cf52e372"
SOURCES=(*progress.SOURCES,progress.RECEIPT,"tools/p09/reproduce_product_request_pre_stored_provider.py",
         "tools/p09/qualify_stored_form_provider.py","tools/p09/tests/test_stored_form_provider_qualification.py",
         "implementation/p09/P09-45_STORED_FORM_PROVIDER_QUALIFICATION_POLICY.md")
GUARDS={
    "test_four_complete_inverses_original_sources_and_current_failure_remain_exact",
    "test_full_original_view_is_authentic_bounded_and_only_four_origins_are_archived",
    "test_original_local_progress_raw_receipt_and_all_twelve_pins_are_preserved",
    "test_paths_accept_original_windows_evidence_but_reject_unsafe_alias_components",
    "test_original_cli_result_rejects_missing_extra_mismatched_coerced_or_failed_output",
    "test_all_real_product_and_guard_protocols_reject_missing_duplicate_skip_filter_extra",
    "test_full_evidence_boundary_excludes_original_progress_private_and_traversal",
    "test_current_sdk_cargo_lock_failure_and_seventeen_source_pins_are_explicit",
}


def source_pins():
    oracle.require(len(SOURCES)==len(set(SOURCES))==17,"stored_provider_qualification_source_inventory")
    return {name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES}


def evidence_path(path):
    target=path.absolute()
    oracle.require(target==ROOT/CAPSULE and ".." not in path.parts,"stored_provider_qualification_boundary")
    oracle.no_links(target.parent)
    if target.exists():oracle.no_links(target)
    return target


def current_sdk_failure():
    try:old.original.old.prior.authority()
    except ValueError as error:
        oracle.require(str(error)=="public_export_source_identity_changed","stored_provider_sdk_failure_changed")
        rejected=[];node=error.__traceback__
        while node:
            value=node.tb_frame.f_locals.get("path")
            if isinstance(value,Path):
                try:rejected.append(value.relative_to(ROOT).as_posix())
                except ValueError:pass
            node=node.tb_next
        oracle.require(rejected and rejected[-1]=="Cargo.lock","stored_provider_sdk_failure_origin")
    else:raise ValueError("stored_provider_sdk_current_failure_missing")
    return {"state":"fail","error_code":"public_export_source_identity_changed","rejected_repository_input":"Cargo.lock",
            "actually_invoked":True,"original_source_locks_unchanged":True,"blocked_class_bodies_not_counted_pass":True}


def guard_protocol(code,stdout,stderr):
    text=stderr.decode("utf-8",errors="strict");found=[]
    for line in text.splitlines():
        match=re.fullmatch(r"(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_stored_form_provider_qualification\.StoredFormProviderQualificationGuards\.([a-z0-9_]+)\) \.\.\. ok",line)
        if match:
            oracle.require(match.group(1)==match.group(2),"stored_provider_actual_guards_failed");found.append(match.group(1))
    oracle.require(code==0 and not stdout.strip() and len(found)==8 and set(found)==GUARDS and text.count(" ... ")==8
                   and len(re.findall(r"Ran 8 tests in [0-9.]+s",text))==1
                   and re.search(r"\nRan 8 tests in [0-9.]+s\s+OK\s*$",text) and "skipped" not in text,
                   "stored_provider_actual_guards_failed")
    return {"passed":8,"failed":0,"errors":0,"skipped":0,"names":sorted(GUARDS),"actually_invoked":True}


def guards():
    code,stdout,stderr=old.original.old.prior.run([sys.executable,"-B","-m","unittest","-v","tools.p09.tests.test_stored_form_provider_qualification"])
    return guard_protocol(code,stdout,stderr)


def qualify():
    before=source_pins();preserved=progress.preserve()
    local_raw=public.checked(ROOT/progress.RECEIPT,PROGRESS_SHA,2*1024*1024);local=progress.record()
    oracle.require(old.original.old.prior.q.shared.lifecycle.canonical_bytes(local)==local_raw,"stored_provider_original_local_progress_reproduction_changed")
    actual_guards=guards();sdk_failure=current_sdk_failure();legacy=old.original.old.prior.legacy();replay=history.reproduce()
    oracle.require(source_pins()==before and progress.preserve()==preserved and current_sdk_failure()==sdk_failure,"stored_provider_qualification_sources_changed")
    return {"schema_version":"hwpx-agent.p09-45-stored-form-provider-source-successor/v1",
            "state":"actual_service_source_and_full_source_successor_qualified_non_green","source_sha256":before,
            "original_local_progress_preservation_as_recorded":preserved,"original_local_progress_receipt_sha256":PROGRESS_SHA,
            "entire_local_progress_reexecuted_byte_exact":True,"actual_stored_provider_product_tests":local["actual_stored_provider_product_tests"],
            "actual_python_source_guards":actual_guards,"complete_original_product_request_reproduction":replay,
            "actual_original_current_source_failure":preserved["actual_original_current_source_failure"],
            "actual_current_sdk_source_failure":sdk_failure,"actual_current_legacy_validators":legacy,
            "claims":{"full_source_successor_qualified":True,"whole_original_p44_reexecuted":True,
                      "actual_revision_artifact_services_and_original_form_compiler_connected":True,"whole_five_output_pairs_predecessor_exact":True,
                      "normal_artifact_service_read_audit_emitted":True,"production_ingest_provision_claim_commit_or_publication":False,
                      "test_scanner_keys_sealed_metadata_are_real_scanner_issuer_native_or_signed_authority":False,
                      "postgres_durability":False,"full_document_import":False,"native_structural_positions":False,
                      "atomic_cas_execution_idempotency":False,"signed_form_authority_or_execution_manifest":False,
                      "cli_form_action_enabled":False,"native_execution_defaults_protection_date_external_validation":False,
                      "render":"not_run","product_differential":"not_run","current_legacy_aggregate_pass":False,"green_rows":0,"p09_complete":False},
            "privacy":{"raw_values_keys_subjects_artifact_ids_or_absolute_paths_present":False,
                       "native_session_started":False,"trust_or_registry_changed":False}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        output=evidence_path(args.output) if args.output else None;verify=evidence_path(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"stored_provider_qualification_exists")
        value=qualify();raw=old.original.old.prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"stored_provider_full_capsule_reproduction_mismatch")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"stored_provider_full_source_qualification_failed"}));return 2
    print(json.dumps({"state":"pass","qualification_sha256":oracle.sha(raw),"capsule_bytes":len(raw),"source_pins":len(SOURCES),
                      "actual_product_tests":8,"actual_python_source_guards":8,"whole_original_p44_reexecuted":True,
                      "native_session_started":False,"green_rows":0}));return 0


if __name__=="__main__":raise SystemExit(main())
