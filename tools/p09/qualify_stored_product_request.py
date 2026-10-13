#!/usr/bin/env python3
"""Full strict-request/stored source successor; no route/CAS/publication/native/Gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import reproduce_stored_provider_pre_product_request as history

ROOT=history.ROOT
progress,old,oracle,public=history.progress,history.old,history.oracle,history.public
prior=old.old.original.old.prior
CAPSULE="implementation/p09/evidence/p09-46-stored-product-request.source-qualified.v1.json"
PROGRESS_SHA="a721ec099d8cc092026e0ef75758dba265446909bae2e0d2d6ae7980ac8a4350"
SOURCES=(*progress.SOURCES,progress.RECEIPT,"tools/p09/reproduce_stored_provider_pre_product_request.py",
         "tools/p09/qualify_stored_product_request.py","tools/p09/tests/test_stored_product_request_qualification.py",
         "implementation/p09/P09-46_STORED_PRODUCT_REQUEST_QUALIFICATION_POLICY.md",*history.MIGRATIONS)
GUARDS={"test_frozen_local_receipt_and_all_nine_sources_remain_immutable",
        "test_complete_original_view_is_authentic_bounded_with_only_two_archive_origins",
        "test_post_provider_pins_override_pre_provider_root_cargo_lock_and_getters",
        "test_all_original_modules_pins_and_graph_origins_preserved_with_current_failure",
        "test_original_cli_result_rejects_missing_extra_coerced_duplicate_failed_or_large_output",
        "test_actual_product_and_python_protocols_reject_missing_extra_ignore_filter_skip",
        "test_full_evidence_and_windows_paths_reject_original_private_traversal_and_aliases",
        "test_current_old_and_sdk_failures_identify_distinct_changed_inputs_and_scope"}

def source_pins():
    oracle.require(len(SOURCES)==len(set(SOURCES))==31,"stored_request_qualification_source_inventory")
    return {name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES}

def evidence_path(path):
    target=path.absolute()
    oracle.require(target==ROOT/CAPSULE and ".." not in path.parts,"stored_request_qualification_boundary")
    oracle.no_links(target.parent)
    if target.exists():oracle.no_links(target)
    return target

def current_original_failure():
    try:old.qualify()
    except ValueError as error:
        oracle.require(str(error)=="public_export_source_identity_changed","stored_request_old_failure_changed")
        paths=[];node=error.__traceback__
        while node:
            value=node.tb_frame.f_locals.get("path")
            if isinstance(value,Path):
                try:paths.append(value.relative_to(ROOT).as_posix())
                except ValueError:pass
            node=node.tb_next
        oracle.require(paths and paths[-1]=="crates/product-cli/src/form_product_request.rs","stored_request_old_failure_origin")
    else:raise ValueError("stored_request_current_old_failure_missing")
    return {"state":"fail","error_code":"public_export_source_identity_changed",
            "rejected_repository_input":"crates/product-cli/src/form_product_request.rs","actually_invoked":True,
            "original_source_locks_unchanged":True,"archived_scope_is_not_current_old_pass":True}

def guard_protocol(code,output,errors):
    text=errors.decode("utf-8",errors="strict");found=[]
    for line in text.splitlines():
        match=re.fullmatch(r"(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_stored_product_request_qualification\.StoredProductRequestQualificationGuards\.([a-z0-9_]+)\) \.\.\. ok",line)
        if match:
            oracle.require(match.group(1)==match.group(2),"stored_request_qualification_guards_failed");found.append(match.group(1))
    oracle.require(code==0 and not output.strip() and len(found)==8 and set(found)==GUARDS and text.count(" ... ")==8
                   and len(re.findall(r"Ran 8 tests in [0-9.]+s",text))==1
                   and re.search(r"\nRan 8 tests in [0-9.]+s\s+OK\s*$",text) and "skipped" not in text,
                   "stored_request_qualification_guards_failed")
    return {"passed":8,"failed":0,"errors":0,"skipped":0,"names":sorted(GUARDS),"actually_invoked":True}

def guards():
    return guard_protocol(*prior.run([sys.executable,"-B","-m","unittest","-v","tools.p09.tests.test_stored_product_request_qualification"]))

def qualify():
    before=source_pins();preserved=progress.preserve()
    raw_local=public.checked(ROOT/progress.RECEIPT,PROGRESS_SHA,2*1024*1024);local=progress.record()
    oracle.require(prior.q.shared.lifecycle.canonical_bytes(local)==raw_local,"stored_request_original_local_progress_reproduction_changed")
    actual_guards=guards();failure=current_original_failure();sdk=old.current_sdk_failure();legacy=prior.legacy();replay=history.reproduce()
    oracle.require(source_pins()==before and progress.preserve()==preserved and current_original_failure()==failure
                   and old.current_sdk_failure()==sdk,"stored_request_qualification_sources_changed")
    return {"schema_version":"hwpx-agent.p09-46-stored-product-request-source-successor/v1",
            "state":"actual_strict_request_to_stored_source_and_full_source_successor_qualified_non_green","source_sha256":before,
            "original_local_progress_preservation_as_recorded":preserved,"original_local_progress_receipt_sha256":PROGRESS_SHA,
            "entire_local_progress_reexecuted_byte_exact":True,"actual_product_tests":local["actual_product_tests"],
            "actual_original_local_source_guards":local["actual_python_guards"],"actual_python_source_guards":actual_guards,
            "complete_original_stored_provider_reproduction":replay,"actual_current_original_source_failure":failure,
            "actual_current_sdk_source_failure":sdk,"actual_current_legacy_validators":legacy,
            "claims":{"full_source_successor_qualified":True,"whole_original_p45_reexecuted":True,
                      "original_strict_parser_and_actual_stored_source_connected":True,"five_whole_output_pairs_predecessor_exact":True,
                      "fresh_real_map_policy_access_head_acl_aead_checks":True,"normal_read_audit_emitted":True,
                      "original_request_digest_is_global_tenant_branch_execution_identity_or_claim":False,
                      "atomic_cas_execution_idempotency":False,"signed_form_authority_or_execution_manifest":False,
                      "production_provision_ingest_claim_commit_publication":False,"cli_form_action_enabled":False,
                      "test_fixtures_are_real_scanner_issuer_postgres_durability_or_native":False,
                      "full_document_import":False,"native_structural_positions":False,
                      "native_defaults_protection_date_validation":"not_run","render":"not_run","product_differential":"not_run",
                      "current_legacy_aggregate_pass":False,"green_rows":0,"p09_complete":False},
            "privacy":{"raw_private_values_keys_subjects_artifact_ids_or_absolute_paths_present":False,
                       "native_session_started":False,"trust_or_registry_changed":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        output=evidence_path(args.output) if args.output else None;verify=evidence_path(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"stored_request_qualification_exists")
        value=qualify();raw=prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"stored_request_full_capsule_reproduction_mismatch")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"stored_request_full_source_qualification_failed"}));return 2
    print(json.dumps({"state":"pass","qualification_sha256":oracle.sha(raw),"capsule_bytes":len(raw),"source_pins":len(SOURCES),
                      "actual_product_tests":8,"actual_python_source_guards":8,"whole_original_p45_reexecuted":True,
                      "native_session_started":False,"green_rows":0}));return 0

if __name__=="__main__":raise SystemExit(main())
