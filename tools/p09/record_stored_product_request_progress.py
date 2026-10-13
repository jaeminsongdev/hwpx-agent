#!/usr/bin/env python3
"""Actual envelope/stored integration and raw preservation, NOT full source proof."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_stored_form_provider as old

ROOT=old.ROOT
oracle,public=old.oracle,old.public
ARCHIVE="implementation/p09/source-archive/p09-46-pre-stored-product-request/"
CHANGED={
    "crates/product-cli/src/form_product_request.rs":("form_product_request.rs","7a58fd84c5e0005fabb650e0fea03dc21158d0c75291f106402a5a55fe3f624d"),
    "crates/product-cli/src/form_stored_provider.rs":("form_stored_provider.rs","e1c2d27a4f2ee239575ab7d55a0f345fda97fb9fdf1ea32d1fc6d5e3db4fa89c"),
}
RECEIPT="implementation/p09/evidence/p09-46-stored-product-request.progress.v1.json"
SOURCES=(*CHANGED,*(ARCHIVE+name for name,_ in CHANGED.values()),
         "crates/product-cli/src/form_product_request/stored.rs","crates/product-cli/tests/form_stored_product_request.rs",
         "tools/p09/record_stored_product_request_progress.py","tools/p09/tests/test_stored_product_request_progress.py",
         "implementation/p09/P09-46_STORED_PRODUCT_REQUEST_POLICY.md")
CAPSULE_SHA="c41c9d37ccba953d2abe380409cfd591efe635514210383098d67a6108930724"
BINDING_DELTA=b'''    /// Internal strict product-envelope binding. Uses the real source before compiling input.
    pub(crate) fn check_product_binding(
        &self,
        project: &domain_ir::ProjectId,
        document: &DocumentId,
        head: RevisionHead,
        source_sha256: &str,
        now: u64,
    ) -> Result<(), StoredFormError> {
        if project.as_str() != self.scope.project.public_id() || document != &self.scope.document {
            return Err(StoredFormError::Scope);
        }
        if self.source(head, now)?.digest.hex() != source_sha256 {
            return Err(StoredFormError::Drift);
        }
        Ok(())
    }

'''
TESTS={
    "stored_request_actual_envelope_and_services_produce_exact_whole_candidate_but_deny_route",
    "stored_request_reuses_original_strict_recursive_parser_before_any_service_read",
    "stored_request_project_document_full_source_revision_generation_cannot_be_substituted",
    "stored_request_all_five_kinds_required_radio_defaults_empty_clear_preserve_whole_oracles",
    "stored_request_fresh_actual_acl_aead_quarantine_fail_before_route_or_publication",
    "stored_request_real_head_advance_rejects_old_request_and_accepts_fresh_same_artifact",
    "stored_request_fresh_actual_map_policy_access_and_provider_scope_drift_rejected",
    "stored_request_canonical_retry_scoped_key_and_public_receipts_are_private_not_idempotency",
}
GUARDS={"test_original_whole_modules_seventeen_pins_and_1490_raw_origins_preserved",
        "test_unique_complete_inverses_reject_missing_duplicate_or_other_body_changes",
        "test_evidence_boundary_rejects_original_full_local_private_and_traversal",
        "test_all_eight_actual_product_case_protocol_and_source_inventory_are_exact"}

def guard_protocol(code,output,errors):
    text=errors.decode("utf-8",errors="strict");found=[]
    for line in text.splitlines():
        match=re.fullmatch(r"(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_stored_product_request_progress\.StoredProductRequestProgressGuards\.([a-z0-9_]+)\) \.\.\. ok",line)
        if match:
            oracle.require(match.group(1)==match.group(2),"stored_request_actual_source_guards_failed");found.append(match.group(1))
    oracle.require(code==0 and not output.strip() and len(found)==4 and set(found)==GUARDS and text.count(" ... ")==4
                   and len(re.findall(r"Ran 4 tests in [0-9.]+s",text))==1
                   and re.search(r"\nRan 4 tests in [0-9.]+s\s+OK\s*$",text) and "skip" not in text,
                   "stored_request_actual_source_guards_failed")
    return {"passed":4,"failed":0,"errors":0,"skipped":0,"names":sorted(GUARDS),"actually_invoked":True}

def inverse(name,current,original):
    delta=b"pub mod stored;\n\n" if name.endswith("form_product_request.rs") else BINDING_DELTA
    oracle.require(current.count(delta)==1 and current.replace(delta,b"",1)==original,"stored_request_complete_original_inverse")

def origin(name,declared):
    old.history.relative(name)
    path=ARCHIVE+CHANGED[name][0] if name in CHANGED else declared[name]["archive"] if name in declared else name
    old.history.relative(path)
    return path

def preserve():
    for name,(file,digest) in CHANGED.items():
        original=public.checked(ROOT/(ARCHIVE+file),digest,2*1024*1024)
        inverse(name,public.bounded_bytes(ROOT/name,2*1024*1024),original)
    raw=public.checked(ROOT/old.CAPSULE,CAPSULE_SHA,2*1024*1024)
    capsule=json.loads(raw,object_pairs_hook=oracle.duplicate_guard)
    oracle.require(len(raw)==223976 and set(capsule["source_sha256"])==set(old.SOURCES),"stored_request_original_capsule_inventory")
    for name,digest in capsule["source_sha256"].items():public.checked(ROOT/origin(name,{}),digest,2*1024*1024)
    replay=capsule["complete_original_product_request_reproduction"]
    graph=replay["source_sha256"];declared=replay["declared_original_changed_sources"]
    oracle.require(len(graph)==1490 and set(declared)==set(old.progress.CHANGED),"stored_request_original_graph_inventory")
    total=sum(len(public.checked(ROOT/origin(name,declared),digest,old.history.SOURCE_BYTES)) for name,digest in graph.items())
    oracle.require(total==49503833,"stored_request_original_graph_bytes")
    try:old.qualify()
    except ValueError as error:
        oracle.require(str(error)=="public_export_source_identity_changed","stored_request_current_failure_changed")
    else:raise ValueError("stored_request_current_old_failure_missing")
    sdk=old.current_sdk_failure()
    return {"original_p45_full_capsule_sha256":CAPSULE_SHA,"original_seventeen_raw_pins_preserved":True,
            "original_graph_files":len(graph),"original_graph_bytes":total,"complete_raw_origin_inventory_preserved":True,
            "two_unique_complete_original_module_inverses_exact":True,
            "actual_current_p45_failure":{"state":"fail","error_code":"public_export_source_identity_changed","actually_invoked":True},
            "actual_current_sdk_failure":sdk,"whole_original_p45_reexecuted":False,"full_source_successor":"not_run_pending"}

def path_guard(path):
    target=path.absolute()
    oracle.require(target==ROOT/RECEIPT and ".." not in path.parts,"stored_request_progress_boundary")
    oracle.no_links(target.parent)
    if target.exists():oracle.no_links(target)
    return target

def record():
    before={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES};guard=preserve()
    code,stdout,_=old.old.original.old.prior.run(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--test","form_stored_product_request"])
    oracle.require(code==0,"stored_request_actual_product_tests_failed")
    tests=old.old.original.old.prior.protocol(stdout,TESTS,8)
    code,output,errors=old.old.original.old.prior.run([sys.executable,"-B","-m","unittest","-v","tools.p09.tests.test_stored_product_request_progress"])
    guards=guard_protocol(code,output,errors)
    oracle.require(guard==preserve() and before=={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES},"stored_request_sources_changed")
    return {"schema_version":"hwpx-agent.p09-46-stored-product-request-progress/v1",
            "state":"actual_strict_request_to_stored_source_and_local_tests_pass_full_source_pending",
            "source_sha256":before,"preservation":guard,"actual_product_tests":tests,
            "actual_python_guards":guards,
            "claims":{"original_strict_parser_and_actual_stored_source_connected":True,"five_whole_output_pairs_exact":True,
                      "fresh_real_map_policy_access_head_acl_aead_checks":True,"normal_read_audit_emitted":True,
                      "full_source_qualified":False,"whole_original_p45_reexecuted":False,"signed_form_authority_or_manifest":False,
                      "atomic_cas_or_execution_idempotency":False,"production_provision_ingest_claim_commit_publication":False,
                      "test_fixtures_are_real_issuer_scanner_durable_storage_or_native":False,"full_document_import":False,
                      "cli_form_action_enabled":False,"native_render_differential":False,"green_rows":0,"p09_complete":False},
            "privacy":{"native_session_started":False,"trust_registry_changed":False,"raw_private_values_or_absolute_paths_present":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        output=path_guard(args.output) if args.output else None;verify=path_guard(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"stored_request_progress_exists")
        value=record();raw=old.old.original.old.prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"stored_request_progress_reproduction_mismatch")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,old.history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"stored_request_progress_failed"}));return 2
    print(json.dumps({"state":"pass","scope":"local_progress_not_full_source_qualification","receipt_sha256":oracle.sha(raw),
                      "receipt_bytes":len(raw),"source_pins":len(SOURCES),"actual_product_tests":8,"actual_python_guards":4,
                      "whole_original_p45_reexecuted":False,"native_session_started":False}));return 0

if __name__=="__main__":raise SystemExit(main())
