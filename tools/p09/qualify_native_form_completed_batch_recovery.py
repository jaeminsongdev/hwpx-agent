#!/usr/bin/env python3
"""Independent full r05 observation recovery; never original dispatch success or Gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_owned_exit_wait_environment as admission
from tools.p09 import run_native_owned_exit_wait_environment_batch as dispatcher

ROOT=admission.ROOT
old,prior,q,binding,public=admission.old,admission.prior,admission.q,admission.binding,admission.public
CAPSULE="implementation/p09/evidence/p09-36-native-form-complete-recovery.r06.json"
ADMISSION_SHA="ec22c16820450168acadfe38aa4f0faeb0ce1dc134457053caa963207922f76f"
SOURCES=("tools/p09/qualify_native_form_completed_batch_recovery.py",
         "tools/p09/tests/test_native_form_completed_batch_recovery.py",
         "implementation/p09/P09-36_NATIVE_COMPLETED_BATCH_RECOVERY_POLICY.md",
         admission.CAPSULE,"tools/p09/run_native_owned_exit_wait_environment_batch.py",
         "tools/p09/qualify_native_owned_exit_wait_environment.py")
GUARDS={"test_frozen_r05_sources_and_actual_missing_top_level_key_are_preserved",
        "test_all_fifteen_actual_traces_seventy_five_files_and_thirty_sessions_are_bound",
        "test_original_trace_binder_rejects_changed_input_identity_without_editing_files",
        "test_actual_public_reader_protocol_retains_failure_and_rejects_forged_digests",
        "test_new_fixed_output_rejects_original_dispatch_bound_private_and_traversal",
        "test_raw_equality_rejects_nonbytes_extra_missing_and_changed_bytes"}

def require(value,code):admission.require(value,code)

def own_pins():return {name:q.sha(public.bounded_bytes(ROOT/name,2097152)) for name in SOURCES}

def frozen_admission():
    raw=public.checked(ROOT/admission.CAPSULE,ADMISSION_SHA,2097152)
    value=json.loads(raw,object_pairs_hook=q.shared.lifecycle.duplicate_guard)
    old.exact(admission.own_pins(),value["source_sha256"],"completed_recovery_r05_sources_changed")
    return raw,value

def dispatch_failure(value):
    require(not (ROOT/admission.DISPATCH).exists() and not (ROOT/admission.BOUND).exists(),"completed_recovery_original_receipt_state_changed")
    source=public.bounded_bytes(ROOT/"tools/p09/run_native_owned_exit_wait_environment_batch.py",65536)
    expression=b'a.old.exact(a.prior_attempts(),admission["prior_partial_batch_preserved"],"owned_exit_dispatch_prior_changed")'
    require(source.count(expression)==1,"completed_recovery_failed_source_changed")
    try:value["prior_partial_batch_preserved"]
    except KeyError as error:
        require(error.args==("prior_partial_batch_preserved",),"completed_recovery_missing_key_changed")
    else:raise ValueError("completed_recovery_original_schema_failure_missing")
    nested=value["prior_r04_admission"]["prior_partial_batch_preserved"]
    old.exact(admission.prior_attempts(),nested,"completed_recovery_original_partial_evidence_changed")
    return {"original_dispatch_receipt_published":False,"original_bound_receipt_published":False,
            "original_dispatch_success_claimed":False,"missing_top_level_key":"prior_partial_batch_preserved",
            "actual_missing_key_exception":"KeyError","actual_schema_lookup_reproduced_without_native_launch":True,
            "correct_nested_prior_batch_is_byte_preserved":True,"failed_dispatcher_source_sha256":q.sha(source)}

def actual_traces():
    manifest=q.shared.lifecycle.checked_json(ROOT/binding.MANIFEST,binding.MANIFEST_SHA)
    records,pins=binding.traces(manifest,admission.PREFIX)
    inventory=binding.session_inventory(records,15)
    require(len(records)==15 and len(pins)==75 and inventory["owned_session_count"]==30
            and inventory["passed_lifecycle_cases"]==15 and inventory["failed_first_open_cases"]==0,
            "completed_recovery_actual_inventory_changed")
    return manifest,records,pins,inventory

def path_guard(path):
    target=path.absolute()
    require(target==ROOT/CAPSULE and ".." not in path.parts,"completed_recovery_output_boundary")
    q.shared.within(target.parent,ROOT/"implementation/p09/evidence")
    if target.exists():q.shared.within(target,ROOT/"implementation/p09/evidence")
    return target

def qualify():
    before=own_pins();raw,recorded=frozen_admission();failure=dispatch_failure(recorded)
    _,records,pins,inventory=actual_traces();dispatcher.hwp_zero()
    # COMPLETE unchanged r05 admission (including complete r04/r03/r02 proofs)
    # is really executed, not substituted with frozen hashes or the narrow tests.
    fresh=admission.qualify();prior.raw_equal(q.shared.lifecycle.canonical_bytes(fresh),raw)
    # Unchanged current diagnostic binder executes the real public Rust reader,
    # original strict verifier and independent complete projection on all30 stages.
    observed=old.bind(admission.PREFIX)
    old.exact(observed["native_evidence_sha256"],pins,"completed_recovery_actual_reader_evidence_changed")
    old.exact(observed["session_inventory"],inventory,"completed_recovery_session_inventory_changed")
    require(len(observed["cases"])==15 and all(row["lifecycle"]=="pass" for row in observed["cases"]),"completed_recovery_partial_batch_refused")
    guards=admission.previous.guards("tools.p09.tests.test_native_form_completed_batch_recovery","CompletedBatchRecoveryTests",GUARDS)
    old.exact(actual_traces()[2],pins,"completed_recovery_native_files_changed")
    old.exact(dispatch_failure(recorded),failure,"completed_recovery_failure_changed")
    frozen_admission();dispatcher.hwp_zero()
    old.exact(own_pins(),before,"completed_recovery_sources_changed")
    return {"schema_version":"hwpx-agent.p09-native-completed-batch-recovery/v1",
            "state":"independently_recovered_complete_r05_actual_observations_non_green",
            "prefix":admission.PREFIX,"source_sha256":before,"admission_sha256":ADMISSION_SHA,
            "whole_original_r05_admission_reexecuted_byte_exact":True,
            "original_dispatch_schema_failure_retained":failure,"native_evidence_sha256":pins,
            "session_inventory":inventory,"actual_native_batch":observed,"actual_recovery_source_guards":guards,
            "harness_sha256":admission.HARNESS_SHA,
            "claims":{"all_fifteen_actual_trace_artifact_sessions_independently_bound":True,
                      "all_thirty_real_public_reader_and_independent_projection_stages_attempted":True,
                      "recovery_is_original_dispatch_success_or_original_bound_receipt":False,
                      "native_semantics_or_color_name_repair_qualified":False,
                      "native_normalization_or_visual_acceptance_qualified":False,
                      "render":"not_run","product_differential":"not_run","signed_production_route":False,
                      "old_authority_or_full_source_pass":False,"green_rows":0,"p09_complete":False},
            "privacy":{"new_native_session_started":False,"computer_use_click_or_type_invoked":False,
                       "permission_click_attestation":"not_attested","raw_document_values_present":False,
                       "absolute_private_paths_present":False,"machine_settings_trust_or_security_changed":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        output=path_guard(args.output) if args.output else None;verify=path_guard(args.verify) if args.verify else None
        require(not output or not output.exists(),"completed_recovery_receipt_exists")
        value=qualify();raw=q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream:stream.write(raw)
        if verify:prior.raw_equal(public.bounded_bytes(verify,2097152),raw)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,admission.subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":value["state"],"sha256":q.sha(raw),"bytes":len(raw),
                      "actual_lifecycle_cases":15,"actual_owned_sessions":30,"native_semantics_qualified":False,"green_rows":0}));return 0

if __name__=="__main__":raise SystemExit(main())
