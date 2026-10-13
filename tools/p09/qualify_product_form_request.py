#!/usr/bin/env python3
"""Full request/head source successor, not signed route/CAS/native/Gate acceptance."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import reproduce_form_operation_pre_request as history

ROOT=history.ROOT
progress,original,oracle,public=history.progress,history.original,history.oracle,history.public
CAPSULE="implementation/p09/evidence/p09-44-product-form-request.source-qualified.v1.json"
PROGRESS_SHA="59233f445601780481f96b6e6e1cdd75c047eb08e9defded848bc326759b00d5"
SOURCES=(*progress.SOURCES,progress.RECEIPT,"tools/p09/reproduce_form_operation_pre_request.py",
         "tools/p09/qualify_product_form_request.py","tools/p09/tests/test_product_form_request_qualification.py",
         "implementation/p09/P09-44_PRODUCT_FORM_REQUEST_QUALIFICATION_POLICY.md")
GUARDS={
    "test_complete_predecessor_sources_and_current_failure_are_preserved",
    "test_authentic_whole_original_view_has_only_declared_product_archive",
    "test_original_local_progress_raw_receipt_and_six_pins_remain_exact",
    "test_relative_paths_accept_frozen_windows_names_without_traversal_ads_or_cache",
    "test_whole_original_cli_result_rejects_missing_extra_false_or_different_fields",
    "test_compiled_inventory_rejects_missing_duplicate_ignored_filtered_and_extra_cases",
    "test_full_evidence_boundary_rejects_original_private_progress_and_traversal",
    "test_source_inventory_requires_all_progress_sources_and_full_replay_tools",
}


def source_pins():
    oracle.require(len(SOURCES)==11 and len(set(SOURCES))==11,"product_request_qualification_source_inventory")
    return {name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES}


def evidence_path(path):
    target=path.absolute()
    oracle.require(target==ROOT/CAPSULE and ".." not in path.parts,"product_request_qualification_boundary")
    oracle.no_links(target.parent)
    if target.exists():oracle.no_links(target)
    return target


def guard_protocol(code,stdout,stderr):
    text=stderr.decode("utf-8",errors="strict")
    found=[]
    for line in text.splitlines():
        match=re.fullmatch(r"(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_product_form_request_qualification\.ProductFormRequestQualificationGuards\.([a-z0-9_]+)\) \.\.\. ok",line)
        if match:
            oracle.require(match.group(1)==match.group(2),"product_request_actual_guards_failed")
            found.append(match.group(1))
    oracle.require(code==0 and not stdout.strip() and len(found)==8 and set(found)==GUARDS
                   and len(re.findall(r"Ran 8 tests in [0-9.]+s",text))==1
                   and re.search(r"\nRan 8 tests in [0-9.]+s\s+OK\s*$",text)
                   and text.count(" ... ")==8 and "skipped" not in text,
                   "product_request_actual_guards_failed")
    return {"passed":8,"failed":0,"errors":0,"skipped":0,"names":sorted(GUARDS),"actually_invoked":True}


def guards():
    code,stdout,stderr=original.old.prior.run([sys.executable,"-B","-m","unittest","-v",
                                            "tools.p09.tests.test_product_form_request_qualification"])
    return guard_protocol(code,stdout,stderr)


def qualify():
    before=source_pins()
    preserved=progress.preserve()
    local_raw=public.checked(ROOT/progress.RECEIPT,PROGRESS_SHA,2*1024*1024)
    local=progress.record()
    oracle.require(original.old.prior.q.shared.lifecycle.canonical_bytes(local)==local_raw,
                   "product_request_original_local_progress_reproduction_changed")
    actual_guards=guards()
    legacy=original.old.prior.legacy()
    replay=history.reproduce()
    oracle.require(progress.preserve()==preserved and source_pins()==before,"product_request_qualification_sources_changed")
    return {"schema_version":"hwpx-agent.p09-44-product-form-request-source-successor/v1",
            "state":"actual_request_provider_readonly_head_and_full_source_successor_qualified_non_green",
            "source_sha256":before,"original_local_progress_preservation_as_recorded":preserved,
            "original_local_progress_receipt_sha256":PROGRESS_SHA,"entire_local_progress_reexecuted_byte_exact":True,
            "actual_public_product_tests":local["actual_public_product_tests"],
            "actual_production_private_tests":local["actual_production_private_tests"],"actual_python_source_guards":actual_guards,
            "complete_original_form_operation_reproduction":replay,
            "actual_original_current_source_failure":preserved["actual_original_current_guard"],
            "actual_current_legacy_validators":legacy,
            "claims":{"full_source_successor_qualified":True,"whole_original_p43_reexecuted":True,
                      "strict_request_provider_actual_readonly_head_preflight_connected":True,
                      "whole_five_output_pairs_predecessor_exact":True,"preflight_initializes_claims_commits":False,
                      "read_only_head_is_atomic_cas":False,"scoped_digest_is_execution_idempotency":False,
                      "in_memory_head_advance_fixture_is_form_manifest_or_publication":False,
                      "signed_form_authority_or_execution_manifest":False,"durable_publication_cas_idempotency":False,
                      "cli_form_action_enabled":False,"full_document_import":False,"native_structural_positions":False,
                      "native_execution":False,"native_defaults_protection_date_external_validation":False,
                      "render":"not_run","product_differential":"not_run","current_legacy_aggregate_pass":False,
                      "green_rows":0,"p09_complete":False},
            "privacy":{"raw_values_keys_or_absolute_paths_present":False,"native_session_started":False,
                       "trust_or_registry_changed":False}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        output=evidence_path(args.output) if args.output else None
        verify=evidence_path(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"product_request_qualification_exists")
        value=qualify();raw=original.old.prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"product_request_full_capsule_reproduction_mismatch")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"product_request_full_source_qualification_failed"}));return 2
    print(json.dumps({"state":"pass","qualification_sha256":oracle.sha(raw),"capsule_bytes":len(raw),
                      "source_pins":len(SOURCES),"actual_public_product_tests":10,"actual_private_tests":2,
                      "actual_python_source_guards":8,"whole_original_p43_reexecuted":True,
                      "native_session_started":False,"green_rows":0}));return 0


if __name__=="__main__":raise SystemExit(main())
