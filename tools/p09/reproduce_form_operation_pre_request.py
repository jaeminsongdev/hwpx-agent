#!/usr/bin/env python3
"""Whole unchanged P09-43 capsule replay in a bounded authentic physical view."""
from __future__ import annotations
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
if not __package__: sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import record_product_form_request_progress as progress

ROOT=progress.ROOT
original,oracle,public=progress.original,progress.oracle,progress.public
LIMIT_FILES=1800
LIMIT_BYTES=64*1024*1024
SOURCE_BYTES=16*1024*1024
BAD_PARTS={".git","target","node_modules","__pycache__"}
EXPECTED_RESULT={"state":"pass","qualification_sha256":progress.PREDECESSOR_SHA,
                 "capsule_bytes":217587,"source_pins":8,"actual_product_operation_cases":9,
                 "whole_output_pairs":5,"complete_original_p42_capsule_reexecuted":True,
                 "native_session_started":False,"green_rows":0}


def relative(name):
    oracle.require(type(name) is str and name and ":" not in name,
                   "product_request_view_relative_path")
    # Frozen Windows evidence has 22 backslash-separated relative keys. Keep
    # those exact manifest keys; validate both separators without path aliases.
    normalized=name.replace("\\","/")
    parts=normalized.split("/")
    oracle.require(not PurePosixPath(normalized).is_absolute()
                   and not any(part in ("",".","..") or part in BAD_PARTS for part in parts),
                   "product_request_view_relative_path")
    return Path(*parts)


def select():
    guard=progress.preserve()
    raw=public.checked(ROOT/original.CAPSULE,progress.PREDECESSOR_SHA,2*1024*1024)
    capsule=json.loads(raw,object_pairs_hook=oracle.duplicate_guard)
    old_view=capsule["complete_original_product_preparation_reproduction"]["source_sha256"]
    oracle.require(len(old_view)==1471 and set(capsule["source_sha256"])==set(original.SOURCES),
                   "product_request_view_original_inventory")
    manifest={**old_view,**capsule["source_sha256"],original.CAPSULE:progress.PREDECESSOR_SHA}
    origins={name:progress.ARCHIVE if name==progress.LIB else name for name in manifest}
    oracle.require(len(manifest)<=LIMIT_FILES and not any("p09-44" in name or "form_product_request" in name
                                                       for name in manifest),"product_request_view_inventory")
    oracle.require(len({str(relative(name)).casefold() for name in manifest})==len(manifest),
                   "product_request_view_path_alias")
    copied={}
    total=0
    for name,digest in sorted(manifest.items()):
        relative(name); relative(origins[name])
        value=public.checked(ROOT/origins[name],digest,SOURCE_BYTES)
        total+=len(value)
        oracle.require(total<=LIMIT_BYTES,"product_request_view_bytes")
        copied[name]=value
    oracle.require(progress.preserve()==guard,"product_request_view_origin_changed")
    return copied,manifest,origins


def inventory(directory,manifest):
    return {name:oracle.sha(public.bounded_bytes(directory/relative(name),SOURCE_BYTES)) for name in manifest}


def validate_result(code,stdout,stderr):
    oracle.require(len(stdout)<=128*1024 and len(stderr)<=1024*1024,"product_request_view_process_limit")
    result=json.loads(stdout.decode("utf-8",errors="strict"),object_pairs_hook=oracle.duplicate_guard)
    canonical=original.old.prior.q.shared.lifecycle.canonical_bytes
    oracle.require(code==0 and canonical(result)==canonical(EXPECTED_RESULT),
                   "product_request_view_whole_original_replay_failed")


def reproduce():
    copied,manifest,origins=select()
    base=ROOT/"fixtures/target-build"
    oracle.no_links(base)
    with tempfile.TemporaryDirectory(prefix="p09-44-source-view-",dir=base) as temporary:
        directory=Path(temporary)
        oracle.no_links(directory)
        oracle.require(directory.resolve().parent==base.resolve() and not any(directory.iterdir()),
                       "product_request_view_scratch_boundary")
        for name,value in copied.items():
            path=directory/relative(name)
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as stream:stream.write(value)
        oracle.require(inventory(directory,manifest)==manifest,"product_request_view_copy_identity")
        environment=dict(os.environ)
        for key in ("PYTHONPATH","PYTHONHOME","PYTHONSTARTUP",original.old.prior.old.ENVIRONMENT):
            environment.pop(key,None)
        environment["PYTHONDONTWRITEBYTECODE"]="1"
        environment["CARGO_TARGET_DIR"]=str(ROOT/"target/p09-44-pre-request-view")
        command=[sys.executable,"-E","-B",str(directory/"tools/p09/qualify_form_value_operation.py"),
                 "--verify",str(directory/original.CAPSULE)]
        process=subprocess.run(command,cwd=directory,env=environment,capture_output=True,timeout=1200,
                               creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        if process.returncode:
            # Keep values/paths/full logs private. Execute the original body only
            # for bounded code and filename:line diagnostics; no function override.
            diagnostic=subprocess.run([sys.executable,"-E","-B","-c",
                                       "from tools.p09 import qualify_form_value_operation as q; q.qualify()"],
                                      cwd=directory,env=environment,capture_output=True,timeout=1200,
                                      creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            oracle.require(len(diagnostic.stdout)<=128*1024 and len(diagnostic.stderr)<=1024*1024,
                           "product_request_view_diagnostic_limit")
            lines=diagnostic.stderr.decode("utf-8",errors="replace").splitlines()
            print(json.dumps({"diagnostic_codes":[line for line in lines if re.fullmatch(r"ValueError: [a-z0-9_:.\-/]+",line)],
                              "diagnostic_frames":[Path(match.group(1)).name+":"+match.group(2) for line in lines
                                  if (match:=re.fullmatch(r'  File "([^\"]+)", line (\d+), in .+',line))]}))
        validate_result(process.returncode,process.stdout,process.stderr)
        oracle.require(inventory(directory,manifest)==manifest,"product_request_view_sources_changed")
    oracle.require(not Path(temporary).exists(),"product_request_view_scratch_not_cleaned")
    for name,digest in manifest.items():public.checked(ROOT/origins[name],digest,SOURCE_BYTES)
    progress.preserve()
    return {"scope":"complete_physical_original_p43_replay_not_current_old_authority_or_native_pass",
            "capsule_sha256":progress.PREDECESSOR_SHA,"complete_original_capsule_byte_exact_reexecution":True,
            "original_cli_result":EXPECTED_RESULT,"files":len(manifest),"bytes":sum(map(len,copied.values())),
            "source_sha256":manifest,"declared_original_product_archive":progress.ARCHIVE,
            "declared_original_product_sha256":progress.ORIGINAL_LIB,
            "no_function_root_test_source_lock_or_expected_hash_override":True,
            "only_logical_product_library_uses_declared_archive":all(actual==(progress.ARCHIVE if name==progress.LIB else name)
                                                                    for name,actual in origins.items()),
            "python_environment_ignored_no_bytecode":True,"installed_user_and_system_site_dependencies_enabled":True,
            "owned_scratch_cleaned":True,"native_session_started":False}


if __name__=="__main__":
    try:value=reproduce()
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"product_request_whole_original_replay_failed"}));raise SystemExit(2)
    print(json.dumps({"state":"pass","complete_original_capsule_reexecution":True,
                      "capsule_sha256":value["capsule_sha256"],"files":value["files"],"bytes":value["bytes"],
                      "native_session_started":False}))
