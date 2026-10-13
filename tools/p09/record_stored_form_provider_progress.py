#!/usr/bin/env python3
"""Actual stored source provider tests/raw preservation; NOT full source qualification."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_product_form_request as old

ROOT=old.ROOT
oracle,public=old.oracle,old.public
ARCHIVE="implementation/p09/source-archive/p09-45-pre-stored-form-provider/"
CAPSULE_SHA="3ad2f371889ff1677db3edf07e4f3f530cdc669bc2f0b9e5294044e3be0bb2cb"
CHANGED={
    "crates/product-cli/src/lib.rs":("lib.rs","698f313b3430fca5ef25462ebdff805bdfbe58a562f020e77276b3f0f6401fbb"),
    "crates/product-cli/Cargo.toml":("product-Cargo.toml","b2a8d2580e5891d0e88dc2bc5a942942863efda94fbabf91cecc9bacd04816a5"),
    "Cargo.lock":("Cargo.lock","eec4be0c6587e11807f12083b8563d154782fb14b5937ce693eabceda5316aa8"),
    "crates/revision-service/src/types.rs":("revision-types.rs","bea6d44a4685dd64211788f0aa2a1d043e8a738f3d866b37f0cd1f92e6fe19da"),
}
RECEIPT="implementation/p09/evidence/p09-45-stored-form-provider.progress.v1.json"
SOURCES=(*CHANGED,*(ARCHIVE+name for name,_ in CHANGED.values()),"crates/product-cli/src/form_stored_provider.rs",
         "crates/product-cli/tests/form_stored_provider.rs","tools/p09/record_stored_form_provider_progress.py",
         "implementation/p09/P09-45_STORED_FORM_PROVIDER_POLICY.md")
TESTS={
    "stored_actual_capture_uses_real_sealed_node_acl_aead_and_original_compiler_without_publish",
    "stored_all_five_kinds_required_radio_defaults_empty_clear_match_whole_predecessor",
    "stored_fresh_acl_revocation_blocks_preparation_verification_and_route",
    "stored_real_head_advance_rejects_old_preparation_even_when_actual_artifact_is_unchanged",
    "stored_provider_tenant_subject_scope_branch_document_cannot_be_substituted",
    "stored_quarantine_unverified_wrong_artifact_kind_and_corrupt_ciphertext_never_prepare",
    "stored_fresh_map_policy_access_and_malformed_input_fail_without_ingest_or_commit",
    "stored_receipts_debug_and_fixed_errors_do_not_expose_source_subject_artifact_or_paths",
}
GETTERS=b'''    /// Exact project owning this sealed node; not caller-supplied artifact routing.
    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    /// Immutable committed result, used as the next revision's actual source.
    #[must_use]
    pub const fn result_artifact_id(&self) -> ArtifactId {
        self.result_artifact_id
    }

'''


def preserve():
    originals={name:public.checked(ROOT/(ARCHIVE+file),digest,2*1024*1024) for name,(file,digest) in CHANGED.items()}
    for name,raw in originals.items():
        current=public.bounded_bytes(ROOT/name,2*1024*1024)
        if name==old.progress.LIB:
            delta=b"pub mod form_stored_provider;\n"
            oracle.require(current.count(delta)==1 and current.replace(delta,b"",1)==raw,"stored_provider_lib_inverse")
        elif name=="crates/product-cli/Cargo.toml":
            for package in ("artifact-service","revision-service"):
                delta=f'{package} = {{ version = "0.1.0", path = "../{package}" }}\n'.encode()
                oracle.require(current.count(delta)==1,"stored_provider_cargo_inverse")
                current=current.replace(delta,b"",1)
            oracle.require(current==raw,"stored_provider_cargo_inverse")
        elif name=="Cargo.lock":
            marker=b'name = "hwpx-agent-cli"\nversion = "0.1.0"\ndependencies = [\n'
            oracle.require(raw.count(marker)==current.count(marker)==1,"stored_provider_lock_inverse")
            start=current.index(marker)+len(marker);end=current.index(b"]",start)
            section=current[start:end]
            for delta in (b' "artifact-service",\n',b' "revision-service",\n'):
                oracle.require(section.count(delta)==1,"stored_provider_lock_inverse");section=section.replace(delta,b"",1)
            oracle.require(current[:start]+section+current[end:]==raw,"stored_provider_lock_inverse")
        else:
            oracle.require(current.count(GETTERS)==1 and current.replace(GETTERS,b"",1)==raw,"stored_provider_revision_node_inverse")
    raw=public.checked(ROOT/old.CAPSULE,CAPSULE_SHA,2*1024*1024)
    capsule=json.loads(raw,object_pairs_hook=oracle.duplicate_guard)
    oracle.require(set(capsule["source_sha256"])==set(old.SOURCES),"stored_provider_original_eleven_sources")
    for name,digest in capsule["source_sha256"].items():
        actual=ARCHIVE+CHANGED[name][0] if name in CHANGED else name
        public.checked(ROOT/actual,digest,2*1024*1024)
    manifest=capsule["complete_original_form_operation_reproduction"]["source_sha256"]
    oracle.require(len(manifest)==1479,"stored_provider_original_view_inventory")
    total=0
    for name,digest in manifest.items():
        old.history.relative(name)
        actual=old.progress.ARCHIVE if name==old.progress.LIB else ARCHIVE+CHANGED[name][0] if name in CHANGED else name
        total+=len(public.checked(ROOT/actual,digest,old.history.SOURCE_BYTES))
        oracle.require(total<=old.history.LIMIT_BYTES,"stored_provider_original_view_bound")
    try:old.qualify()
    except ValueError as error:
        oracle.require(str(error)=="product_request_original_complete_inverse","stored_provider_current_failure_changed")
    else:raise ValueError("stored_provider_original_current_failure_missing")
    return {"original_p44_capsule_sha256":CAPSULE_SHA,"original_eleven_raw_sources_preserved":True,
            "original_physical_view_files":1479,"original_physical_view_bytes":total,
            "all_original_physical_view_raw_origins_preserved":True,"four_unique_complete_raw_inverses_exact":True,
            "actual_original_current_source_failure":{"state":"fail","error_code":"product_request_original_complete_inverse","actually_invoked":True},
            "whole_original_p44_physical_reexecution_this_successor":False,"full_source_successor_qualification":"not_run_pending"}


def record():
    before={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES}
    guard=preserve()
    code,stdout,_=old.original.old.prior.run(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--test","form_stored_provider"])
    oracle.require(code==0,"stored_provider_actual_tests_failed")
    tests=old.original.old.prior.protocol(stdout,TESTS,8)
    oracle.require(guard==preserve() and before=={name:oracle.sha(public.bounded_bytes(ROOT/name,2*1024*1024)) for name in SOURCES},"stored_provider_sources_changed")
    return {"schema_version":"hwpx-agent.p09-45-stored-form-provider-progress/v1",
            "state":"actual_service_source_and_local_tests_pass_full_source_qualification_pending","source_sha256":before,
            "preservation":guard,"actual_stored_provider_product_tests":tests,
            "claims":{"actual_revision_artifact_services_and_original_form_compiler_connected":True,
                      "whole_five_output_pairs_predecessor_exact":True,"normal_artifact_service_access_audit_emitted":True,
                      "production_ingest_provision_claim_commit_or_publication":False,"scanner_keys_and_sealed_metadata_setup_test_fixture_only":True,
                      "real_scanner_external_issuer_postgres_durability":False,"full_source_successor_qualified":False,
                      "whole_original_p44_reexecuted":False,"atomic_cas_execution_idempotency":False,
                      "signed_form_authority_or_execution_manifest":False,"full_document_import":False,"cli_form_action_enabled":False,
                      "native_execution":False,"current_legacy_aggregate_pass":False,"green_rows":0,"p09_complete":False},
            "privacy":{"raw_values_keys_subjects_artifact_ids_or_absolute_paths_present":False,
                       "native_session_started":False,"trust_or_registry_changed":False}}


def path_guard(path):
    target=path.absolute()
    oracle.require(target==ROOT/RECEIPT and ".." not in path.parts,"stored_provider_progress_boundary")
    oracle.no_links(target.parent)
    if target.exists():oracle.no_links(target)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path)
    args=parser.parse_args()
    try:
        output=path_guard(args.output) if args.output else None;verify=path_guard(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(),"stored_provider_progress_exists")
        value=record();raw=old.original.old.prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:oracle.require(public.bounded_bytes(verify,2*1024*1024)==raw,"stored_provider_progress_reproduction_mismatch")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,old.history.subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"stored_provider_progress_failed"}));return 2
    print(json.dumps({"state":"pass","scope":"local_progress_not_full_source_qualification","receipt_sha256":oracle.sha(raw),
                      "receipt_bytes":len(raw),"source_pins":len(SOURCES),"actual_product_tests":8,
                      "full_source_qualification":"not_run_pending","native_session_started":False}));return 0


if __name__=="__main__":raise SystemExit(main())
