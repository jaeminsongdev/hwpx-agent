#!/usr/bin/env python3
"""Full coupled-color source successor; no native or form publication authority."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import reproduce_pre_native_form_color as history

progress,io=history.progress,history.progress.io
ROOT=history.ROOT
LOCAL_SHA="e4cc17f1d6382e04bdf09d6c19235a48a188d626704c4acbdae37632766d32a3"
CAPSULE="implementation/p09/evidence/p09-48-native-form-color-preparation.source-qualified.v1.json"
POLICY="implementation/p09/P09-48_NATIVE_FORM_COLOR_PREPARATION_QUALIFICATION_POLICY.md"
SOURCES=(*progress.SOURCES,progress.CAPSULE,history.ORIGINAL,
    "tools/p09/reproduce_pre_native_form_color.py","tools/p09/tests/test_pre_native_form_color_reproduction.py",
    "tools/p09/qualify_native_form_color_preparation.py","tools/p09/tests/test_native_form_color_preparation_qualification.py",POLICY)
GUARD_MODULES=("tools.p09.tests.test_pre_native_form_color_reproduction","tools.p09.tests.test_native_form_color_preparation_qualification")
GUARDS={
    "test_authentic_complete_source_view_overrides_predecessor_with_original_p46_pins",
    "test_exact_original_cli_protocol_rejects_missing_extra_coerced_failure_and_duplicate",
    "test_short_source_boundary_rejects_workspace_root_other_parent_and_other_name",
    "test_original_launch_retains_installed_dependencies_without_environment_or_authority_override",
    "test_diagnostic_protocol_is_not_cli_success_and_rejects_duplicate_missing_or_exit_mismatch",
    "test_frozen_local_receipt_and_original_sources_are_not_reclassified",
    "test_complete_current_graph_uses_live_color_roots_and_whole_original_graph",
    "test_raw_archives_and_frozen_predecessor_receipts_remain_exact",
    "test_guard_protocol_rejects_missing_duplicate_extra_filter_skip_or_failed_body",
    "test_exclusive_output_boundary_rejects_old_private_alias_and_traversal_paths",
    "test_diagnostic_and_original_cli_claims_remain_distinct"}

def require(value,code):progress.require(value,code)

def pins():
    require(len(SOURCES)==len(set(SOURCES))==23,"color_qualification_source_inventory")
    return {name:io.sha(io.read(ROOT/name)) for name in SOURCES}

def local_receipt():
    raw=io.checked(ROOT/progress.CAPSULE,LOCAL_SHA)
    require(len(raw)==20860,"color_qualification_local_receipt_bytes")
    value=json.loads(raw,object_pairs_hook=io.duplicate_guard)
    require(progress.pins()==value["source_sha256"] and progress.preserve()==value["preservation"],"color_qualification_local_preservation_changed")
    return raw,value

def current_graph():
    _,original,_=history.select()
    expected={**original,**pins()}
    # All old graph inputs are actual current files except two original roots;
    # those are declared new roots, with whole raw inverses separately preserved.
    require(len(expected)<=history.LIMIT_FILES,"color_qualification_graph_inventory")
    paths=[history.progress.original.history.relative(name) for name in expected]
    require(len({str(path).casefold() for path in paths})==len(paths),"color_qualification_graph_alias")
    total=0
    for name,digest in expected.items():
        raw=history.progress.original.public.checked(ROOT/name,digest,history.MAX_SOURCE)
        total+=len(raw);require(total<=history.LIMIT_BYTES,"color_qualification_graph_bytes")
    return {"source_sha256":expected,"files":len(expected),"bytes":total,
            "current_live_color_exports_and_all_original_transitive_inputs_bound":True,
            "original_pre_color_root_archive_is_not_substituted_for_current_root":True}

def evidence_path(path):
    target=path.absolute()
    require(target==ROOT/CAPSULE and ".." not in path.parts,"color_qualification_output_boundary")
    # Existing reader checks links for every real ancestor without creating files.
    io.read(ROOT/progress.CAPSULE)
    if target.exists():io.read(target)
    return target

def guard_protocol(code,stdout,stderr):
    text=stderr.decode("utf-8",errors="strict")
    # Windows subprocess stderr uses CRLF; parse actual lines, not a LF-only $
    # boundary. Names/counts/outcome/summary remain exact, with no failed skips.
    pattern=r"(test_[a-z0-9_]+) \(tools\.p09\.tests\.(test_[a-z0-9_]+)\.([A-Za-z]+)\.([a-z0-9_]+)\) \.\.\. ok"
    matches=[match.groups() for line in text.splitlines() if (match:=re.fullmatch(pattern,line))]
    names=[row[0] for row in matches]
    require(code==0 and not stdout.strip() and len(names)==11 and set(names)==GUARDS
        and all(row[0]==row[3] for row in matches) and text.count(" ... ")==11
        and re.search(r"\nRan 11 tests in [0-9.]+s\s+OK\s*$",text)
        and "skipped" not in text,"color_qualification_guards_failed")
    return {"passed":11,"failed":0,"errors":0,"skipped":0,"names":sorted(names),"actually_invoked":True}

def guards():
    actual=progress.call([sys.executable,"-E","-B","-X","utf8","-m","unittest","-v",*GUARD_MODULES])
    return guard_protocol(actual.returncode,actual.stdout,actual.stderr)

def qualify():
    before=pins();preserved=progress.preserve();graph=current_graph();raw_local,_=local_receipt()
    value=progress.record()
    require(io.canonical(value)==raw_local,"color_qualification_whole_local_reproduction_changed")
    actual_guards=guards()
    # This invokes the unchanged ORIGINAL CLI and compares its exact full result.
    # It must finish the full original P46/P45/P44/P43/P42 chain; no diagnostic proxy.
    replay=history.reproduce()
    require(before==pins() and graph==current_graph() and preserved==progress.preserve(),"color_qualification_inputs_changed")
    return {"schema_version":"hwpx-agent.p09-48-coupled-color-source-successor/v1",
        "state":"actual_coupled_color_product_preparation_and_complete_source_successor_qualified_non_green",
        "source_sha256":before,"complete_current_source_graph":graph,
        "original_local_progress_sha256":LOCAL_SHA,"entire_local_progress_reexecuted_byte_exact":True,
        "original_local_preservation":preserved,"actual_sdk_tests":value["actual_sdk_tests"],
        "actual_product_tests":value["actual_product_tests"],"actual_entire_product_library_tests":value["actual_entire_product_library_tests"],
        "actual_python_source_guards":actual_guards,"warnings_denied_clippy":value["warnings_denied_clippy"],
        "actual_current_predecessor_failures":value["actual_current_predecessor_failures"],
        "complete_original_pre_color_reproduction":replay,
        "claims":{"full_color_source_successor_qualified":True,"whole_original_p46_and_nested_predecessors_reexecuted":True,
            "current_old_predecessor_verifiers_pass":False,"native_color_name_tab_fix_qualified":False,
            "native_defaults_input_date_protection_validation":"not_run","signed_form_route_manifest_publication":False,
            "stored_source_access_integration":False,"atomic_cas_or_product_idempotency":False,
            "cli_or_full_document_import":False,"render":"not_run","product_differential":"not_run",
            "green_rows":0,"p09_complete":False},
        "privacy":{"raw_document_values_or_absolute_private_paths_present":False,"native_session_started":False,
            "original_sources_receipts_tests_locks_machine_settings_or_dependencies_changed":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output",type=Path);mode.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        path=evidence_path(args.output or args.verify);require(not args.output or not path.exists(),"color_qualification_exists")
        value=qualify();raw=io.canonical(value)
        if args.output:
            with path.open("xb") as stream:stream.write(raw)
        else:require(io.read(path)==raw,"color_qualification_fresh_whole_result_changed")
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,history.subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch("[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2
    print(json.dumps({"state":"pass","scope":"full_color_source_successor_not_native_or_form_publication",
        "sha256":io.sha(raw),"bytes":len(raw),"source_pins":len(SOURCES),"current_graph_files":value["complete_current_source_graph"]["files"],
        "actual_sdk_tests":10,"actual_product_tests":4,"actual_python_source_guards":11,
        "whole_original_p46_reexecuted":True,"native_session_started":False,"green_rows":0}));return 0

if __name__=="__main__":raise SystemExit(main())
