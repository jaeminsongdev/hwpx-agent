#!/usr/bin/env python3
"""Coupled color/product progress only; complete archived source replay/native remain pending."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import diagnose_native_form_readback as io
from tools.p09 import qualify_native_owned_exit_wait_environment as admission
from tools.p09 import qualify_stored_product_request as original

ROOT=io.ROOT
CAPSULE="implementation/p09/evidence/p09-48-native-form-color-preparation.progress.v1.json"
ARCHIVE="implementation/p09/source-archive/p09-48-pre-native-form-color/"
CHANGED={"crates/hwpx-package/src/lib.rs":("lib.rs","bf31a1b7ac34a11724280fd498a722a28bced3c2a264a48a101c058f0ab262bd",b"pub mod native_form_color;\n"),
         "crates/product-cli/src/lib.rs":("product-lib.rs","f6df1cf2480264046e1881a7c3fb297f6a11640ce3608ba7c8ed91cba40841a2",b"pub mod form_color_preparation;\n")}
PREVIOUS={"implementation/p09/evidence/p09-46-stored-product-request.source-qualified.v1.json":("2d4386dda7efe9a9d9e6ab5efaa301816756818a3cb49c71129408f7fdb398ac","source_sha256"),
          io.RECOVERY:(io.RECOVERY_SHA,"source_sha256"),io.CAPSULE:("f93d38bd4ef0adceb55af0ee2b1adadbdf29c2081d93b7c6b34ab6db975a7e28","immediate_source_sha256")}
SOURCES=(*CHANGED,*(ARCHIVE+name for name,_,_ in CHANGED.values()),
    "crates/hwpx-package/src/native_form_color.rs","crates/hwpx-package/tests/native_form_color_public.rs",
    "crates/product-cli/src/form_color_preparation.rs","crates/product-cli/tests/form_color_preparation.rs",
    "tools/p09/record_native_form_color_preparation.py","tools/p09/tests/test_native_form_color_preparation_progress.py",
    "implementation/p09/P09-48_NATIVE_FORM_COLOR_PREPARATION_POLICY.md",
    "tools/p09/diagnose_native_form_readback.py","tools/p09/qualify_native_owned_exit_wait_environment.py",
    "tools/p09/qualify_stored_product_request.py","Cargo.lock",io.MANIFEST)
SDK_TESTS={"all_fifteen_complete_inputs_and_arbitrary_exact_colors_preserve_full_other_control_state",
    "cloned_styles_keep_every_font_metric_effect_and_existing_catalog_semantic_field",
    "exact_style_reuse_and_repeated_preparation_do_not_duplicate_catalogs",
    "external_verification_rejects_changed_foreground_header_and_unrelated_metadata",
    "duplicate_missing_oversized_color_and_empty_requests_are_rejected",
    "stale_source_and_swapped_policies_maps_fail_before_output",
    "finite_limits_and_debug_output_do_not_disclose_private_controls",
    "document_protection_signal_is_not_bypassed_by_catalog_color_preparation",
    "nonform_section_before_target_is_preserved_without_section_iterator_misalignment",
    "two_global_targets_share_one_semantically_exact_style_without_font_approximation"}
PRODUCT_TESTS={"real_product_preparation_matches_whole_public_sdk_for_all_fifteen_inputs_but_denies_signed_route",
    "fresh_full_source_and_valid_map_policy_substitution_invalidate_old_preparation",
    "empty_duplicate_unknown_and_out_of_range_product_intents_fail_closed",
    "canonical_retry_and_redacted_receipts_are_not_publication_or_product_idempotency"}
LIB_TESTS={"form_color_preparation::tests::bounded_hash_writer_rejects_overrun_before_hash_or_byte_count_change",
    "form_product_request::tests::finite_json_writer_rejects_first_oversize_without_append",
    "form_product_request::tests::finite_json_writer_rejects_overrun_before_any_partial_append",
    "form_value_preparation::tests::private_binding_writer_checks_limit_before_hash_or_count_change",
    "form_value_preparation::tests::private_binding_writer_rejects_arithmetic_overflow_without_mutation",
    "tests::route_attestation_signature_and_scope_are_required"}

def require(value,code):io.require(value,code)

def pins():return {name:io.sha(io.read(ROOT/name)) for name in SOURCES}

def inverse(name,raw):
    archived,digest,delta=CHANGED[name]
    before=io.checked(ROOT/(ARCHIVE+archived),digest)
    require(raw.count(delta)==1 and raw.replace(delta,b"",1)==before,"color_progress_complete_inverse_changed")
    return digest

def preserve():
    inverses={name:inverse(name,io.read(ROOT/name)) for name in CHANGED}
    receipts={};counts={}
    for name,(digest,field) in PREVIOUS.items():
        value=json.loads(io.checked(ROOT/name,digest),object_pairs_hook=io.duplicate_guard)
        for path,pin in value[field].items():
            if path in CHANGED:
                require(pin==CHANGED[path][1],"color_progress_predecessor_archive_origin")
                inverse(path,io.read(ROOT/path))
            else:io.checked(ROOT/path,pin)
        receipts[name]=digest;counts[name]=len(value[field])
    recovery=json.loads(io.checked(ROOT/io.RECOVERY,io.RECOVERY_SHA),object_pairs_hook=io.duplicate_guard)
    native=io.native_pins(recovery)
    saved=json.loads(io.checked(ROOT/admission.CAPSULE,"ec22c16820450168acadfe38aa4f0faeb0ce1dc134457053caa963207922f76f"),object_pairs_hook=io.duplicate_guard)
    old=admission.prior_attempts()
    require(old==saved["prior_r04_admission"]["prior_partial_batch_preserved"],"color_progress_old_native_evidence_changed")
    return {"two_complete_root_inverses":inverses,"predecessor_receipts_sha256":receipts,
            "predecessor_direct_pin_counts":counts,"all_predecessor_direct_pins_or_declared_archive_origins_exact":True,
            "all_seventy_five_native_file_pins":native,"old_partial_batch_is_exact":True,
            "whole_archived_predecessor_capsules_reexecuted":False}

def rust_protocol(raw,names):
    text=raw.decode("utf-8",errors="strict")
    actual=re.findall(r"^test ([a-z_:]+) \.\.\. ok$",text,re.M)
    require(len(actual)==len(names) and set(actual)==names and text.count(" ... ")==len(names)
        and re.search(rf"test result: ok\. {len(names)} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;",text)
        and "FAILED" not in text,"color_progress_rust_protocol")
    return {"passed":len(names),"failed":0,"ignored":0,"filtered":0,"names":sorted(actual),"actually_invoked":True}

def call(args):
    result=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return result

def passed(args):
    result=call(args);require(result.returncode==0,"color_progress_actual_command_failed");return result.stdout

def old_failures():
    results={}
    attempts=(("p46",[sys.executable,"-B","-X","utf8","tools/p09/qualify_stored_product_request.py","--verify",next(iter(PREVIOUS))],"stored_request_full_source_qualification_failed"),
              ("r06",[sys.executable,"-B","-X","utf8","tools/p09/qualify_native_form_completed_batch_recovery.py","--verify",io.RECOVERY],"public_export_source_identity_changed"),
              ("p47",[sys.executable,"-B","-X","utf8","tools/p09/diagnose_native_form_readback.py","--verify",io.CAPSULE],"diagnosis_fresh_whole_result_changed"))
    for key,args,code in attempts:
        result=call(args)
        require(result.returncode==2 and not result.stderr.strip() and json.loads(result.stdout,object_pairs_hook=io.duplicate_guard)=={"state":"fail","error_code":code},"color_progress_old_failure_changed")
        results[key]={"state":"fail","error_code":code,"exit_code":2,"actually_invoked":True,"original_guard_or_capsule_unchanged":True}
    try:original.progress.preserve()
    except ValueError as error:require(str(error)=="public_export_source_identity_changed","color_progress_old_cause_changed")
    else:raise ValueError("color_progress_original_current_failure_missing")
    results["p46_actual_preservation_cause"]={"state":"fail","error_code":"public_export_source_identity_changed","actually_invoked":True}
    return results

def target(path):
    value=path.absolute();require(value==ROOT/CAPSULE and ".." not in path.parts,"color_progress_output_boundary")
    # Existing readonly helper enforces links for all ancestors; check a real parent file.
    io.read(ROOT/io.RECOVERY)
    if value.exists():io.read(value)
    return value

def record():
    before=pins();origins=preserve()
    sdk=rust_protocol(passed(["cargo","test","--locked","--offline","-p","hwpx-package","--test","native_form_color_public"]),SDK_TESTS)
    product=rust_protocol(passed(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--test","form_color_preparation"]),PRODUCT_TESTS)
    library=rust_protocol(passed(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--lib"]),LIB_TESTS)
    passed(["cargo","clippy","--locked","--offline","-p","hwpx-package","--test","native_form_color_public","-p","hwpx-agent-cli","--test","form_color_preparation","--lib","--","-D","warnings"])
    passed([sys.executable,"-B","-m","unittest","-v","tools.p09.tests.test_native_form_color_preparation_progress"])
    failures=old_failures()
    require(pins()==before and preserve()==origins,"color_progress_before_after_changed")
    return {"schema_version":"hwpx-agent.p09-coupled-color-product-progress/v1",
            "state":"actual_coupled_color_and_product_preparation_pass_full_source_and_native_pending",
            "source_sha256":before,"preservation":origins,"actual_sdk_tests":sdk,"actual_product_tests":product,
            "actual_entire_product_library_tests":library,"warnings_denied_clippy":True,"actual_current_predecessor_failures":failures,
            "claims":{"exact_arbitrary_rgb_and_complete_style_dependency_preparation":True,
                "actual_product_library_consumes_real_complete_sdk":True,"ninety_pinned_input_color_combinations_executed":True,
                "all_fifteen_product_candidates_whole_sdk_exact":True,"whole_archived_source_successor_qualified":False,
                "native_color_fix_qualified":False,"native_name_tab_fix_qualified":False,"new_native_session_started":False,
                "signed_form_route_or_publication":False,"atomic_cas_or_product_idempotency":False,"full_document_import":False,
                "render":"not_run","product_differential":"not_run","green_rows":0,"p09_complete":False},
            "privacy":{"raw_document_values_or_absolute_private_paths_present":False,"original_sources_evidence_or_machine_settings_changed":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        path=target(args.output or args.verify);require(not args.output or not path.exists(),"color_progress_receipt_exists")
        value=record();raw=io.canonical(value)
        if args.output:
            with path.open("xb") as stream:stream.write(raw)
        else:require(io.read(path)==raw,"color_progress_fresh_result_changed")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch("[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":"local_product_preparation_not_full_source_or_native","bytes":len(raw),"sha256":io.sha(raw),"sdk_tests":10,"product_tests":4,"product_library_tests":6,"native_fix_qualified":False}));return 0

if __name__=="__main__":raise SystemExit(main())
