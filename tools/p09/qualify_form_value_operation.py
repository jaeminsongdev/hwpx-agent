#!/usr/bin/env python3
"""Real product form inventory compilation, not enabled route/publication/native acceptance."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
if not __package__: sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import reproduce_form_preparation_pre_operation as history

ROOT=history.ROOT
old,oracle,public=history.old,history.oracle,history.public
CAPSULE="implementation/p09/evidence/p09-43-form-value-operation.current-2020.v1.json"
SOURCES=(old.LIB,history.ARCHIVE,"crates/product-cli/src/form_value_operation.rs",
         "crates/product-cli/tests/form_value_operation.rs",
         "tools/p09/reproduce_form_preparation_pre_operation.py",
         "tools/p09/qualify_form_value_operation.py",
         "tools/p09/tests/test_form_value_operation.py",
         "implementation/p09/P09-43_FORM_VALUE_OPERATION_POLICY.md")
TESTS={
    "actual_captured_control_compiles_real_form_selector_and_matches_whole_product_candidate",
    "all_five_kinds_required_radio_defaults_empty_and_clear_keep_complete_output_and_atomic_group",
    "every_inventory_node_and_compiled_target_carries_complete_original_or_target_control_state",
    "exact_retry_and_json_formatting_retain_same_semantic_compiler_plan_not_publication_idempotency",
    "provider_revision_plan_and_document_identities_are_not_interchangeable",
    "fresh_access_revocation_or_protection_digest_change_blocks_verification_and_route_first",
    "fresh_policy_map_and_source_drift_never_rebind_an_old_compiled_plan",
    "malformed_unknown_native_date_external_validator_and_partial_radio_never_compile",
    "finite_identity_limits_and_public_receipts_debug_errors_never_expose_values_or_paths",
}


def authority():
    copied,manifest,origins=history.select()
    return {"original_p42_capsule_sha256":history.CAPSULE_SHA,"original_13_sources_exact":True,
            "original_product_raw_archive_sha256":history.OLD_LIB,"new_product_complete_inverse_byte_exact":True,
            "authentic_original_view_files":len(manifest),"authentic_original_view_bytes":sum(map(len,copied.values())),
            "authentic_original_view_manifest_sha256":oracle.sha(old.prior.q.shared.lifecycle.canonical_bytes(manifest)),
            "only_logical_product_library_uses_declared_archive":all(actual==(history.ARCHIVE if name==old.LIB else name) for name,actual in origins.items())}


def qualify():
    before={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES}
    guard=authority()
    code,stdout,_=old.prior.run(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--test","form_value_operation"])
    oracle.require(code==0,"form_operation_actual_compiled_tests_failed")
    tests=old.prior.protocol(stdout,TESTS,9)
    try: old.authority()
    except ValueError as error:
        oracle.require(str(error)=="product_preparation_complete_inverse_invalid","form_operation_old_current_failure_changed")
        failure={"state":"fail","error_code":str(error),"actually_invoked":True,"old_locks_unchanged":True}
    else: raise ValueError("form_operation_old_current_failure_missing")
    legacy=old.prior.legacy()
    replay=history.reproduce()
    oracle.require(guard==authority() and before=={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES},"form_operation_sources_changed")
    return {"schema_version":"hwpx-agent.p09-43-product-form-value-operation/v1",
            "state":"actual_form_inventory_selectors_compiler_and_whole_output_qualified_non_green",
            "source_sha256":before,"source_preservation":guard,"actual_product_operation_tests":tests,
            "complete_original_product_preparation_reproduction":replay,
            "actual_old_current_source_failure":failure,"actual_current_legacy_validators":legacy,
            "claims":{"actual_form_inventory_compiler_connected":True,"dummy_paragraph_operations":False,
                      "entire_form_state_and_changed_target_states_preserved":True,"atomic_input_and_package_hashes_shared":True,
                      "whole_five_product_output_pairs_predecessor_byte_exact":True,
                      "form_route_publication_denied":True,"full_document_import":False,"native_structural_positions":False,
                      "execution_manifest_or_verified_form_route_created":False,"product_routing":False,
                      "publication_cas_idempotency":False,"cli_form_action_enabled":False,"native_execution":False,
                      "native_protection":False,"native_defaults":False,"native_date":False,"external_validation":False,
                      "current_legacy_aggregate_pass":False,"render":"not_run","product_differential":"not_run",
                      "green_rows":0,"p09_complete":False},
            "privacy":{"raw_document_values_present":False,"absolute_private_paths_present":False,
                       "native_session_started":False,"trust_or_registry_changed":False}}


def evidence_path(path):
    target=path.absolute()
    oracle.require(target==ROOT/CAPSULE and ".." not in path.parts,"form_operation_evidence_boundary")
    oracle.no_links(target.parent)
    if target.exists(): oracle.no_links(target)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        output=evidence_path(args.output) if args.output else None
        verify=evidence_path(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"form_operation_evidence_exists")
        value=qualify();raw=old.prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"form_operation_capsule_reproduction_mismatch")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"form_operation_qualification_failed"}));return 2
    print(json.dumps({"state":"pass","qualification_sha256":oracle.sha(raw),"capsule_bytes":len(raw),
                      "source_pins":len(SOURCES),"actual_product_operation_cases":9,"whole_output_pairs":5,
                      "complete_original_p42_capsule_reexecuted":True,"native_session_started":False,"green_rows":0}));return 0


if __name__=="__main__":raise SystemExit(main())
