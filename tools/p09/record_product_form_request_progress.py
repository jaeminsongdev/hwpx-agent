#!/usr/bin/env python3
"""Actual local request/head tests and raw preservation; NOT full source qualification."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_form_value_operation as original

ROOT=original.ROOT
oracle,public=original.oracle,original.public
LIB="crates/product-cli/src/lib.rs"
ARCHIVE="implementation/p09/source-archive/p09-44-pre-product-form-request/lib.rs"
ORIGINAL_LIB="45b5d46ef25bcfc47f50c0c6c10daeb994df07e8e0751acef1358ffe984f53c9"
PREDECESSOR_SHA="bf9ef7121f9b6cf06b3dcb2bff61d4f3e9d2c4eb57c88cd3710e6e1d3a036a1e"
RECEIPT="implementation/p09/evidence/p09-44-product-form-request.progress.v1.json"
SOURCES=(LIB,ARCHIVE,"crates/product-cli/src/form_product_request.rs","crates/product-cli/tests/form_product_request.rs",
         "tools/p09/record_product_form_request_progress.py","implementation/p09/P09-44_PRODUCT_FORM_REQUEST_POLICY.md")
TESTS={
    "actual_product_envelope_uses_real_head_and_compiler_without_claim_commit_or_publish",
    "five_kinds_required_radio_defaults_empty_clear_and_complete_bytes_match_predecessor",
    "duplicate_escaped_nested_unknown_coerced_and_trailing_json_never_prepares",
    "wrong_provider_project_document_or_full_raw_source_is_rejected_before_compilation",
    "missing_stream_wrong_revision_zero_or_wrong_generation_never_initializes_or_claims",
    "actual_revision_service_cas_advancement_invalidates_prepared_old_head_even_with_same_source",
    "same_source_in_other_provider_scope_cannot_verify_or_authorize_old_preparation",
    "fresh_access_and_policy_revocation_propagate_before_route_and_do_not_reserve_key",
    "exact_retry_semantic_formatting_and_key_binding_are_not_execution_idempotency",
    "bounded_request_provider_ids_and_redacted_output_do_not_leak_private_values_or_keys",
}
PRIVATE={"form_product_request::tests::finite_json_writer_rejects_overrun_before_any_partial_append",
         "form_product_request::tests::finite_json_writer_rejects_first_oversize_without_append"}


def preserve():
    raw=public.checked(ROOT/original.CAPSULE,PREDECESSOR_SHA,2*1024*1024)
    capsule=json.loads(raw,object_pairs_hook=oracle.duplicate_guard)
    oracle.require(set(capsule["source_sha256"])==set(original.SOURCES),"product_request_original_sources")
    for name,digest in capsule["source_sha256"].items():public.checked(ROOT/(ARCHIVE if name==LIB else name),digest,2*1024*1024)
    archived=public.checked(ROOT/ARCHIVE,ORIGINAL_LIB)
    current=public.bounded_bytes(ROOT/LIB,2*1024*1024)
    delta=b"pub mod form_product_request;\n"
    oracle.require(current.count(delta)==1 and current.replace(delta,b"",1)==archived,"product_request_original_complete_inverse")
    try:original.authority()
    except ValueError as error:
        oracle.require(str(error)=="form_operation_product_inverse_invalid","product_request_original_failure_changed")
    else:raise ValueError("product_request_original_current_failure_missing")
    return {"original_capsule_sha256":PREDECESSOR_SHA,"original_eight_raw_sources_preserved":True,
            "original_product_library_sha256":ORIGINAL_LIB,"new_namespace_complete_inverse_exact":True,
            "actual_original_current_guard":{"state":"fail","error_code":"form_operation_product_inverse_invalid","actually_invoked":True},
            "complete_original_capsule_physical_reexecution_this_successor":False,
            "full_source_successor_qualification":"not_run_pending"}


def record():
    before={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES}
    guard=preserve()
    code,stdout,_=original.old.prior.run(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--test","form_product_request"])
    oracle.require(code==0,"product_request_actual_tests_failed")
    public_tests=original.old.prior.protocol(stdout,TESTS,10)
    code,stdout,_=original.old.prior.run(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--lib","form_product_request::tests::"])
    oracle.require(code==0,"product_request_actual_private_tests_failed")
    units=original.old.prior.protocol(stdout,PRIVATE,2,3)
    oracle.require(preserve()==guard and before=={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES},"product_request_sources_changed")
    return {"schema_version":"hwpx-agent.p09-44-product-form-request-progress/v1",
            "state":"implemented_local_tests_pass_full_source_successor_qualification_pending",
            "source_sha256":before,"preservation":guard,"actual_public_product_tests":public_tests,"actual_production_private_tests":units,
            "claims":{"strict_product_request_and_actual_head_preflight_connected":True,"whole_five_output_pairs_predecessor_exact":True,
                      "actual_head_advance_fixture_is_service_metadata_only":True,"preflight_claims_or_initializes_or_commits":False,
                      "execution_idempotency_or_atomic_cas":False,"signed_form_route_or_execution_manifest":False,
                      "publication":False,"cli_form_action_enabled":False,"native_execution":False,"full_source_successor_qualified":False,
                      "whole_original_p43_reexecuted":False,"current_legacy_aggregate_pass":False,"green_rows":0,"p09_complete":False},
            "privacy":{"raw_values_keys_or_absolute_paths_present":False,"native_session_started":False,"trust_or_registry_changed":False}}


def path_guard(path):
    target=path.absolute()
    oracle.require(target==ROOT/RECEIPT and ".." not in path.parts,"product_request_progress_boundary")
    oracle.no_links(target.parent)
    if target.exists():oracle.no_links(target)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        output=path_guard(args.output) if args.output else None
        verify=path_guard(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"product_request_progress_exists")
        value=record();raw=original.old.prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"product_request_progress_reproduction_mismatch")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,original.history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"product_request_progress_failed"}));return 2
    print(json.dumps({"state":"pass","scope":"local_progress_not_full_source_qualification","receipt_sha256":oracle.sha(raw),"receipt_bytes":len(raw),
                      "actual_public_tests":10,"actual_private_tests":2,"full_source_qualification":"not_run_pending","native_session_started":False}));return 0


if __name__=="__main__":raise SystemExit(main())
